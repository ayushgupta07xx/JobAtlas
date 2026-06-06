# JobAtlas — Gap Analysis

Current state of Indian tech job discovery versus the target state JobAtlas enables, with bridging actions. A second section tracks the product's own maturity gaps honestly.

## Market / capability gaps

| Dimension | Current state (status quo) | Target state | Gap | Bridging action |
|---|---|---|---|---|
| Discovery | Same roles searched separately across 6+ portals | One unified, deduplicated search | No single source of truth | Aggregate sources; collapse duplicates at Jaccard ≥ 0.85 (F1, F36) |
| Match relevance | Keyword search rewards exact titles | Semantic match with score + explanation | Non-linear careers filtered out | Embedding-based ranking and skill-overlap explanation (F5, F12, F14) |
| Career-switcher support | Transferable skills ignored | Adjacent-function roles surfaced | Switchers underserved | Transferable-skill surfacing (F15) |
| Salary transparency | Inconsistent or absent pay data | Salary by role/city where available, with disclosure | Opacity; no benchmarks | Salary normalisation + coverage-disclosed views (F17, F18, F23) |
| Skill intelligence | No view of in-demand skills | Top-skills-by-city explorer | Seekers can't prioritise learning | Skill-demand explorer (F21, F22) |
| Senior discovery | Senior roles buried under junior listings + recruiter noise | Short, high-precision senior matches | Poor signal for passive seniors | Score-ranked precision results + seniority filter (F4, F12) |
| Data quality | Stale, duplicated, unverified listings | Fresh, deduplicated, quality-gated index | Trust deficit | Daily refresh + dedup + expectation gates (F37, F36, F39) |

## Product maturity gaps (internal)

| Area | Current state | Target state | Bridging action |
|---|---|---|---|
| Source diversity | One aggregator ~84% of corpus | Balanced multi-source index | Expand per-company ATS feeds as a balance layer |
| Salary depth | Salary on a minority of postings | Broader salary coverage | Add structured-salary sources; disclose coverage meanwhile |
| Accounts & retention | No accounts; save/track/alerts planned (US-13/14/15) | Persisted saved state and alerts | Build account layer and notification flow |
| Validation | Pre-launch; metrics from a simulated cohort | Validated on organic traffic | Launch, collect real behaviour, re-run the experiment |
| Dedup scaling | Pairwise approach adequate at current size | LSH-indexed dedup | Move to MinHashLSH before scaling well beyond current volume |
