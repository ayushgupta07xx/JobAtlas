# Engineering notes

A running log of the design decisions behind JobAtlas — the problem each one
solves and what it trades off. Distilled into the README's design section as
features stabilize.

## Search: sort and filter scoped to a relevant pool

**Problem.** With a query active, switching the sort to recency or salary
re-ordered the *entire* index, so the freshest or highest-paying *unrelated*
jobs buried the ones that actually matched the search.

**Approach.** When a query is present, the search first selects a top-N
relevant-candidate pool (top 200 by cosine similarity); relevance, salary, and
recency then order *within* that pool, and source filtering and pagination run
server-side against it. With no query, sorting browses the full index.

**Trade-off.** A query paginates at most ~200 results instead of the whole
index — accepted, because past the top ~200 a search is no longer relevant
anyway. Rejected alternative: a fixed "largest source first" ordering, which
would have contradicted the semantic-relevance promise and over-weighted
whichever feed is biggest (one aggregator is ~84% of rows).

## Job detail: intercepting-route modal

**Problem.** Opening a job and pressing Back lost the scroll position and the
search/filter state. Client-side scroll restoration (sessionStorage capture +
deferred `requestAnimationFrame`) couldn't reliably win against the router's own
scroll reset and the list's empty-then-async re-render.

**Approach.** Next.js parallel + intercepting routes. From the results list,
`/jobs/:id` renders as a modal over the still-mounted list, so scroll and
filters are preserved *structurally* rather than restored after the fact. A
direct visit, refresh, or new tab renders the full standalone detail page.

**Trade-off / alternatives.** Considered opening jobs in a new tab — reliable,
but it abandons the same-tab Back flow. The modal keeps that flow *and* keeps
`/jobs/:id` a real, shareable URL; the cost is the parallel-route wiring (a
`@modal` slot plus a `(.)jobs/[id]` intercept).

## Résumé matching reuses the search pipeline

**Problem.** Match results were a single fixed page — no pagination, sort, or
filter — and opening a matched job lost the uploaded résumé.

**Approach.** `/match` now mirrors `/search`: the résumé embedding selects the
same relevant-candidate pool, with sort, source filter, and pagination layered
on top. The detail modal keeps the match page mounted, so the résumé survives
opening and closing a job. Pagination re-sends the file and re-embeds per page
rather than holding server-side session state.

**Constraint preserved.** The existing PostHog experiment still governs the
relevance ordering — control = pure cosine, variant = cosine blended with
résumé/job skill-overlap coverage. The variant now reranks the full pool instead
of a fixed candidate count.

**Trade-off.** Stateless matching costs a résumé re-embed per page (cheap once
the model is warm). A full browser refresh still needs a re-upload, since a file
can't persist across reload.

## Honest handling of preview-only descriptions

**Problem.** Some descriptions were full, others truncated with "…", even when
the source site had the whole text.

**Cause.** The aggregator API (the largest feed) returns only a *preview* of the
description; the per-company ATS feeds return the full text.

