"""
Embedded HTML UI for the Document RAG Search application.
"""

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Document RAG Search</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0c0e14;--surface:#13161f;--surface2:#1a1e2e;--border:#252a3a;
  --accent:#7c8cf5;--accent2:#a78bfa;--text:#e2e8f0;--muted:#64748b;
  --green:#22c55e;--red:#ef4444;--amber:#f59e0b;
  --radius:10px;
}
[data-theme="light"]{
  --bg:#f5f7fa;--surface:#ffffff;--surface2:#eef1f6;--border:#d8dce5;
  --accent:#5b6abf;--accent2:#7c5cbf;--text:#1e293b;--muted:#64748b;
  --green:#16a34a;--red:#dc2626;--amber:#d97706;
}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* Header */
header{display:grid;grid-template-columns:auto 1fr auto;align-items:center;padding:12px 20px;border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0}
header .logo{width:36px;height:36px;background:linear-gradient(135deg,var(--accent),var(--accent2));border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px}
header .brand{display:flex;align-items:center;gap:14px}
header h1{font-size:17px;font-weight:600}
header .center-controls{display:flex;align-items:center;justify-content:center;gap:12px}
header .right-controls{display:flex;align-items:center;gap:12px;justify-self:end}
header .sub{font-size:12px;color:var(--muted)}
.theme-btn{background:var(--surface2);border:1px solid var(--border);color:var(--text);border-radius:8px;width:36px;height:36px;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:border-color .15s}
.theme-btn:hover{border-color:var(--accent)}
.badge{font-size:11px;padding:4px 10px;border-radius:20px;background:var(--surface2);border:1px solid var(--border);color:var(--muted)}
.badge.ok{color:var(--green);border-color:rgba(34,197,94,.3)}

/* Tabs */
.tabs{display:flex;gap:0;border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0}
.tab{padding:10px 24px;font-size:13px;font-weight:500;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;transition:all .15s}
.tab:hover{color:var(--text)}
.tab.active{color:var(--accent);border-color:var(--accent)}

/* Panels */
.panel{display:none;flex:1;overflow:hidden}
.panel.active{display:flex;flex-direction:column}

/* Layout */
.layout{display:flex;flex:1;overflow:hidden}

/* Sidebar */
aside{width:260px;flex-shrink:0;border-right:1px solid var(--border);background:var(--surface);display:flex;flex-direction:column;padding:16px;gap:16px;overflow-y:auto}
aside h3{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:8px}
.dir-stat{display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:13px}
.dir-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;background:var(--accent)}
.dir-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dir-count{color:var(--muted);font-size:12px}
.chip{display:block;width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:9px 12px;font-size:12px;text-align:left;cursor:pointer;margin-bottom:6px;transition:border-color .15s,background .15s;line-height:1.4}
.chip:hover{border-color:var(--accent);background:var(--surface)}

