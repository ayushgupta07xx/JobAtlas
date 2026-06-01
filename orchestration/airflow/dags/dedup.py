"""dedup: MinHash LSH near-duplicate detection across staging.jobs.

Runs jobatlas.dedup in the isolated JobAtlas venv. Jaccard threshold from the
Airflow Variable `dedup_jaccard` (default 0.85), templated into the command.
"""

from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

PY = "/opt/jobatlas-venv/bin/python"

with DAG(
    dag_id="dedup",
    description="MinHash LSH dedup across staging.jobs; sets is_duplicate + dedup_group_id.",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Kolkata"),
    catchup=False,
    tags=["jobatlas", "quality"],
) as dag:
    BashOperator(
        task_id="minhash_dedup",
        bash_command="cd /opt/jobatlas && "
        + PY
        + " -m jobatlas.dedup --threshold {{ var.value.dedup_jaccard }}",
    )
