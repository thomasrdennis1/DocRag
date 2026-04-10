"""
Embedding model: lazy-loaded singleton + helpers.
"""

import threading
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import EMBED_MODEL

_embedder = None
_embedder_lock = threading.Lock()


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                print(f"Loading embedding model: {EMBED_MODEL} ...")
                _embedder = SentenceTransformer(EMBED_MODEL)
                print("Embedding model loaded.")
    return _embedder


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_embedder()
    return model.encode(texts, show_progress_bar=False, normalize_embeddings=True)


def embedding_to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def blob_to_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)
