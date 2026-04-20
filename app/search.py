"""
Hybrid search: FTS5 keyword + vector cosine similarity with reciprocal rank fusion.
"""

import sqlite3
import numpy as np

from .config import TOP_K
from .db import get_db
from .embeddings import embed_texts, blob_to_embedding


STOP_WORDS = frozenset({
    "what", "when", "does", "happen", "with", "that", "this",
    "have", "from", "will", "their", "they", "been", "into",
    "than", "then", "some", "such", "about", "after", "should",
    "would", "could", "which", "there", "where", "how", "why",
    "are", "the", "and", "for", "not", "but", "can", "was",
})


def search_fts(conn: sqlite3.Connection, question: str, top_k: int) -> list[dict]:
    terms = [w for w in question.lower().split() if len(w) > 2 and w not in STOP_WORDS]
    if not terms:
        terms = question.lower().split()

    fts_phrase = f'"{question}"'
    fts_or = " OR ".join(f'"{t}"' for t in terms)

    sql = """
        SELECT c.id, c.doc_id, c.text, c.page, c.chunk_index, c.embedding,
               d.filename, d.directory, rank
        FROM chunks_fts
        JOIN chunks c ON chunks_fts.rowid = c.id
        JOIN documents d ON c.doc_id = d.id
        WHERE chunks_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """

    def run(query):
        try:
            return [dict(r) for r in conn.execute(sql, (query, top_k * 2)).fetchall()]
        except Exception:
            return []

    results = run(fts_phrase)
    if len(results) < top_k:
        or_results = run(fts_or)
        seen = {r["id"] for r in results}
        for r in or_results:
            if r["id"] not in seen:
                results.append(r)
                seen.add(r["id"])

    return results[:top_k * 2]


def search_vector(conn: sqlite3.Connection, question: str, top_k: int) -> list[dict]:
    q_emb = embed_texts([question])[0]

    rows = conn.execute(
        "SELECT c.id, c.doc_id, c.text, c.page, c.chunk_index, c.embedding, "
        "d.filename, d.directory FROM chunks c JOIN documents d ON c.doc_id = d.id"
    ).fetchall()

    if not rows:
        return []

    ids = []
    embeddings = []
    row_data = {}

    for r in rows:
        r = dict(r)
        if r["embedding"]:
            ids.append(r["id"])
            embeddings.append(blob_to_embedding(r["embedding"]))
            row_data[r["id"]] = r

    if not embeddings:
        return []

    emb_matrix = np.stack(embeddings)
    scores = emb_matrix @ q_emb  # cosine similarity (normalized)

    top_indices = np.argsort(scores)[::-1][:top_k * 2]

    results = []
    for idx in top_indices:
        chunk_id = ids[idx]
        r = row_data[chunk_id]
        r["score"] = float(scores[idx])
        results.append(r)

    return results


def hybrid_search(db_path: str, question: str, top_k: int = TOP_K) -> list[dict]:
    conn = get_db(db_path)
    fts_results = search_fts(conn, question, top_k)
    vec_results = search_vector(conn, question, top_k)
    conn.close()

    # Reciprocal Rank Fusion (k=60)
    k = 60
    scores = {}
    chunk_data = {}

    for rank, r in enumerate(fts_results):
        cid = r["id"]
        scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank + 1)
        chunk_data[cid] = r

    for rank, r in enumerate(vec_results):
        cid = r["id"]
        scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank + 1)
        chunk_data[cid] = r

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    return [
        {
            "id": cid,
            "text": chunk_data[cid]["text"],
            "page": chunk_data[cid]["page"],
            "filename": chunk_data[cid]["filename"],
            "directory": chunk_data[cid]["directory"],
            "score": score,
        }
        for cid, score in ranked
    ]


