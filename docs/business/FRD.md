# JobAtlas — Functional Requirements Document (FRD)

| | |
|---|---|
| **Document** | Functional Requirements Document |
| **Product** | JobAtlas |
| **Version** | 1.0 |
| **Owner** | Product Owner |
| **Last updated** | 2026 |

## 1. Introduction

This document specifies the functional requirements (F1–F40), non-functional requirements (NFR-1 to NFR-12), data requirements, integration points and constraints for JobAtlas. Business context is in `BRD.md`; each functional requirement traces to a user story in `user_stories.md` (see §6 traceability). Requirement IDs are stable references for testing and change control. *Shall* denotes a mandatory requirement.

## 2. Functional requirements

### 2.1 Search & Discovery

- **F1** — The system shall return results from all indexed sources in a single ranked list for a given query. *(US-01)*
- **F2** — The system shall label each result with its originating source. *(US-01, US-17)*
- **F3** — The system shall accept a keyword query with an optional location parameter. *(US-01)*
- **F4** — The system shall provide faceted filters for city, role, experience level and source. *(US-02, US-04)*
- **F5** — The system shall rank results using embedding-based semantic similarity in addition to keyword relevance. *(US-03)*
- **F6** — The system shall offer sort options including posted-date recency. *(US-04)*
- **F7** — The system shall update filtered results without a full page reload. *(US-02)*
- **F8** — The system shall present a job-detail view with a sanitised description; for preview-only sources it shall mark preview status and link out to the original posting. *(US-08, US-17)*

### 2.2 Resume Matching

- **F9** — The system shall accept a resume upload in supported formats and reject unsupported types with a clear validation error. *(US-05)*
- **F10** — The system shall embed the resume using a sentence-transformers model producing 384-dimension vectors. *(US-05)*
- **F11** — The system shall retrieve nearest-neighbour jobs via a pgvector HNSW index. *(US-05)*
- **F12** — The system shall return a ranked match list with a similarity score per job, ordered by score descending. *(US-05, US-08)*
- **F13** — The system shall display match scores on a consistent, interpretable scale. *(US-06)*
- **F14** — The system shall show the overlapping skills that drove each match. *(US-06, US-07)*
- **F15** — The system shall surface roles from adjacent job families where transferable skills overlap. *(US-07)*
- **F16** — The system shall set the HNSW `ef_search` parameter to at least the retrieval pool size before issuing a similarity query. *(US-05)*

### 2.3 Salary & Skill Intelligence

- **F17** — The system shall present salary distributions by role and city for postings where salary data exists. *(US-09)*
- **F18** — The system shall disclose salary coverage and shall not interpolate missing values implicitly. *(US-09, US-10, US-11)*
- **F19** — The system shall allow side-by-side salary comparison between two roles for the same city. *(US-10)*
- **F20** — The system shall provide a senior-band salary view with the sample basis disclosed. *(US-11)*
- **F21** — The system shall list the top skills by posting frequency for a selected city. *(US-12)*
- **F22** — The system shall allow navigation from a skill to current postings requiring it. *(US-12)*
- **F23** — The system shall normalise salary at ingestion (ranges, lakh/k notation, currency). *(supports F17–F20)*

### 2.4 Account & Retention

- **F24** — The system shall allow a user to save a job to a shortlist. *(US-13)*
- **F25** — The system shall persist a user's shortlist across the session/account. *(US-13)*
- **F26** — The system shall record apply-click events as the user's application history. *(US-14)*
- **F27** — The system shall notify a user when new jobs match their saved profile above a threshold. *(US-15)*
- **F28** — The system shall link each notification directly to the matching jobs. *(US-15)*
- **F29** — The system shall support account sign-in to persist saved state. *(enables F25–F27)*

### 2.5 Recruiter

- **F30** — The system shall return all aggregated, deduplicated openings for a searched company name. *(US-16)*
- **F31** — The system shall allow company results to be sorted by recency. *(US-16)*
- **F32** — The system shall display the source and posted date on every posting. *(US-17)*

### 2.6 Data Ingestion & Pipeline

- **F33** — The system shall ingest postings from official APIs and permitted feeds only. *(US-19)*
- **F34** — The system shall land raw payloads in a raw document store before transformation. *(US-19)*
- **F35** — The system shall normalise raw payloads into a staging schema (title, company, location, salary, skills, source, source_url, posted_date). *(US-19)*
- **F36** — The system shall deduplicate across sources using MinHash signatures, clustering records at Jaccard ≥ 0.85 to a single canonical posting. *(US-18)*
- **F37** — The system shall run a daily orchestrated refresh and record freshness and row-count metrics. *(US-19)*
- **F38** — The system shall transform staged data into warehouse marts, maintaining SCD Type 2 history on the job dimension. *(US-19)*
- **F39** — The system shall enforce a data-quality gate that fails the pipeline and quarantines records on a failing expectation suite. *(US-20)*
- **F40** — The system shall support a feature-flagged match-algorithm variant with pre-registered guardrail metrics for experimentation. *(supports product analytics)*

