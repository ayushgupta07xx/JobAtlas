"""Benchmark the pgvector match query latency (p50/p95/p99).

Backs the "<100 ms p95" semantic-match latency claim. Run from the repo root
against the LOCAL Docker Postgres -- the claim is about query latency, not
network round-trip to a remote warehouse:

    python scripts/bench_match_latency.py
"""

from __future__ import annotations

import os
import random
import statistics
import time

from dotenv import load_dotenv
from sqlalchemy import Engine, bindparam, create_engine, text
from sqlalchemy.engine import make_url

from jobatlas.sources import MATCH_EXCLUDED_SOURCES

SQL = text(
    """
    SELECT j.id, 1 - (e.embedding <=> CAST(:qvec AS vector)) AS score
    FROM staging.jobs j
    JOIN staging.jobs_embeddings e ON e.job_id = j.id
    WHERE j.is_active = true AND j.is_duplicate = false
      AND j.source NOT IN :excluded
    ORDER BY e.embedding <=> CAST(:qvec AS vector)
    LIMIT :pool
    """
).bindparams(bindparam("excluded", expanding=True))


def rand_vec(dim: int = 384) -> str:
    v = [random.gauss(0, 1) for _ in range(dim)]
    norm = sum(x * x for x in v) ** 0.5
    return "[" + ",".join(f"{x / norm:.6f}" for x in v) + "]"


def bench(engine: Engine, pool: int, runs: int = 200) -> None:
    excluded = list(MATCH_EXCLUDED_SOURCES)
    lat: list[float] = []
    with engine.connect() as conn:
        # Match the live endpoint: lift the HNSW candidate ceiling so the query
        # retrieves the full pool instead of the default ~40 rows.
        conn.execute(text("SET hnsw.ef_search = 400"))
        for _ in range(10):  # warm: connection, plan, index pages into cache
            conn.execute(SQL, {"qvec": rand_vec(), "pool": pool, "excluded": excluded}).all()
        for _ in range(runs):
            params = {"qvec": rand_vec(), "pool": pool, "excluded": excluded}
            t0 = time.perf_counter()
            conn.execute(SQL, params).all()
            lat.append((time.perf_counter() - t0) * 1000)
    lat.sort()

    def pct(q: float) -> float:
        return lat[min(int(q * len(lat)), len(lat) - 1)]

    print(
        f"pool={pool:<3} runs={runs}  "
        f"p50={statistics.median(lat):6.2f}ms  "
        f"p95={pct(0.95):6.2f}ms  "
        f"p99={pct(0.99):6.2f}ms  "
        f"max={lat[-1]:6.2f}ms"
    )


def main() -> None:
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL not set (load_dotenv reads the repo .env).")
    engine = create_engine(url)
    print(f"DB host: {make_url(url).host}  (use local Docker Postgres for this claim)")
    # Both arms share one 200-candidate pool (MATCH_POOL); control orders it by
    # cosine, test reranks it in Python. This times the shared pgvector fetch.
    bench(engine, pool=200)


if __name__ == "__main__":
    main()
