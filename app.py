"""
ValoremDB — Document RAG Search (Streamlit)
=============================================
All backend modules (db, search, embeddings, ingest, claude) are reused as-is.
Settings are stored in a local settings.json file.
Auth is handled by Streamlit Cloud (viewer access control).
"""

import os
import json
import threading
from pathlib import Path

import streamlit as st

# ── Page config (must be first Streamlit call) ───────────────────────
st.set_page_config(
    page_title="ValoremDB",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS to match the original polished UI ─────────────────────
st.markdown("""
<style>
/* ── Global ─────────────────────────────────────────── */
:root {
    --accent: #5b6abf;
    --accent2: #7c5cbf;
    --green: #16a34a;
    --red: #dc2626;
    --amber: #d97706;
    --muted: #64748b;
    --border: #d8dce5;
    --surface: #ffffff;
    --surface2: #eef1f6;
    --radius: 10px;
}

/* Hide default Streamlit chrome */
#MainMenu {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}
footer {visibility: hidden;}

/* ── Sidebar ────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMetric label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
}

/* ── Tabs ───────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 500;
}

/* ── Result cards ───────────────────────────────────── */
.result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    margin-bottom: 10px;
    transition: border-color 0.15s;
}
.result-card:hover {
    border-color: var(--accent);
}
.result-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.result-rank {
    background: var(--accent);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    width: 26px;
    height: 26px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.result-file {
    font-size: 13px;
    font-weight: 600;
    flex: 1;
    word-break: break-all;
    color: #1e293b;
}
.result-page {
    font-size: 11px;
    color: var(--muted);
    white-space: nowrap;
}
.result-score {
    font-size: 11px;
    color: var(--accent);
    white-space: nowrap;
    font-weight: 600;
}
.result-text {
    font-size: 13px;
    line-height: 1.65;
    color: #334155;
    white-space: pre-wrap;
    max-height: 200px;
    overflow-y: auto;
    background: var(--surface2);
    border-radius: 6px;
    padding: 12px;
    margin-top: 6px;
}

/* ── Source cards ────────────────────────────────────── */
.source-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    display: flex;
    gap: 10px;
    align-items: flex-start;
    margin-bottom: 6px;
}
.source-num {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    font-weight: 600;
    flex-shrink: 0;
    color: var(--accent);
}
.source-title {
    font-weight: 500;
    margin-bottom: 2px;
    color: #1e293b;
}
.source-meta {
    color: var(--muted);
    font-size: 11px;
}

/* ── Document list ──────────────────────────────────── */
.doc-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: 13px;
}
.doc-row .doc-icon { font-size: 16px; flex-shrink: 0; }
.doc-row .doc-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.doc-row .doc-meta { color: var(--muted); font-size: 12px; white-space: nowrap; }

/* ── Stats badges ───────────────────────────────────── */
.stat-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 20px;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--muted);
}
.stat-badge.ok { color: var(--green); border-color: rgba(22, 163, 74, 0.3); }

/* ── Empty state ────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
}
.empty-state .icon { font-size: 52px; opacity: 0.35; margin-bottom: 12px; }
.empty-state h3 { font-size: 18px; color: #1e293b; margin-bottom: 6px; }
.empty-state p { font-size: 14px; max-width: 420px; margin: 0 auto; line-height: 1.6; }

/* ── Buttons ────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    border-radius: var(--radius);
}

/* ── Settings section headers ───────────────────────── */
.settings-section {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin: 16px 0 8px 0;
}
</style>
""", unsafe_allow_html=True)

from rag.config import load_settings, save_settings, SETTINGS_FILE
from rag.db import init_db, db_stats, get_db
from rag.search import hybrid_search
from rag.claude import stream_claude
from rag.ingest import ingest_directory, ingest_status, ingest_lock

# ── Load live settings ───────────────────────────────────────────────
settings = load_settings()

DB_PATH   = settings["db_path"]
DOCS_DIR  = settings["docs_dir"]
TOP_K     = settings["top_k"]
MODEL_NAME = settings["model_name"]

# Set API key into env so anthropic client picks it up
_api_key = settings.get("anthropic_api_key") or ""
try:
    _api_key = st.secrets.get("ANTHROPIC_API_KEY", _api_key)
except FileNotFoundError:
    pass
if _api_key:
    os.environ["ANTHROPIC_API_KEY"] = _api_key

DOCS_PATH = Path(DOCS_DIR).resolve()
init_db(DB_PATH)
DOCS_PATH.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📄 ValoremDB")
    st.caption("Document Intelligence Search")
    st.divider()

    # Database stats
    stats = db_stats(DB_PATH)
    c1, c2, c3 = st.columns(3)
    c1.metric("Docs", stats.get("total_docs", 0))
    c2.metric("Chunks", stats.get("total_chunks", 0))
    c3.metric("Pages", stats.get("total_pages", 0))

    # Indexed directories
    dirs = stats.get("directories", [])
    if dirs:
        st.divider()
        st.markdown('<p class="settings-section">Indexed Folders</p>', unsafe_allow_html=True)
        for d in dirs:
            name = d.get("directory") or "Root"
            st.markdown(
                f'<div class="doc-row">'
                f'<span class="doc-icon">📁</span>'
                f'<span class="doc-name">{name}</span>'
                f'<span class="doc-meta">{d["docs"]} docs · {d["chunks"]} chunks</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # Ingest controls
    with ingest_lock:
        running = ingest_status.get("running", False)

    if running:
        with ingest_lock:
            msg = ingest_status.get("message", "Working…")
            pct = ingest_status.get("progress", 0) / 100.0
        st.progress(min(pct, 1.0), text=msg)
        if st.button("↻ Refresh", use_container_width=True):
            st.rerun()
    else:
        if st.button("🔄 Re-index Documents", use_container_width=True):
            threading.Thread(
                target=ingest_directory,
                args=(DB_PATH, str(DOCS_PATH)),
                daemon=True,
            ).start()
            st.toast("Indexing started…")
            st.rerun()
        with ingest_lock:
            last = ingest_status.get("message", "")
        if last:
            st.caption(last)

    st.divider()
    st.markdown(
        f'<span class="stat-badge">Model: {MODEL_NAME}</span>',
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════════
#  MAIN TABS
# ═════════════════════════════════════════════════════════════════════
tab_ask, tab_search, tab_docs, tab_settings = st.tabs(
    ["💬 Ask", "🔍 Search", "📄 Documents", "⚙️ Settings"]
)


# ────────── ASK TAB ──────────────────────────────────────────────────
with tab_ask:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Empty state
    if not st.session_state.chat_history:
        st.markdown(
            '<div class="empty-state">'
            '<div class="icon">📄</div>'
            '<h3>Ask anything about your documents</h3>'
            '<p>Type a question below and the AI will search your indexed documents '
            'and provide an answer with source citations.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Render past messages
    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])
            if entry.get("sources"):
                with st.expander(f"📚 {len(entry['sources'])} sources"):
                    for i, s in enumerate(entry["sources"], 1):
                        st.markdown(
                            f'<div class="source-card">'
                            f'<span class="source-num">{i}</span>'
                            f'<div><div class="source-title">{s["label"]}</div>'
                            f'<div class="source-meta">Page {s["page"]} · '
                            f'Score {s["score"]:.4f}</div></div></div>',
                            unsafe_allow_html=True,
                        )

    if prompt := st.chat_input("Ask a question about your documents…"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        chunks = hybrid_search(DB_PATH, prompt, top_k=TOP_K)

        sources = []
        for c in chunks:
            label = (
                f"{c.get('directory', '')}/{c['filename']}"
                if c.get("directory")
                else c["filename"]
            )
            sources.append({"label": label, "page": c["page"], "score": c["score"]})

        with st.chat_message("assistant"):
            if not chunks:
                msg = "No relevant documents found. Try different search terms or index more documents."
                st.warning(msg)
                st.session_state.chat_history.append({"role": "assistant", "content": msg})
            else:
                with st.expander(f"📚 {len(sources)} sources", expanded=False):
                    for i, s in enumerate(sources, 1):
                        st.markdown(
                            f'<div class="source-card">'
                            f'<span class="source-num">{i}</span>'
                            f'<div><div class="source-title">{s["label"]}</div>'
                            f'<div class="source-meta">Page {s["page"]} · '
                            f'Score {s["score"]:.4f}</div></div></div>',
                            unsafe_allow_html=True,
                        )

                response = st.write_stream(stream_claude(prompt, chunks))
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": response, "sources": sources}
                )


# ────────── SEARCH TAB ───────────────────────────────────────────────
with tab_search:
    st.markdown("#### Direct Search")
    st.caption("Search your documents without AI — see the raw matched passages.")

    query = st.text_input(
        "Search query:",
        key="search_input",
        placeholder="Search your documents…",
        label_visibility="collapsed",
    )

    if st.button("Search", type="primary", key="search_btn") and query:
        with st.spinner("Searching…"):
            st.session_state.search_results = hybrid_search(DB_PATH, query, top_k=TOP_K)
            st.session_state.search_query = query

    results = st.session_state.get("search_results", [])
    sq = st.session_state.get("search_query", "")

    if results:
        st.caption(f"**{len(results)}** results for *\"{sq}\"*")
        for i, r in enumerate(results, 1):
            source = (
                f"{r.get('directory', '')}/{r['filename']}"
                if r.get("directory")
                else r["filename"]
            )
            # Escape HTML in text
            import html
            safe_text = html.escape(r["text"][:800])
            st.markdown(
                f'<div class="result-card">'
                f'<div class="result-header">'
                f'<span class="result-rank">{i}</span>'
                f'<span class="result-file">{html.escape(source)}</span>'
                f'<span class="result-page">Page {r["page"]}</span>'
                f'<span class="result-score">{r["score"]:.4f}</span>'
                f'</div>'
                f'<div class="result-text">{safe_text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    elif sq:
        st.markdown(
            '<div class="empty-state">'
            '<div class="icon">🔍</div>'
            '<h3>No results found</h3>'
            '<p>Try different search terms or index more documents.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="empty-state">'
            '<div class="icon">🔍</div>'
            '<h3>Search your document library</h3>'
            '<p>Enter a query above to find relevant passages across all indexed documents. '
            'Results are ranked by hybrid keyword + semantic similarity.</p>'
            '</div>',
            unsafe_allow_html=True,
        )


# ────────── DOCUMENTS TAB ────────────────────────────────────────────
with tab_docs:
    st.markdown("#### Manage Documents")
    st.caption("Upload PDFs and manage your indexed document library.")

    # File uploader
    uploaded = st.file_uploader(
        "Upload PDFs to index",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded:
        existing_dirs = ["(root)"] + sorted(
            d.name
            for d in DOCS_PATH.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )
        folder = st.selectbox("Target folder:", existing_dirs)

        if st.button("💾 Save uploaded files", type="primary"):
            target = DOCS_PATH if folder == "(root)" else DOCS_PATH / folder
            target.mkdir(parents=True, exist_ok=True)
            for f in uploaded:
                (target / f.name).write_bytes(f.getvalue())
            st.success(
                f"Saved {len(uploaded)} file(s). "
                "Click **Re-index Documents** in the sidebar to index them."
            )
            st.rerun()

    st.divider()

    # Indexed documents
    conn = get_db(DB_PATH)
    rows = conn.execute(
        "SELECT id, filename, directory, pages, chunks_count, ingested_at "
        "FROM documents ORDER BY directory, filename"
    ).fetchall()
    conn.close()

    if rows:
        st.markdown(f"**{len(rows)} indexed documents**")

        # Group by directory
        from collections import defaultdict
        grouped = defaultdict(list)
        for r in rows:
            r = dict(r)
            grouped[r.get("directory") or "Root"].append(r)

        for folder_name, docs in sorted(grouped.items()):
            st.markdown(
                f'<p class="settings-section">📁 {folder_name} ({len(docs)} files)</p>',
                unsafe_allow_html=True,
            )
            for r in docs:
                c1, c2, c3, c4, c5 = st.columns([5, 1, 1, 2, 0.5])
                c1.markdown(f"📄 **{r['filename']}**")
                c2.caption(f"{r['pages']}p")
                c3.caption(f"{r['chunks_count']}ch")
                c4.caption(r["ingested_at"][:16].replace("T", " "))
                if c5.button("✕", key=f"del_{r['id']}", help="Remove from index"):
                    conn = get_db(DB_PATH)
                    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (r["id"],))
                    conn.execute("DELETE FROM documents WHERE id = ?", (r["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
    else:
        st.markdown(
            '<div class="empty-state">'
            '<div class="icon">📄</div>'
            '<h3>No documents indexed</h3>'
            '<p>Upload PDFs above, then click <strong>Re-index Documents</strong> '
            'in the sidebar to start indexing.</p>'
            '</div>',
            unsafe_allow_html=True,
        )


# ────────── SETTINGS TAB ──────────────────────────────────────────────
with tab_settings:
    st.markdown("#### Application Settings")
    st.caption(f"Stored in `{SETTINGS_FILE}`")
    st.divider()

    _live = load_settings()

    st.markdown('<p class="settings-section">Paths</p>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    new_docs_dir = col_a.text_input(
        "Documents folder",
        value=_live["docs_dir"],
        help="Local folder where PDFs are stored. Subfolders become categories.",
    )
    new_db_path = col_b.text_input(
        "Database file",
        value=_live["db_path"],
        help="SQLite database that stores chunks and embeddings.",
    )

    st.markdown('<p class="settings-section">API</p>', unsafe_allow_html=True)
    new_api_key = st.text_input(
        "Anthropic API key",
        value=_live.get("anthropic_api_key", ""),
        type="password",
        help="Required for the Ask (Claude) feature. Stored locally in settings.json.",
    )
    new_model = st.text_input("Claude model", value=_live["model_name"])

    st.markdown('<p class="settings-section">Search & Ingestion</p>', unsafe_allow_html=True)
    col_c, col_d, col_e = st.columns(3)
    new_top_k = col_c.number_input("Top K results", value=_live["top_k"], min_value=1, max_value=50)
    new_chunk_target = col_d.number_input("Chunk size (chars)", value=_live["chunk_target"], min_value=200, max_value=5000, step=100)
    new_chunk_overlap = col_e.number_input("Chunk overlap (chars)", value=_live["chunk_overlap"], min_value=0, max_value=1000, step=50)

    col_f, col_g = st.columns(2)
    new_embed_model = col_f.text_input("Embedding model", value=_live["embed_model"])
    new_embed_batch = col_g.number_input("Embed batch size", value=_live["embed_batch_size"], min_value=1, max_value=1024)

    st.divider()

    if st.button("💾 Save Settings", type="primary"):
        updated = {
            **_live,
            "docs_dir":         new_docs_dir,
            "db_path":          new_db_path,
            "anthropic_api_key": new_api_key,
            "model_name":       new_model,
            "top_k":            int(new_top_k),
            "chunk_target":     int(new_chunk_target),
            "chunk_overlap":    int(new_chunk_overlap),
            "embed_model":      new_embed_model,
            "embed_batch_size": int(new_embed_batch),
        }
        save_settings(updated)
        st.success("Settings saved. Restart the app for path changes to take effect.")
        st.rerun()
