# JobAtlas — Business Requirements Document (BRD)

| | |
|---|---|
| **Document** | Business Requirements Document |
| **Product** | JobAtlas |
| **Version** | 1.0 |
| **Status** | Approved for build |
| **Owner** | Product Owner |
| **Last updated** | 2026 |

---

## 1. Executive summary

JobAtlas is a unified job-discovery and intelligence platform for the Indian tech market. Job seekers today must search the same roles across six or more disconnected portals, wade through duplicate listings, and apply with no reliable signal of whether they are a genuine fit. JobAtlas aggregates postings from multiple sources into a single deduplicated index, lets a user upload a resume to receive AI-ranked matches with an interpretable score, and surfaces salary and skill-demand intelligence to support better decisions.

The product targets three job-seeker segments — fresh graduates, career switchers and senior hires — representing a combined modelled serviceable opportunity of **₹333.6 cr/year** within an Indian online-recruitment market sized at approximately **₹8,400 cr growing ~22% YoY**. JobAtlas runs entirely on free-tier and open-source infrastructure at **₹0/month** in production, with any cloud-warehouse capability demonstrated in short, torn-down cycles rather than kept live.

This document defines the business problem, objectives, scope, stakeholders, success criteria, assumptions and risks. Functional and non-functional detail is specified separately in `FRD.md`.

## 2. Problem statement

The Indian tech job market is fragmented across portals such as Naukri, LinkedIn, Wellfound, Hirist, Instahyre and several aggregators. This fragmentation creates four concrete problems:

- **Discovery cost.** A seeker must repeat the same search on every portal and still cannot be confident they have seen all relevant roles.
- **Duplication.** The same posting appears across multiple sources under slightly varied titles, inflating apparent volume and wasting time.
- **No fit signal.** Keyword search rewards exact-title matches and penalises non-linear careers; seekers apply broadly with low conversion because they cannot judge fit before applying.
- **Opacity.** Salary information is inconsistent or absent, and seekers lack a view of which skills are actually in demand.

The cost falls unevenly across segments: fresh graduates over-apply with no fit signal, career switchers are filtered out by literal keyword matching, and senior candidates cannot discover high-fit roles without wading through noise.

## 3. Business objectives

| ID | Objective | Measure of success |
|---|---|---|
| O1 | Unify multiple sources into one deduplicated, searchable index | 6,000–8,000 live postings; duplicates collapsed at Jaccard ≥ 0.85 |
| O2 | Deliver AI resume-to-job matching with an interpretable score | Ranked matches returned at p95 < 100 ms |
| O3 | Provide salary and skill-demand intelligence | Salary views by role/city (where data exists) and top-skills-by-city explorer live |
| O4 | Instrument the product and establish a North Star metric | 24 events / 3 funnels / 5 cohorts; North Star = Weekly Matched Applications, plus 8 tracked KPIs |
| O5 | Operate free-forever after cloud demonstration teardown | ₹0/month production cost sustained |

The **North Star metric** is *Weekly Matched Applications* — the count of apply-click events where match score ≥ 0.7 — chosen because it captures the moment the product delivers real value (a confident, well-matched application) rather than vanity engagement.

## 4. Project scope

### In scope
- Aggregation, normalisation and deduplication of postings from permitted sources (official APIs and permitted feeds).
- Unified keyword and semantic search with faceted filters.
- Resume upload and embedding-based matching with score and explanation.
- Salary and skill-demand intelligence where source data supports it.
- Company-name aggregation view for recruiter/benchmarking use.
- Product analytics instrumentation and a feature-flagged match-algorithm experiment.
- Public business-intelligence dashboards and an executive workbook.

### Out of scope (non-goals)
- **In-app application submission** — apply actions redirect the user to the original source posting.
- **Employer-side applicant tracking (ATS).**
- **Commercial redistribution or resale of aggregated data.**
- **Defeating bot protection** — no residential proxies, stealth plugins or CAPTCHA-solving; blocked sources fall back to official APIs and are treated as best-effort.
- **Non-tech job verticals** and **non-English postings.**
- **User-facing real-time streaming** — change-data-capture feeds the warehouse near-real-time, not the end-user surface.

## 5. Stakeholders

| Stakeholder | Interest | Involvement |
|---|---|---|
| Product Owner | Defines vision, prioritises backlog, owns success metrics | Accountable |
| Engineering / Data team | Builds and operates pipeline, API, frontend, warehouse | Responsible |
| Job seekers (Anjali, Rohit, Sneha personas) | Primary users; discovery, matching, intelligence | Consulted (via persona research) |
| Recruiters | Secondary users; company benchmarking | Consulted |
| Data-source providers (API/feed owners) | Govern access terms and rate limits | Informed (terms respected) |
| Reviewers (technical & non-technical) | Evaluate product quality and architecture | Informed |

## 6. Success criteria

- Multi-source index live with 6,000–8,000 deduplicated postings, refreshed daily.
- Resume-match flow live end-to-end with score and explanation, meeting the latency target.
- Salary and skill-demand views live, with coverage disclosed where source data is sparse.
- Analytics live (24 events / 3 funnels / 5 cohorts) and a North Star plus 8 KPIs defined and tracked.
- Public Tableau and Looker Studio dashboards live and verified in a logged-out window.
- Match-algorithm experiment documented with methodology; **pre-launch results validated against a simulated cohort** (no organic traffic yet).
- Production cost held at ₹0/month; cloud-warehouse cycles demonstrated and torn down.

### KPI set (8)

| KPI | Definition |
|---|---|
| Weekly Matched Applications (North Star) | Apply-clicks with match score ≥ 0.7, per week |
| Stickiness | DAU / MAU ratio |
| WAU | Weekly active users |
| W1 / W4 retention | Share of a cohort returning in week 1 / week 4 |
| Churn | Share of prior-active users not returning in period |
| Search→apply conversion | Apply-clicks per search session |
| Match latency (p95) | 95th-percentile resume-match response time |
| Dedup rate | Share of ingested postings collapsed as duplicates |

## 7. Assumptions

- Official source APIs and permitted feeds remain available at current rate limits; the index is expected to be aggregator-heavy as a consequence of free-source availability.
- Free-tier and open-source infrastructure is sufficient for early/portfolio scale.
- Users upload resumes in standard, machine-readable formats.
- Salary data is present in only a minority of postings; intelligence features must degrade gracefully.
- Market and persona sizing are modelled top-down estimates, not measured demand.
- All experiment results prior to launch derive from a simulated cohort and are labelled as such.

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Source blocks / anti-scraping | Volume shortfall | Respectful rate limits and robots.txt; official APIs as the volume engine; no bot-wall defeat; blocked scrapes treated as best-effort |
| Single-source concentration (one aggregator ~84% of corpus) | Fragility if that source changes terms | Diversify via per-company ATS feeds and additional APIs as a balance layer; document dependency |
| Sparse salary coverage | Weak salary intelligence | Disclose coverage transparently; never interpolate missing values implicitly |
| Free-tier limits / cold starts | Latency or quota issues | Engineer within limits; tolerate managed-DB idle-resume latency for demo scale |
| Cloud cost overrun | Budget breach on shared billing | Per-cycle teardown protocol; hard budget alerts; investigate above threshold |
| Time-boxed warehouse trial expiry | Lost parallel-warehouse proof | Complete and screenshot the trial-warehouse work inside its window |

---

*End of BRD.*
