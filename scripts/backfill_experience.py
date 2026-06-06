"""One-off backfill: populate staging.jobs.experience_min/max from description
using the same extractor the normalizer now applies. Idempotent.
Run: python scripts/backfill_experience.py   (.venv active, target in DATABASE_URL)
"""

import os

from apps.normalizer.parsers import experience_from_description
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"], future=True)

updated = 0
with engine.begin() as conn:
    rows = conn.execute(
        text("SELECT id, description FROM staging.jobs WHERE description IS NOT NULL")
    ).all()
    for job_id, desc in rows:
        lo, hi = experience_from_description(desc)
        if lo is None:
            continue
        conn.execute(
            text(
                "UPDATE staging.jobs SET experience_min = :lo, experience_max = :hi WHERE id = :id"
            ),
            {"lo": lo, "hi": hi, "id": job_id},
        )
        updated += 1

with engine.connect() as conn:
    n_with = conn.execute(
        text("SELECT count(*) FROM staging.jobs WHERE experience_min IS NOT NULL")
    ).scalar()
    n_tot = conn.execute(text("SELECT count(*) FROM staging.jobs")).scalar()
engine.dispose()
print("backfilled", updated, "rows; experience populated on", n_with, "of", n_tot)
