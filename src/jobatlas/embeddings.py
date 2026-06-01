"""Generate BGE-small (384-dim) embeddings for staging.jobs lacking one.

Runs in the JobAtlas venv. Writes staging.jobs_embeddings (HNSW cosine index);
vectors are L2-normalized so cosine == inner product. Idempotent: only jobs that
don't already have an embedding are encoded.
"""

from __future__ import annotations

import argparse
import logging
import os

from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker

from jobatlas.db.models import Job, JobEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"
log = logging.getLogger("jobatlas.embeddings")


def run(batch_size: int) -> None:
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        stmt = (
            select(Job.id, Job.title, Job.description)
            .outerjoin(JobEmbedding, JobEmbedding.job_id == Job.id)
            .where(Job.is_active.is_(True), JobEmbedding.job_id.is_(None))
            .order_by(Job.id)
        )
        rows = session.execute(stmt).all()
        log.info("embedding %d new jobs (batch=%d)", len(rows), batch_size)
        if not rows:
            return

        ids = [r.id for r in rows]
        texts = [f"{r.title}. {r.description or ''}".strip() for r in rows]

        model = SentenceTransformer(MODEL_NAME)
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        payload = [
            {"job_id": jid, "embedding": vec.tolist(), "model_name": MODEL_NAME}
            for jid, vec in zip(ids, vectors, strict=True)
        ]
        ins = (
            pg_insert(JobEmbedding)
            .values(payload)
            .on_conflict_do_nothing(index_elements=["job_id"])
        )
        session.execute(ins)
        session.commit()
    engine.dispose()
    log.info("wrote %d embeddings", len(rows))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=32)
    run(ap.parse_args().batch_size)


if __name__ == "__main__":
    main()
