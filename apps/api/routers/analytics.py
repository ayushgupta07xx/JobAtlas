"""Public analytics: salary aggregates for the dashboard / salary explorer."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.db import get_session
from apps.api.schemas import SalaryTrendResponse, SalaryTrendRow

router = APIRouter(tags=["analytics"])

_SALARY_SQL = text(
    """
    SELECT j.city,
           count(*) AS job_count,
           round(avg(j.salary_min)) AS avg_salary_min,
           round(avg(j.salary_max)) AS avg_salary_max
    FROM staging.jobs j
    WHERE j.is_active = true AND j.is_duplicate = false
      AND j.city IS NOT NULL
      AND (j.salary_min IS NOT NULL OR j.salary_max IS NOT NULL)
    GROUP BY j.city
    HAVING count(*) >= :min_jobs
    ORDER BY job_count DESC
    LIMIT :limit
    """
)


@router.get("/analytics/salary-trend", response_model=SalaryTrendResponse)
def salary_trend(
    db: Session = Depends(get_session),
    min_jobs: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SalaryTrendResponse:
    rows = db.execute(_SALARY_SQL, {"min_jobs": min_jobs, "limit": limit}).mappings().all()
    data = [SalaryTrendRow(**row) for row in rows]
    return SalaryTrendResponse(count=len(data), rows=data)
