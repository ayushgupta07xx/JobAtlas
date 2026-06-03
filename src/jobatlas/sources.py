"""Per-source compliance policy registry.

Some feeds are free + public yet carry ToS duties owed to the *platform*:
attribution, link-back to the source listing, no re-syndication, and not sitting
behind a signup / PII flow. A user-facing disclaimer does not cure a duty owed
to the platform, so we honour them in code rather than in fine print:

  * the harvester tags provenance (source + source_url),
  * the API filters `exclude_from_match` sources out of the resume-match flow,
  * the frontend renders required attribution and an apply button that links
    back to the source listing (never an internal apply).

Anything not listed here defaults to permissive (own-board feeds, Adzuna, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourcePolicy:
    key: str
    display_name: str
    # show a "via <source>" credit on the card
    attribution_required: bool = False
    # apply button -> source_url (the original listing), not an internal route
    apply_url_is_source: bool = True
    # never surface in /match (resume/PII flow); search + browse still allowed
    exclude_from_match: bool = False
    # the feed is intentionally delayed at the source (informational only)
    freshness_offset_hours: int = 0
    notes: str = ""


SOURCES: dict[str, SourcePolicy] = {
    # --- own-board / structured feeds: aggregate-and-display is intended use ---
    "adzuna": SourcePolicy("adzuna", "Adzuna"),
    "jobicy": SourcePolicy("jobicy", "Jobicy"),
    "greenhouse": SourcePolicy("greenhouse", "Greenhouse"),
    "lever": SourcePolicy("lever", "Lever"),
    "ashby": SourcePolicy("ashby", "Ashby"),
    # --- conditioned: usable with attribution + apply-link-back to source ------
    "himalayas": SourcePolicy(
        "himalayas",
        "Himalayas",
        attribution_required=True,
        notes=(
            "Link back to the Himalayas listing and name Himalayas as source; "
            "do not re-syndicate to third-party aggregators."
        ),
    ),
    "remoteok": SourcePolicy("remoteok", "RemoteOK", attribution_required=True),
    "arbeitnow": SourcePolicy("arbeitnow", "Arbeitnow", attribution_required=True),
    # --- Remotive: kept under strict constraints (see chat decision) -----------
    "remotive": SourcePolicy(
        "remotive",
        "Remotive",
        attribution_required=True,
        exclude_from_match=True,
        freshness_offset_hours=24,
        notes=(
            "ToS: no third-party redistribution, mandatory link-back + "
            "attribution, jobs are 24h-delayed, and must not be displayed behind "
            "a signup / email-collection flow -- hence excluded from /match."
        ),
    ),
}

# permissive fallback for any source not explicitly registered
_DEFAULT = SourcePolicy("unknown", "Unknown")


def policy(source: str) -> SourcePolicy:
    """Return the compliance policy for a source (permissive default)."""
    return SOURCES.get(source, _DEFAULT)


# sources the /match endpoint MUST exclude (resume/PII flow). Import this in the
# API match router:  WHERE source NOT IN :excluded
MATCH_EXCLUDED_SOURCES: frozenset[str] = frozenset(
    k for k, v in SOURCES.items() if v.exclude_from_match
)
