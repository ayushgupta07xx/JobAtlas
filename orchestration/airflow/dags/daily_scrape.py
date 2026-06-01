"""daily_scrape: API scrapers (parallel) -> normalize -> report.

App tasks run in the isolated JobAtlas venv (/opt/jobatlas-venv) so SQLAlchemy 2.0
+ scrapy stay out of Airflow's own env (Airflow 2.9 pins SQLAlchemy <2.0). API
spiders only; Playwright spiders stay host/best-effort (ADR-0004). Source list is
the Airflow Variable `jobatlas_sources`.
"""

from __future__ import annotations

import pendulum
from airflow.models import Variable
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

REPO = "/opt/jobatlas"
PY = "/opt/jobatlas-venv/bin/python"
SOURCES = Variable.get("jobatlas_sources", default_var=["adzuna", "jobicy"], deserialize_json=True)

with DAG(
    dag_id="daily_scrape",
    description="Scrape API sources in parallel, normalize to staging.jobs, report counts.",
    schedule="0 2 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Kolkata"),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": pendulum.duration(minutes=2)},
    tags=["jobatlas", "ingest"],
) as dag:
    normalize = BashOperator(
        task_id="normalize",
        bash_command=f"cd {REPO} && {PY} -m apps.normalizer.normalize",
    )
    report = BashOperator(
        task_id="report",
        bash_command=f"cd {REPO} && {PY} -m jobatlas.report",
    )
    for src in SOURCES:
        scrape = BashOperator(
            task_id=f"scrape_{src}",
            bash_command=f"cd {REPO}/scrapers && {PY} -m scrapy crawl {src} -L INFO",
        )
        scrape >> normalize
    normalize >> report
