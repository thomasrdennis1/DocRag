"""
SQLite database helpers: schema, connections, stats.
"""

import sqlite3
from pathlib import Path


DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    filename     TEXT NOT NULL,
    directory    TEXT,
    file_hash    TEXT NOT NULL,
    pages        INTEGER DEFAULT 0,
    chunks_count INTEGER DEFAULT 0,
    ingested_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id       INTEGER NOT NULL REFERENCES documents(id),
    text         TEXT NOT NULL,
    page         INTEGER,
    chunk_index  INTEGER,
    embedding    BLOB,
    UNIQUE(doc_id, page, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text,
    content='chunks',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;

CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.id, old.text);
    INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
END;
"""


def get_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db(db_path: str):
    conn = get_db(db_path)
    conn.executescript(DDL)
    conn.close()


def db_stats(db_path: str) -> dict:
    try:
        conn = get_db(db_path)
        total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        total_pages = conn.execute("SELECT COALESCE(SUM(pages), 0) FROM documents").fetchone()[0]
        dirs = conn.execute(
            "SELECT directory, COUNT(*) as docs, SUM(chunks_count) as chunks "
            "FROM documents GROUP BY directory ORDER BY chunks DESC"
        ).fetchall()
        conn.close()
        return {
            "total_chunks": total_chunks,
            "total_docs": total_docs,
            "total_pages": total_pages,
            "directories": [dict(r) for r in dirs],
            "db_path": db_path,
        }
    except Exception as e:
        return {"error": str(e), "total_chunks": 0, "total_docs": 0, "total_pages": 0, "directories": []}
