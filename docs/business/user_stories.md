# JobAtlas — Product Backlog (User Stories)

## Overview

This backlog is managed on the JobAtlas **GitHub Projects** board under an **Agile-Scrum** process: two-week sprints, planning-poker estimation on a **Fibonacci scale (1, 2, 3, 5, 8, 13)**, and a five-sprint horizon. Twenty stories span six epics, totalling **91 story points**.

**Board columns:** Backlog → Ready → In Progress → In Review → Done.
**Board fields:** Epic · Persona/Role · Story Points · Sprint · Priority (MoSCoW) · Status.

**Actors.** The three product personas — **Anjali** (fresh graduate), **Rohit** (career switcher) and **Sneha** (senior hire) — anchor 15 of the 20 stories (see `personas.md`). Two supporting *roles*, **Recruiter** and **Platform/Data team**, cover non-job-seeker workflows; these are operational actors, not personas.

**Epics**

| ID | Epic |
|---|---|
| E1 | Discovery & Search |
| E2 | Resume Matching |
| E3 | Salary & Skill Intelligence |
| E4 | Account, Saving & Retention |
| E5 | Recruiter Tools |
| E6 | Data Platform & Quality |

---

## E1 — Discovery & Search

### US-01 — Unified cross-portal search
*Epic: E1 · Persona: Anjali · Points: 5 · Sprint: 1 · Priority: Must*

> As a fresh-graduate job seeker (Anjali), I want to search every source from one box, so that I don't have to repeat the same search across five portals.

**Acceptance criteria**
- Given a keyword and optional location, when I search, then results from all indexed sources appear in a single ranked list with the source labelled on each card.
- Given duplicate postings across sources, when results render, then near-duplicates are collapsed to one canonical card.
- Given a result list, when it loads, then p95 search latency is under 500 ms.

### US-02 — Filter by location, role and experience
*Epic: E1 · Persona: Anjali · Points: 3 · Sprint: 1 · Priority: Must*

> As a fresh-graduate job seeker (Anjali), I want to filter by city, role and experience level, so that I only see roles I can realistically apply to.

**Acceptance criteria**
- Given the result list, when I apply one or more filter chips, then results update without a full page reload.
- Given an experience filter set to "fresher/0–1 yr", when applied, then senior-only postings are excluded.

### US-03 — Semantic search beyond exact title
*Epic: E1 · Persona: Rohit · Points: 8 · Sprint: 2 · Priority: Must*

> As a career switcher (Rohit), I want search to understand intent rather than exact keywords, so that roles matching my transferable skills surface even when the title differs.

**Acceptance criteria**
- Given a query, when I search, then results include semantically related roles (embedding similarity), not only literal keyword matches.
- Given a transferable-skill query, when results return, then at least one role from an adjacent job family appears in the top results.

### US-04 — Senior filtering with freshness sort
*Epic: E1 · Persona: Sneha · Points: 3 · Sprint: 5 · Priority: Should*

> As a senior hire (Sneha), I want to restrict results to senior roles and sort by recency, so that I see only relevant, current openings.

**Acceptance criteria**
- Given a seniority filter, when applied, then only senior/lead/manager-level postings remain.
- Given a sort-by-newest option, when selected, then results order by posted date descending.

---

## E2 — Resume Matching

### US-05 — Resume upload to ranked matches
*Epic: E2 · Persona: Anjali · Points: 13 · Sprint: 2 · Priority: Must*

> As a fresh-graduate job seeker (Anjali), I want to upload my resume and get ranked job matches with a score, so that I know which roles I'm genuinely competitive for.

**Acceptance criteria**
- Given an uploaded resume, when matching runs, then a ranked list of jobs is returned each with a similarity score, ordered by score descending.
- Given the embedding-and-retrieval pipeline (BGE-small, 384-dim, pgvector), when a match is requested, then p95 match latency is under 100 ms.
- Given an unsupported file type, when uploaded, then a clear validation error is shown and no match is attempted.

### US-06 — Match explanation
*Epic: E2 · Persona: Anjali · Points: 5 · Sprint: 3 · Priority: Should*

> As a fresh-graduate job seeker (Anjali), I want to see why a job matched me, so that I trust the score and learn what employers value.

**Acceptance criteria**
- Given a match result, when I open its detail, then the overlapping skills driving the score are shown.
- Given a match score, when displayed, then it is presented on a consistent, interpretable scale.

### US-07 — Transferable-skill matching
*Epic: E2 · Persona: Rohit · Points: 5 · Sprint: 3 · Priority: Should*

