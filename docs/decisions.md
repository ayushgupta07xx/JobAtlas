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

## ADR-0004 — Source reliability: APIs for volume, JS scrapes best-effort

**Status:** Accepted

**Context:** Wellfound (and likely Naukri) deploy managed bot protection
(Cloudflare/DataDome-style). Our scrapy-playwright spider with a real Chrome
fingerprint renders the listing and lands jobs whenever a request returns 200
(verified: 585 KB / 42 jobs in recon), but after a burst of automated hits the
IP is reputation-flagged and returns 403 for an indeterminate cooldown. §19
anticipated exactly this.

**Decision:** Treat JS-scraped sources (Wellfound, and later Naukri/Hirist/
Instahyre) as best-effort/opportunistic. Do NOT escalate evasion — residential
proxies, stealth plugins, JS-challenge/CAPTCHA solving — which crosses the
LEGAL.md + §21 rule 6 politeness/ToS line and is over-engineering. Guaranteed
volume comes from official APIs (Adzuna ~3k/refresh, Jobicy supplementary).
Retain the Wellfound spider; run it spaced out / via the daily scrape; accept
intermittent yield.

**Consequences:** The volume floor rests on API sources (defensible per §19's
fallback). The Scrapy + Playwright keyword stays fully earned — the spider is
built, renders, and lands when unblocked. No new dependencies (no proxy/stealth
stack). Wellfound to be re-validated on a clean session in a few days.

## ADR-0005 — Normalizer reads bulk fields from Postgres, Mongo only for MinHash

**Context:** `raw.jobs_raw.payload` (JSONB) mirrors the Mongo payload, but the
128-perm MinHash signature lives only in the Mongo raw doc.

**Decision:** The Day-5 normalizer (`apps/normalizer/`) iterates `raw.jobs_raw`
(gives `raw_id` lineage + payload), batch-fetches `minhash_signature` from Mongo
by `mongo_object_id`, parses per-source (`adzuna`, `jobicy`), and UPSERTs into
`staging.jobs` on `(source, source_url)` — idempotent across re-runs, with
in-batch dedup (last id wins) to avoid ON CONFLICT double-affect. Adzuna India →
INR/IN; Jobicy currency from `salaryCurrency`, country from `jobGeo`→ISO-3166
(unknown/worldwide → `ZZ`). Skills via deterministic keyword match (best-effort).
HTML sources (Wellfound/Naukri) are skipped until a real raw doc exists.

**Consequences:** Re-runnable normalization; location/skills are best-effort;
cross-source dedup on the carried MinHash is Day 7.

## ADR-0006 — Custom Airflow image with an isolated app venv (first Dockerfile, Day 6)

**Context:** DAG tasks run inside the Airflow containers, which on the stock image
lack our deps/code/DB env. Installing our package directly into Airflow's env
upgrades SQLAlchemy to 2.0 (our models use the 2.0 DeclarativeBase API), but
Airflow 2.9 pins SQLAlchemy <2.0 and its ORM breaks under 2.0.