**Approach.** Mark the preview case in the UI ("Preview only — full description
on the employer's site") and link out to the source, rather than scraping the
employer page behind the redirect — which would mean defeating its bot
protection and breaching the feed's terms. Coverage grows by adding official
feeds, never by working around a wall.

## Encoding repair

**Problem.** A subset of titles and descriptions showed mojibake — UTF-8 misread
as Latin-1 upstream, e.g. an en-dash rendered as `â€"`.

**Approach.** A one-time `ftfy.fix_text` repair pass over stored
title/company/description (run against both the local and production
databases), plus the same normalization in the ingestion path so new records
stay clean. `ftfy` leaves already-correct text untouched, so it is safe to run
over the whole table.

## Production on free tiers; cloud as a demonstration

**Decision.** The running product is FastAPI on a Hugging Face Docker Space, the
Next.js frontend on Vercel (pointed at the Space via `NEXT_PUBLIC_API_URL`), and
the search index on Neon serverless Postgres — all free tiers, so steady-state
cost is zero. Bringing production live involved fixing the Space's container
boot, migrating the full deduplicated index to Neon, and backfilling embeddings
there so résumé matching covers the whole index. Managed-cloud warehouse work is
provisioned with Terraform, demonstrated, and destroyed.

## Retrieval recall: tuning the HNSW candidate window

**Problem.** The relevance pool is the top ~200 by cosine similarity, yet matching sometimes skipped obviously-relevant postings that were in the index.

**Cause.** `hnsw.ef_search` defaults to 40 — below the 200-candidate pool — so the index explored too few neighbours and the pool was truncated before ranking ran.

**Approach.** Set `hnsw.ef_search = 400` before each similarity query in the search and match paths, comfortably above the pool size.

**Trade-off.** A wider search window costs slightly more per query; at the 200-pool it stays ~6 ms p95 on local Postgres, so the recall fix is effectively free at this scale. (ADR-0013.)

## Deduplication: signature over `title + company + city`, not full text

**Problem.** The same role recurs across feeds and within one feed; an early full-text MinHash over-merged distinct postings that merely shared aggregator boilerplate.

**Approach.** Compute the MinHash signature over `title + company + city` only, with a Jaccard threshold, so near-duplicates collapse on the fields that actually identify a posting.

**Result / trade-off.** ~1,409 of 10,423 (13.5%) collapse as duplicates, leaving ~9,000 canonical. The narrower signature can under-merge genuine dupes with reformatted titles — accepted, because full-text over-merging silently dropped real jobs. (ADR-0007.)

## Salary explorer: one currency, real cities

**Problem.** The salary endpoint mixed INR and USD postings on one axis and surfaced raw aggregator localities ("Richmond Town", "Mini Sectt.") as if they were cities, so the chart was noise.

**Approach.** Filter to INR only and fold localities into canonical metros by substring match, with a minimum-postings floor per metro.

**Result / trade-off.** Nine legible metros (Delhi → Gurugram). Localities that don't name a known metro fall to "Other" or drop below the floor — accepted, because a chart a reader can trust beats one listing every neighbourhood.

## The disclosed-salary reality (a planned analysis, rescoped)

**Problem.** The plan assumed salary modelling over a large slice of the index. In practice Indian tech postings rarely publish a structured salary — only ~670 of 9,000+ carried an INR range.

**Approach.** Scope the regression and K-means clustering to that disclosed-salary subset rather than inflate it — folding USD remote roles in, for instance, would contaminate an India-salary model with a different population.

**Result / trade-off.** A small, honest n. The model is descriptive, not predictive (experience dominates; city and role aren't significant in this slice), and salary opacity becomes a finding in its own right. Better a defensible ~670 than a misleading large number.

## Ingestion: official feeds and ATS over bot walls

**Problem.** The original source list leaned on scraping Naukri, Wellfound, Hirist, Instahyre, Indeed — all of which gate automated access.

**Approach.** Build one Scrapy spider per source, but draw real volume from official APIs and open ATS feeds (Adzuna, The Muse, Jobicy, Greenhouse/Lever/Ashby, RemoteOK, Remotive). The Naukri/Wellfound spiders exist but are best-effort: when a wall appears they fall back to APIs rather than escalating to proxies, stealth, or CAPTCHA-solving.

**Result / trade-off.** Eight working sources, one aggregator ~80% of the index. The cost is an aggregator-heavy index and fewer India-native boards — accepted, because the alternative breaches both the platforms' terms and this project's own rule. Coverage grows by adding feeds, never by defeating protection.

## Multi-warehouse without forking the models

**Problem.** The same dbt models had to materialise into both Postgres (live source) and Snowflake (trial), but array handling and date functions differ, and the embedding table exists only in Postgres.

**Approach.** Dialect-gate the models: Postgres reads live sources with native `unnest`; Snowflake reads pre-exported CSV seeds with Snowflake date functions; `stg_jobs_embeddings` is disabled off-Postgres.

**Trade-off.** Two read paths to maintain — accepted as the price of a genuine multi-warehouse demonstration rather than a single-engine project wearing two labels.
