"""
DocRAG Search — Streamlit Application
======================================
Replaces the Flask + HTML frontend with Streamlit.
All backend modules (db, search, embeddings, ingest, claude) are reused as-is.
Settings are stored in a local settings.json file.
"""

import os
import json
import threading
from pathlib import Path

import streamlit as st
import yaml
from yaml.loader import SafeLoader

# ── Page config (must be first Streamlit call) ───────────────────────
st.set_page_config(
    page_title="DocRAG Search",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
# Streamlit Cloud: secrets take priority
try:
    _api_key = st.secrets.get("ANTHROPIC_API_KEY", _api_key)
except FileNotFoundError:
    pass
if _api_key:
    os.environ["ANTHROPIC_API_KEY"] = _api_key

DOCS_PATH = Path(DOCS_DIR).resolve()
init_db(DB_PATH)
DOCS_PATH.mkdir(parents=True, exist_ok=True)


# ── Authentication ───────────────────────────────────────────────────
import bcrypt
import streamlit_authenticator as stauth

CONFIG_PATH = Path("config.yaml")

def _load_auth_config() -> dict:
    """Load auth config from config.yaml (local) or st.secrets (cloud)."""
    # 1. Local file
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            cfg = yaml.load(f, Loader=SafeLoader)
        # Auto-hash plaintext passwords
        dirty = False
        for _user, _data in cfg.get("credentials", {}).get("usernames", {}).items():
            _pw = _data.get("password", "")
            if _pw and not _pw.startswith("$2b$"):
                _data["password"] = bcrypt.hashpw(_pw.encode(), bcrypt.gensalt()).decode()
                dirty = True
        if dirty:
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(cfg, f, default_flow_style=False)
        return cfg

    # 2. Streamlit Cloud secrets
    try:
        secrets_auth = st.secrets.get("auth", {})
        if secrets_auth:
            return dict(secrets_auth)
    except FileNotFoundError:
        pass

    st.error("Missing `config.yaml` (local) or `[auth]` in Streamlit secrets.")
    st.stop()

auth_config = _load_auth_config()

authenticator = stauth.Authenticate(
    auth_config["credentials"],
    auth_config["cookie"]["name"],
    auth_config["cookie"]["key"],
    auth_config["cookie"]["expiry_days"],
)

authenticator.login()

if st.session_state.get("authentication_status") is False:
    st.error("Invalid username or password.")
    st.stop()
if st.session_state.get("authentication_status") is None:
    st.markdown("### 📄 DocRAG Search")
    st.info("Enter your credentials to continue.")
    st.stop()


# ═════════════════════════════════════════════════════════════════════
#  AUTHENTICATED — everything below is gated
# ═════════════════════════════════════════════════════════════════════

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📄 DocRAG Search")
    authenticator.logout("Logout", key="sidebar_logout")
    st.caption(f"Signed in as **{st.session_state.get('name', '')}**")
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
        st.markdown("**Indexed Folders**")
        for d in dirs:
            name = d.get("directory") or "Root"
            st.caption(f"📁 {name} — {d['docs']} docs, {d['chunks']} chunks")

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
    st.caption(f"Model: `{MODEL_NAME}`")
    st.caption(f"DB: `{DB_PATH}`")


# ── Main Tabs ────────────────────────────────────────────────────────
tab_ask, tab_search, tab_docs, tab_settings = st.tabs(
    ["💬 Ask", "🔍 Search", "📄 Documents", "⚙️ Settings"]
)


# ────────── ASK TAB (chat interface) ─────────────────────────────────
with tab_ask:
    # Session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Render past messages
    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])
            if entry.get("sources"):
                with st.expander(f"📚 {len(entry['sources'])} sources"):
                    for i, s in enumerate(entry["sources"], 1):
                        st.caption(
                            f"**[{i}]** {s['label']} — Page {s['page']} "
                            f"(score {s['score']:.4f})"
                        )

    # Chat input (pinned to bottom)
    if prompt := st.chat_input("Ask a question about your documents…"):
        # Show user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Search
        chunks = hybrid_search(DB_PATH, prompt, top_k=TOP_K)

        # Build source list for display
        sources = []
        for c in chunks:
            label = (
                f"{c.get('directory', '')}/{c['filename']}"
                if c.get("directory")
                else c["filename"]
            )
            sources.append({"label": label, "page": c["page"], "score": c["score"]})

        # Assistant response
        with st.chat_message("assistant"):
            if not chunks:
                msg = "No relevant documents found. Try different terms or index more documents."
                st.warning(msg)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": msg}
                )
            else:
                # Sources expander
                with st.expander(f"📚 {len(sources)} sources", expanded=False):
                    for i, s in enumerate(sources, 1):
                        st.caption(
                            f"**[{i}]** {s['label']} — Page {s['page']} "
                            f"(score {s['score']:.4f})"
                        )

                # Stream Claude response
                response = st.write_stream(stream_claude(prompt, chunks))

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": response, "sources": sources}
                )


# ────────── SEARCH TAB ───────────────────────────────────────────────
with tab_search:
    query = st.text_input(
        "Search query:",
        key="search_input",
        placeholder="Search your documents…",
    )

    if st.button("Search", type="primary", key="search_btn") and query:
        with st.spinner("Searching…"):
            st.session_state.search_results = hybrid_search(
                DB_PATH, query, top_k=TOP_K
            )
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
            with st.expander(
                f"**#{i}** {source} — Page {r['page']}  "
                f"(score {r['score']:.4f})"
            ):
                st.text(r["text"])


# ────────── DOCUMENTS TAB ────────────────────────────────────────────
with tab_docs:
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

        if st.button("💾 Save uploaded files"):
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
        for r in rows:
            r = dict(r)
            c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 2, 0.5])
            label = (
                f"{r['directory']}/{r['filename']}"
                if r["directory"]
                else r["filename"]
            )
            c1.markdown(f"📄 {label}")
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
        st.info(
            "No documents indexed yet. Upload PDFs above, then click "
            "**Re-index Documents** in the sidebar."
        )


# ────────── SETTINGS TAB ────────────────────────────────────────────
with tab_settings:
    st.markdown("### Application Settings")
    st.caption(f"Stored in `{SETTINGS_FILE}`")
    st.divider()

    # Reload fresh from disk so edits aren't stale
    _live = load_settings()

    # -- Paths --
    st.markdown("**Paths**")
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

    # -- API --
    st.markdown("**API**")
    new_api_key = st.text_input(
        "Anthropic API key",
        value=_live.get("anthropic_api_key", ""),
        type="password",
        help="Required for the Ask (Claude) feature. Stored locally in settings.json.",
    )
    new_model = st.text_input(
        "Claude model",
        value=_live["model_name"],
    )

    # -- Search / Ingestion --
    st.markdown("**Search & Ingestion**")
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
