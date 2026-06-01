"""Print staging.jobs counts + duplicate count. Runs in the JobAtlas venv."""

from __future__ import annotations

import logging
import os

from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with engine.connect() as conn:
        counts = conn.execute(
            text("select source, count(*) from staging.jobs group by source order by 1")
        ).all()
        dups = conn.execute(text("select count(*) from staging.jobs where is_duplicate")).scalar()
    engine.dispose()
    logging.getLogger("jobatlas.report").info(
        "staging.jobs by source=%s | duplicates=%s", counts, dups
    )


if __name__ == "__main__":
    main()
