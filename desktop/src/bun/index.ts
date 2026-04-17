import { BrowserWindow, ApplicationMenu } from "electrobun/bun";
import { spawn } from "bun";
import Electrobun from "electrobun/bun";
import { existsSync } from "fs";
import { resolve, join } from "path";

// ── Configuration ────────────────────────────────────────────────────
const PORT = 5001;
const FLASK_URL = `http://127.0.0.1:${PORT}`;

// Find the project root by looking for run.py + rag/ directory
function findProjectRoot(): string {
  // Check env override first
  if (process.env.DOCRAG_ROOT && existsSync(join(process.env.DOCRAG_ROOT, "run.py"))) {
    return resolve(process.env.DOCRAG_ROOT);
  }

  // Known candidates: relative to desktop/ dir, cwd, home
  const candidates = [
    resolve(__dirname, "../../../../.."),       // inside .app bundle: Contents/Resources/app/bun -> up 5
    resolve(__dirname, "../../.."),             // dev: src/bun -> up 3
    resolve(process.cwd(), ".."),              // desktop/ cwd -> up 1
    resolve(process.cwd()),                    // maybe launched from project root
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

// Wait for Flask to be ready
async function waitForServer(url: string, timeoutMs = 15000): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) return;
    } catch {
      // not ready yet
    }
    await Bun.sleep(200);
  }
  throw new Error(`Flask server did not start within ${timeoutMs / 1000}s`);
}

// ── Main ─────────────────────────────────────────────────────────────
async function main() {
  const PROJECT_ROOT = findProjectRoot();
  console.log(`[DocRag] Project root: ${PROJECT_ROOT}`);

  // Find Python
  const python = await findPython(PROJECT_ROOT);
  console.log(`[DocRag] Using Python: ${python}`);

  // Start Flask server
  const flask = spawn({
    cmd: [python, "run.py", "--port", String(PORT)],
    cwd: PROJECT_ROOT,
    stdout: "inherit",
    stderr: "inherit",
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1",
    },
  });

  console.log(`[DocRag] Flask server starting (PID ${flask.pid})...`);

  // Clean up Flask on exit
  const cleanup = () => {
    try {
      flask.kill();
    } catch {
      // already dead
    }
  };

  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);
  process.on("exit", cleanup);

  // Wait for Flask to be ready
  try {
    await waitForServer(`${FLASK_URL}/api/stats`);
  } catch (e) {
    console.error(`[DocRag] ${e}`);
    cleanup();
    process.exit(1);
  }

  console.log(`[DocRag] Flask server ready at ${FLASK_URL}`);

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

  // Open the native window pointing to Flask
  const win = new BrowserWindow({
    title: "DocRag — Document Search",
    url: FLASK_URL,
    frame: {
      width: 1400,
      height: 900,
      x: 100,
      y: 100,
    },
    titleBarStyle: "hiddenInset",
  });

  // Kill Flask when the window closes
  win.on("close", () => {
    cleanup();
  });
}

main().catch((err) => {
  console.error("[DocRag] Fatal:", err);
  process.exit(1);
});