/* Mode toggle */
.mode-toggle{display:flex;gap:0;background:var(--surface2);border-radius:8px;border:1px solid var(--border);overflow:hidden}
.mode-btn{flex:1;padding:8px 0;font-size:12px;font-weight:500;text-align:center;cursor:pointer;color:var(--muted);transition:all .15s;border:none;background:none}
.mode-btn.active{background:var(--accent);color:#fff}
.mode-btn:hover:not(.active){color:var(--text)}

/* Direct search results */
.search-results{display:flex;flex-direction:column;gap:10px;padding:4px 0}
.result-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;transition:border-color .15s}
.result-card:hover{border-color:var(--accent)}
.result-header{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.result-rank{background:var(--accent);color:#fff;font-size:11px;font-weight:700;width:24px;height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.result-file{font-size:13px;font-weight:500;flex:1;word-break:break-all}
.result-page{font-size:11px;color:var(--muted);white-space:nowrap}
.result-score{font-size:11px;color:var(--accent);white-space:nowrap;font-weight:600}
.result-text{font-size:13px;line-height:1.65;color:var(--text);white-space:pre-wrap;max-height:200px;overflow-y:auto;background:var(--surface2);border-radius:6px;padding:12px;margin-top:6px}

/* Chat */
main{flex:1;display:flex;flex-direction:column;overflow:hidden}
#chat{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:20px}
.msg{max-width:820px;width:100%}.msg.user{align-self:flex-end}.msg.assistant{align-self:flex-start}
.msg-bubble{padding:14px 18px;border-radius:var(--radius);line-height:1.7;font-size:14px;white-space:pre-wrap}
.user .msg-bubble{background:var(--accent);color:#fff;border-bottom-right-radius:3px}
.assistant .msg-bubble{background:var(--surface);border:1px solid var(--border);border-bottom-left-radius:3px}
.msg-meta{font-size:11px;color:var(--muted);margin-top:5px;padding:0 4px}
.user .msg-meta{text-align:right}

/* Sources */
.sources{margin-top:10px;display:flex;flex-direction:column;gap:5px}
.source-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;font-size:12px;display:flex;gap:10px;align-items:flex-start}
.source-num{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:2px 7px;font-size:11px;font-weight:600;flex-shrink:0;color:var(--accent)}
.source-body{flex:1;min-width:0}
.source-title{font-weight:500;margin-bottom:2px;word-break:break-all}
.source-meta{color:var(--muted);margin-bottom:3px}
.source-preview{color:var(--muted);font-size:11px;line-height:1.4;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}

/* Empty */
.empty{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:var(--muted);text-align:center;padding:40px}
.empty-icon{font-size:52px;opacity:.35}
.empty h2{font-size:18px;color:var(--text)}
.empty p{font-size:14px;max-width:420px;line-height:1.6}

/* Typing */
.typing-indicator{display:flex;gap:4px;padding:14px 18px}
.typing-indicator span{width:7px;height:7px;background:var(--muted);border-radius:50%;animation:bounce .9s infinite}
.typing-indicator span:nth-child(2){animation-delay:.15s}
.typing-indicator span:nth-child(3){animation-delay:.3s}
@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}

/* Input bar */
.input-bar{padding:14px 20px;border-top:1px solid var(--border);background:var(--surface);display:flex;gap:10px;align-items:flex-end}
#question{flex:1;background:var(--surface2);border:1px solid var(--border);color:var(--text);border-radius:var(--radius);padding:12px 16px;font-size:14px;resize:none;min-height:48px;max-height:140px;line-height:1.5;font-family:inherit;transition:border-color .15s}
#question:focus{outline:none;border-color:var(--accent)}
#question::placeholder{color:var(--muted)}
.send-btn{background:var(--accent);border:none;color:#fff;border-radius:var(--radius);width:48px;height:48px;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:opacity .15s}
.send-btn:hover{opacity:.85}
.send-btn:disabled{opacity:.4;cursor:not-allowed}

/* Ingest panel */
.ingest-panel{padding:32px;overflow-y:auto;flex:1;max-width:900px;margin:0 auto;width:100%}
.ingest-panel h2{font-size:20px;margin-bottom:6px}
.ingest-panel .desc{color:var(--muted);font-size:14px;margin-bottom:24px;line-height:1.5}
.form-row{display:flex;gap:10px;margin-bottom:16px}
.form-row input[type=text]{flex:1;background:var(--surface2);border:1px solid var(--border);color:var(--text);border-radius:var(--radius);padding:12px 16px;font-size:14px;font-family:inherit}
.form-row input:focus{outline:none;border-color:var(--accent)}
.form-row input::placeholder{color:var(--muted)}
.btn{background:var(--accent);border:none;color:#fff;border-radius:var(--radius);padding:12px 24px;font-size:14px;font-weight:500;cursor:pointer;transition:opacity .15s;white-space:nowrap}
.btn:hover{opacity:.85}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn.danger{background:var(--red)}

/* Progress */
.progress-wrap{margin:20px 0;display:none}
.progress-wrap.active{display:block}
.progress-bar-bg{height:8px;background:var(--surface2);border-radius:4px;overflow:hidden;margin-bottom:8px}
.progress-bar{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:4px;transition:width .3s}
.progress-text{font-size:13px;color:var(--muted)}

/* Doc list */
.doc-list{margin-top:24px}
.doc-list h3{font-size:14px;margin-bottom:12px;color:var(--text)}
.doc-item{display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:6px;font-size:13px}
.doc-item .doc-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.doc-item .doc-meta{color:var(--muted);font-size:12px;white-space:nowrap}
.doc-item .doc-del{background:none;border:none;color:var(--red);cursor:pointer;font-size:16px;padding:4px 8px;border-radius:4px;opacity:.6;transition:opacity .15s}
.doc-item .doc-del:hover{opacity:1}

/* ─── Manage Files panel ─── */
.manage-panel{padding:32px;overflow-y:auto;flex:1;max-width:1000px;margin:0 auto;width:100%}
.manage-panel h2{font-size:20px;margin-bottom:6px}
.manage-panel .desc{color:var(--muted);font-size:14px;margin-bottom:20px;line-height:1.5}
.manage-top{display:flex;gap:10px;margin-bottom:20px;align-items:center;flex-wrap:wrap}
.manage-top .btn{flex-shrink:0}

/* Drop zone */
.drop-zone{border:2px dashed var(--border);border-radius:var(--radius);padding:40px 20px;text-align:center;color:var(--muted);font-size:14px;transition:all .2s;cursor:pointer;margin-bottom:24px;position:relative}
.drop-zone.over{border-color:var(--accent);background:rgba(124,140,245,.06);color:var(--text)}
.drop-zone input{position:absolute;inset:0;opacity:0;cursor:pointer}
.drop-zone .drop-icon{font-size:36px;margin-bottom:10px;opacity:.4}
.drop-zone .drop-hint{font-size:12px;color:var(--muted);margin-top:6px}

/* Upload target select */
.upload-target{display:flex;gap:10px;align-items:center;margin-bottom:16px;font-size:13px}
.upload-target select{background:var(--surface2);border:1px solid var(--border);color:var(--text);border-radius:8px;padding:8px 12px;font-size:13px;font-family:inherit}
.upload-target select:focus{outline:none;border-color:var(--accent)}

/* Folder grid */
.folder-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:16px}
.folder-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px;transition:border-color .15s}
.folder-card:hover{border-color:var(--accent)}
.folder-card.drag-over{border-color:var(--accent);background:rgba(124,140,245,.06)}
.folder-header{display:flex;align-items:center;gap:8px;margin-bottom:10px;font-size:14px;font-weight:600}
.folder-header .folder-icon{font-size:18px}
.folder-header .folder-count{margin-left:auto;font-size:11px;color:var(--muted);font-weight:400}
.folder-files{display:flex;flex-direction:column;gap:4px}
.file-row{display:flex;align-items:center;gap:8px;padding:6px 10px;background:var(--surface2);border:1px solid transparent;border-radius:6px;font-size:12px;cursor:grab;transition:all .15s}
.file-row:hover{border-color:var(--border)}
.file-row.dragging{opacity:.4}
.file-row .file-icon{font-size:14px;flex-shrink:0}
.file-row .file-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.file-row .file-del{background:none;border:none;color:var(--red);cursor:pointer;font-size:13px;padding:2px 6px;border-radius:4px;opacity:0;transition:opacity .15s}
.file-row:hover .file-del{opacity:.6}
.file-row .file-del:hover{opacity:1}
.empty-folder{font-size:12px;color:var(--muted);padding:8px 10px;font-style:italic}
.file-status{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600;flex-shrink:0;white-space:nowrap}
.file-status.ingested{background:rgba(34,197,94,.12);color:var(--green);border:1px solid rgba(34,197,94,.25)}
.file-status.pending{background:rgba(245,158,11,.1);color:var(--amber);border:1px solid rgba(245,158,11,.25)}
.folder-summary{font-size:11px;color:var(--muted);margin-top:8px;padding-top:8px;border-top:1px solid var(--border)}

/* ─── Tabular results ─── */
.results-table-wrap{overflow-x:auto;padding:4px 0}
.results-table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px}
.results-table thead th{position:sticky;top:0;background:var(--surface);text-align:left;padding:10px 14px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);border-bottom:2px solid var(--border);white-space:nowrap}
.results-table tbody tr{transition:background .12s}
.results-table tbody tr:hover{background:var(--surface2)}
.results-table td{padding:10px 14px;border-bottom:1px solid var(--border);vertical-align:top}
.results-table .rank-cell{text-align:center;font-weight:700;color:var(--accent);width:40px}
.results-table .score-cell{font-weight:600;color:var(--accent);white-space:nowrap;width:70px}
.results-table .file-cell{font-weight:500;white-space:nowrap;max-width:220px;overflow:hidden;text-overflow:ellipsis}
.results-table .page-cell{white-space:nowrap;color:var(--muted);width:60px;text-align:center}
.results-table .preview-cell{color:var(--text);line-height:1.55;max-width:500px}
.results-table .preview-cell .preview-text{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.results-table .expand-btn{background:none;border:none;color:var(--accent);cursor:pointer;font-size:11px;padding:2px 0;margin-top:2px}
.results-table .pages-cell{white-space:nowrap;color:var(--muted);font-size:12px}
.results-table .chunks-cell{display:flex;flex-direction:column;gap:4px}
.results-table .chunk-pill{background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:6px 10px;font-size:12px;line-height:1.45;color:var(--text);cursor:pointer;transition:border-color .15s}
.results-table .chunk-pill:hover{border-color:var(--accent)}
.results-table .chunk-pill .chunk-meta{font-size:10px;color:var(--muted);margin-bottom:2px;display:flex;align-items:center;gap:6px}
.results-table .chunk-pill .chunk-meta .expand-hint{color:var(--accent);font-style:italic}
.results-table .chunk-pill .chunk-preview{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.results-table .chunk-pill.expanded .chunk-preview{-webkit-line-clamp:unset;white-space:pre-wrap}

/* PDF upload search zone */
.pdf-search-zone{border:2px dashed var(--border);border-radius:var(--radius);padding:32px 20px;text-align:center;color:var(--muted);font-size:14px;transition:all .2s;cursor:pointer;position:relative}
.pdf-search-zone.over{border-color:var(--accent);background:rgba(124,140,245,.06);color:var(--text)}
.pdf-search-zone input{position:absolute;inset:0;opacity:0;cursor:pointer}
.pdf-search-zone .drop-icon{font-size:32px;opacity:.4;margin-bottom:8px}
.pdf-search-zone .drop-hint{font-size:11px;color:var(--muted);margin-top:6px}
.pdf-search-zone.has-file{border-color:var(--green);border-style:solid}
.pdf-search-zone.has-file .drop-icon{opacity:.7}
.pdf-search-zone.searching{opacity:.6;pointer-events:none}

/* PDF Match panel */
.pdf-panel{padding:24px 32px;overflow-y:auto;flex:1}
.pdf-panel h2{font-size:20px;margin-bottom:6px}
.pdf-panel .desc{color:var(--muted);font-size:14px;margin-bottom:20px;line-height:1.5}

/* Summary bar for PDF results */
.pdf-result-summary{display:flex;align-items:center;gap:12px;padding:14px 18px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin:20px 0 16px;font-size:13px}
.pdf-result-summary .summary-icon{font-size:20px}
.pdf-result-summary .summary-text{flex:1}
.pdf-result-summary .summary-text strong{color:var(--text)}
.pdf-result-summary .summary-count{color:var(--accent);font-weight:600}

/* Loading spinner for PDF search */
.pdf-loading{display:flex;align-items:center;gap:10px;padding:20px 0;color:var(--muted);font-size:14px}
.pdf-loading .spinner{width:20px;height:20px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.pdf-no-results{padding:24px;text-align:center;color:var(--muted);font-size:14px}

/* Scrollbar */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="logo">&#x1F50D;</div>
    <h1>Document RAG Search</h1>
    <span id="db-badge" class="badge">loading...</span>
  </div>
  <div class="center-controls">
    <div class="mode-toggle">
      <button class="mode-btn active" id="mode-ai" onclick="setMode('ai')">AI Answer</button>
      <button class="mode-btn" id="mode-direct" onclick="setMode('direct')">Direct Search</button>
      <button class="mode-btn" id="mode-pdf" onclick="setMode('pdf')">PDF Match</button>
    </div>
  </div>
  <div class="right-controls">
    <span class="sub">Powered by Claude + Local Embeddings</span>
    <button class="theme-btn" id="theme-btn" onclick="toggleTheme()" title="Toggle light/dark mode">&#x2600;</button>
  </div>
</header>

<div class="tabs">
  <div class="tab active" onclick="switchTab('search')">Search</div>
  <div class="tab" onclick="switchTab('manage')">Manage Files</div>
  <div class="tab" onclick="switchTab('library')">Library</div>
</div>

<!-- ═══ SEARCH PANEL (AI + Direct) ═══ -->
<div class="panel active" id="panel-search">
  <div class="layout">
    <aside>
      <div>
        <h3>Database</h3>
        <div id="dir-stats"><div style="color:var(--muted);font-size:12px">Loading...</div></div>
      </div>

    </aside>
    <main>
      <div id="chat">
        <div class="empty" id="empty-state">
          <div class="empty-icon">&#x1F4DA;</div>
          <h2>Ask anything about your documents</h2>
          <p>I'll search your document library using hybrid keyword + semantic search, then synthesize an answer with citations using Claude.</p>
        </div>
      </div>
      <div id="text-input-bar" class="input-bar">
        <textarea id="question" placeholder="Ask a question about your documents..." rows="1"></textarea>
        <button class="send-btn" id="send-btn" onclick="sendQuestion()" title="Ask">&#x27A4;</button>
      </div>
    </main>
  </div>
</div>

<!-- ═══ PDF MATCH PANEL ═══ -->
<div class="panel" id="panel-pdf">
  <div class="layout">
    <aside>
      <div>
        <h3>Database</h3>
        <div id="dir-stats-pdf"><div style="color:var(--muted);font-size:12px">Loading...</div></div>
      </div>
    </aside>
    <main>
      <div class="pdf-panel">
        <h2>PDF Match</h2>
        <p class="desc">Upload a PDF to find related documents in your library. Uses semantic + keyword matching — no AI needed.</p>
        <div class="pdf-search-zone" id="pdf-drop-zone">
          <input type="file" accept=".pdf" id="pdf-file-input" />
          <div class="drop-icon">&#x1F4C4;</div>
          <div id="pdf-drop-label">Drop a PDF here or click to find matching documents</div>
          <div class="drop-hint">Uploads are not stored — used only for search</div>
        </div>
        <div id="pdf-results"></div>
      </div>
    </main>
  </div>
</div>

<!-- ═══ MANAGE FILES PANEL ═══ -->
<div class="panel" id="panel-manage">
  <div class="manage-panel">
    <h2>Manage Files</h2>
    <p class="desc">Drag &amp; drop PDFs to upload, organize into folders, then ingest. Drag files between folders to reorganize.</p>

    <div class="upload-target">
      <label>Upload to:</label>
      <select id="upload-folder">
        <option value="">Root (no folder)</option>
      </select>
      <button class="btn" onclick="promptNewFolder()" style="padding:8px 14px;font-size:12px">+ New Folder</button>
    </div>

    <div class="drop-zone" id="drop-zone">
      <input type="file" multiple accept=".pdf" id="file-input" />
      <div class="drop-icon">&#x1F4C4;</div>
      <div>Drop PDF files here or click to browse</div>
      <div class="drop-hint">PDF files only · Max 200 MB per file</div>
    </div>

    <div class="manage-top">
      <button class="btn" id="ingest-all-btn" onclick="ingestManaged()">&#x26A1; Ingest All Files</button>
      <div class="progress-wrap" id="progress-wrap" style="flex:1;min-width:200px">
        <div class="progress-bar-bg"><div class="progress-bar" id="progress-bar" style="width:0%"></div></div>
        <div class="progress-text" id="progress-text"></div>
      </div>
    </div>

    <div id="folder-container"></div>
  </div>
</div>

<!-- ═══ LIBRARY PANEL ═══ -->
<div class="panel" id="panel-library">
  <div class="ingest-panel">
    <h2>Document Library</h2>
    <p class="desc">All ingested documents. You can remove individual documents from the database.</p>
    <div class="doc-list" id="doc-list">Loading...</div>
  </div>
</div>

<script>
// ─── Tab switching ───
function switchTab(name) {
  document.querySelectorAll('.tab').forEach((t,i) => {
    t.classList.toggle('active', ['search','manage','library'][i] === name);
  });
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-'+name).classList.add('active');
  if (name === 'library') loadDocuments();
  if (name === 'manage') loadFiles();
  if (name === 'search') loadStats();
  // Sync mode toggle back
  if (name === 'search' && searchMode === 'pdf') setMode('ai');
}

// ─── Stats ───
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const d = await res.json();
    const badge = document.getElementById('db-badge');
    if (d.error) { badge.textContent = 'DB error'; return; }
    badge.textContent = `${d.total_docs} docs · ${d.total_pages.toLocaleString()} pages · ${d.total_chunks.toLocaleString()} chunks`;
    badge.classList.add('ok');
    const el = document.getElementById('dir-stats');
    if (!d.directories.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:12px">No documents yet. Go to Ingest tab.</div>';
      return;
    }
    const dirHtml = d.directories.map(f => `
      <div class="dir-stat">
        <div class="dir-dot"></div>
        <span class="dir-name">${esc(f.directory||'Root')}</span>
        <span class="dir-count">${f.docs}d · ${(f.chunks||0).toLocaleString()}c</span>
      </div>`).join('');
    el.innerHTML = dirHtml;
    // Mirror into PDF panel sidebar
    const el2 = document.getElementById('dir-stats-pdf');
    if (el2) el2.innerHTML = dirHtml;
  } catch(e) { document.getElementById('db-badge').textContent = 'Server offline'; }
}
loadStats();

// ─── Textarea auto-resize ───
const ta = document.getElementById('question');
ta.addEventListener('input', () => { ta.style.height='auto'; ta.style.height=Math.min(ta.scrollHeight,140)+'px'; });
ta.addEventListener('keydown', e => { if(e.key==='Enter' && !e.shiftKey){e.preventDefault();sendQuestion()} });

// ─── Theme toggle ───
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  const next = current === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', next === 'dark' ? '' : 'light');
  if (next === 'dark') html.removeAttribute('data-theme');
  document.getElementById('theme-btn').innerHTML = next === 'light' ? '&#x1F319;' : '&#x2600;';
  localStorage.setItem('rag-theme', next);
}
(function(){
  const saved = localStorage.getItem('rag-theme');
  if (saved === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    document.getElementById('theme-btn').innerHTML = '&#x1F319;';
  }
})()

