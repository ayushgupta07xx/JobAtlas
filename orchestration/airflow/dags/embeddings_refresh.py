"""embeddings_refresh: BGE-small (384-dim) embeddings for jobs lacking one.

Runs jobatlas.embeddings in the JobAtlas venv (sentence-transformers + CPU torch,
model baked into the image). Batch size from the Airflow Variable `embed_batch_size`.
"""

from __future__ import annotations

import pendulum
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

PY = "/opt/jobatlas-venv/bin/python"

with DAG(
    dag_id="embeddings_refresh",
    description="Generate BGE-small embeddings for new staging.jobs (pgvector).",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Kolkata"),
    catchup=False,
    tags=["jobatlas", "ml"],
) as dag:
    BashOperator(
        task_id="generate_embeddings",
        bash_command="cd /opt/jobatlas && "
        + PY
        + " -m jobatlas.embeddings --batch-size {{ var.value.embed_batch_size }}",
    )
