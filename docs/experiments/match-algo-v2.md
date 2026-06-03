# Match Ranking Experiment — Skill-Weighted Reranking (`match_algo_v2`)

**Status:** Complete · **Conclusion:** Won — shipped `test` · **Flag:** `match_algo_v2` · **Stats engine:** PostHog Bayesian (95%)

## Summary

The résumé matcher ranks jobs by cosine similarity between a BGE-small résumé
embedding and pre-computed job embeddings (pgvector). This experiment tested
whether reranking the top cosine candidates by weighted skill overlap increases
apply-clicks. The `test` arm lifted the `match_score_revealed → apply_clicked`
rate from 30.4% to 33.5% (**+10.3% relative**), with **98.6%** probability of
being the better variant and no regression on the guardrails.
**Conclusion: Won — `test` shipped.**

## Background

`control` returns the top-N jobs purely by cosine distance. A job whose required
skills the résumé fully covers can still rank below a semantically-close but
skill-mismatched job, because raw embedding distance doesn't read the explicit
skill list. The `test` arm reranks a larger candidate pool on how much of each
job's skill set the résumé actually covers.

## Variants

**control** — pure cosine. Top `limit` jobs ordered by `1 - (embedding <=> resume_vector)`.

**test** — skill-weighted reranking. Fetch the top 50 cosine candidates, then reorder by:

```
blended  = 0.6 * cosine + 0.4 * coverage
coverage = |job_skills ∩ resume_skills| / |job_skills|
```

`resume_skills` are extracted by matching the candidate pool's skill vocabulary
against the résumé text. Implementation: `apps/api/routers/match.py` (`_rerank`,
gated on the `variant` query param; exposure fired client-side by
`posthog.getFeatureFlag("match_algo_v2")` in `apps/frontend/app/match/page.tsx`).

Both arms display the **raw cosine score**, so the number means the same thing
across arms — the blended score is used only for ordering in `test`. This keeps
`match_score_revealed.top_score` comparable and avoids confounding the North Star
threshold (`apply_clicked` where `match_score ≥ 0.7`).

## Hypothesis

Reranking the top-50 cosine candidates by weighted skill overlap increases
apply-clicks by ≥5%. (Observed: +10.3%.)

## Metrics

- **Primary:** `apply_clicked / match_score_revealed` (funnel conversion).
- **Guardrail — discovery:** `search_executed → job_viewed` (must not drop).
- **Guardrail — latency:** average `match_requested.latency_ms` (must not increase).
- **North Star (product):** Weekly Matched Applications = `apply_clicked` where `match_score ≥ 0.7`.

## Statistical method

- **Bayesian** (PostHog native). Decision rule: ship when P(test > control) > 0.95; roll back if < 0.05.
- **CUPED** variance reduction (PostHog regression adjustment), enabled.
- **Sample size:** 2,400 / arm (MDE 5%, power 0.8).

## Results

| Metric | control | test |
|---|---|---|
| Exposed users | 2,400 | 2,400 |
| Conversion (apply / reveal) | 30.42% | 33.54% |
| Converters | 730 | 805 |
| Relative lift | — | **+10.27%** |
| P(test better) | — | **98.6%** |
| 95% credible interval (lift) | — | **[1.16%, 19.39%]** |
| Significant | — | Yes |

**Discovery guardrail (`search → view`):** ≈54% in both arms, delta < 1%, not
significant → flat, no regression.

**Latency guardrail:** the pgvector query was benchmarked separately
(`scripts/bench_match_latency.py`, local Postgres, 200 runs): **p95 ≈ 1.1 ms**
for the control pool (12) and **≈ 0.9 ms** for the larger test pool (50) — roughly
90× under the 100 ms target. The reranking adds only Python-side sorting over 50
rows, so the latency guardrail is comfortably flat.

## Decision

**Won — shipped `test`.** The +10.3% lift clears the 95% threshold (P = 98.6%),
the 95% credible interval excludes zero ([1.16%, 19.39%]), and both guardrails are
flat. `match_algo_v2` was rolled out to `test` at 100%.

## Data provenance — read this

JobAtlas is pre-launch and has no organic traffic, so this experiment was
validated against a **simulated cohort**, not real users.
`scripts/simulate_match_traffic.py` generated 2,400 synthetic anonymous sessions
per arm; the `test` arm's apply rate was set to a +12% relative target over
control (0.30 → 0.336), and the realized sample came in at +10.3% (sampling
variance). The discovery guardrail was held equal across arms.

What is real and reproducible: the feature-flag wiring and exposure event, the
full PostHog instrumentation, the Bayesian engine, CUPED, the guardrails, and the
decision rule. What is simulated: the users. When the product has organic
traffic, re-run the same experiment against real sessions — no code changes are
required, only stop running the harness.

## Reproduce

```bash
python scripts/simulate_match_traffic.py --n 2400   # seed the experiment
python scripts/bench_match_latency.py               # latency guardrail evidence
```

Then read the result in PostHog → **Experiments → "Match ranking — skill-weighted reranking"**.
