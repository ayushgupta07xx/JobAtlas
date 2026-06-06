#!/usr/bin/env bash
# create_board_issues.sh
# Creates epic/points labels, 5 sprint milestones, and 20 user-story issues
# (with acceptance criteria), then closes the 17 shipped ones.
# Run ONCE from inside ~/code/JobAtlas:  bash create_board_issues.sh
# Re-running will create DUPLICATES — only run once.

set -u

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Target repo: $REPO"

# ---------- Labels (ignore "already exists") ----------
gh label create "epic:E1" --color 1f77b4 --description "Discovery & Search"        2>/dev/null || true
gh label create "epic:E2" --color ff7f0e --description "Resume Matching"            2>/dev/null || true
gh label create "epic:E3" --color 2ca02c --description "Salary & Skill Intelligence" 2>/dev/null || true
gh label create "epic:E4" --color d62728 --description "Account & Retention"        2>/dev/null || true
gh label create "epic:E5" --color 9467bd --description "Recruiter"                  2>/dev/null || true
gh label create "epic:E6" --color 8c564b --description "Data Platform & Quality"    2>/dev/null || true
for p in 1 2 3 5 8 13; do
  gh label create "points:$p" --color cccccc --description "Story points: $p" 2>/dev/null || true
done

# ---------- Sprint milestones (ignore duplicates) ----------
for s in 1 2 3 4 5; do
  gh api "repos/$REPO/milestones" -f title="Sprint $s" >/dev/null 2>&1 || true
done

# ---------- Helper ----------
mk() {  # title  epic  points  sprint  state(done|planned)  body
  local title="$1" epic="$2" pts="$3" sprint="$4" state="$5" body="$6"
  local url
  url=$(gh issue create --title "$title" --body "$body" \
        --label "epic:$epic,points:$pts" --milestone "Sprint $sprint")
  echo "created: $url"
  if [ "$state" = "done" ]; then
    gh issue close "$url" >/dev/null && echo "  closed (shipped)"
  fi
}

# ===================== EPIC 1 — Discovery & Search =====================
b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to search every source from one box, **so that** I don't repeat the same search across five portals.

**Acceptance criteria**
- Results from all indexed sources appear in one ranked list, each card labelled with its source.
- Near-duplicate postings are collapsed to one canonical card.
- Search p95 latency is under 500 ms.

_Full spec: docs/business/user_stories.md (US-01)_
EOF
); mk "US-01 — Unified cross-portal search" E1 5 1 done "$b"

b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to filter by city, role and experience, **so that** I only see roles I can realistically apply to.

**Acceptance criteria**
- Applying filter chips updates results without a full page reload.
- An experience filter of "fresher/0–1 yr" excludes senior-only postings.

_Full spec: docs/business/user_stories.md (US-02)_
EOF
); mk "US-02 — Filter by location, role and experience" E1 3 1 done "$b"

b=$(cat <<'EOF'
**As a** career switcher (Rohit), **I want** search to understand intent, not exact keywords, **so that** roles matching my transferable skills surface even when the title differs.

**Acceptance criteria**
- Results include semantically related roles (embedding similarity), not only literal keyword matches.
- A transferable-skill query returns at least one adjacent-job-family role in the top results.

_Full spec: docs/business/user_stories.md (US-03)_
EOF
); mk "US-03 — Semantic search beyond exact title" E1 8 2 done "$b"

b=$(cat <<'EOF'
**As a** senior hire (Sneha), **I want** to restrict results to senior roles and sort by recency, **so that** I see only relevant, current openings.

**Acceptance criteria**
- A seniority filter leaves only senior/lead/manager-level postings.
- A sort-by-newest option orders results by posted date descending.

_Full spec: docs/business/user_stories.md (US-04)_
EOF
); mk "US-04 — Senior filtering with freshness sort" E1 3 5 done "$b"

# ===================== EPIC 2 — Resume Matching =====================
b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to upload my resume and get ranked job matches with a score, **so that** I know which roles I'm genuinely competitive for.

**Acceptance criteria**
- A ranked list of jobs is returned, each with a similarity score, ordered by score descending.
- Match p95 latency is under 100 ms (BGE-small 384-dim embeddings, pgvector retrieval).
- An unsupported file type shows a clear validation error and no match is attempted.

_Full spec: docs/business/user_stories.md (US-05)_
EOF
); mk "US-05 — Resume upload to ranked matches" E2 13 2 done "$b"

b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to see why a job matched me, **so that** I trust the score and learn what employers value.

**Acceptance criteria**
- A match's detail shows the overlapping skills that drove the score.
- The match score is presented on a consistent, interpretable scale.

_Full spec: docs/business/user_stories.md (US-06)_
EOF
); mk "US-06 — Match explanation" E2 5 3 done "$b"

b=$(cat <<'EOF'
**As a** career switcher (Rohit), **I want** matches to credit my transferable skills, **so that** adjacent-function roles appear even though my current title doesn't match them.

**Acceptance criteria**
- A resume from one function returns roles in a target adjacent function with overlapping skills.
- The match detail lists the transferable skills responsible.

_Full spec: docs/business/user_stories.md (US-07)_
EOF
); mk "US-07 — Transferable-skill matching" E2 5 3 done "$b"

b=$(cat <<'EOF'
**As a** senior hire (Sneha), **I want** a short list of strong matches rather than a long noisy one, **so that** I can evaluate quickly.

**Acceptance criteria**
- Results are ranked by descending score with the strongest matches first.
- Each item shows its score so weak tail matches are visually distinguishable.

_Full spec: docs/business/user_stories.md (US-08)_
EOF
); mk "US-08 — High-precision senior matches" E2 3 3 done "$b"

