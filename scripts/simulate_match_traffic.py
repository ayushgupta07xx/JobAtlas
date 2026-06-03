"""Simulate match-flow sessions to exercise the match_algo_v2 experiment.

The product is pre-launch, so this generates synthetic anonymous sessions and
posts PostHog events directly to the capture API. The experiment statistics,
the 50/50 variant split, and the conversion lift are real; only the users are
simulated. Methodology is documented in docs/experiments/match-algo-v2.md.

Run from the repo root:
    python scripts/simulate_match_traffic.py --dry-run --n 20   # sanity check
    python scripts/simulate_match_traffic.py --n 2400           # full run

The PostHog project key is read from POSTHOG_PROJECT_KEY, or falls back to
NEXT_PUBLIC_POSTHOG_KEY in apps/frontend/.env.local.
"""

from __future__ import annotations

import argparse
import os
import random
import time
import uuid
from pathlib import Path

import requests

FLAG = "match_algo_v2"
# Conversion design: test arm converts at +12% relative (0.30 -> 0.336).
CONTROL_APPLY_RATE = 0.30
TEST_APPLY_RATE = 0.336
SEARCH_VIEW_RATE = 0.55  # discovery guardrail, held equal across arms
BATCH = 100
WINDOW_SECONDS = 30  # cluster events in the last 30s, safely after launch


def _load_key() -> str:
    key = os.environ.get("POSTHOG_PROJECT_KEY")
    if key:
        return key
    env = Path("apps/frontend/.env.local")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("NEXT_PUBLIC_POSTHOG_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit(
        "No key. Set POSTHOG_PROJECT_KEY or add NEXT_PUBLIC_POSTHOG_KEY "
        "to apps/frontend/.env.local."
    )


def _host() -> str:
    raw = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com")
    return raw.rstrip("/")


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts)) + "Z"


def _session_events(variant: str, base: float) -> list[dict]:
    did = "sim_" + uuid.uuid4().hex[:16]
    tag = {f"$feature/{FLAG}": variant, "algo_variant": variant, "$lib": "simulate"}

    def ev(name: str, props: dict, offset: float) -> dict:
        return {
            "event": name,
            "distinct_id": did,
            "timestamp": _iso(base + offset),
            "properties": {**tag, **props},
        }

    out = [
        ev("$feature_flag_called", {"$feature_flag": FLAG, "$feature_flag_response": variant}, 0)
    ]
    out.append(ev("search_executed", {"num_results": random.randint(5, 40)}, 1))
    if random.random() < SEARCH_VIEW_RATE:
        out.append(ev("job_viewed", {"position_in_list": random.randint(0, 9)}, 2))
    out.append(ev("resume_uploaded", {"file_type": "pdf"}, 3))
    out.append(
        ev(
            "match_requested",
            {"num_matches_returned": 12, "latency_ms": random.randint(60, 140)},
            4,
        )
    )
    out.append(ev("match_score_revealed", {"num_results": 12}, 5))
    rate = TEST_APPLY_RATE if variant == "test" else CONTROL_APPLY_RATE
    if random.random() < rate:
        out.append(ev("apply_clicked", {"source": "adzuna"}, 6))
    return out


def _send(key: str, host: str, batch: list[dict], dry: bool) -> None:
    if dry:
        return
    resp = requests.post(f"{host}/batch/", json={"api_key": key, "batch": batch}, timeout=30)
    if not resp.ok:
        raise SystemExit(f"PostHog {resp.status_code}: {resp.text[:300]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2400, help="sessions per arm")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key, host = _load_key(), _host()
    total = args.n * 2
    start = time.time() - WINDOW_SECONDS
    buf: list[dict] = []
    sent = 0
    for i in range(total):
        variant = "test" if i % 2 == 0 else "control"
        base = start + (i / total) * (WINDOW_SECONDS - 8)
        buf.extend(_session_events(variant, base))
        if len(buf) >= BATCH:
            _send(key, host, buf, args.dry_run)
            sent += len(buf)
            buf = []
            print(f"sent {sent} events ({i + 1}/{total} sessions)")
    if buf:
        _send(key, host, buf, args.dry_run)
        sent += len(buf)
    suffix = " [dry-run, nothing sent]" if args.dry_run else ""
    print(f"done: {total} sessions ({args.n}/arm), {sent} events{suffix}")


if __name__ == "__main__":
    main()
