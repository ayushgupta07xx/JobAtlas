"""Shared helpers + curated company-slug seed for the public ATS spiders.

Greenhouse / Lever / Ashby expose public, unauthenticated job-board JSON APIs --
the same endpoints their own careers pages call from the browser. We read only
those feeds: no login, no proxy, no anti-bot bypass (project no-escalation rule).

Each board returns a company's *global* postings; the spiders keep only
India-relevant roles (city/region match or India-eligible remote) so the raw
zone stays India-scoped and small -- the Neon free-tier constraint at volume.

The slug dicts map board slug -> display company name. This is a SEED, not the
full list. Volume scales ~linearly with breadth: ~400-600 boards => ~15-25k
India roles. Grow it by adding the slug straight from a company's public
careers URL:

    Greenhouse  boards.greenhouse.io/<slug>
    Lever       jobs.lever.co/<slug>
    Ashby       jobs.ashbyhq.com/<slug>

A wrong/stale slug is harmless: Greenhouse returns an empty list, Lever/Ashby
404, and the spider just logs and skips it -- nothing is billed or broken.
"""

from __future__ import annotations

import html as _html
import re as _re

# --- Greenhouse: confirmed-live boards that hire engineering in India -------
# (filtered to India roles at scrape time). Add India-HQ boards as you find them.
GREENHOUSE: dict[str, str] = {
    "stripe": "Stripe",
    "airbnb": "Airbnb",
    "databricks": "Databricks",
    "cloudflare": "Cloudflare",
    "mongodb": "MongoDB",
    "datadog": "Datadog",
    "gitlab": "GitLab",
    "figma": "Figma",
    "reddit": "Reddit",
    "discord": "Discord",
    "pinterest": "Pinterest",
    "lyft": "Lyft",
    "robinhood": "Robinhood",
    "instacart": "Instacart",
    "anthropic": "Anthropic",
    "postman": "Postman",
    "druva": "Druva",
    "groww": "Groww",
    "phonepe": "PhonePe",
    "slice": "Slice",
    "twilio": "Twilio",
    "elastic": "Elastic",
    "samsara": "Samsara",
}

# --- Lever: EXAMPLES -- verify each at jobs.lever.co/<slug> before relying on it.
LEVER: dict[str, str] = {
    "jumpcloud": "JumpCloud",
    "zimperium": "Zimperium",
    "hevodata": "Hevo Data",
    "stable-money1": "Stable Money",
    "cred": "CRED",
    "fampay": "FamPay",
    "epifi": "Fi Money",
}

# --- Ashby: EXAMPLES -- verify each at jobs.ashbyhq.com/<slug>.
ASHBY: dict[str, str] = {
    "linear": "Linear",
    "ramp": "Ramp",
    "vanta": "Vanta",
    "atlan": "Atlan",
    "composio": "Composio",
    "spotdraft": "SpotDraft",
}

# Lowercase tokens that mark a posting as India-relevant. High-precision on
# purpose (this is an India board). Add "apac"/"asia"/"remote" to widen.
_INDIA_TOKENS: tuple[str, ...] = (
    "india",
    "bengaluru",
    "bangalore",
    "mumbai",
    "pune",
    "hyderabad",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "chennai",
    "kolkata",
    "ahmedabad",
    "jaipur",
    "indore",
    "kochi",
    "coimbatore",
    "thiruvananthapuram",
)

_TAG_RE = _re.compile(r"<[^>]+>")
_WS_RE = _re.compile(r"\s+")


# India-eligible remote: worldwide / global / APAC-region remote that an
# India-based applicant can actually take. Bare "remote" is intentionally
# excluded (usually country-locked by default) -- we require an explicit signal.
_REMOTE_TOKENS: tuple[str, ...] = (
    "worldwide",
    "global",
    "anywhere",
    "fully remote",
    "apac",
    "asia pacific",
    "asia",
)


def is_india_location(*parts: object) -> bool:
    """India-located OR India-eligible remote (global / APAC).

    Name kept for call-site stability; scope is now broader than India-only.
    """
    blob = " ".join(str(p) for p in parts if p).lower()
    return any(t in blob for t in _INDIA_TOKENS) or any(t in blob for t in _REMOTE_TOKENS)


def clean_text(value: object) -> str | None:
    """Strip HTML tags + collapse whitespace (for the MinHash text in the item).

    The verbatim payload is still landed untouched; this is only so the early
    cross-source dedup signature is computed on readable text, not markup.
    """
    if not value:
        return None
    text = _html.unescape(_TAG_RE.sub(" ", str(value)))
    text = _WS_RE.sub(" ", text).strip()
    return text or None
