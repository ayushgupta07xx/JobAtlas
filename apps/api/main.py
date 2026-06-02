"""JobAtlas API: unified search over India tech jobs (FastAPI + pgvector)."""

from __future__ import annotations

from fastapi import FastAPI

from apps.api.routers import analytics, jobs, match, search

app = FastAPI(title="JobAtlas API", version="0.1.0")
app.include_router(jobs.router)
app.include_router(search.router)
app.include_router(match.router)
app.include_router(analytics.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