**Decision:** `orchestration/airflow/Dockerfile` extends the stock image and builds
a SEPARATE venv at `/opt/jobatlas-venv` (`pip install .` -> scrapy, pymongo,
datasketch, psycopg, SQLAlchemy 2.0; no torch). Airflow's own env stays at 1.4. DAG
files import only airflow/pendulum; all app work runs via
`/opt/jobatlas-venv/bin/python -m ...` BashOperators (scrape, normalize,
jobatlas.dedup, jobatlas.report). Live code is bind-mounted and wins via PYTHONPATH.
Service-name DB URLs + Connections/Variables come from the Airflow env. First
Dockerfile lands at Day 6 (vs Day 13); hadolint hook (deferred #3) comes due.

**Consequences:** Image rebuild when app deps change (e.g. sentence-transformers for
embeddings_refresh, which will run in the same venv). Playwright browsers omitted —
JS spiders stay host/best-effort (ADR-0004).

## ADR-0007 — Dedup recomputes MinHash over title+company+city, not the carried full-text signature

**Context:** The scrape-time MinHash (`staging.jobs.minhash_signature`) spans
title+company+location+description. Aggregators (e.g. Turing) post many DISTINCT
roles with near-identical boilerplate descriptions, so full-text Jaccard exceeds 0.85
across different roles — the first dedup run merged 33 distinct Turing postings into
one "duplicate" group. False positive: distinct roles, not reposts.

**Decision:** `jobatlas.dedup` recomputes the MinHash over title+company+city
(role-identity), not the carried full-text signature. Same num_perm=128, 3-word
shingles, Jaccard via Variable `dedup_jaccard`. The carried signature stays in the
column for lineage.

**Consequences:** Dedup groups true reposts (same role+company+city) and no longer
collapses distinct roles sharing boilerplate. Cross-source dedup with differing title
formatting may need a fuzzier key later; revisit when real cross-source overlap exists.

## ADR-0008 — dbt in an isolated venv with a multi-target profile
**Context:** dbt's transitive pins (jinja2/agate/protobuf) conflict with the app `.venv` (torch-cpu, scrapy, sentence-transformers, SQLAlchemy 2.0); the project also needs Postgres + BigQuery + Snowflake targets.
**Decision:** Dedicated `.venv-dbt` at repo root (gitignored), mirroring the Airflow isolated-venv precedent (ADR-0006). One committed `profiles.yml` (secrets via `env_var`) with postgres/bigquery/snowflake targets — only postgres exercised locally. Marts materialize into the existing `marts` schema (migration 0001); staging/intermediate into `dbt_staging`/`dbt_intermediate` via a `generate_schema_name` override. Layered staging → intermediate → marts; dbt_utils for surrogate keys and date spine.
**Consequences:** dbt deps isolated from app code; profiles portable. BigQuery target waits on GCP setup (deferred), Snowflake on the Day-10 trial. dbt SQL is excluded from the repo sqlfluff hook via `.sqlfluffignore`.

## ADR-0009 — dim_job as SCD Type 2 via dbt snapshot (check strategy)
**Context:** Resume contract commits to SCD Type 2 on dim_job tracking title/salary/description changes.
**Decision:** YAML-defined snapshot `dim_job_snapshot` (dbt 1.9+ form) over `int_jobs_active`, `check` strategy on [title, company, salary_min, salary_max, description], `unique_key=id`, schema `snapshots`. The `dim_job` mart reads the snapshot, exposing `job_version_sk` / stable `job_sk` / `dbt_valid_from` / `dbt_valid_to` / `is_current`; `fact_jobs` joins via `job_sk`.
**Consequences:** Initial snapshot is the baseline (0 changes); versions accrue as `daily_scrape` re-runs mutate source rows, growing toward the ≥100-version target. Star covered by 28 tests.

## ADR-0010 — Multi-warehouse via target-gated dbt models + seeds
**Context:** The product contract commits to dbt models materializing into both BigQuery and Snowflake. Source data lives in Postgres; the other warehouses have no live connection to it.
**Decision:** `profiles.yml` carries postgres/snowflake/bigquery targets. Models are target-gated: Postgres reads the live `staging.jobs` source and unnests `skills` natively; non-Postgres targets read CSV seeds (`jobs_seed`, pre-unnested `job_skills_seed`) and use dialect-appropriate date functions (`dayofweek`/`dayname` vs `extract(dow)`/`to_char(...,'Day')`). `stg_jobs_embeddings` is disabled off-Postgres (pgvector-only). Fresh warehouses build with `dbt build` (DAG-ordered). Seeds are gitignored (scraped content; LEGAL no-redistribution) and regenerated via `\copy` (documented in `docs/multi-warehouse.md`).
**Consequences:** Identical star schema + SCD2 build on Postgres and Snowflake (502/264 parity, 28 tests green on each). BigQuery target ready, pending GCP setup. Snowflake uses a dedicated `TRANSFORM` role + X-SMALL auto-suspend warehouse; it is a 30-day-trial demonstration, not the free-forever stack (Postgres/DuckDB).

---

## ADR-0011 — Change Data Capture via Debezium (Postgres -> Redpanda -> Snowflake)

**Status:** Accepted (Day 11)

**Context**
The warehouse must reflect operational changes to `staging.jobs` without batch reloads or dual writes. Postgres is the system of record; Snowflake is the live analytical target during the trial.

**Decision**
- Enable Postgres logical replication (`wal_level=logical`) with publication `jobatlas_cdc_pub` over `staging.jobs` and `REPLICA IDENTITY FULL`.
- Capture changes with the Debezium Postgres connector (`pgoutput`) on a Kafka Connect worker against the existing Redpanda broker.
- Emit to a single topic `cdc.jobs` (RegexRouter rename), schema-less JSON, `decimal.handling.mode=double` so `numeric` salaries are usable numbers.
- Sink with a Python consumer applying staged `MERGE`/`DELETE` to `JOBATLAS.CDC.JOBS_STREAM`, committing offsets only after a successful write (at-least-once with idempotent merges).

**Consequences**
- Near-real-time warehouse sync, no polling.
- The consumer exposes a second sink seam for BigQuery, deferred until GCP setup.
- `cdc.companies` deferred: no operational companies table exists yet (`dim_company` is a dbt mart); revisit with a `staging.companies` table.

## ADR-0012 — Great Expectations runs in an isolated `.venv-gx`

**Context:** GX 1.x pulls a heavy dependency tree (pandas, numpy, SQLAlchemy 2.x, altair, marshmallow) that conflicts with the app `.venv`'s pinned Scrapy / confluent-kafka / snowflake-connector stack. Airflow's own runtime is pinned to SQLAlchemy 1.4.52, which GX 1.x does not support either.

**Decision:** GX lives in a dedicated `.venv-gx`, with deps in `warehouse/great_expectations/requirements.txt`, mirroring the `.venv-dbt` isolation pattern from ADR-0008. Suites are defined programmatically via the GX 1.x Fluent API (no CLI scaffold) and validated against local Postgres via a file-backed context at `warehouse/great_expectations/gx/`. The Airflow integration bakes GX into its own venv inside the `jobatlas/airflow:2.9.3` image, separate from both Airflow's env and the baked `/opt/jobatlas-venv`; the app `.venv` is never modified.

**Status:** Accepted.

## ADR-0013: pgvector HNSW queries set hnsw.ef_search = 400

The HNSW `ef_search` GUC defaults to 40, silently capping `ORDER BY embedding <=> q LIMIT N` to ~40 rows regardless of N. This had crippled `/search` and `/match` to ~40 of 9,014 jobs and produced phantom pagination — `total` counted all matches while the pool ran dry past ~40. Every similarity query now sets `ef_search ≥ pool size` before running (`search.py`, `match.py`, `bench_match_latency.py`); call sites carry inline comments.
