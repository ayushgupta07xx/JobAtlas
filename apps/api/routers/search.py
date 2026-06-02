"""Search endpoint: structured filters + optional pgvector semantic ranking."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.config import settings
from apps.api.db import get_session
from apps.api.embeddings import embed_text
from apps.api.schemas import SearchHit, SearchResponse

router = APIRouter(tags=["search"])

_BASE_COLS = """
    j.id, j.title, j.company, j.city, j.state, j.country, j.source,
    j.source_url, j.salary_min, j.salary_max, j.currency, j.posted_date,
    j.skills, j.scraped_at
"""


@router.get("/search", response_model=SearchResponse)
def search(
    db: Session = Depends(get_session),
    q: str | None = Query(default=None, description="Semantic query text"),
    city: str | None = None,
    source: str | None = None,
    salary_min: float | None = None,
    limit: int = Query(default=settings.search_default_limit, ge=1, le=settings.search_max_limit),
) -> SearchResponse:
    filters = ["j.is_active = true", "j.is_duplicate = false"]
    params: dict[str, object] = {"limit": limit}
    if city:
        filters.append("lower(j.city) = lower(:city)")
        params["city"] = city
    if source:
        filters.append("j.source = :source")
        params["source"] = source
    if salary_min is not None:
        filters.append("j.salary_max >= :salary_min")
        params["salary_min"] = salary_min
    where = " AND ".join(filters)

    if q:
        vec = embed_text(q)
        params["qvec"] = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        sql = text(
            f"""
            SELECT {_BASE_COLS},
                   1 - (e.embedding <=> CAST(:qvec AS vector)) AS score
            FROM staging.jobs j
            JOIN staging.jobs_embeddings e ON e.job_id = j.id
            WHERE {where}
            ORDER BY e.embedding <=> CAST(:qvec AS vector)
            LIMIT :limit
            """
        )
    else:
        sql = text(
            f"""
            SELECT {_BASE_COLS}, NULL::float AS score
            FROM staging.jobs j
            WHERE {where}
            ORDER BY j.posted_date DESC NULLS LAST, j.scraped_at DESC
            LIMIT :limit
            """
        )

    rows = db.execute(sql, params).mappings().all()
    hits = [SearchHit(**row) for row in rows]
    return SearchResponse(count=len(hits), query=q, results=hits)