// ─── Search mode ───
let searchMode = 'ai'; // 'ai', 'direct', or 'pdf'
function setMode(m) {
  searchMode = m;
  document.getElementById('mode-ai').classList.toggle('active', m==='ai');
  document.getElementById('mode-direct').classList.toggle('active', m==='direct');
  document.getElementById('mode-pdf').classList.toggle('active', m==='pdf');

  if (m === 'pdf') {
    // Show the PDF panel, hide search panel
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-pdf').classList.add('active');
    // Deactivate tab highlights (PDF Match lives in mode toggle, not tabs)
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  } else {
    // Show search panel
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-search').classList.add('active');
    document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', i===0));
    document.getElementById('question').placeholder = m==='ai'
      ? 'Ask a question about your documents...'
      : 'Search your documents (returns raw matching passages)...';
  }
}

// ─── Chat ───
let isLoading = false;

function addMsg(role, html, meta='') {
  const empty = document.getElementById('empty-state');
  if(empty) empty.remove();
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg '+role;
  div.innerHTML = `<div class="msg-bubble">${html}</div>${meta?`<div class="msg-meta">${meta}</div>`:''}`;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function addTyping() {
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className='msg assistant'; div.id='typing';
  div.innerHTML='<div class="msg-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
  chat.appendChild(div); chat.scrollTop=chat.scrollHeight;
  return div;
}

function buildSources(sources) {
  if(!sources.length) return '';
  return `<div class="sources">${sources.map((s,i) => `
    <div class="source-card">
      <div class="source-num">${i+1}</div>
      <div class="source-body">
        <div class="source-title">${esc(s.directory?s.directory+'/':'')}${esc(s.filename)}</div>
        <div class="source-meta">Page ${s.page}</div>
        <div class="source-preview">${esc(s.preview)}</div>
      </div>
    </div>`).join('')}</div>`;
}

async function sendQuestion() {
  if(isLoading) return;
  const q = ta.value.trim();
  if(!q) return;
  isLoading = true;
  document.getElementById('send-btn').disabled = true;
  ta.value=''; ta.style.height='auto';

  addMsg('user', esc(q));

  if (searchMode === 'direct') { await directSearch(q); return; }

  const typing = addTyping();

  try {
    const res = await fetch('/api/ask', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({question:q})
    });
    if(!res.ok) throw new Error('Server error '+res.status);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf='', sources=[], answer='', bubble=null;
    typing.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className='msg assistant';
    document.getElementById('chat').appendChild(msgDiv);

    while(true) {
      const {done,value} = await reader.read();
      if(done) break;
      buf += decoder.decode(value,{stream:true});
      const lines = buf.split('\n'); buf = lines.pop();
      for(const line of lines) {
        if(!line.startsWith('data: ')) continue;
        const p = JSON.parse(line.slice(6));
        if(p.sources){ sources=p.sources; msgDiv.innerHTML='<div class="msg-bubble"></div>'; bubble=msgDiv.querySelector('.msg-bubble'); }
        else if(p.delta){ answer+=p.delta; if(bubble) bubble.textContent=answer; document.getElementById('chat').scrollTop=9e9; }
        else if(p.done){
          if(bubble && sources.length){
            msgDiv.innerHTML = `<div class="msg-bubble">${esc(answer)}</div>${buildSources(sources)}<div class="msg-meta">${sources.length} source${sources.length>1?'s':''}</div>`;
          }
        }
        else if(p.error){ if(bubble) bubble.textContent='Error: '+p.error; }
      }
    }
  } catch(err) { typing.remove(); addMsg('assistant','Error: '+err.message); }

  isLoading=false;
  document.getElementById('send-btn').disabled=false;
  ta.focus();
}

