"""Lazy BGE-small loader via fastembed (ONNX, no torch).

Query-side embeddings for /search and /match. Uses the ONNX build of
BAAI/bge-small-en-v1.5 so the API stays lightweight (~200 MB) and fits
free-tier hosting. Vectors are compatible with the pgvector job
embeddings produced by sentence-transformers in the ingestion pipeline.
"""

from __future__ import annotations

from functools import lru_cache

from apps.api.config import settings


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.embedding_model)


@lru_cache(maxsize=512)
def embed_text(text_value: str) -> list[float]:
    vec = next(iter(_model().embed([text_value])))
    return [float(x) for x in vec]