## 3. Non-functional requirements

- **NFR-1 (Performance)** — Search response time shall be under 500 ms at p95.
- **NFR-2 (Performance)** — Resume-match response time shall be under 100 ms at p95.
- **NFR-3 (Availability)** — The system shall degrade gracefully on free-tier infrastructure, tolerating managed-database idle-resume latency.
- **NFR-4 (Scalability)** — The index shall scale to tens of thousands of postings; the deduplication approach shall move to an LSH-indexed method before exceeding the point where pairwise comparison degrades.
- **NFR-5 (Security)** — Secrets shall never be committed to source; they shall be supplied via environment or secret store, and all traffic shall use HTTPS.
- **NFR-6 (Privacy)** — Resumes shall be processed transiently for matching with no unnecessary retention; no personal data shall appear in URLs or logs.
- **NFR-7 (Maintainability)** — The codebase shall enforce pre-commit linting/typing and CI test gates, and shall document architectural decisions as ADRs.
- **NFR-8 (Cost / Portability)** — Production shall run free-forever on open-source/free-tier hosting at ₹0/month; cloud-warehouse demonstrations shall be torn down after use.
- **NFR-9 (Accessibility)** — The interface shall be mobile-first and pass an automated accessibility audit in CI.
- **NFR-10 (Data quality)** — Staging and mart layers shall be validated by expectation suites; a failing suite shall fail the pipeline.
- **NFR-11 (Compliance / Legal)** — Ingestion shall respect robots.txt and source terms, use official APIs, avoid commercial redistribution, and never defeat bot protection.
- **NFR-12 (Observability)** — The product shall emit analytics (24 events / 3 funnels / 5 cohorts) and the pipeline shall emit freshness and row-count metrics.

## 4. Data requirements

- **Zoned storage** — raw zone (unmodified payloads) → staging (normalised) → warehouse marts (star schema: fact_jobs with dim_company, dim_skill, dim_location, dim_date; SCD Type 2 on the job dimension).
- **Core posting fields** — title, company, location (city/state/country), salary_min/max + currency, posted_date, source, source_url, description, skills array.
- **Salary sparsity** — salary is present on only a minority of postings; features must treat absence as the common case and disclose coverage.
- **Embeddings** — 384-dimension vectors stored in pgvector with an HNSW index for similarity retrieval.
- **Retention / PII** — resumes are transient inputs to matching and are not retained beyond the request lifecycle.

## 5. Integration points

| System | Purpose |
|---|---|
| Aggregator job APIs (e.g. Adzuna, Jobicy) | Primary structured posting volume |
| Per-company ATS feeds (Greenhouse / Lever / Ashby / TheMuse) | Original-posting and balance layer with full descriptions |
| Product analytics platform (PostHog) | Event tracking, funnels, cohorts, feature flags, experiment |
| Operational database (Postgres + pgvector) | Serving store and vector search |
| Warehouse (BigQuery / Snowflake, demo cycles) | dbt marts and analytical queries |
| BI tools (Tableau Public, Looker Studio) | Public dashboards |

## 6. Constraints

- One aggregator is expected to supply the large majority (~84%) of the corpus and returns truncated previews only; full descriptions come from ATS feeds, and preview-only postings must link out.
- Salary data is present on a minority of postings.
- Cloud warehouse usage is demonstration-only with mandatory teardown; the parallel-warehouse trial is time-boxed.
- No residential proxies, stealth plugins or CAPTCHA-solving may be used; blocked sources are best-effort.
- Postings are English-language and tech-vertical only.
- Apply actions redirect to the source; no application is submitted in-app.

## 7. Traceability (user story → requirements)

| Story | Requirements |
|---|---|
| US-01 | F1, F2, F3 |
| US-02 | F4, F7 |
| US-03 | F5 |
| US-04 | F4, F6 |
| US-05 | F9, F10, F11, F12, F16 |
| US-06 | F13, F14 |
| US-07 | F14, F15 |
| US-08 | F8, F12 |
| US-09 | F17, F18 |
| US-10 | F18, F19 |
| US-11 | F18, F20 |
| US-12 | F21, F22 |
| US-13 | F24, F25 |
| US-14 | F26 |
| US-15 | F27, F28 |
| US-16 | F30, F31 |
| US-17 | F2, F8, F32 |
| US-18 | F36 |
| US-19 | F33, F34, F35, F37, F38 |
| US-20 | F39 |

*End of FRD.*