// ─── Direct (non-agentic) search — tabular ───
async function directSearch(q) {
  try {
    const res = await fetch('/api/search', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({question:q})
    });
    const data = await res.json();
    if(data.error) { addMsg('assistant','Error: '+data.error); }
    else if(!data.results.length) { addMsg('assistant','No matching passages found. Try different search terms.'); }
    else {
      const html = buildResultsTable(data.results);
      const msgDiv = addMsg('assistant','');
      msgDiv.querySelector('.msg-bubble').innerHTML = html;
      msgDiv.innerHTML += `<div class="msg-meta">${data.results.length} passages found</div>`;
    }
  } catch(err) { addMsg('assistant','Error: '+err.message); }
  isLoading=false;
  document.getElementById('send-btn').disabled=false;
  ta.focus();
}

function buildResultsTable(results) {
  return `<div class="results-table-wrap"><table class="results-table">
    <thead><tr>
      <th>#</th><th>Document</th><th>Page</th><th>Score</th><th>Passage</th>
    </tr></thead>
    <tbody>${results.map((r,i) => `<tr>
      <td class="rank-cell">${i+1}</td>
      <td class="file-cell" title="${esc(r.directory?r.directory+'/':'')}${esc(r.filename)}">${esc(r.directory?r.directory+'/':'')}${esc(r.filename)}</td>
      <td class="page-cell">${r.page}</td>
      <td class="score-cell">${(r.score*100).toFixed(1)}%</td>
      <td class="preview-cell"><div class="preview-text" id="prev-${i}">${esc(r.preview||r.text?.substring(0,300)||'')}</div>${r.text && r.text.length > 300 ? `<button class="expand-btn" onclick="toggleExpand(this, ${i}, '${btoa(unescape(encodeURIComponent(r.text)))}')">Show more</button>` : ''}</td>
    </tr>`).join('')}</tbody></table></div>`;
}

