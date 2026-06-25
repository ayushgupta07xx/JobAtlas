# JobAtlas — Retrospective

A three-week build of a unified India tech job-discovery platform: ingest from 8 sources, deduplicate, model in a multi-warehouse dbt project, embed for semantic resume matching, instrument with product analytics, and ship a live web app — all on a free-forever stack.

## What shipped

- **Unified index** — 9,014 active, deduplicated postings across 8 live sources (10 spiders; Naukri + Wellfound built but bot-walled, ≈0 volume). MinHash dedup on a `title + company + city` signature collapsed a 13.5% duplicate rate (1,409 of 10,423 raw).
- **Multi-warehouse modeling** — one dbt project, 40 models on a star schema with SCD Type 2 on the job dimension, materialized to BigQuery and Snowflake (and Postgres in dev), 93 data tests green on each target. 502/264 seed-subset row parity across all three.
- **Semantic matching** — `BGE-small-en-v1.5` embeddings in a pgvector HNSW index; ~6 ms p95 retrieval over a 200-candidate pool (`scripts/bench_match_latency.py`, ef_search=400).
- **Streaming + orchestration** — Debezium CDC off Postgres into Kafka; Airflow DAGs for scrape, embeddings, and dedup.
- **Product analytics + experiment** — PostHog taxonomy (24 events, 3 funnels, 5 cohorts); a Bayesian A/B test on the match algorithm showing a +10.3% apply-click lift (CI [1.2%, 19.4%], P=98.6%), validated against a simulated cohort.
- **BI** — Tableau Public (market view, salary by city/role, skill heatmap, hiring velocity) and Looker Studio (executive KPIs), both public and incognito-verified.
- **Analyst + BA artifacts** — R salary regression (N=669 disclosed-salary postings), Excel executive workbook with native pivots, and the full BA suite (BRD, FRD, user stories, BPMN, SWOT, PESTLE, gap, personas, market sizing, Figma wireframes).
- **Live product** — Next.js 14 frontend on Vercel, FastAPI backend on Hugging Face Spaces, Neon Postgres, Cloudflare R2. Production runtime cost: ₹0/month.
- **Infra + CI** — Terraform modules (GCP, Snowflake, Vercel, PostHog), 5 GitHub Actions workflows, CI green.

## What went well

- **One dbt codebase, three warehouses.** Forcing the same models through Postgres, Snowflake, and BigQuery without per-warehouse forks held up — the dialect gaps were absorbed by cross-db macros and target conditionals (see ADR-0017), so adding a warehouse was a profile change, not a rewrite.
- **Precision-over-recall discipline on derived fields.** Experience extraction (ADR-0016) deliberately traded recall for precision so the salary dimension never ingests a fabricated value — ~29% populated, the rest honestly "Not specified."
- **Free-forever constraint forced good architecture.** Every paid service had a free-tier substitute decided up front; GCP was a time-boxed demonstration (BigQuery, Cloud SQL, GCS), torn down per cycle, not standing infrastructure.

## What was hard / what I'd do differently

- **BigQuery dialect divergence is silent.** A dbt project green on Postgres said nothing about BigQuery — `date_trunc` argument order, missing type names, and a CTE named `source` shadowing the `source` column (range-variable wins → whole-row STRUCT) all compiled clean elsewhere and broke or mis-resolved only on BQ. Captured in ADR-0017 so the next BigQuery project starts from the fixes, not the failures.
- **Public artifacts drift independently of the spec.** Numbers correct in the spec went stale in the README and dashboards because they were edited separately. The fix was a single Canonical Numbers block that every surface reconciles to, plus a pre-milestone grep of the README and `docs/` — not just the spec — against it.
- **Instrumentation that no-ops silently.** Analytics wrappers that quietly do nothing without a key mean "the app works" proves nothing about whether events land; the lesson was to verify at the provider's live feed, not in the app.

## Honest limitations

- **Scheduled scraping is gated off pre-launch.** The daily-refresh cron and the resulting SCD2 version-change accrual won't run until ungated, so the SCD Type 2 dimension is wired and correct but has not accumulated ≥100 version-changes. The mechanism is proven on demonstration data, not on a live daily cadence.
- **The A/B result is a simulated cohort.** With no organic traffic pre-launch, the +10.3% lift is validated against a simulated cohort and is framed as such everywhere — it is evidence the methodology and pipeline are sound, not evidence of real-user behavior.
- **Two sources are bot-walled.** Naukri and Wellfound spiders exist but are gated off rather than escalated past bot protection; volume is met entirely through official APIs and open ATS feeds.
- **Warehouse targets beyond Postgres are demonstrations.** Snowflake (30-day trial) and BigQuery (GCP demo window) were built, verified, and — for BigQuery — torn down. The free-forever production target is Postgres (Neon).

## By the numbers

| Metric | Value |
|---|---|
| Active jobs / sources | 9,014 / 8 live (10 spiders) |
| Duplicate rate collapsed | 13.5% (1,409 of 10,423) |
| dbt models / tests | 40 (BQ/Snowflake) / 93 |
| p95 vector retrieval | ~6 ms (200-pool, HNSW) |
| A/B apply-click lift | +10.3%, CI [1.2%, 19.4%], P=98.6% (simulated cohort) |
| Salary regression N | 669 disclosed-salary postings |
| Production runtime cost | ₹0/month |
