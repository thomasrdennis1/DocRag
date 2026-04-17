"""
Configuration — loads from settings.json, falls back to defaults.
"""

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "settings.json"

_DEFAULTS = {
    "db_path":          "./rag_search.db",
    "docs_dir":         "./documents",
    "port":             5001,
    "top_k":            12,
    "model_name":       "claude-sonnet-4-6",
    "embed_model":      "all-MiniLM-L6-v2",
    "chunk_target":     1200,
    "chunk_overlap":    200,
    "min_chunk_len":    80,
    "embed_batch_size": 128,
    "embed_dim":        384,
    "anthropic_api_key": "",
}


def load_settings() -> dict:
    """Read settings.json, creating it from defaults if missing."""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE) as f:
            saved = json.load(f)
        # Merge with defaults so new keys are always present
        merged = {**_DEFAULTS, **saved}
        return merged
    save_settings(_DEFAULTS)
    return dict(_DEFAULTS)


def save_settings(settings: dict):
    """Write settings dict to settings.json."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def get(key: str):
    """Get a single setting value."""
    return load_settings().get(key, _DEFAULTS.get(key))


# ── Module-level constants (read once at import) ─────────────────────
_s = load_settings()

DEFAULT_DB       = _s["db_path"]
DEFAULT_PORT     = _s["port"]
DOCS_DIR         = _s["docs_dir"]
TOP_K            = _s["top_k"]
MODEL_NAME       = _s["model_name"]
EMBED_MODEL      = _s["embed_model"]
CHUNK_TARGET     = _s["chunk_target"]
CHUNK_OVERLAP    = _s["chunk_overlap"]
MIN_CHUNK_LEN    = _s["min_chunk_len"]
EMBED_BATCH_SIZE = _s["embed_batch_size"]
EMBED_DIM        = _s["embed_dim"]