def search_by_document(db_path: str, doc_text: str, top_k: int = TOP_K) -> list[dict]:
    """Search the database using full document text as the query.

    Embeds the document text (averaged across chunks), then finds the
    most similar stored chunks.  Also runs FTS on extracted key terms.
    Results are aggregated to the *document* level so callers get a
    ranked list of matching documents instead of raw chunks.
    """
    from .ingest import chunk_text  # local import to avoid circular

    # --- 1. Chunk the query document and embed --------------------------
    chunks = chunk_text(doc_text)
    if not chunks:
        return []

    chunk_embeddings = embed_texts(chunks)
    query_emb = chunk_embeddings.mean(axis=0)
    query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-10)

    # --- 2. Vector search with the aggregate embedding ------------------
    conn = get_db(db_path)

    rows = conn.execute(
        "SELECT c.id, c.doc_id, c.text, c.page, c.chunk_index, c.embedding, "
        "d.filename, d.directory FROM chunks c JOIN documents d ON c.doc_id = d.id"
    ).fetchall()

    if not rows:
        conn.close()
        return []

    ids, embeddings, row_data = [], [], {}
    for r in rows:
        r = dict(r)
        if r["embedding"]:
            ids.append(r["id"])
            embeddings.append(blob_to_embedding(r["embedding"]))
            row_data[r["id"]] = r

    vec_results = []
    if embeddings:
        emb_matrix = np.stack(embeddings)
        scores = emb_matrix @ query_emb
        top_indices = np.argsort(scores)[::-1][:top_k * 3]
        for idx in top_indices:
            chunk_id = ids[idx]
            r = row_data[chunk_id]
            r["score"] = float(scores[idx])
            vec_results.append(r)

    # --- 3. FTS on key extracted terms ----------------------------------
    # Take a representative sample of the query text for keyword search
    sample = doc_text[:3000]
    terms = [w for w in sample.lower().split()
             if len(w) > 3 and w not in STOP_WORDS and w.isalpha()]
    # Pick the most frequent substantive terms
    from collections import Counter
    top_terms = [t for t, _ in Counter(terms).most_common(15)]
    fts_query = " OR ".join(f'"{t}"' for t in top_terms) if top_terms else ""

    fts_results = []
    if fts_query:
        sql = """
            SELECT c.id, c.doc_id, c.text, c.page, c.chunk_index, c.embedding,
                   d.filename, d.directory, rank
            FROM chunks_fts
            JOIN chunks c ON chunks_fts.rowid = c.id
            JOIN documents d ON c.doc_id = d.id
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        try:
            fts_results = [dict(r) for r in conn.execute(sql, (fts_query, top_k * 3)).fetchall()]
        except Exception:
            pass

    conn.close()

    # --- 4. RRF at chunk level ------------------------------------------
    k = 60
    chunk_scores = {}
    chunk_data = {}

    for rank, r in enumerate(fts_results):
        cid = r["id"]
        chunk_scores[cid] = chunk_scores.get(cid, 0) + 1.0 / (k + rank + 1)
        chunk_data[cid] = r

    for rank, r in enumerate(vec_results):
        cid = r["id"]
        chunk_scores[cid] = chunk_scores.get(cid, 0) + 1.0 / (k + rank + 1)
        chunk_data[cid] = r

    # --- 5. Aggregate to document level ---------------------------------
    doc_scores: dict[str, dict] = {}   # keyed by "directory/filename"

    for cid, score in chunk_scores.items():
        c = chunk_data[cid]
        doc_key = (c.get("directory") or "") + "/" + c["filename"]
        if doc_key not in doc_scores:
            doc_scores[doc_key] = {
                "filename": c["filename"],
                "directory": c.get("directory", ""),
                "total_score": 0.0,
                "top_chunks": [],
                "matching_pages": set(),
            }
        entry = doc_scores[doc_key]
        entry["total_score"] += score
        entry["matching_pages"].add(c["page"])
        entry["top_chunks"].append({
            "page": c["page"],
            "preview": c["text"][:250].replace("\n", " "),
            "text": c["text"],
            "score": round(score, 4),
        })

    # Sort documents by aggregated score
    ranked_docs = sorted(doc_scores.values(), key=lambda d: d["total_score"], reverse=True)[:top_k]

    for doc in ranked_docs:
        doc["matching_pages"] = sorted(doc["matching_pages"])
        doc["top_chunks"] = sorted(doc["top_chunks"], key=lambda c: c["score"], reverse=True)[:3]
        doc["total_score"] = round(doc["total_score"], 4)

    return ranked_docs