> As a career switcher (Rohit), I want matches to credit my transferable skills, so that adjacent-function roles appear even though my current title doesn't match them.

**Acceptance criteria**
- Given a resume from one function, when matching runs, then roles in a target adjacent function with overlapping skills appear in the ranked results.
- Given such a match, when its detail opens, then the transferable skills responsible are listed.

### US-08 — High-precision senior matches
*Epic: E2 · Persona: Sneha · Points: 3 · Sprint: 3 · Priority: Could*

> As a senior hire (Sneha), I want a short list of strong matches rather than a long noisy one, so that I can evaluate quickly.

**Acceptance criteria**
- Given a senior resume, when matching runs, then results are ranked by descending score with the strongest matches first.
- Given the ranked list, when displayed, then each item shows its score so weak tail matches are visually distinguishable.

---

## E3 — Salary & Skill Intelligence

### US-09 — Entry-level salary by city and role
*Epic: E3 · Persona: Anjali · Points: 5 · Sprint: 4 · Priority: Should*

> As a fresh-graduate job seeker (Anjali), I want to see typical entry-level pay by city and role, so that I can set realistic expectations.

**Acceptance criteria**
- Given a role and city, when I open the salary view, then a salary distribution is shown for postings where salary data is available.
- Given that salary coverage is sparse across the corpus, when data is missing, then the view states coverage transparently rather than implying full coverage.

### US-10 — Cross-role salary comparison
*Epic: E3 · Persona: Rohit · Points: 5 · Sprint: 4 · Priority: Should*

> As a career switcher (Rohit), I want to compare pay between my current role and a target role, so that I can quantify the financial impact of switching.

**Acceptance criteria**
- Given two roles, when I compare them, then their salary distributions appear side by side for the same city, where data exists.
- Given missing data for a role/city pair, when comparing, then the gap is labelled rather than interpolated.

### US-11 — Senior-band compensation benchmarking
*Epic: E3 · Persona: Sneha · Points: 3 · Sprint: 4 · Priority: Could*

> As a senior hire (Sneha), I want compensation benchmarks at senior bands, so that I can judge whether a role is worth a conversation.

**Acceptance criteria**
- Given a senior role and city, when I open the salary view, then the senior-band distribution is shown where data is available.
- Given thin senior-band data, when displayed, then the sample basis is disclosed.

### US-12 — Skill-demand explorer
*Epic: E3 · Persona: Anjali · Points: 3 · Sprint: 4 · Priority: Should*

> As a fresh-graduate job seeker (Anjali), I want to see the most in-demand skills by city, so that I can prioritise what to learn.

**Acceptance criteria**
- Given a city, when I open the explorer, then the top skills by posting frequency are listed.
- Given a skill, when selected, then I can navigate to current postings requiring it.

---

## E4 — Account, Saving & Retention

### US-13 — Save and shortlist jobs
*Epic: E4 · Persona: Anjali · Points: 1 · Sprint: 5 · Priority: Could*

> As a fresh-graduate job seeker (Anjali), I want to save jobs to a shortlist, so that I can return to them later.

**Acceptance criteria**
- Given a job card, when I save it, then it is added to my shortlist and the save state persists for my session/account.
- Given my shortlist, when I open it, then all saved jobs are listed with their source.

### US-14 — Application tracking
*Epic: E4 · Persona: Anjali · Points: 3 · Sprint: 5 · Priority: Could*

> As a fresh-graduate job seeker (Anjali), I want to see which jobs I've clicked through to apply to, so that I don't apply to the same role twice.

**Acceptance criteria**
- Given an apply-click, when it occurs, then the job is recorded in my application history.
- Given my history, when I view it, then each entry shows the job, source and date.

### US-15 — New-match alerts
*Epic: E4 · Persona: Rohit · Points: 5 · Sprint: 5 · Priority: Could*

> As a career switcher (Rohit), I want to be notified when new matching roles appear, so that I don't have to keep re-running searches.

**Acceptance criteria**
- Given a saved profile/resume, when new jobs match above a threshold, then I receive a notification.
- Given a notification, when I open it, then it links directly to the matching jobs.

---

## E5 — Recruiter Tools

### US-16 — Company-name aggregation search
*Epic: E5 · Role: Recruiter · Points: 3 · Sprint: 5 · Priority: Should*

> As a recruiter, I want to type a company name and see all of its openings aggregated across sources, so that I can benchmark a competitor's hiring at a glance.