function buildDocResultsTable(results) {
  return `<div class="results-table-wrap"><table class="results-table">
    <thead><tr>
      <th>#</th><th>Document</th><th>Score</th><th>Matching Pages</th><th>Top Matching Passages</th>
    </tr></thead>
    <tbody>${results.map((r,i) => `<tr>
      <td class="rank-cell">${i+1}</td>
      <td class="file-cell" title="${esc(r.directory?r.directory+'/':'')}${esc(r.filename)}">${esc(r.directory?r.directory+'/':'')}${esc(r.filename)}</td>
      <td class="score-cell">${(r.total_score*100).toFixed(1)}%</td>
      <td class="pages-cell">${r.matching_pages?.join(', ')||'—'}</td>
      <td class="chunks-cell">${(r.top_chunks||[]).map((c,ci) => `<div class="chunk-pill" onclick="this.classList.toggle('expanded')" title="Click to expand"><div class="chunk-meta">p.${c.page} · ${(c.score*100).toFixed(1)}% <span class="expand-hint">click to expand</span></div><div class="chunk-preview">${esc(c.text||c.preview)}</div></div>`).join('')}</td>
    </tr>`).join('')}</tbody></table></div>`;
}

function toggleExpand(btn, idx, b64) {
  const el = document.getElementById('prev-'+idx);
  if (btn.textContent === 'Show more') {
    try { el.textContent = decodeURIComponent(escape(atob(b64))); } catch(e) { el.textContent = atob(b64); }
    el.style.webkitLineClamp = 'unset';
    btn.textContent = 'Show less';
  } else {
    el.style.webkitLineClamp = '3';
    btn.textContent = 'Show more';
  }
}

