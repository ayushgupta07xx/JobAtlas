"""data_quality: Great Expectations gate over staging.jobs + marts.
Runs warehouse/great_expectations/build_suites.py in the isolated GX venv
(ephemeral context, no disk writes). A non-zero exit fails the task and the
DAG on any quality regression: row counts, nulls, ranges, URL regex.
GX venv is baked into the image; the script is bind-mounted read-only.
"""

from __future__ import annotations

import pendulum
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

GX_PY = "/opt/jobatlas-gx-venv/bin/python"
with DAG(
    dag_id="data_quality",
    description="Great Expectations quality gate over staging.jobs and marts.",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Kolkata"),
    catchup=False,
    tags=["jobatlas", "data-quality"],
) as dag:
    BashOperator(
        task_id="run_gx_checkpoint",
        bash_command="cd /opt/jobatlas && "
        + GX_PY
        + " warehouse/great_expectations/build_suites.py --ephemeral",
    )
