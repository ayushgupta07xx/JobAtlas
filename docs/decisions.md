# Architecture Decisions

Chronological record of architectural decisions for JobAtlas. Each entry is short: what was chosen, what was considered, why.

---

## 2026-05-19 — Initial stack

**Decision.** Python 3.11, Postgres 16 + pgvector, MongoDB for raw zone, Redpanda for streaming, MinIO for local object storage, Airflow for orchestration, dbt for transformations targeting BigQuery and Snowflake in parallel.

**Why.** Each role this repo targets (Data Analyst, Product Analyst, Business Analyst, Data Engineer) needs a different surface area. The stack gives a credible end-to-end path for all four without piling on tools that don't earn their slot.

**Alternatives considered.** Single-warehouse (BigQuery only): rejected because dual-warehouse demonstrates dbt's adapter-agnostic property. Kafka over Redpanda: equivalent semantics, Redpanda runs in fewer containers locally.

## ADR-0002 — Table ownership: Alembic (OLTP) vs dbt (marts)
**Status:** Accepted (Day 2)
**Context:** §8 Day 2 lists `marts.fact_jobs`/`dim_*`, but §8 Day 8–9 has dbt build the star schema (SCD Type 2 via snapshots). Two owners of `marts.*` causes drift.
**Decision:** Alembic owns `raw.jobs_raw`, `staging.jobs`, `staging.jobs_embeddings` and creates the empty `marts` schema. dbt (dbt-postgres locally; BigQuery/Snowflake later) owns all tables inside `marts.*`. First migration is hand-authored for reliable pgvector/HNSW DDL.
**Consequence:** Star-schema keywords earned by dbt (Day 8–9), unchanged. Reversible if we later want Alembic-managed marts.
**Note:** Alembic lives at repo root (`alembic/` + `alembic.ini`), the standard convention, rather than §9's `warehouse/sql/migrations/` placeholder.

## ADR-0003 — Single Scrapy project for all sources

**Status:** Accepted

**Context:** §9 sketches per-source scraper directories (`scrapers/adzuna_api/`,
`scrapers/wellfound/`, ...). Scrapy is designed around a single project: one
settings module, shared `items.py` / `pipelines.py` / `middlewares.py`, and a
`spiders/` package with one spider per source. Sibling project dirs would
duplicate settings and the MinHash/Mongo/Postgres pipeline per source.

**Decision:** One Scrapy project at `scrapers/` (package `jobatlas_scrapers/`),
one spider module per source under `spiders/` (adzuna, wellfound, naukri, ...).
Shared item schema, pipelines, middlewares, settings live once at the package
root. Mirrors ADR-0002's "standard tool convention over placeholder path".

**Consequences:** `scrapy` commands run from `scrapers/`; adding a source is one
file in `spiders/`. §9's per-source directory sketch is superseded for scrapers
(documented here; no other code change). Raw payloads still land per §8: API
JSON -> Mongo `raw_api_responses`, HTML -> Mongo `raw_html`, plus the CDC-able
copy in `raw.jobs_raw`.
