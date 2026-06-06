#!/usr/bin/env bash
# fix_missing_issues.sh
# Recreates the two issues that failed in the first run (US-04, US-12) and closes them (shipped).
# Run from inside ~/code/JobAtlas:  bash fix_missing_issues.sh
set -u

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

b=$(cat <<'EOF'
**As a** senior hire (Sneha), **I want** to restrict results to senior roles and sort by recency, **so that** I see only relevant, current openings.

**Acceptance criteria**
- A seniority filter leaves only senior/lead/manager-level postings.
- A sort-by-newest option orders results by posted date descending.

_Full spec: docs/business/user_stories.md (US-04)_
EOF
); mk "US-04 — Senior filtering with freshness sort" E1 3 5 done "$b"

b=$(cat <<'EOF'
**As a** fresh-graduate job seeker (Anjali), **I want** to see the most in-demand skills by city, **so that** I can prioritise what to learn.

**Acceptance criteria**
- The top skills by posting frequency are listed for a selected city.
- Selecting a skill navigates to current postings requiring it.

_Full spec: docs/business/user_stories.md (US-12)_
EOF
); mk "US-12 — Skill-demand explorer" E3 3 4 done "$b"

echo
echo "Created the 2 missing issues. Re-verify: gh issue list --state all --limit 25"
