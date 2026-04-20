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

// ─── Theme ───
function setTheme(t) {
  if (t === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
  localStorage.setItem('rag-theme', t);
  document.getElementById('theme-dark').classList.toggle('active', t === 'dark');
  document.getElementById('theme-light').classList.toggle('active', t === 'light');
}
(function(){
  const saved = localStorage.getItem('rag-theme') || 'dark';
  setTheme(saved);
})()

// ─── Settings ───
let _settingsData = {};

function openSettings() {
  document.getElementById('settings-overlay').classList.add('open');
  loadSettingsData();
}
function closeSettings() {
  document.getElementById('settings-overlay').classList.remove('open');
  document.getElementById('settings-status').classList.remove('visible');
}

async function loadSettingsData() {
  try {
    const res = await fetch('/api/settings');
    _settingsData = await res.json();
    document.getElementById('api-key-input').value = '';
    document.getElementById('api-key-input').placeholder = _settingsData.anthropic_api_key_set
      ? _settingsData.anthropic_api_key_masked
      : 'sk-ant-...';
    document.getElementById('model-input').value = _settingsData.model_name || '';
    document.getElementById('settings-path-info').textContent =
      'Documents: ' + _settingsData.docs_dir + '\nDatabase: ' + _settingsData.db_path;
    // Sync theme toggles
    const currentTheme = localStorage.getItem('rag-theme') || 'dark';
    document.getElementById('theme-dark').classList.toggle('active', currentTheme === 'dark');
    document.getElementById('theme-light').classList.toggle('active', currentTheme === 'light');
  } catch(e) { console.error('Failed to load settings:', e); }
}

async function saveSettings() {
  const payload = {};
  const theme = document.getElementById('theme-dark').classList.contains('active') ? 'dark' : 'light';
  payload.theme = theme;
  setTheme(theme);
  const newKey = document.getElementById('api-key-input').value.trim();
  if (newKey) payload.anthropic_api_key = newKey;
  const model = document.getElementById('model-input').value.trim();
  if (model) payload.model_name = model;
  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const status = document.getElementById('settings-status');
    status.classList.add('visible');
    setTimeout(() => status.classList.remove('visible'), 2500);
    if (newKey) {
      document.getElementById('api-key-input').value = '';
      document.getElementById('api-key-input').placeholder = newKey.slice(0,4) + '…' + newKey.slice(-4);
    }
  } catch(e) { alert('Failed to save: ' + e.message); }
}

async function revealFolder(target) {
  await fetch('/api/settings/reveal', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target}),
  });
}

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
