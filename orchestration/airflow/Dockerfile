FROM apache/airflow:2.9.3-python3.11

USER root
# JobAtlas app code runs in its OWN venv so SQLAlchemy 2.0 + scrapy never touch
# Airflow's env (Airflow 2.9 pins SQLAlchemy <2.0; upgrading it breaks Airflow's
# ORM). DAG tasks call /opt/jobatlas-venv/bin/python; live code via PYTHONPATH.
COPY --chown=airflow:0 pyproject.toml README.md /tmp/build/
COPY --chown=airflow:0 src /tmp/build/src
# hadolint ignore=DL3013
RUN python3 -m venv /opt/jobatlas-venv \
    && /opt/jobatlas-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/jobatlas-venv/bin/pip install --no-cache-dir /tmp/build \
    && rm -rf /tmp/build \
    && chown -R airflow:0 /opt/jobatlas-venv
USER airflow
