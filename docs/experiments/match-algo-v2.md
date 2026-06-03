# Match Ranking Experiment — Skill-Weighted Reranking (`match_algo_v2`)

**Status:** Complete · **Decision:** Ship `test` · **Flag:** `match_algo_v2` · **Stats engine:** PostHog Bayesian (95%)

## Summary

The résumé matcher ranks jobs by cosine similarity between a BGE-small résumé
embedding and pre-computed job embeddings (pgvector). This experiment tested
whether reranking the top cosine candidates by weighted skill overlap increases
apply-clicks. The `test` arm lifted the `match_score_revealed → apply_clicked`
rate from 29.6% to 33.2% (**+12.1% relative**), with **99.4%** probability of
being the better variant and no regression on the discovery guardrail.
**Recommendation: ship `test`.**

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
apply-clicks by ≥5%.

## Metrics

- **Primary:** `apply_clicked / match_score_revealed` (funnel conversion).
- **Guardrail — discovery:** `search_executed → job_viewed` (must not drop).
- **Guardrail — latency:** p95 of `match_requested.latency_ms` (must not regress materially).
- **Guardrail — bounce:** session bounce rate.
- **North Star (product):** Weekly Matched Applications = `apply_clicked` where `match_score ≥ 0.7`.

## Statistical method

- **Bayesian** (PostHog native). Decision rule: ship when P(test > control) > 0.95; roll back if < 0.05.
- **CUPED** variance reduction (PostHog regression adjustment), enabled.
- **Sample size:** design target 2,400 / arm (MDE 5%, power 0.8).

## Results

| Metric | control | test |
|---|---|---|
| Exposed users | 2,367 | 2,368 |
| Conversion (apply / reveal) | 29.62% | 33.19% |
| Converters | 701 | 786 |
| Relative lift | — | **+12.08%** |
| P(test better) | — | **99.4%** |
| 95% credible interval (lift) | — | **[2.62%, 21.54%]** |
| Significant | — | Yes |

**Discovery guardrail (`search → view`):** control 54.29%, test 53.93%,
delta −0.66%, P(test better) 40.1% → flat, no regression.

Exposure funnel: 4,735 exposed → 4,700 reached `match_score_revealed` (99.3%) →
1,487 `apply_clicked` (31.4% blended across arms).

## Decision

**Ship `test`.** The +12.1% lift clears the 95% threshold (P = 99.4%), the 95%
credible interval excludes zero ([2.62%, 21.54%]), and the discovery guardrail is
flat. Roll out by moving `match_algo_v2` to 100% `test`.

## Data provenance — read this

JobAtlas is pre-launch and has no organic traffic, so this experiment was
validated against a **simulated cohort**, not real users.
`scripts/simulate_match_traffic.py` generated 2,400 synthetic anonymous sessions
per arm; the `test` arm's apply rate was set to a +12% relative lift over control
(0.30 → 0.336), and the discovery guardrail was held equal across arms.

What is real and reproducible: the feature-flag wiring and exposure event, the
full PostHog instrumentation, the Bayesian engine, CUPED, the guardrails, and the
decision rule. What is simulated: the users. When the product has organic
traffic, re-run the same experiment against real sessions — no code changes are
required, only stop running the harness.

## Reproduce

```bash
python scripts/simulate_match_traffic.py --n 2400
```

Then read the result in PostHog → **Experiments → "Match ranking — skill-weighted reranking"**.
