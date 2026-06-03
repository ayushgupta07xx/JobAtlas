"""Resume match endpoint: upload resume -> embed -> ranked jobs (pgvector)."""

from __future__ import annotations

import io
import re
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from apps.api.config import settings
from apps.api.db import get_session
from apps.api.embeddings import embed_text
from apps.api.schemas import SearchHit, SearchResponse

router = APIRouter(tags=["match"])

# Mirrors jobatlas.sources.MATCH_EXCLUDED_SOURCES (source keys with
# exclude_from_match=True). Inlined so apps/api ships standalone to the HF
# Space without the jobatlas package; keep in sync if a source flag changes.
MATCH_EXCLUDED_SOURCES: frozenset[str] = frozenset({"remotive"})

RERANK_POOL = 50
W_COS = 0.6
W_SKILL = 0.4

_MATCH_SQL = text(
    """
    SELECT j.id, j.title, j.company, j.city, j.state, j.country, j.source,
           j.source_url, j.salary_min, j.salary_max, j.currency, j.posted_date,
           j.skills, j.scraped_at,
           1 - (e.embedding <=> CAST(:qvec AS vector)) AS score
    FROM staging.jobs j
    JOIN staging.jobs_embeddings e ON e.job_id = j.id
    WHERE j.is_active = true AND j.is_duplicate = false
      AND j.source NOT IN :excluded
    ORDER BY e.embedding <=> CAST(:qvec AS vector)
    LIMIT :pool
    """
).bindparams(bindparam("excluded", expanding=True))


def _extract_text(file: UploadFile, raw: bytes) -> str:
    name = (file.filename or "").lower()
    if name.endswith(".pdf") or file.content_type == "application/pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="Unsupported file type") from exc


def _as_skill_list(val: Any) -> list[str]:
    if isinstance(val, list):
        return [str(s).strip().lower() for s in val if str(s).strip()]
    if isinstance(val, str):
        return [p.strip().lower() for p in re.split(r"[;,]", val) if p.strip()]
    return []


def _resume_skills(resume_text: str, vocab: set[str]) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9+#. ]", " ", resume_text.lower())
    tokens = set(cleaned.split())
    found: set[str] = set()
    for skill in vocab:
        hit = skill in cleaned if " " in skill else skill in tokens
        if hit:
            found.add(skill)
    return found


def _rerank(rows: list[dict[str, Any]], resume_text: str, limit: int) -> list[dict[str, Any]]:
    per_job: dict[Any, set[str]] = {}
    vocab: set[str] = set()
    for r in rows:
        sk = set(_as_skill_list(r.get("skills")))
        per_job[r["id"]] = sk
        vocab |= sk
    rskills = _resume_skills(resume_text, vocab)

    def blended(r: dict[str, Any]) -> float:
        sk = per_job[r["id"]]
        cos = float(r.get("score") or 0.0)
        coverage = len(sk & rskills) / len(sk) if sk else 0.0
        return W_COS * cos + W_SKILL * coverage

    return sorted(rows, key=blended, reverse=True)[:limit]


@router.post("/match", response_model=SearchResponse)
def match(
    db: Session = Depends(get_session),
    file: UploadFile = File(...),
    limit: int = Query(default=settings.search_default_limit, ge=1, le=settings.search_max_limit),
    variant: str = Query(default="control"),
) -> SearchResponse:
    raw = file.file.read()
    resume_text = _extract_text(file, raw).strip()
    if not resume_text:
        raise HTTPException(status_code=422, detail="Could not extract resume text")
    vec = embed_text(resume_text)
    qvec = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
    pool = max(limit, RERANK_POOL) if variant == "test" else limit
    rows: list[dict[str, Any]] = [
        dict(r)
        for r in db.execute(
            _MATCH_SQL,
            {"qvec": qvec, "pool": pool, "excluded": list(MATCH_EXCLUDED_SOURCES)},
        )
        .mappings()
        .all()
    ]
    ranked = _rerank(rows, resume_text, limit) if variant == "test" else rows[:limit]
    hits = [SearchHit(**row) for row in ranked]
    return SearchResponse(count=len(hits), query="resume", results=hits)
