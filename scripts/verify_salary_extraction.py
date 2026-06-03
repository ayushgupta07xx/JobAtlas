#!/usr/bin/env python3
"""Verify salary_from_description on real DB rows BEFORE wiring it into the
normalizer. The salary columns feed the §17 dashboards and the salary
regression, so we check precision on actual data first.

Read-only. Add salary_from_description to apps/normalizer/parsers.py first, then:
    set -a; source .env; set +a
    python scripts/verify_salary_extraction.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# repo root on path so `apps` / `jobatlas` import the same way the normalizer does
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apps.normalizer.parsers import salary_from_description  # noqa: E402
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from jobatlas.db.models import Job  # noqa: E402

SHOW = 30  # sample hits to print for eyeballing


def _snippet(desc: str) -> str:
    low = desc.lower()
    for cue in ("pay range", "salary", "compensation", "ctc", "₹", "lpa", "lakh", "per annum"):
        i = low.find(cue)
        if i >= 0:
            return " ".join(desc[i : i + 90].split())
    return ""


def main() -> None:
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    hits = 0
    by_source: dict[str, int] = {}
    printed = 0
    with Session(engine) as s:
        stmt = select(Job.source, Job.title, Job.description).where(
            Job.salary_min.is_(None),
            Job.salary_max.is_(None),
            Job.description.isnot(None),
        )
        rows = s.execute(stmt).all()
        for source, title, desc in rows:
            smin, smax = salary_from_description(desc)
            if smin is None:
                continue
            hits += 1
            by_source[source] = by_source.get(source, 0) + 1
            if printed < SHOW:
                printed += 1
                print(
                    f"[{source:<10}] {(title or '')[:40]:<40} "
                    f"{smin:>12,.0f} - {smax:<12,.0f} | {_snippet(desc or '')}"
                )
    engine.dispose()
    print("-" * 90)
    print(f"scanned {len(rows)} null-salary rows -> {hits} would now get a salary")
    for src, n in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {src}: {n}")


if __name__ == "__main__":
    main()
