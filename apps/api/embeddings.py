"""Lazy BGE-small loader.

Imports sentence-transformers only on first use, so the API starts without
torch loaded and only pays the memory cost when a semantic query or resume
match actually needs an embedding.
"""

from __future__ import annotations

from functools import lru_cache

from apps.api.config import settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


@lru_cache(maxsize=512)
def embed_text(text_value: str) -> list[float]:
    vec = _model().encode(text_value, normalize_embeddings=True)
    return [float(x) for x in vec.tolist()]
