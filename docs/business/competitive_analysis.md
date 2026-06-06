# JobAtlas — Competitive Analysis

A teardown of JobAtlas against the principal players in Indian tech job discovery: **Naukri, LinkedIn, Hirect, Apna** (scored) and **Cutshort** (qualitative). Scoring is reproduced from the `Competitive_Landscape` sheet of the executive workbook.

## Methodology

Each platform is scored 1–5 (higher = better) on six weighted criteria; the weighted total is `SUMPRODUCT(weights, scores)`. Weights sum to 100%. JobAtlas is scored alongside competitors as the reference column. Cutshort is profiled qualitatively only — it serves a different (employer-side) use case and is not included in the weighted matrix.

## Weighted scoring matrix

| Criterion | Weight | Naukri | LinkedIn | Hirect | Apna | JobAtlas |
|---|---|---|---|---|---|---|
| Cross-portal aggregation | 22% | 2 | 2 | 1 | 1 | 5 |
| AI / semantic match | 20% | 3 | 4 | 2 | 2 | 5 |
| Salary transparency | 15% | 3 | 2 | 2 | 3 | 4 |
| UX / speed | 15% | 3 | 4 | 3 | 4 | 4 |
| Coverage / scale | 18% | 5 | 5 | 2 | 4 | 3 |
| Price (lower = better) | 10% | 2 | 2 | 4 | 5 | 5 |
| **Weighted total** | **100%** | **3.04** | **3.24** | **2.13** | **2.89** | **4.34** |

## Ranking

1. **JobAtlas — 4.34**
2. **LinkedIn — 3.24**
3. **Naukri — 3.04**
4. **Apna — 2.89**
5. **Hirect — 2.13**

## Competitor profiles

### Naukri
- **Positioning:** Long-standing market leader in Indian online recruitment by database scale and traffic; broad coverage across functions and seniority.
- **Pricing:** Employer-paid (job postings, database access, branding); largely free for seekers.
- **Features / UX:** Deep listings, resume database, recruiter tooling; mature but conventional keyword-driven search.
- **Relative scale:** Largest. Strength is coverage; weakness is cross-portal aggregation and semantic relevance.

### LinkedIn
- **Positioning:** Global professional network with a strong India presence; combines jobs with networking, content and employer branding.
- **Pricing:** Employer-paid recruiter seats and ads; freemium for members.
- **Features / UX:** Strong profile-based matching and polished UX; oriented to white-collar/professional roles.
- **Relative scale:** Very large. Strength is reach and relevance signals; weakness is aggregation across other portals and salary transparency.

### Hirect
- **Positioning:** Direct-chat hiring app focused on startup roles, connecting seekers to hiring managers without intermediaries. Scaled rapidly, then contracted through a 2022 restructuring; now operates at reduced scale.
- **Pricing:** Free for seekers; employer-side monetisation.
- **Features / UX:** Instant chat and in-app communication; narrower catalogue.
- **Relative scale:** Niche and diminished. Strength is direct contact and seeker pricing; weakness is coverage and aggregation.

### Apna
- **Positioning:** Mass-market, mobile-first platform with deep strength in entry-level and blue/grey-collar hiring, plus community features.
- **Pricing:** Free for seekers; employer-paid postings.
- **Features / UX:** Highly accessible mobile UX at large user scale; lighter on senior tech and semantic matching.
- **Relative scale:** Large in its segment. Strength is reach and price; weakness is tech-role aggregation and AI matching.

### Cutshort *(qualitative — not in the weighted matrix)*
- **Positioning:** Employer-side AI hiring platform focused on curated tech talent — quality over quantity — rather than open seeker-facing discovery.
- **Pricing:** Employer subscription and managed (vendor) models.
- **Features / UX:** AI candidate matching, screening and pipeline tooling for recruiters.
- **Why qualitative only:** Its primary user is the employer, not the job seeker; it is not directly comparable on seeker-facing aggregation, so it is excluded from the seeker-oriented weighted matrix and noted here for completeness.

## Teardown — where JobAtlas wins and loses

- **Wins:** Cross-portal aggregation (5 vs 1–2 everywhere else) and AI/semantic match (5) are the decisive differentiators, with best-in-class price (free). These three carry the top weighted total.
- **Loses:** Coverage/scale (3) trails Naukri and LinkedIn (5) — the honest consequence of a free-sourced, aggregator-concentrated index. This is the primary gap to close.
- **Net:** JobAtlas leads on the unify-and-match value proposition incumbents structurally don't serve, while remaining behind on raw catalogue depth — a position to defend by deepening source diversity rather than competing on volume alone.
