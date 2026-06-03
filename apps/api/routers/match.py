"""Resume match endpoint: upload resume -> embed -> ranked jobs (pgvector)."""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from apps.api.config import settings
from apps.api.db import get_session
from apps.api.embeddings import embed_text
from apps.api.schemas import SearchHit, SearchResponse
from jobatlas.sources import MATCH_EXCLUDED_SOURCES

router = APIRouter(tags=["match"])

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
    LIMIT :limit
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


@router.post("/match", response_model=SearchResponse)
def match(
    db: Session = Depends(get_session),
    file: UploadFile = File(...),
    limit: int = Query(default=settings.search_default_limit, ge=1, le=settings.search_max_limit),
) -> SearchResponse:
    raw = file.file.read()
    resume_text = _extract_text(file, raw).strip()
    if not resume_text:
        raise HTTPException(status_code=422, detail="Could not extract resume text")
    vec = embed_text(resume_text)
    qvec = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
    rows = (
        db.execute(
            _MATCH_SQL,
            {"qvec": qvec, "limit": limit, "excluded": list(MATCH_EXCLUDED_SOURCES)},
        )
        .mappings()
        .all()
    )
    hits = [SearchHit(**row) for row in rows]
    return SearchResponse(count=len(hits), query="resume", results=hits)
