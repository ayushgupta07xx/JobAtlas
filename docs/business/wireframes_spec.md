# JobAtlas — Wireframe Specification

Build plan for the JobAtlas wireframes. **Fidelity:** low — greyscale boxes, labels, and annotations, not high-fidelity mockups. **Platform:** mobile-first (390×844), with desktop (1440) variants for the two highest-traffic screens (Search, Job Detail). **Segments:** the three personas (Anjali / Rohit / Sneha) plus the recruiter role.

---

## Global components (build once, reuse)

- **Header** — logo (left), account/sign-in placeholder (right, *planned*).
- **SearchBar** — keyword field + location field + Search button; "Company" mode toggle for the recruiter flow.
- **FilterChip** — pill; states: default / active. Set: City, Role, Experience, Source.
- **ResultCard** — variants: (a) default, (b) with-match-score, (c) preview-only. Anatomy: role title (link) · company + logo placeholder · location chip · experience chip · salary line *(or "Salary not listed")* · **source badge** + **posted-date/freshness** · match-score badge *(variant b only)* · save icon *(planned)*. Tap → Job Detail.
- **Badge** — source (Adzuna/Greenhouse/Lever/…), freshness (e.g. "2d ago"), match score (e.g. "0.91").
- **Button** — primary / secondary.
- **Tabs** — used on the Salary Explorer.
- **States** — EmptyState, LoadingSkeleton (skeleton cards), ErrorState.

---

## Screen 1 — Search & Results

**Serves:** all segments (primary: Anjali). **Stories:** US-01/02/03/04. **FRs:** F1–F8. **Perf:** NFR-1 (<500 ms p95).

**Layout (mobile, top → bottom)**
1. Header.
2. SearchBar (keyword + location + Search).
3. Filter-chip row (horizontally scrollable) → opens a filter sheet (City / Role / Experience / Source).
4. Result count + Sort dropdown (Relevance · Newest).
5. Result list — ResultCard (default variant).
6. "Load more" (no full page reload — F7).

**Annotations**
- Unified list spans all sources, deduplicated; each card shows its source (F1, F2).
- Ranking blends keyword + semantic similarity — *annotate that adjacent-function roles surface here even on a non-matching title* (F5; Rohit).
- Sort → Newest demonstrates freshness ordering (F6; Sneha pairs this with Experience = senior).
- **States:** no query → popular searches / suggestions; loading → skeleton cards; no results → empty state with filter-reset; error → retry.

---

## Screen 2 — Resume Match

**Serves:** all segments (Rohit transferable-skill; Sneha precision). **Stories:** US-05/06/07/08. **FRs:** F9–F16. **Perf:** NFR-2 (<100 ms p95).

**Layout — three states on one frame set**
1. **Upload state** — drop zone + file picker; supported-formats note; inline validation error for unsupported types (F9).
2. **Processing state** — "Finding your matches…" loader (embedding + vector retrieval happen server-side; not shown in UI).
3. **Results state** — ranked ResultCards (with-match-score variant), ordered by score descending (F12); each card has a **"Why matched"** expander listing overlapping skills (F13, F14).

**Annotations**
- Rohit: overlapping-skill chips emphasise *transferable* skills driving an adjacent-function match (F15).
- Sneha: short list of strong, score-sorted matches (precision framing; F12).
- **Edge:** a full browser refresh clears the uploaded resume → show a "re-upload your resume" empty state (known behaviour).

---

## Screen 3 — Salary Explorer (Salary & Skills)

**Serves:** Anjali (entry pay + skills), Rohit (compare), Sneha (senior band). **Stories:** US-09/10/11/12. **FRs:** F17–F23.

**Layout — tabbed**
- **Tab A · Salary**
  1. Filters: Role · City · Experience band.
  2. Distribution chart (Recharts placeholder).
  3. **Coverage disclosure banner** — "Based on N of M postings with salary data" — prominent, because salary is present on only a minority of postings (F18). Never imply full coverage.
  4. Compare toggle → add a second role for side-by-side, same city (F19; Rohit).
  5. Senior-band view with sample-basis note (F20; Sneha).
- **Tab B · Skills**
  1. City selector.
  2. Top skills by posting frequency (ranked bar list) (F21).
  3. Tap a skill → deep-link into Search pre-filtered by that skill (F22; Anjali).

**Annotations**
- **States:** sparse/zero salary data → explicit "not enough data" state rather than an empty chart.

---

## Screen 4 — Job Detail

**Serves:** all segments + recruiter. **Stories:** US-08/17. **FRs:** F8, F13, F14, F32.

**Layout (top → bottom)**
1. Back / header.
2. Title · company · location · experience · posted date · **source badge**.
3. Salary block — shown where available, else "Salary not listed".
4. Match block — score + overlapping skills *(only when arrived from Resume Match)*.
5. Description — **full sanitised text** for ATS sources; **truncated preview + "Preview only — view full posting on [source]"** for preview-only sources (F8, F32).
6. Primary CTA: **"Apply on [source]"** → external redirect (no in-app apply); fires `apply_clicked`.
7. Save (secondary, *planned*).

**Annotations**
- Description HTML is sanitised before render (DOMPurify).
- Apply always leaves the product to the original posting.

---

## Screen 5 — Recruiter Company View

**Serves:** recruiter role. **Stories:** US-16/17. **FRs:** F30, F31, F32.

**Layout (top → bottom)**
1. SearchBar in "Company" mode (company-name input).
2. Company header — name · total openings count · sources represented.
3. Sort: Newest · Relevance (F31).
4. List of that company's openings — deduplicated, each card showing source + posted date (F30, F32).
5. Tap → Job Detail.

**Annotations**
- This is the "type your company name, see everything" benchmarking moment.
- **States:** company not found → empty state; single-source vs multi-source headers differ.

---

## Per-segment flow mapping (for the three Figma segment pages)

| Segment | Primary flow (screens in order) |
|---|---|
| Anjali (fresh graduate) | Search (entry-level filters) → Job Detail → Apply · also Resume Match → Job Detail · Salary Explorer (entry pay + Skills tab) |
| Rohit (career switcher) | Resume Match (transferable-skill emphasis) → Job Detail · Search (semantic) · Salary Explorer (compare current vs target) |
| Sneha (senior hire) | Search (Experience = senior + Newest) → Job Detail · Resume Match (few strong) · Salary Explorer (senior band) |
| Recruiter (role) | Recruiter Company View → Job Detail |

*Out of scope for this wireframe set (planned, account-dependent): saved shortlist, application history, new-match alerts (US-13/14/15).*

---

## Figma build guide

- **File name:** `JobAtlas — Wireframes`.
- **Pages:** `01 Components` · `02 Anjali` · `03 Rohit` · `04 Sneha` · `05 Recruiter` (segment pages satisfy the "three user segments" commitment; recruiter as a fourth).
- **Frames:** mobile `390×844` primary; desktop `1440×1024` variants for Search and Job Detail.
- **Components to create:** Header, SearchBar, FilterChip, ResultCard (3 variants), Badge (source/freshness/match), Button (primary/secondary), Tabs, SalaryChart placeholder, SkillBar, EmptyState, LoadingSkeleton.
- **Style:** greyscale low-fi; boxes + text labels; annotate FR/US IDs in the margin of each frame for traceability.
- **Prototype:** wire frame-to-frame arrows along each segment flow above (optional but quick, and it makes the flows self-demonstrating).
