"""Single job detail endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.db import get_session
from apps.api.schemas import JobDetail

router = APIRouter(tags=["jobs"])

_JOB_SQL = text(
    """
    SELECT id, title, company, city, state, country, source, source_url,
           salary_min, salary_max, currency, posted_date, skills,
           description, scraped_at
    FROM staging.jobs
    WHERE id = :job_id AND is_duplicate = false
    """
)


@router.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: int, db: Session = Depends(get_session)) -> JobDetail:
    row = db.execute(_JOB_SQL, {"job_id": job_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobDetail(**row)
