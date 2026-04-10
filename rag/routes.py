"""
Flask routes: API endpoints and HTML serving.
"""

import json
import os
import threading
from pathlib import Path

from flask import Flask, request, jsonify, Response
from werkzeug.utils import secure_filename

from .config import TOP_K, DOCS_DIR
from .db import get_db, db_stats
from .search import hybrid_search
from .claude import ask_claude
from .ingest import ingest_directory, ingest_status, ingest_lock, extract_pages


def _docs_root() -> Path:
    p = Path(DOCS_DIR).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def create_app(db_path: str) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB upload limit

    @app.route("/")
    def index():
        from .ui import HTML_PAGE
        return HTML_PAGE

    @app.route("/api/stats")
    def stats():
        return jsonify(db_stats(app.config["DB_PATH"]))

    @app.route("/api/ask", methods=["POST"])
    def ask():
        data = request.get_json()
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "No question provided"}), 400

        chunks = hybrid_search(app.config["DB_PATH"], question, top_k=TOP_K)

        sources = [
            {
                "filename":  c["filename"],
                "directory": c["directory"],
                "page":      c["page"],
                "preview":   c["text"][:300].replace("\n", " "),
                "score":     round(c["score"], 4),
            }
            for c in chunks
        ]

        def generate():
            yield "data: " + json.dumps({"sources": sources}) + "\n\n"
            if not chunks:
                yield "data: " + json.dumps({"delta": "No relevant passages found. Try different search terms or ingest more documents."}) + "\n\n"
                yield "data: " + json.dumps({"done": True}) + "\n\n"
                return
            yield from ask_claude(question, chunks)

        return Response(generate(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.route("/api/search", methods=["POST"])
    def search():
        data = request.get_json()
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "No question provided"}), 400

        chunks = hybrid_search(app.config["DB_PATH"], question, top_k=TOP_K)

        results = [
            {
                "filename":  c["filename"],
                "directory": c["directory"],
                "page":      c["page"],
                "text":      c["text"],
                "preview":   c["text"][:300].replace("\n", " "),
                "score":     round(c["score"], 4),
            }
            for c in chunks
        ]

        return jsonify({"results": results, "query": question})

    @app.route("/api/search/pdf", methods=["POST"])
    def search_by_pdf():
        from .search import search_by_document

        if "file" not in request.files:
            return jsonify({"error": "No PDF file provided"}), 400
        f = request.files["file"]
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            return jsonify({"error": "File must be a PDF"}), 400

        # Save to temp file, extract text, delete
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            f.save(tmp.name)
            tmp_path = Path(tmp.name)

        try:
            pages = extract_pages(tmp_path)
            if not pages:
                return jsonify({"error": "Could not extract text from PDF"}), 400
            full_text = "\n\n".join(p["text"] for p in pages)
            results = search_by_document(app.config["DB_PATH"], full_text, top_k=TOP_K)
        finally:
            tmp_path.unlink(missing_ok=True)

        return jsonify({
            "results": results,
            "query_filename": f.filename,
            "query_pages": len(pages),
        })

    @app.route("/api/ingest", methods=["POST"])
    def ingest_route():
        data = request.get_json()
        docs_dir = data.get("directory", "").strip()
        if not docs_dir:
            return jsonify({"error": "No directory provided"}), 400

        with ingest_lock:
            if ingest_status.get("running"):
                return jsonify({"error": "Ingestion already in progress"}), 409
            ingest_status["running"] = True
            ingest_status["message"] = "Starting..."
            ingest_status["progress"] = 0

        thread = threading.Thread(
            target=ingest_directory,
            args=(app.config["DB_PATH"], docs_dir),
            daemon=True,
        )
        thread.start()
        return jsonify({"status": "started", "directory": docs_dir})

    @app.route("/api/ingest/status")
    def ingest_status_route():
        with ingest_lock:
            return jsonify(ingest_status)

    @app.route("/api/documents")
    def list_documents():
        conn = get_db(app.config["DB_PATH"])
        rows = conn.execute(
            "SELECT id, filename, directory, pages, chunks_count, ingested_at "
            "FROM documents ORDER BY directory, filename"
        ).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/documents/<int:doc_id>", methods=["DELETE"])
    def delete_document(doc_id):
        conn = get_db(app.config["DB_PATH"])
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})

    # ─── File management (managed documents directory) ───

    @app.route("/api/files")
    def list_files():
        root = _docs_root()
        # Get set of already-ingested filenames from DB
        conn = get_db(app.config["DB_PATH"])
        ingested_rows = conn.execute("SELECT filename, file_hash, pages, chunks_count FROM documents").fetchall()
        conn.close()
        ingested = {}
        for r in ingested_rows:
            ingested[r["filename"]] = {"pages": r["pages"], "chunks": r["chunks_count"], "hash": r["file_hash"]}

        folders = {}
        for f in sorted(root.iterdir()):
            if f.is_file() and f.suffix.lower() == ".pdf":
                rel = f.name
                info = {"name": f.name, "ingested": rel in ingested}
                if rel in ingested:
                    info["pages"] = ingested[rel]["pages"]
                    info["chunks"] = ingested[rel]["chunks"]
                folders.setdefault("", []).append(info)
            elif f.is_dir() and not f.name.startswith("."):
                folder_files = []
                for p in sorted(f.iterdir()):
                    if p.is_file() and p.suffix.lower() == ".pdf":
                        rel = f.name + "/" + p.name
                        info = {"name": p.name, "ingested": rel in ingested}
                        if rel in ingested:
                            info["pages"] = ingested[rel]["pages"]
                            info["chunks"] = ingested[rel]["chunks"]
                        folder_files.append(info)
                folders[f.name] = folder_files
        return jsonify({"root": str(root), "folders": folders})

    @app.route("/api/files/upload", methods=["POST"])
    def upload_files():
        root = _docs_root()
        folder = request.form.get("folder", "").strip()
        # Sanitize folder name
        if folder:
            folder = secure_filename(folder)
        target = root / folder if folder else root
        target.mkdir(parents=True, exist_ok=True)

        uploaded = []
        for f in request.files.getlist("files"):
            if not f.filename:
                continue
            name = secure_filename(f.filename)
            if not name.lower().endswith(".pdf"):
                continue
            dest = target / name
            f.save(str(dest))
            uploaded.append({"filename": name, "folder": folder})

        return jsonify({"uploaded": uploaded})

    @app.route("/api/files/folder", methods=["POST"])
    def create_folder():
        data = request.get_json()
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "No folder name"}), 400
        safe_name = secure_filename(name)
        if not safe_name:
            return jsonify({"error": "Invalid folder name"}), 400
        folder_path = _docs_root() / safe_name
        folder_path.mkdir(exist_ok=True)
        return jsonify({"folder": safe_name})

    @app.route("/api/files/move", methods=["POST"])
    def move_file():
        data = request.get_json()
        filename = data.get("filename", "")
        from_folder = data.get("from", "")
        to_folder = data.get("to", "")
        root = _docs_root()

        src = root / from_folder / filename if from_folder else root / filename
        if not src.is_file():
            return jsonify({"error": "File not found"}), 404
        # Ensure src is under root
        if not str(src.resolve()).startswith(str(root)):
            return jsonify({"error": "Invalid path"}), 400

        if to_folder:
            safe_to = secure_filename(to_folder)
            dest_dir = root / safe_to
        else:
            dest_dir = root
        dest_dir.mkdir(exist_ok=True)

        dest = dest_dir / filename
        if not str(dest.resolve()).startswith(str(root)):
            return jsonify({"error": "Invalid path"}), 400

        src.rename(dest)
        return jsonify({"status": "moved", "to": to_folder})

    @app.route("/api/files/delete", methods=["POST"])
    def delete_file():
        data = request.get_json()
        filename = data.get("filename", "")
        folder = data.get("folder", "")
        root = _docs_root()

        target = root / folder / filename if folder else root / filename
        if not str(target.resolve()).startswith(str(root)):
            return jsonify({"error": "Invalid path"}), 400
        if target.is_file():
            target.unlink()
        return jsonify({"status": "deleted"})

    @app.route("/api/files/ingest", methods=["POST"])
    def ingest_managed():
        """Ingest all files from the managed documents directory."""
        root = _docs_root()
        with ingest_lock:
            if ingest_status.get("running"):
                return jsonify({"error": "Ingestion already in progress"}), 409
            # Mark running immediately so polls/re-clicks don't double-fire
            ingest_status["running"] = True
            ingest_status["message"] = "Starting..."
            ingest_status["progress"] = 0
        thread = threading.Thread(
            target=ingest_directory,
            args=(app.config["DB_PATH"], str(root)),
            daemon=True,
        )
        thread.start()
        return jsonify({"status": "started", "directory": str(root)})

    return app
