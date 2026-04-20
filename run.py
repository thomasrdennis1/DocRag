#!/usr/bin/env python3
"""
Document RAG Search — Local Desktop App
=========================================
Ingest PDFs and search them with natural language via Anthropic Claude.
Hybrid search: SQLite FTS5 keyword + vector cosine similarity with
reciprocal rank fusion.

SETUP:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY="sk-ant-..."

USAGE:
    python run.py                                # default DB + port
    python run.py --db ./my_docs.db              # custom database path
    python run.py --port 5050                    # custom port
    python run.py --docs ./path/to/pdfs          # auto-ingest on startup

    Then open: http://localhost:5001
"""

import os
import socket
import sys
import argparse
import threading
from pathlib import Path

from app.config import DEFAULT_DB, DEFAULT_PORT, DOCS_DIR, MODEL_NAME, APP_DIR, get as cfg_get
from app.db import init_db
from app.routes import create_app
from app.ingest import ingest_directory


def main():
    parser = argparse.ArgumentParser(
        description="Document RAG Search — local desktop app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--db",   default=DEFAULT_DB,   help=f"SQLite database path (default: {DEFAULT_DB})")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--docs", default=None, help="Auto-ingest PDFs from this directory on startup")
    args = parser.parse_args()

    init_db(args.db)

    # Ensure managed documents directory exists
    docs_path = Path(DOCS_DIR).resolve()
    docs_path.mkdir(parents=True, exist_ok=True)

    # Load API key from env or settings.json
    api_key = os.environ.get("ANTHROPIC_API_KEY", "") or cfg_get("anthropic_api_key") or ""
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key
    else:
        print("\nANTHROPIC_API_KEY not set.")
        print("Get a key at: https://console.anthropic.com")
        print("Then:  export ANTHROPIC_API_KEY='sk-ant-...'  and restart.\n")

    ingest_dir = args.docs or str(docs_path)
    # Only auto-ingest if there are PDFs to process
    target = Path(ingest_dir).resolve()
    if any(target.rglob("*.pdf")):
        print(f"\nAuto-ingesting from: {ingest_dir}")
        thread = threading.Thread(target=ingest_directory, args=(args.db, ingest_dir), daemon=True)
        thread.start()

    app = create_app(args.db)

    # Resolve port: 0 means pick a free port dynamically
    port = args.port
    if port == 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]

    url = f"http://localhost:{port}"

    # Machine-readable line for Electrobun to detect the port
    print(f"DOCRAG_PORT={port}", flush=True)

    print(f"\nDocument RAG Search running at {url}")
    print(f"Database: {Path(args.db).resolve()}")
    print(f"Documents: {docs_path}")
    print(f"App Data: {APP_DIR}")
    print(f"Model: {MODEL_NAME}")
    print(f"\nOpen {url} in your browser. Press Ctrl+C to stop.\n")

    try:
        import webbrowser
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    except Exception:
        pass

    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
