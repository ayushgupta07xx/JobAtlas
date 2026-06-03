"""Search endpoint: structured filters + sort modes (relevance / salary / recency)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.config import settings
from apps.api.db import get_session
from apps.api.embeddings import embed_text
from apps.api.schemas import SearchHit, SearchResponse, SourceFacet

router = APIRouter(tags=["search"])

_BASE_COLS = """
    j.id, j.title, j.company, j.city, j.state, j.country, j.source,
    j.source_url, j.salary_min, j.salary_max, j.currency, j.posted_date,
    j.skills, j.scraped_at
"""


@router.get("/sources", response_model=list[SourceFacet])
def sources(db: Session = Depends(get_session)) -> list[SourceFacet]:
    """Distinct active, non-duplicate sources with job counts (for the filter)."""
    sql = text(
        """
        SELECT j.source, count(*) AS count
        FROM staging.jobs j
        WHERE j.is_active = true AND j.is_duplicate = false
        GROUP BY j.source
        ORDER BY count DESC
        """
    )
    rows = db.execute(sql).mappings().all()
    return [SourceFacet(**row) for row in rows]


@router.get("/search", response_model=SearchResponse)
def search(
    db: Session = Depends(get_session),
    q: str | None = Query(default=None, description="Semantic query text"),
    city: str | None = None,
    source: str | None = Query(
        default=None, description="Comma-separated source filter (one or more)"
    ),
    salary_min: float | None = None,
    sort: str = Query(default="relevance", pattern="^(relevance|salary|recency)$"),
    limit: int = Query(default=settings.search_default_limit, ge=1, le=settings.search_max_limit),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    filters = ["j.is_active = true", "j.is_duplicate = false"]
    fparams: dict[str, object] = {}
    if city:
        filters.append("lower(j.city) = lower(:city)")
        fparams["city"] = city
    if source:
        srcs = [s.strip() for s in source.split(",") if s.strip()]
        if srcs:
            placeholders = ", ".join(f":src{i}" for i in range(len(srcs)))
            filters.append(f"j.source IN ({placeholders})")
            for i, s in enumerate(srcs):
                fparams[f"src{i}"] = s
    if salary_min is not None:
        filters.append("j.salary_max >= :salary_min")
        fparams["salary_min"] = salary_min
    where = " AND ".join(filters)

    # Semantic ranking applies only when there's a query AND the relevance sort.
    use_semantic = bool(q) and sort == "relevance"

    join = "JOIN staging.jobs_embeddings e ON e.job_id = j.id" if use_semantic else ""
    total = db.execute(
        text(f"SELECT count(*) FROM staging.jobs j {join} WHERE {where}"),
        fparams,
    ).scalar_one()

    params: dict[str, object] = {**fparams, "limit": limit, "offset": offset}
    if use_semantic:
        assert q  # guaranteed by use_semantic; narrows for the type checker
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
            LIMIT :limit OFFSET :offset
            """
        )
    else:
        # salary: highest first, unlisted salaries last. recency (and relevance
        # with no query): newest first.
        if sort == "salary":
            order_by = "j.salary_max DESC NULLS LAST, j.posted_date DESC NULLS LAST"
        else:
            order_by = "j.posted_date DESC NULLS LAST, j.scraped_at DESC"
        sql = text(
            f"""
            SELECT {_BASE_COLS}, NULL::float AS score
            FROM staging.jobs j
            WHERE {where}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
            """
        )

    rows = db.execute(sql, params).mappings().all()
    hits = [SearchHit(**row) for row in rows]
    return SearchResponse(count=len(hits), total=total, query=q, results=hits)
