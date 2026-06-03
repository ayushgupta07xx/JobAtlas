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

# When there's a query, results are limited to the top-N most relevant jobs
# (the candidate pool); the chosen sort then orders within that pool, so
# Recency / Salary stay scoped to the search instead of the whole index.
_RELEVANT_POOL = 200


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
    if sort == "salary":
        filters.append("(j.salary_min IS NOT NULL OR j.salary_max IS NOT NULL)")
    where = " AND ".join(filters)

    has_query = bool(q)

    # Order applied to the result set. Unqualified column names work for both the
    # single-table browse query and the SELECT over the candidate pool.
    if sort == "salary":
        result_order = "COALESCE(salary_max, salary_min) DESC, posted_date DESC NULLS LAST"
    elif sort == "recency":
        result_order = "posted_date DESC NULLS LAST, scraped_at DESC"
    else:  # relevance
        result_order = "score DESC" if has_query else "posted_date DESC NULLS LAST, scraped_at DESC"

    join = "JOIN staging.jobs_embeddings e ON e.job_id = j.id" if has_query else ""
    matching = int(
        db.execute(
            text(f"SELECT count(*) FROM staging.jobs j {join} WHERE {where}"),
            fparams,
        ).scalar_one()
    )

    params: dict[str, object] = {**fparams, "limit": limit, "offset": offset}
    if has_query:
        assert q  # guaranteed by has_query; narrows for the type checker
        vec = embed_text(q)
        params["qvec"] = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        params["pool"] = _RELEVANT_POOL
        total = min(_RELEVANT_POOL, matching)
        sql = text(
            f"""
            WITH pool AS (
                SELECT {_BASE_COLS},
                       1 - (e.embedding <=> CAST(:qvec AS vector)) AS score
                FROM staging.jobs j
                JOIN staging.jobs_embeddings e ON e.job_id = j.id
                WHERE {where}
                ORDER BY e.embedding <=> CAST(:qvec AS vector)
                LIMIT :pool
            )
            SELECT * FROM pool
            ORDER BY {result_order}
            LIMIT :limit OFFSET :offset
            """
        )
    else:
        total = matching
        sql = text(
            f"""
            SELECT {_BASE_COLS}, NULL::float AS score
            FROM staging.jobs j
            WHERE {where}
            ORDER BY {result_order}
            LIMIT :limit OFFSET :offset
            """
        )

    rows = db.execute(sql, params).mappings().all()
    hits = [SearchHit(**row) for row in rows]
    return SearchResponse(count=len(hits), total=total, query=q, results=hits)
