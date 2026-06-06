"""One-off backfill: populate staging.jobs.experience_min/max from description
using the same extractor the normalizer applies. Idempotent; a single bulk
UPDATE so it stays fast over a remote (Neon) connection. Targets DATABASE_URL.
Run: DATABASE_URL="$NEON_URL" PYTHONPATH=. python scripts/backfill_experience.py
"""

import os

import psycopg2
from apps.normalizer.parsers import experience_from_description
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()
conn = psycopg2.connect(os.environ["DATABASE_URL"])
try:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, description FROM staging.jobs "
        "WHERE description IS NOT NULL "
        "AND (description ILIKE '%year%' OR description ILIKE '%yr%')"
    )
    updates = []
    for job_id, desc in cur.fetchall():
        lo, hi = experience_from_description(desc)
        if lo is not None:
            updates.append((job_id, lo, hi))

    if updates:
        execute_values(
            cur,
            "UPDATE staging.jobs AS j SET experience_min = v.lo, "
            "experience_max = v.hi FROM (VALUES %s) AS v (id, lo, hi) "
            "WHERE j.id = v.id",
            updates,
            template="(%s, %s, %s)",
            page_size=1000,
        )
    conn.commit()

    cur.execute("SELECT count(*) FROM staging.jobs WHERE experience_min IS NOT NULL")
    n_with = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM staging.jobs")
    n_tot = cur.fetchone()[0]
finally:
    conn.close()
print("backfilled", len(updates), "rows; experience populated on", n_with, "of", n_tot)