# ===================== EPIC 3 — Salary & Skill Intelligence =====================
b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to see typical entry-level pay by city and role, **so that** I can set realistic expectations.

**Acceptance criteria**
- A salary distribution is shown for postings where salary data is available.
- When data is missing, the view states coverage transparently rather than implying full coverage.

_Full spec: docs/business/user_stories.md (US-09)_
EOF
); mk "US-09 — Entry-level salary by city and role" E3 5 4 done "$b"

b=$(cat <<'EOF'
**As a** career switcher (Rohit), **I want** to compare pay between my current and a target role, **so that** I can quantify the impact of switching.

**Acceptance criteria**
- Two roles' salary distributions appear side by side for the same city, where data exists.
- Missing role/city data is labelled rather than interpolated.

_Full spec: docs/business/user_stories.md (US-10)_
EOF
); mk "US-10 — Cross-role salary comparison" E3 5 4 done "$b"

b=$(cat <<'EOF'
**As a** senior hire (Sneha), **I want** compensation benchmarks at senior bands, **so that** I can judge whether a role is worth a conversation.

**Acceptance criteria**
- A senior-band distribution is shown for a role/city where data is available.
- Thin senior-band data has its sample basis disclosed.

_Full spec: docs/business/user_stories.md (US-11)_
EOF
); mk "US-11 — Senior-band compensation benchmarking" E3 3 4 done "$b"

b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to see the most in-demand skills by city, **so that** I can prioritise what to learn.

**Acceptance criteria**
- The top skills by posting frequency are listed for a selected city.
- Selecting a skill navigates to current postings requiring it.

_Full spec: docs/business/user_stories.md (US-12)_
EOF
); mk "US-12 — Skill-demand explorer" E3 3 4 done "$b"

# ===================== EPIC 4 — Account, Saving & Retention =====================
b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to save jobs to a shortlist, **so that** I can return to them later.

**Acceptance criteria**
- Saving a job adds it to my shortlist and the state persists for my session/account.
- My shortlist lists all saved jobs with their source.

_Full spec: docs/business/user_stories.md (US-13)_
EOF
); mk "US-13 — Save and shortlist jobs" E4 1 5 planned "$b"

b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to see which jobs I've clicked through to apply to, **so that** I don't apply to the same role twice.

**Acceptance criteria**
- An apply-click is recorded in my application history.
- Each history entry shows the job, source and date.

_Full spec: docs/business/user_stories.md (US-14)_
EOF
); mk "US-14 — Application tracking" E4 3 5 planned "$b"

b=$(cat <<'EOF'
**As a** career switcher (Rohit), **I want** to be notified when new matching roles appear, **so that** I don't keep re-running searches.

**Acceptance criteria**
- When new jobs match my saved profile above a threshold, I receive a notification.
- The notification links directly to the matching jobs.

_Full spec: docs/business/user_stories.md (US-15)_
EOF
); mk "US-15 — New-match alerts" E4 5 5 planned "$b"

# ===================== EPIC 5 — Recruiter Tools =====================
b=$(cat <<'EOF'
**As a** recruiter, **I want** to type a company name and see all of its openings aggregated across sources, **so that** I can benchmark a competitor's hiring at a glance.

**Acceptance criteria**
- All indexed postings for the company appear, deduplicated, with each source labelled.
- The company result set is sortable by recency.

_Full spec: docs/business/user_stories.md (US-16)_
EOF
); mk "US-16 — Company-name aggregation search" E5 3 5 done "$b"

b=$(cat <<'EOF'
**As a** recruiter, **I want** each posting to show its source and how recent it is, **so that** I can judge data reliability.

**Acceptance criteria**
- Every posting shows its originating source and posted date.
- A preview-only source is marked as preview and links out to the original posting.

_Full spec: docs/business/user_stories.md (US-17)_
EOF
); mk "US-17 — Source and freshness transparency" E5 2 5 done "$b"

# ===================== EPIC 6 — Data Platform & Quality =====================
b=$(cat <<'EOF'
**As a** member of the platform team, **I want** near-duplicate postings collapsed across sources, **so that** users never see the same job twice.

**Acceptance criteria**
- Records with MinHash Jaccard similarity >= 0.85 are clustered to a single canonical posting.
- The canonical record retains the richest available fields.

_Full spec: docs/business/user_stories.md (US-18)_
EOF
); mk "US-18 — Cross-source deduplication" E6 8 1 done "$b"

b=$(cat <<'EOF'
**As a** member of the platform team, **I want** the index refreshed daily, **so that** users aren't shown stale or filled roles.

**Acceptance criteria**
- The daily orchestrated run ingests new postings and the index reflects them.
- A completed run records freshness and row-count metrics for monitoring.

_Full spec: docs/business/user_stories.md (US-19)_
EOF
); mk "US-19 — Daily freshness refresh" E6 5 1 done "$b"

b=$(cat <<'EOF'
**As a** member of the platform team, **I want** quality checks to block bad records before the warehouse, **so that** downstream analytics stay trustworthy.

**Acceptance criteria**
- A failing expectation suite (row counts, null limits, value ranges, URL patterns) fails the pipeline task.
- Offending records are quarantined and surfaced for review.

_Full spec: docs/business/user_stories.md (US-20)_
EOF
); mk "US-20 — Data-quality gate" E6 3 5 done "$b"

echo
echo "Done. Created 20 issues (17 closed = shipped, 3 open = backlog), 12 labels, 5 milestones."
echo "Verify: gh issue list --state all --limit 25"
