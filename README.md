# JobAtlas

> Unified search across India's tech job boards. Upload a resume, get ranked matches.

The Indian tech job market is split across eight-plus portals — Naukri, Wellfound, Hirist, Instahyre, Indeed, LinkedIn, Adzuna, Jobicy. Each has its own search, its own filters, its own quirks. A senior backend engineer looking for a role in Bangalore opens five tabs and pastes the same query into each. The result is dozens of overlapping postings and no good way to compare.

JobAtlas aggregates these sources into one searchable, deduplicated index. Drop in a resume and the matcher ranks postings by semantic similarity to your experience, not keyword overlap alone.

## Status

In active development. Architecture decisions in [`docs/decisions.md`](docs/decisions.md).

## Sources

| Source | Method |
|---|---|
| Naukri.com | Scrape |
| Wellfound | Scrape |
| Hirist | Scrape |
| Instahyre | Scrape |
| Indeed India | Scrape (limited) |
| Adzuna India | Official API |
| Jobicy | Official API |

## How it works

    scrapers → MongoDB (raw) → normalizer → Postgres (operational + pgvector)
                                              ↓
                                      dbt → BigQuery + Snowflake
                                              ↓
                                        FastAPI → Next.js

Resume matching uses sentence-transformers (`BGE-small-en-v1.5`) over a pgvector HNSW index. Change data capture is handled by Debezium streaming through Kafka. Orchestration is Airflow. Both warehouses are populated in parallel via dbt's multi-target build.

## Local setup

Prerequisites: Python 3.11, Docker, Docker Compose v2.

    git clone https://github.com/ayushgupta07xx/JobAtlas.git
    cd JobAtlas
    python3.11 -m venv .venv && source .venv/bin/activate
    pip install -e ".[dev]"
    pre-commit install
    cp .env.example .env
    docker compose up -d

## License & legal

Apache 2.0. Scraping practices documented in [`LEGAL.md`](LEGAL.md). Non-commercial.
