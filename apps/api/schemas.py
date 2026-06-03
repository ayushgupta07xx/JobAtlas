"""Pydantic response models for the JobAtlas API."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: int
    title: str
    company: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    source: str
    source_url: str
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    posted_date: date | None = None
    skills: list[str] | None = None
    scraped_at: datetime | None = None


class JobDetail(JobOut):
    description: str | None = None


class SearchHit(JobOut):
    score: float | None = None


class SearchResponse(BaseModel):
    count: int
    total: int = 0
    query: str | None = None
    results: list[SearchHit]


class SourceFacet(BaseModel):
    source: str
    count: int


class SalaryTrendRow(BaseModel):
    city: str
    job_count: int
    avg_salary_min: float | None = None
    avg_salary_max: float | None = None


class SalaryTrendResponse(BaseModel):
    count: int
    rows: list[SalaryTrendRow]
