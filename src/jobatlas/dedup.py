"""MinHash LSH dedup over staging.jobs. Runs in the JobAtlas venv.

Dedup signature is computed over title+company+city (role-identity fields), NOT the
scrape-time signature carried in staging.jobs.minhash_signature: that one spans full
text incl. description, which over-merges distinct roles sharing an aggregator's
boilerplate description (see ADR-0007). Threshold via CLI.
"""

from __future__ import annotations

import argparse
import logging
import os
import re

from datasketch import MinHash, MinHashLSH
from sqlalchemy import create_engine, text

NUM_PERM = 128
SHINGLE_K = 3
log = logging.getLogger("jobatlas.dedup")


def _shingles(value: str, k: int = SHINGLE_K) -> list[str]:
    words = re.findall(r"[a-z0-9]+", value.lower())
    if len(words) < k:
        return [" ".join(words)] if words else []
    return [" ".join(words[i : i + k]) for i in range(len(words) - k + 1)]


def _minhash(value: str) -> MinHash:
    m = MinHash(num_perm=NUM_PERM)
    for sh in _shingles(value):
        m.update(sh.encode("utf-8"))
    return m


def run(threshold: float) -> None:
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with engine.begin() as conn:
        rows = conn.execute(
            text("select id, title, company, city from staging.jobs where is_active")
        ).all()
        log.info("dedup over %d jobs (threshold=%.2f)", len(rows), threshold)

        mh: dict[int, MinHash] = {}
        lsh = MinHashLSH(threshold=threshold, num_perm=NUM_PERM)
        for jid, title, company, city in rows:
            key = " ".join(p for p in (title, company, city) if p)
            m = _minhash(key)
            mh[jid] = m
            lsh.insert(str(jid), m)

        parent: dict[int, int] = {jid: jid for jid in mh}

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)

        for jid, m in mh.items():
            for cand_key in lsh.query(m):
                cand = int(cand_key)
                if cand != jid and m.jaccard(mh[cand]) >= threshold:
                    union(jid, cand)

        groups: dict[int, list[int]] = {}
        for jid in mh:
            groups.setdefault(find(jid), []).append(jid)

        updates = [
            {"jid": jid, "grp": root, "dup": jid != root}
            for root, members in groups.items()
            for jid in members
        ]
        if updates:
            conn.execute(
                text(
                    "update staging.jobs set is_duplicate = :dup, dedup_group_id = :grp "
                    "where id = :jid"
                ),
                updates,
            )
        dup_count = sum(1 for u in updates if u["dup"])
        multi = sum(1 for m in groups.values() if len(m) > 1)
        log.info("marked %d duplicates across %d multi-member groups", dup_count, multi)
    engine.dispose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.85)
    run(ap.parse_args().threshold)


if __name__ == "__main__":
    main()
