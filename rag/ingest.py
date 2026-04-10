"""
PDF ingestion: extraction, chunking, embedding, and storage.
"""

import hashlib
import threading
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF

from .config import CHUNK_TARGET, CHUNK_OVERLAP, MIN_CHUNK_LEN, EMBED_BATCH_SIZE
from .db import get_db
from .embeddings import get_embedder, embed_texts, embedding_to_blob

# Ingestion progress (shared state)
ingest_status = {"running": False, "message": "", "progress": 0, "total": 0, "done": 0}
ingest_lock = threading.Lock()


def extract_pages(pdf_path: Path) -> list[dict]:
    pages = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({"page": page_num, "text": text})
        doc.close()
    except Exception as exc:
        print(f"  Could not read {pdf_path.name}: {exc}")
    return pages


def chunk_text(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        candidate = (current + "\n\n" + para) if current else para
        if len(candidate) <= CHUNK_TARGET:
            current = candidate
        else:
            if current:
                chunks.append(current)
                overlap_seed = current[-CHUNK_OVERLAP:] if len(current) > CHUNK_OVERLAP else current
                current = overlap_seed + "\n\n" + para
            else:
                for start in range(0, len(para), CHUNK_TARGET - CHUNK_OVERLAP):
                    piece = para[start : start + CHUNK_TARGET]
                    if len(piece) >= MIN_CHUNK_LEN:
                        chunks.append(piece)
                current = ""

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if len(c) >= MIN_CHUNK_LEN]


def file_hash(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def ingest_directory(db_path: str, docs_dir: str):
    global ingest_status
    docs_path = Path(docs_dir).resolve()

    if not docs_path.exists():
        with ingest_lock:
            ingest_status = {"running": False, "message": f"Directory not found: {docs_path}", "progress": 0, "total": 0, "done": 0}
        return

    pdf_files = sorted(docs_path.rglob("*.pdf"))
    if not pdf_files:
        with ingest_lock:
            ingest_status = {"running": False, "message": f"No PDF files found in {docs_path}", "progress": 0, "total": 0, "done": 0}
        return

    with ingest_lock:
        ingest_status = {"running": True, "message": f"Found {len(pdf_files)} PDFs...", "progress": 0, "total": len(pdf_files), "done": 0}

    conn = get_db(db_path)
    existing = {}
    for row in conn.execute("SELECT filename, file_hash FROM documents").fetchall():
        existing[row["filename"]] = row["file_hash"]

    get_embedder()  # pre-load

    new_count = 0
    skip_count = 0

    for i, pdf_path in enumerate(pdf_files):
        rel_path = str(pdf_path.relative_to(docs_path))
        fhash = file_hash(pdf_path)
        parent_dir = pdf_path.parent.name if pdf_path.parent != docs_path else "Root"

        with ingest_lock:
            ingest_status["message"] = f"Processing: {pdf_path.name}"
            ingest_status["done"] = i
            ingest_status["progress"] = int(100 * i / len(pdf_files))

        if rel_path in existing and existing[rel_path] == fhash:
            skip_count += 1
            continue

        old_doc = conn.execute("SELECT id FROM documents WHERE filename = ?", (rel_path,)).fetchone()
        if old_doc:
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (old_doc["id"],))
            conn.execute("DELETE FROM documents WHERE id = ?", (old_doc["id"],))

        pages = extract_pages(pdf_path)
        if not pages:
            continue

        all_chunks = []
        for page_data in pages:
            for ci, chunk_val in enumerate(chunk_text(page_data["text"])):
                all_chunks.append({"text": chunk_val, "page": page_data["page"], "chunk_index": ci})

        if not all_chunks:
            continue

        cur = conn.execute(
            "INSERT INTO documents (filename, directory, file_hash, pages, chunks_count, ingested_at) VALUES (?, ?, ?, ?, ?, ?)",
            (rel_path, parent_dir, fhash, len(pages), len(all_chunks), datetime.now().isoformat()),
        )
        doc_id = cur.lastrowid

        texts = [c["text"] for c in all_chunks]
        for batch_start in range(0, len(texts), EMBED_BATCH_SIZE):
            batch_end = min(batch_start + EMBED_BATCH_SIZE, len(texts))
            embeddings = embed_texts(texts[batch_start:batch_end])

            for j, emb in enumerate(embeddings):
                c = all_chunks[batch_start + j]
                conn.execute(
                    "INSERT INTO chunks (doc_id, text, page, chunk_index, embedding) VALUES (?, ?, ?, ?, ?)",
                    (doc_id, c["text"], c["page"], c["chunk_index"], embedding_to_blob(emb)),
                )

        conn.commit()
        new_count += 1
        print(f"  Ingested: {rel_path} ({len(pages)} pages, {len(all_chunks)} chunks)")

    conn.close()

    with ingest_lock:
        ingest_status = {
            "running": False,
            "message": f"Done. {new_count} new, {skip_count} skipped (unchanged).",
            "progress": 100, "total": len(pdf_files), "done": len(pdf_files),
        }

    print(f"\nIngestion complete: {new_count} new, {skip_count} skipped.")
