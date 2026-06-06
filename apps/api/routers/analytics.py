"""Public analytics: salary aggregates for the dashboard / salary explorer."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.db import get_session
from apps.api.schemas import SalaryTrendResponse, SalaryTrendRow

router = APIRouter(tags=["analytics"])

# Salary explorer: average INR salary by canonical metro. Adzuna stores the
# most-specific locality in `city` (e.g. "Richmond Town"), so fold known metros
# via substring match and drop the rest; INR-only keeps the average coherent
# (no mixing with USD remote postings). strpos avoids LIKE %-escaping with text().
_SALARY_SQL = text(
    """
    WITH base AS (
        SELECT
            CASE
                WHEN strpos(lower(city), 'bangalore') > 0
                    OR strpos(lower(city), 'bengaluru') > 0 THEN 'Bangalore'
                WHEN strpos(lower(city), 'mumbai') > 0 THEN 'Mumbai'
                WHEN strpos(lower(city), 'delhi') > 0 THEN 'Delhi'
                WHEN strpos(lower(city), 'gurgaon') > 0
                    OR strpos(lower(city), 'gurugram') > 0 THEN 'Gurugram'
                WHEN strpos(lower(city), 'noida') > 0 THEN 'Noida'
                WHEN strpos(lower(city), 'pune') > 0 THEN 'Pune'
                WHEN strpos(lower(city), 'hyderabad') > 0 THEN 'Hyderabad'
                WHEN strpos(lower(city), 'chennai') > 0 THEN 'Chennai'
                WHEN strpos(lower(city), 'kolkata') > 0 THEN 'Kolkata'
                WHEN strpos(lower(city), 'ahmedabad') > 0 THEN 'Ahmedabad'
                ELSE NULL
            END AS city,
            salary_min,
            salary_max
        FROM staging.jobs
        WHERE is_active = true AND is_duplicate = false
          AND currency = 'INR'
          AND (salary_min IS NOT NULL OR salary_max IS NOT NULL)
    )
    SELECT city,
           count(*) AS job_count,
           round(avg(salary_min)) AS avg_salary_min,
           round(avg(salary_max)) AS avg_salary_max
    FROM base
    WHERE city IS NOT NULL
    GROUP BY city
    HAVING count(*) >= :min_jobs
    ORDER BY job_count DESC
    LIMIT :limit
    """
)


@router.get("/analytics/salary-trend", response_model=SalaryTrendResponse)
def salary_trend(
    db: Session = Depends(get_session),
    min_jobs: int = Query(default=10, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SalaryTrendResponse:
    rows = db.execute(_SALARY_SQL, {"min_jobs": min_jobs, "limit": limit}).mappings().all()
    data = [SalaryTrendRow(**row) for row in rows]
    return SalaryTrendResponse(count=len(data), rows=data)
