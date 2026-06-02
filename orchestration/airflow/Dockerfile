FROM apache/airflow:2.9.3-python3.11

USER root
# JobAtlas app code runs in its OWN venv so SQLAlchemy 2.0 + scrapy never touch
# Airflow's env (Airflow 2.9 pins SQLAlchemy <2.0; upgrading it breaks its ORM).
# CPU-only torch keeps the image lean; BGE-small is baked so runs need no download.
COPY --chown=airflow:0 pyproject.toml README.md /tmp/build/
COPY --chown=airflow:0 src /tmp/build/src
# CPU torch in its own cacheable layer (192 MB; avoids re-download on a retry).
# hadolint ignore=DL3013
RUN python3 -m venv /opt/jobatlas-venv \
    && /opt/jobatlas-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/jobatlas-venv/bin/pip install --no-cache-dir --retries 10 torch --index-url https://download.pytorch.org/whl/cpu
# App package + [embeddings] extra (scrapy, sqlalchemy, sentence-transformers, ...).
# hadolint ignore=DL3013,DL3059
RUN /opt/jobatlas-venv/bin/pip install --no-cache-dir --retries 10 "/tmp/build[embeddings]" \
    && rm -rf /tmp/build \
    && chown -R airflow:0 /opt/jobatlas-venv
USER airflow
RUN /opt/jobatlas-venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
# GX runs in its OWN venv: GX 1.x needs SQLAlchemy 2.x, Airflow pins <2.0, and the
# app venv is separate too. Appended last so the torch/BGE layers above stay cached.
USER root
# hadolint ignore=DL3013
RUN python3 -m venv /opt/jobatlas-gx-venv \
    && /opt/jobatlas-gx-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/jobatlas-gx-venv/bin/pip install --no-cache-dir --retries 10 "great-expectations[postgresql]>=1.17" python-dotenv \
    && chown -R airflow:0 /opt/jobatlas-gx-venv
USER airflow
