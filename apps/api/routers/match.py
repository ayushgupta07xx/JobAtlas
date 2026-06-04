"""Resume match endpoint: upload resume -> embed -> ranked jobs (pgvector).

Mirrors /search's relevant-pool model: the resume embedding selects a top-N
candidate pool, then sort / source filter / pagination operate within it. The
A/B variant drives only the relevance ordering (control = cosine, test =
blended cosine + skill coverage).
"""

from __future__ import annotations

import io
import re
from datetime import date
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

# Candidate pool: the top-N jobs by resume similarity. Sort, source filter and
# pagination all operate within this relevant set (mirrors /search's
# _RELEVANT_POOL); the test-variant rerank blends over it.
MATCH_POOL = 200
W_COS = 0.6
W_SKILL = 0.4

# pgvector's HNSW index returns at most `hnsw.ef_search` candidates per query
# (default 40), which would cap the pool far below MATCH_POOL. Lift it.
_HNSW_EF_SEARCH = 400

_BASE_COLS = """
    j.id, j.title, j.company, j.city, j.state, j.country, j.source,
    j.source_url, j.salary_min, j.salary_max, j.currency, j.posted_date,
    j.skills, j.scraped_at
"""


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


def _rerank(rows: list[dict[str, Any]], resume_text: str) -> list[dict[str, Any]]:
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

    return sorted(rows, key=blended, reverse=True)


def _by_salary(r: dict[str, Any]) -> float:
    val = r.get("salary_max") or r.get("salary_min")
    return float(val) if val is not None else -1.0


def _by_recency(r: dict[str, Any]) -> tuple[int, date]:
    pd = r.get("posted_date")
    return (1, pd) if isinstance(pd, date) else (0, date.min)


@router.post("/match", response_model=SearchResponse)
def match(
    db: Session = Depends(get_session),
    file: UploadFile = File(...),
    limit: int = Query(default=settings.search_default_limit, ge=1, le=settings.search_max_limit),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="relevance", pattern="^(relevance|salary|recency)$"),
    source: str | None = Query(default=None, description="Comma-separated source filter"),
    variant: str = Query(default="control"),
) -> SearchResponse:
    raw = file.file.read()
    resume_text = _extract_text(file, raw).strip()
    if not resume_text:
        raise HTTPException(status_code=422, detail="Could not extract resume text")
    vec = embed_text(resume_text)
    qvec = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

    filters = [
        "j.is_active = true",
        "j.is_duplicate = false",
        "j.source NOT IN :excluded",
    ]
    params: dict[str, Any] = {
        "qvec": qvec,
        "pool": MATCH_POOL,
        "excluded": list(MATCH_EXCLUDED_SOURCES),
    }
    if source:
        srcs = [s.strip() for s in source.split(",") if s.strip()]
        if srcs:
            placeholders = ", ".join(f":src{i}" for i in range(len(srcs)))
            filters.append(f"j.source IN ({placeholders})")
            for i, s in enumerate(srcs):
                params[f"src{i}"] = s
    if sort == "salary":
        filters.append("(j.salary_min IS NOT NULL OR j.salary_max IS NOT NULL)")
    where = " AND ".join(filters)

    # Lift the HNSW candidate ceiling so the pool can reach MATCH_POOL.
    db.execute(text(f"SET hnsw.ef_search = {_HNSW_EF_SEARCH}"))

    pool_sql = text(
        f"""
        SELECT {_BASE_COLS},
               1 - (e.embedding <=> CAST(:qvec AS vector)) AS score
        FROM staging.jobs j
        JOIN staging.jobs_embeddings e ON e.job_id = j.id
        WHERE {where}
        ORDER BY e.embedding <=> CAST(:qvec AS vector)
        LIMIT :pool
        """
    ).bindparams(bindparam("excluded", expanding=True))
    rows: list[dict[str, Any]] = [dict(r) for r in db.execute(pool_sql, params).mappings().all()]

    if sort == "salary":
        ranked = sorted(rows, key=_by_salary, reverse=True)
    elif sort == "recency":
        ranked = sorted(rows, key=_by_recency, reverse=True)
    elif variant == "test":
        ranked = _rerank(rows, resume_text)
    else:
        ranked = rows  # control: pure cosine order (pool already sorted)

    total = len(rows)
    page = ranked[offset : offset + limit]
    hits = [SearchHit(**row) for row in page]
    return SearchResponse(count=len(hits), total=total, query="resume", results=hits)
