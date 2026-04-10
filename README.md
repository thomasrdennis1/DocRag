# DocRag

Local document search engine that ingests PDFs and lets you search them with hybrid keyword + semantic vector search. Optionally uses Claude to synthesize answers from matched passages.

Everything runs locally except the optional Claude API calls. Your documents never leave your machine.

## Features

- **Hybrid Search** — combines SQLite FTS5 keyword search with vector cosine similarity (all-MiniLM-L6-v2), fused via reciprocal rank fusion
- **AI Answer Mode** — Claude reads matched passages and synthesizes an answer with citations
- **Direct Search Mode** — tabular results with ranked passages, no AI required
- **PDF Match Mode** — upload a PDF to find related documents in your library using vector + keyword similarity, aggregated to the document level with expandable chunk previews
- **File Management** — drag-and-drop upload, folder organization, batch ingestion
- **Dark/Light Themes**
- **Zero external dependencies at search time** — embeddings run locally, SQLite is the only database

## Quick Start

```bash
# Clone
git clone https://github.com/thomasrdennis1/DocRag.git
cd DocRag

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set API key for AI Answer mode
export ANTHROPIC_API_KEY="sk-ant-..."

# Run
python3 run.py
```

Open **http://localhost:5001** in your browser.

## Usage

### Ingest Documents

Drop PDFs into the `documents/` folder (or use the **Manage Files** tab to upload), then click **Ingest All Files**. Documents are chunked, embedded, and stored in a local SQLite database.

```bash
# Or auto-ingest a directory on startup
python3 run.py --docs ./path/to/pdfs
```

### Search Modes

| Mode | What it does | Needs API key |
|------|-------------|---------------|
| **AI Answer** | Searches docs, then Claude synthesizes an answer with citations | Yes |
| **Direct Search** | Returns ranked matching passages in a table | No |
| **PDF Match** | Upload a PDF → find related documents in your library | No |

### PDF Match

Upload any PDF and the app will:
1. Extract text and chunk it
2. Embed chunks and average into a document-level vector
3. Run vector similarity + keyword search against all stored documents
4. Return a ranked list of matching documents with expandable passage previews

The uploaded PDF is temporary — never stored or added to your database.

## CLI Options

```
python3 run.py --db ./my_docs.db    # custom database path
python3 run.py --port 5050          # custom port
python3 run.py --docs ./pdfs        # auto-ingest on startup
```

## Architecture

```
run.py              # Entry point, CLI args, auto-ingest
rag/
  config.py         # Constants (model, chunk size, TOP_K, etc.)
  db.py             # SQLite schema, connection helpers
  embeddings.py     # Sentence-transformer singleton, embed/blob helpers
  ingest.py         # PDF extraction (PyMuPDF), chunking, embedding, storage
  search.py         # FTS5 search, vector search, hybrid RRF, document-level search
  routes.py         # Flask API endpoints
  claude.py         # Claude streaming API integration
  ui.py             # Embedded HTML/CSS/JS frontend
```

## Models

- **Embeddings**: `all-MiniLM-L6-v2` (384-dim, runs locally via sentence-transformers)
- **LLM**: `claude-sonnet-4-6` (optional, for AI Answer mode only)

## Requirements

- Python 3.10+
- ~500 MB disk for the embedding model (downloaded on first run)
- No GPU required (CPU inference is fast for this model)
