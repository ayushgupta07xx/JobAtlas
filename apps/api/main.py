"""JobAtlas API: unified search over India tech jobs (FastAPI + pgvector)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import analytics, jobs, match, search

app = FastAPI(title="JobAtlas API", version="0.1.0")
app.include_router(jobs.router)
app.include_router(search.router)
app.include_router(match.router)
app.include_router(analytics.router)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+|https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
