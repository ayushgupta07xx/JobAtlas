# Architecture Decisions

Chronological record of architectural decisions for JobAtlas. Each entry is short: what was chosen, what was considered, why.

---

## 2026-05-19 — Initial stack

**Decision.** Python 3.11, Postgres 16 + pgvector, MongoDB for raw zone, Redpanda for streaming, MinIO for local object storage, Airflow for orchestration, dbt for transformations targeting BigQuery and Snowflake in parallel.

**Why.** Each role this repo targets (Data Analyst, Product Analyst, Business Analyst, Data Engineer) needs a different surface area. The stack gives a credible end-to-end path for all four without piling on tools that don't earn their slot.

**Alternatives considered.** Single-warehouse (BigQuery only): rejected because dual-warehouse demonstrates dbt's adapter-agnostic property. Kafka over Redpanda: equivalent semantics, Redpanda runs in fewer containers locally.
