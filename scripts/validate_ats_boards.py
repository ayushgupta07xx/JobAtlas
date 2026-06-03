#!/usr/bin/env python3
"""Validate candidate ATS board slugs against the live public APIs.

Read-only. Hits the same public Greenhouse / Lever / Ashby job-board JSON
endpoints the spiders use (no auth, no proxy, no anti-bot bypass). For each
candidate slug it reports whether the board is live and how many of its open
roles pass the project's India filter -- so we only add boards that actually
yield India roles, never dead/empty slugs.

    python scripts/validate_ats_boards.py          # validate all candidates
    python scripts/validate_ats_boards.py --min 3  # keeper threshold (default 1)

Output ends with ready-to-paste dict additions for ats_common.py.
A wrong/stale slug is harmless: Greenhouse returns [], Lever/Ashby 404 -- logged
and skipped, nothing billed. The India counts are PRE-dedup; the clean gain
after MinHash dedup against the existing index will be lower.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Reuse the EXACT India filter + existing seed dicts from the spiders' shared
# module, so reported counts match what the spider keeps and we never re-suggest
# an already-seeded slug. ats_common is stdlib-only, so this import is cheap.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scrapers"))
from jobatlas_scrapers.ats_common import (  # noqa: E402
    ASHBY,
    GREENHOUSE,
    LEVER,
    is_india_location,
)

UA = "JobAtlas-board-validator/1.0 (+https://github.com/ayushgupta07xx/JobAtlas)"
TIMEOUT = 12
DELAY = 0.5  # polite; matches the spiders' DOWNLOAD_DELAY

URLS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
}

# (ats, slug, display_name) -- best-guess slugs; the validator confirms each.
CANDIDATES: list[tuple[str, str, str]] = [
    # ---- Greenhouse: India-HQ / large India engineering (high yield) ----
    ("greenhouse", "razorpay", "Razorpay"),
    ("greenhouse", "meesho", "Meesho"),
    ("greenhouse", "sprinklr", "Sprinklr"),
    ("greenhouse", "innovaccer", "Innovaccer"),
    ("greenhouse", "browserstack", "BrowserStack"),
    ("greenhouse", "hasura", "Hasura"),
    ("greenhouse", "chargebee", "Chargebee"),
    ("greenhouse", "zeta", "Zeta"),
    ("greenhouse", "setu", "Setu"),
    ("greenhouse", "mindtickle", "Mindtickle"),
    ("greenhouse", "gupshup", "Gupshup"),
    ("greenhouse", "whatfix", "Whatfix"),
    ("greenhouse", "cars24", "CARS24"),
    ("greenhouse", "spinny", "Spinny"),
    ("greenhouse", "upgrad", "upGrad"),
    ("greenhouse", "navi", "Navi"),
    ("greenhouse", "m2pfintech", "M2P Fintech"),
    ("greenhouse", "leadsquared", "LeadSquared"),
    ("greenhouse", "yellowai", "Yellow.ai"),
    ("greenhouse", "zepto", "Zepto"),
    ("greenhouse", "apna", "Apna"),
    ("greenhouse", "moengage", "MoEngage"),
    ("greenhouse", "porter", "Porter"),
    ("greenhouse", "acko", "Acko"),
    # ---- Greenhouse: global firms with sizeable India engineering ----
    ("greenhouse", "coinbase", "Coinbase"),
    ("greenhouse", "dropbox", "Dropbox"),
    ("greenhouse", "twilio", "Twilio"),
    ("greenhouse", "hashicorp", "HashiCorp"),
    ("greenhouse", "elastic", "Elastic"),
    ("greenhouse", "confluent", "Confluent"),
    ("greenhouse", "hubspot", "HubSpot"),
    ("greenhouse", "asana", "Asana"),
    ("greenhouse", "doordash", "DoorDash"),
    ("greenhouse", "samsara", "Samsara"),
    ("greenhouse", "plaid", "Plaid"),
    ("greenhouse", "brex", "Brex"),
    ("greenhouse", "retool", "Retool"),
    ("greenhouse", "wise", "Wise"),
    # ---- Lever: verify at jobs.lever.co/<slug> ----
    ("lever", "epifi", "Fi Money"),
    ("lever", "smallcase", "smallcase"),
    ("lever", "plum", "Plum"),
    ("lever", "zolve", "Zolve"),
    ("lever", "jarapp", "Jar"),
    ("lever", "uni", "Uni Cards"),
    # ---- Ashby: verify at jobs.ashbyhq.com/<slug> ----
    ("ashby", "fold", "Fold"),
    ("ashby", "spotdraft", "SpotDraft"),
    ("ashby", "pocketfm", "Pocket FM"),
    ("ashby", "rocketlane", "Rocketlane"),
    ("ashby", "composio", "Composio"),
    ("ashby", "fireflies", "Fireflies.ai"),
]


def _india_count_greenhouse(payload: object) -> tuple[int, int]:
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    n = 0
    for j in jobs:
        loc = (j.get("location") or {}).get("name")
        offices = " ".join(o.get("location") or "" for o in (j.get("offices") or []))
        if is_india_location(loc, offices):
            n += 1
    return len(jobs), n


def _india_count_lever(payload: object) -> tuple[int, int]:
    if not isinstance(payload, list):
        return 0, 0
    n = 0
    for j in payload:
        cats = j.get("categories") or {}
        if is_india_location(
            cats.get("location"), j.get("workplaceType"), cats.get("allLocations")
        ):
            n += 1
    return len(payload), n


def _india_count_ashby(payload: object) -> tuple[int, int]:
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    n = 0
    for j in jobs:
        sec = " ".join(s.get("location") or "" for s in (j.get("secondaryLocations") or []))
        addr = ((j.get("address") or {}).get("postalAddress")) or {}
        if is_india_location(j.get("location"), sec, addr.get("addressCountry")):
            n += 1
    return len(jobs), n


COUNTERS = {
    "greenhouse": _india_count_greenhouse,
    "lever": _india_count_lever,
    "ashby": _india_count_ashby,
}


def _fetch(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310 (https only)
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--min", type=int, default=1, help="min India roles to count a board as a keeper"
    )
    args = ap.parse_args()

    existing = {"greenhouse": GREENHOUSE, "lever": LEVER, "ashby": ASHBY}
    keepers: dict[str, dict[str, tuple[str, int]]] = {"greenhouse": {}, "lever": {}, "ashby": {}}
    skipped = 0

    print(f"{'ATS':<11}{'SLUG':<16}{'COMPANY':<18}{'TOTAL':>6}{'INDIA':>6}  STATUS")
    print("-" * 78)
    for ats, slug, company in CANDIDATES:
        if slug in existing[ats]:
            skipped += 1
            continue
        try:
            total, india = COUNTERS[ats](_fetch(URLS[ats].format(slug=slug)))
            status = "LIVE" if india >= args.min else ("0-india" if total else "empty")
            if india >= args.min:
                keepers[ats][slug] = (company, india)
        except urllib.error.HTTPError as e:
            total = india = 0
            status = f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001 -- diagnostic tool, report and continue
            total = india = 0
            status = f"ERR {type(e).__name__}"
        print(f"{ats:<11}{slug:<16}{company:<18}{total:>6}{india:>6}  {status}")
        time.sleep(DELAY)

    print("-" * 78)
    grand = 0
    for ats in ("greenhouse", "lever", "ashby"):
        if not keepers[ats]:
            continue
        roles = sum(c[1] for c in keepers[ats].values())
        grand += roles
        print(
            f"\n# --- add to {ats.upper()} in ats_common.py "
            f"({len(keepers[ats])} new boards, {roles} India roles pre-dedup) ---"
        )
        for slug, (company, _india) in sorted(keepers[ats].items()):
            print(f'    "{slug}": "{company}",')

    boards = sum(len(k) for k in keepers.values())
    print(
        f"\nValidated {boards} new boards -> ~{grand} India roles (PRE-dedup; "
        f"clean gain will be lower). Skipped {skipped} already-seeded."
    )


if __name__ == "__main__":
    main()