// ─── PDF Search ───
const pdfDropZone = document.getElementById('pdf-drop-zone');
const pdfFileInput = document.getElementById('pdf-file-input');

pdfDropZone.addEventListener('dragover', e => { e.preventDefault(); pdfDropZone.classList.add('over'); });
pdfDropZone.addEventListener('dragleave', () => pdfDropZone.classList.remove('over'));
pdfDropZone.addEventListener('drop', e => { e.preventDefault(); pdfDropZone.classList.remove('over'); if(e.dataTransfer.files.length) searchByPdf(e.dataTransfer.files[0]); });
pdfFileInput.addEventListener('change', () => { if(pdfFileInput.files.length) searchByPdf(pdfFileInput.files[0]); });

async function searchByPdf(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) { alert('Please select a PDF file'); return; }

  const resultsEl = document.getElementById('pdf-results');

  // Update drop zone to show selected file
  pdfDropZone.classList.add('has-file', 'searching');
  document.getElementById('pdf-drop-label').textContent = `Searching with: ${file.name} ...`;
  resultsEl.innerHTML = '<div class="pdf-loading"><div class="spinner"></div>Analyzing document and searching library...</div>';

  try {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/search/pdf', {method:'POST', body:form});
    const data = await res.json();

    if (data.error) {
      resultsEl.innerHTML = `<div class="pdf-no-results">Error: ${esc(data.error)}</div>`;
    } else if (!data.results || !data.results.length) {
      resultsEl.innerHTML = '<div class="pdf-no-results">No matching documents found in the database.</div>';
    } else {
      const summary = `<div class="pdf-result-summary">
        <div class="summary-icon">&#x1F50D;</div>
        <div class="summary-text">Searched <strong>${esc(data.query_filename)}</strong> (${data.query_pages} pages) against your library</div>
        <div class="summary-count">${data.results.length} matching document${data.results.length>1?'s':''}</div>
      </div>`;
      resultsEl.innerHTML = summary + buildDocResultsTable(data.results);
    }
  } catch(err) {
    resultsEl.innerHTML = `<div class="pdf-no-results">Error: ${esc(err.message)}</div>`;
  }

  // Reset drop zone
  pdfDropZone.classList.remove('has-file', 'searching');
  document.getElementById('pdf-drop-label').textContent = 'Drop a PDF here or click to find matching documents';
  pdfFileInput.value = '';
}