**Acceptance criteria**
- Given a company name, when I search, then all indexed postings for that company appear, deduplicated, with each source labelled.
- Given the company result set, when displayed, then postings are sortable by recency.

### US-17 — Source and freshness transparency
*Epic: E5 · Role: Recruiter · Points: 2 · Sprint: 5 · Priority: Could*

> As a recruiter, I want each posting to show its source and how recent it is, so that I can judge data reliability.

**Acceptance criteria**
- Given any posting, when displayed, then its originating source and posted date are visible.
- Given a preview-only source, when shown, then the card indicates preview status and links out to the original posting.

---

## E6 — Data Platform & Quality

### US-18 — Cross-source deduplication
*Epic: E6 · Role: Platform/Data team · Points: 8 · Sprint: 1 · Priority: Must*

> As a member of the platform team, I want near-duplicate postings collapsed across sources, so that users never see the same job twice.

**Acceptance criteria**
- Given postings from multiple sources, when dedup runs, then records with MinHash Jaccard similarity ≥ 0.85 are clustered to a single canonical posting.
- Given a duplicate cluster, when resolved, then the canonical record retains the richest available fields.

### US-19 — Daily freshness refresh
*Epic: E6 · Role: Platform/Data team · Points: 5 · Sprint: 1 · Priority: Must*

> As a member of the platform team, I want the index refreshed daily, so that users aren't shown stale or filled roles.

**Acceptance criteria**
- Given the orchestration schedule, when the daily run executes, then new postings are ingested and the index reflects them.
- Given a completed run, when it finishes, then freshness and row-count metrics are recorded for monitoring.

### US-20 — Data-quality gate
*Epic: E6 · Role: Platform/Data team · Points: 3 · Sprint: 5 · Priority: Should*

> As a member of the platform team, I want quality checks to block bad records before they reach the warehouse, so that downstream analytics stay trustworthy.

**Acceptance criteria**
- Given a staging load, when expectations run (row counts, null limits, value ranges, URL patterns), then a failing suite fails the pipeline task.
- Given a quality failure, when it occurs, then the offending records are quarantined and surfaced for review.

---

## Backlog summary

| ID | Title | Epic | Persona/Role | Pts | Sprint | Priority | Status |
|---|---|---|---|---|---|---|---|
| US-01 | Unified cross-portal search | E1 | Anjali | 5 | 1 | Must | Done |
| US-02 | Filter by location/role/experience | E1 | Anjali | 3 | 1 | Must | Done |
| US-03 | Semantic search beyond exact title | E1 | Rohit | 8 | 2 | Must | Done |
| US-04 | Senior filtering with freshness sort | E1 | Sneha | 3 | 5 | Should | Done |
| US-05 | Resume upload to ranked matches | E2 | Anjali | 13 | 2 | Must | Done |
| US-06 | Match explanation | E2 | Anjali | 5 | 3 | Should | Done |
| US-07 | Transferable-skill matching | E2 | Rohit | 5 | 3 | Should | Done |
| US-08 | High-precision senior matches | E2 | Sneha | 3 | 3 | Could | Done |
| US-09 | Entry-level salary by city/role | E3 | Anjali | 5 | 4 | Should | Done |
| US-10 | Cross-role salary comparison | E3 | Rohit | 5 | 4 | Should | Done |
| US-11 | Senior-band comp benchmarking | E3 | Sneha | 3 | 4 | Could | Done |
| US-12 | Skill-demand explorer | E3 | Anjali | 3 | 4 | Should | Done |
| US-13 | Save and shortlist jobs | E4 | Anjali | 1 | 5 | Could | Planned |
| US-14 | Application tracking | E4 | Anjali | 3 | 5 | Could | Planned |
| US-15 | New-match alerts | E4 | Rohit | 5 | 5 | Could | Planned |
| US-16 | Company-name aggregation search | E5 | Recruiter | 3 | 5 | Should | Done |
| US-17 | Source and freshness transparency | E5 | Recruiter | 2 | 5 | Could | Done |
| US-18 | Cross-source deduplication | E6 | Platform/Data team | 8 | 1 | Must | Done |
| US-19 | Daily freshness refresh | E6 | Platform/Data team | 5 | 1 | Must | Done |
| US-20 | Data-quality gate | E6 | Platform/Data team | 3 | 5 | Should | Done |

**Totals:** 20 stories · 91 points · 6 epics · 5 sprints. Status reflects build state: 17 delivered, 3 (US-13/14/15, all account-dependent) in the planned backlog.
