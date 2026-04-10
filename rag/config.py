"""
Configuration constants for the RAG search application.
"""

DEFAULT_DB       = "./rag_search.db"
DEFAULT_PORT     = 5001
DOCS_DIR         = "./documents"
TOP_K            = 12
MODEL_NAME       = "claude-sonnet-4-6"
EMBED_MODEL      = "all-MiniLM-L6-v2"
CHUNK_TARGET     = 1200
CHUNK_OVERLAP    = 200
MIN_CHUNK_LEN    = 80
EMBED_BATCH_SIZE = 128
EMBED_DIM        = 384  # dimension for all-MiniLM-L6-v2
