"""Regenerate the regression input extract from the warehouse.

The CSV at analysis/data/salary_model_input.csv is a derived extract and is
gitignored; this script is its source of record. It reads the disclosed-salary
mart (marts.mart_salary_model_input) and writes the 669-row CSV the salary
notebooks consume.

Usage (from repo root, venv active):
    set -a; source .env; set +a
    PYTHONPATH=. python analysis/export_data.py
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

from sqlalchemy import create_engine, text

OUT = Path(__file__).resolve().parent / "data" / "salary_model_input.csv"


def main() -> None:
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        schema = conn.execute(
            text(
                "select table_schema from information_schema.tables "
                "where table_name = 'mart_salary_model_input' limit 1"
            )
        ).scalar()
        rows = (
            conn.execute(text(f'select * from "{schema}".mart_salary_model_input')).mappings().all()
        )

    if not rows:
        raise SystemExit("mart_salary_model_input returned no rows")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with OUT.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dict(r) for r in rows)

    print(f"wrote {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
