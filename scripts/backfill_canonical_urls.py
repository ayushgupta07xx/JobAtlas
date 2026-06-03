"""One-time backfill: canonicalize existing staging.jobs.source_url values.

Groups rows by (source, canonical_url). For each group with no already-canonical
member, rewrites one keeper (prefer non-duplicate, else lowest id) to the
canonical URL; param-variant rows are left in place (already marked
is_duplicate by the dedup pass). Collision-safe: only one keeper per group is
rewritten, and groups that already contain the canonical URL are skipped, so the
(source, source_url) unique constraint is never violated.

Run the `dedup` job afterwards. Run from the repo root:

    python scripts/backfill_canonical_urls.py --dry-run
    python scripts/backfill_canonical_urls.py
"""

from __future__ import annotations

import argparse
import os
from collections import defaultdict

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from jobatlas.urls import canonicalize_url


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    load_dotenv()
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with engine.begin() as conn:
        rows = conn.execute(
            text("select id, source, source_url, is_duplicate from staging.jobs")
        ).all()

        groups: dict[tuple[str, str], list[tuple[int, str, bool]]] = defaultdict(list)
        for jid, source, url, is_dup in rows:
            groups[(source, canonicalize_url(url))].append((jid, url, is_dup))

        updates: list[dict[str, object]] = []
        variants_left = 0
        for (_source, canon), members in groups.items():
            if len(members) > 1:
                variants_left += len(members) - 1
            if any(url == canon for _, url, _ in members):
                continue  # canonical row already exists; leave the group as-is
            keeper = sorted(members, key=lambda m: (m[2], m[0]))[0]
            updates.append({"jid": keeper[0], "url": canon})

        print(
            f"rows={len(rows)} groups={len(groups)} "
            f"keepers_to_rewrite={len(updates)} param_variants_left={variants_left}"
        )
        if args.dry_run:
            print("dry-run: no writes")
            return

        for start in range(0, len(updates), 1000):
            conn.execute(
                text("update staging.jobs set source_url = :url where id = :jid"),
                updates[start : start + 1000],
            )
        print(f"rewrote {len(updates)} keeper URLs to canonical form")
    engine.dispose()


if __name__ == "__main__":
    main()