// ─── File Management ───
let pollTimer = null;
let dragData = null;

async function loadFiles() {
  try {
    const res = await fetch('/api/files');
    const data = await res.json();
    const container = document.getElementById('folder-container');
    const sel = document.getElementById('upload-folder');

    // Rebuild folder select
    sel.innerHTML = '<option value="">Root (no folder)</option>';
    for (const folder of Object.keys(data.folders).sort()) {
      if (folder) sel.innerHTML += `<option value="${esc(folder)}">${esc(folder)}</option>`;
    }

    // Render folder cards
    const folderNames = Object.keys(data.folders).sort((a,b) => {
      if (a === '') return -1; if (b === '') return 1; return a.localeCompare(b);
    });

    container.innerHTML = '<div class="folder-grid">' + folderNames.map(folder => {
      const files = data.folders[folder];
      const label = folder || 'Unsorted';
      const ingested = files.filter(f => f.ingested).length;
      const total = files.length;
      return `
        <div class="folder-card" data-folder="${esc(folder)}"
             ondragover="folderDragOver(event)" ondragleave="folderDragLeave(event)" ondrop="folderDrop(event)">
          <div class="folder-header">
            <span class="folder-icon">&#x1F4C1;</span>
            <span>${esc(label)}</span>
            <span class="folder-count">${total} file${total!==1?'s':''}</span>
          </div>
          <div class="folder-files">
            ${files.length ? files.map(f => `
              <div class="file-row" draggable="true" data-filename="${esc(f.name)}" data-folder="${esc(folder)}"
                   ondragstart="fileDragStart(event)" ondragend="fileDragEnd(event)">
                <span class="file-icon">&#x1F4C4;</span>
                <span class="file-name" title="${esc(f.name)}">${esc(f.name)}</span>
                ${f.ingested
                  ? `<span class="file-status ingested">${f.pages}pp · ${f.chunks}c</span>`
                  : '<span class="file-status pending">Not ingested</span>'}
                <button class="file-del" onclick="deleteFile('${esc(f.name)}','${esc(folder)}')" title="Delete">&#x2715;</button>
              </div>`).join('')
              : '<div class="empty-folder">Drop files here</div>'}
          </div>
          ${total > 0 ? `<div class="folder-summary">${ingested}/${total} ingested</div>` : ''}
        </div>`;
    }).join('') + '</div>';
  } catch(e) { document.getElementById('folder-container').innerHTML = 'Error loading files'; }
}

