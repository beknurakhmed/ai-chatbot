"""
Celebrity lookalike service.
Compares user face embedding against a database of celebrity embeddings.
"""

import json
import numpy as np
from pathlib import Path

CELEB_DB_PATH = Path(__file__).parent.parent / "data" / "celebrities" / "embeddings.json"

_celeb_cache: list[dict] | None = None


def load_celebrity_db() -> list[dict]:
    """Load celebrity embeddings from JSON file."""
    global _celeb_cache
    if _celeb_cache is not None:
        return _celeb_cache

    if not CELEB_DB_PATH.exists():
        _celeb_cache = []
        return _celeb_cache

    try:
        data = json.loads(CELEB_DB_PATH.read_text(encoding="utf-8"))
        _celeb_cache = [
            {"name": item["name"], "embedding": np.array(item["embedding"], dtype=np.float32)}
            for item in data
        ]
    except Exception:
        _celeb_cache = []

    return _celeb_cache


def reload_celebrity_db():
    """Force reload of celebrity database."""
    global _celeb_cache
    _celeb_cache = None
    return load_celebrity_db()


def find_lookalike(embedding: np.ndarray, top_k: int = 3) -> list[dict]:
    """
    Find the closest celebrity matches for a given face embedding.
    Returns list of {name, similarity} sorted by similarity (highest first).
    """
    celebs = load_celebrity_db()
    if not celebs:
        return []

    emb_norm = embedding / (np.linalg.norm(embedding) + 1e-6)
    results = []

    for celeb in celebs:
        celeb_norm = celeb["embedding"] / (np.linalg.norm(celeb["embedding"]) + 1e-6)
        similarity = float(np.dot(emb_norm, celeb_norm))
        results.append({
            "name": celeb["name"],
            "similarity": round(similarity, 3),
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]
