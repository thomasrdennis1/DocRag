import { BrowserWindow, ApplicationMenu } from "electrobun/bun";
import { spawn, type Subprocess } from "bun";
import Electrobun from "electrobun/bun";
import { existsSync } from "fs";
import { resolve, join } from "path";

// ── Configuration ────────────────────────────────────────────────────
const MAX_RESTARTS = 3;
const RESTART_DELAY_MS = 1500;

// Find the project root by looking for run.py + rag/ directory
function findProjectRoot(): string {
  if (process.env.DOCRAG_ROOT && existsSync(join(process.env.DOCRAG_ROOT, "run.py"))) {
    return resolve(process.env.DOCRAG_ROOT);
  }

  const candidates = [
    resolve(__dirname, "../../../../.."),
    resolve(__dirname, "../../.."),
    resolve(process.cwd(), ".."),
    resolve(process.cwd()),
  ];

  for (const dir of candidates) {
    if (existsSync(join(dir, "run.py")) && existsSync(join(dir, "rag"))) {
      return dir;
    }
  }

  throw new Error(
    "Could not find DocRag project root (run.py + rag/). " +
    "Set DOCRAG_ROOT environment variable to the project directory."
  );
}

// Find a working Python with Flask available
async function findPython(projectRoot: string): Promise<string> {
  const candidates = [
    join(projectRoot, ".venv/bin/python"),
    join(projectRoot, ".venv/bin/python3"),
    "python3",
    "python",
  ];

  for (const py of candidates) {
    try {
      const proc = spawn({
        cmd: [py, "-c", "import flask; print('ok')"],
        stdout: "pipe",
        stderr: "pipe",
        cwd: projectRoot,
      });
      const exitCode = await proc.exited;
      if (exitCode === 0) return py;
    } catch {
      // try next
    }
  }
  throw new Error("No Python with Flask found. Run: pip install -r requirements.txt");
}

// Start Flask with --port 0 and parse the dynamically assigned port from stdout
async function startFlask(
  python: string,
  projectRoot: string,
): Promise<{ proc: Subprocess; port: number; url: string }> {
  const proc = spawn({
    cmd: [python, "run.py", "--port", "0"],
    cwd: projectRoot,
    stdout: "pipe",
    stderr: "inherit",
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1",
    },
  });

  // Read stdout line by line to find DOCRAG_PORT=<n>
  const reader = proc.stdout.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let port = 0;
  const timeout = setTimeout(() => {
    if (!port) {
      console.error("[DocRag] Timed out waiting for Flask to report port");
      try { proc.kill(); } catch {}
    }
  }, 20000);

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    process.stdout.write(chunk); // mirror to console
    buf += chunk;
    const match = buf.match(/DOCRAG_PORT=(\d+)/);
    if (match) {
      port = parseInt(match[1], 10);
      break;
    }
  }
  clearTimeout(timeout);

  if (!port) {
    throw new Error("Flask exited without reporting a port");
  }

  // Release the reader and pipe remaining stdout to console
  reader.releaseLock();
  (async () => {
    const r = proc.stdout.getReader();
    const d = new TextDecoder();
    try {
      while (true) {
        const { done, value } = await r.read();
        if (done) break;
        process.stdout.write(d.decode(value, { stream: true }));
      }
    } catch {}
  })();

  const url = `http://127.0.0.1:${port}`;

  // Wait for Flask to respond
  const start = Date.now();
  while (Date.now() - start < 15000) {
    try {
      const res = await fetch(`${url}/api/stats`);
      if (res.ok) {
        console.log(`[DocRag] Flask server ready at ${url}`);
        return { proc, port, url };
      }
    } catch {
      // not ready yet
    }
    await Bun.sleep(200);
  }

  throw new Error("Flask server did not respond in time");
}

// ── Main ─────────────────────────────────────────────────────────────
async function main() {
  const PROJECT_ROOT = findProjectRoot();
  console.log(`[DocRag] Project root: ${PROJECT_ROOT}`);

  const python = await findPython(PROJECT_ROOT);
  console.log(`[DocRag] Using Python: ${python}`);

  let flask: Subprocess;
  let flaskUrl: string;
  let restarts = 0;
  let shuttingDown = false;

  // Start Flask (initial)
  const initial = await startFlask(python, PROJECT_ROOT);
  flask = initial.proc;
  flaskUrl = initial.url;
  console.log(`[DocRag] Flask PID ${flask.pid} on port ${initial.port}`);

  // Cleanup helper
  const killFlask = () => {
    try { flask.kill(); } catch {}
  };

  process.on("SIGINT", () => { shuttingDown = true; killFlask(); });
  process.on("SIGTERM", () => { shuttingDown = true; killFlask(); });
  process.on("exit", killFlask);

  // Set up native macOS menu
  ApplicationMenu.setApplicationMenu([
    {
      submenu: [{ label: "Quit DocRag", role: "quit" }],
    },
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "pasteAndMatchStyle" },
        { role: "delete" },
        { role: "selectAll" },
      ],
    },
    {
      label: "View",
      submenu: [
        {
          label: "Actual Size",
          action: "zoom-reset",
        },
      ],
    },
  ]);

  // Open the native window
  const win = new BrowserWindow({
    title: "DocRag — Document Search",
    url: flaskUrl,
    frame: {
      width: 1400,
      height: 900,
      x: 100,
      y: 100,
    },
    titleBarStyle: "hiddenInset",
  });

  win.on("close", () => {
    shuttingDown = true;
    killFlask();
  });

  // ── Crash recovery: watch Flask process and restart ──
  (async () => {
    while (!shuttingDown) {
      await flask.exited;
      if (shuttingDown) break;

      restarts++;
      if (restarts > MAX_RESTARTS) {
        console.error(`[DocRag] Flask crashed ${restarts} times, giving up`);
        break;
      }

      console.warn(`[DocRag] Flask exited unexpectedly (restart ${restarts}/${MAX_RESTARTS})`);
      await Bun.sleep(RESTART_DELAY_MS);

      if (shuttingDown) break;

      try {
        const restarted = await startFlask(python, PROJECT_ROOT);
        flask = restarted.proc;
        flaskUrl = restarted.url;
        console.log(`[DocRag] Flask restarted — PID ${flask.pid} on port ${restarted.port}`);

        // Navigate window to new URL (port may have changed)
        win.loadURL(flaskUrl);
      } catch (err) {
        console.error(`[DocRag] Failed to restart Flask:`, err);
      }
    }
  })();
}

main().catch((err) => {
  console.error("[DocRag] Fatal:", err);
  process.exit(1);
});