// ─── Drag & drop upload ───
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('over'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('over'); uploadFiles(e.dataTransfer.files); });
fileInput.addEventListener('change', () => { if(fileInput.files.length) uploadFiles(fileInput.files); });

async function uploadFiles(files) {
  const folder = document.getElementById('upload-folder').value;
  const form = new FormData();
  form.append('folder', folder);
  for (const f of files) {
    if (f.name.toLowerCase().endsWith('.pdf')) form.append('files', f);
  }
  try {
    const res = await fetch('/api/files/upload', {method:'POST', body:form});
    const data = await res.json();
    if (data.uploaded && data.uploaded.length) loadFiles();
    else alert('No valid PDF files selected');
  } catch(e) { alert('Upload failed: '+e.message); }
  fileInput.value = '';
}

function promptNewFolder() {
  const name = prompt('New folder name:');
  if (!name || !name.trim()) return;
  fetch('/api/files/folder', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:name.trim()})})
    .then(r => r.json()).then(d => { if(d.error) alert(d.error); else loadFiles(); });
}

// ─── Drag between folders ───
function fileDragStart(e) {
  const row = e.target.closest('.file-row');
  dragData = {filename: row.dataset.filename, from: row.dataset.folder};
  row.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
}
function fileDragEnd(e) { e.target.closest('.file-row')?.classList.remove('dragging'); dragData=null; }
function folderDragOver(e) { if(dragData){e.preventDefault(); e.currentTarget.classList.add('drag-over');} }
function folderDragLeave(e) { e.currentTarget.classList.remove('drag-over'); }
function folderDrop(e) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (!dragData) return;
  const toFolder = e.currentTarget.dataset.folder;
  if (toFolder === dragData.from) return;
  fetch('/api/files/move', {method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({filename:dragData.filename, from:dragData.from, to:toFolder})
  }).then(r=>r.json()).then(d => { if(d.error) alert(d.error); else loadFiles(); });
  dragData = null;
}

async function deleteFile(filename, folder) {
  if (!confirm(`Delete ${filename}?`)) return;
  await fetch('/api/files/delete', {method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({filename, folder})});
  loadFiles();
}

// ─── Ingest managed directory ───
async function ingestManaged() {
  document.getElementById('ingest-all-btn').disabled = true;
  try {
    const res = await fetch('/api/files/ingest', {method:'POST'});
    const data = await res.json();
    if (data.error) { alert(data.error); document.getElementById('ingest-all-btn').disabled=false; return; }
    document.getElementById('progress-wrap').classList.add('active');
    pollTimer = setInterval(pollIngest, 800);
  } catch(e) { alert('Failed: '+e.message); document.getElementById('ingest-all-btn').disabled=false; }
}

async function pollIngest() {
  try {
    const res = await fetch('/api/ingest/status');
    const d = await res.json();
    document.getElementById('progress-bar').style.width = d.progress+'%';
    document.getElementById('progress-text').textContent = d.message + (d.total ? ` (${d.done}/${d.total})` : '');
    if(!d.running) {
      clearInterval(pollTimer);
      document.getElementById('ingest-all-btn').disabled = false;
      loadFiles();
      loadStats();
    }
  } catch(e) {}
}

// ─── Library ───
async function loadDocuments() {
  try {
    const res = await fetch('/api/documents');
    const docs = await res.json();
    const el = document.getElementById('doc-list');
    if(!docs.length) { el.innerHTML='<div style="color:var(--muted)">No documents ingested yet.</div>'; return; }
    el.innerHTML = docs.map(d => `
      <div class="doc-item" id="doc-${d.id}">
        <div class="dir-dot"></div>
        <div class="doc-name" title="${esc(d.filename)}">${esc(d.directory?d.directory+'/':'')}${esc(d.filename)}</div>
        <div class="doc-meta">${d.pages}pp · ${d.chunks_count}c</div>
        <button class="doc-del" onclick="deleteDoc(${d.id})" title="Remove">&#x2715;</button>
      </div>`).join('');
  } catch(e) { document.getElementById('doc-list').innerHTML='Error loading documents'; }
}

async function deleteDoc(id) {
  if(!confirm('Remove this document from the database?')) return;
  await fetch('/api/documents/'+id, {method:'DELETE'});
  document.getElementById('doc-'+id)?.remove();
  loadStats();
}

function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>'); }
</script>
</body>
</html>
"""
