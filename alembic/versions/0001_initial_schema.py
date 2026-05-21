"""initial schema: raw, staging, marts + pgvector embeddings

Revision ID: 0001
Revises:
Create Date: 2026-05-21
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    op.execute("CREATE SCHEMA IF NOT EXISTS staging;")
    op.execute("CREATE SCHEMA IF NOT EXISTS marts;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.execute(
        """
        CREATE TABLE raw.jobs_raw (
            id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            source          VARCHAR(50) NOT NULL,
            source_job_id   TEXT,
            source_url      TEXT,
            mongo_object_id VARCHAR(24),
            payload         JSONB NOT NULL,
            content_hash    VARCHAR(64),
            scraped_at      TIMESTAMPTZ,
            ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX ix_jobs_raw_source ON raw.jobs_raw (source);")
    op.execute("CREATE INDEX ix_jobs_raw_content_hash ON raw.jobs_raw (content_hash);")

    op.execute(
        """
        CREATE TABLE staging.jobs (
            id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            raw_id            BIGINT REFERENCES raw.jobs_raw (id) ON DELETE SET NULL,
            source            VARCHAR(50) NOT NULL,
            source_job_id     TEXT,
            source_url        TEXT NOT NULL,
            title             TEXT NOT NULL,
            company           TEXT,
            city              TEXT,
            state             TEXT,
            country           VARCHAR(2) NOT NULL DEFAULT 'IN',
            salary_min        NUMERIC(12,2),
            salary_max        NUMERIC(12,2),
            currency          VARCHAR(3) NOT NULL DEFAULT 'INR',
            posted_date       DATE,
            description       TEXT,
            skills            TEXT[],
            minhash_signature BIGINT[],
            content_hash      VARCHAR(64),
            is_active         BOOLEAN NOT NULL DEFAULT TRUE,
            is_duplicate      BOOLEAN NOT NULL DEFAULT FALSE,
            dedup_group_id    BIGINT,
            scraped_at        TIMESTAMPTZ,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_jobs_source_url UNIQUE (source, source_url)
        );
        """
    )
    op.execute("CREATE INDEX ix_jobs_posted_date ON staging.jobs (posted_date);")
    op.execute("CREATE INDEX ix_jobs_content_hash ON staging.jobs (content_hash);")
    op.execute("CREATE INDEX ix_jobs_dedup_group_id ON staging.jobs (dedup_group_id);")

    op.execute(
        """
        CREATE TABLE staging.jobs_embeddings (
            job_id     BIGINT PRIMARY KEY REFERENCES staging.jobs (id) ON DELETE CASCADE,
            embedding  vector(384) NOT NULL,
            model_name VARCHAR(64) NOT NULL DEFAULT 'BAAI/bge-small-en-v1.5',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE INDEX ix_jobs_embeddings_embedding_hnsw
        ON staging.jobs_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS staging.jobs_embeddings;")
    op.execute("DROP TABLE IF EXISTS staging.jobs;")
    op.execute("DROP TABLE IF EXISTS raw.jobs_raw;")
    op.execute("DROP SCHEMA IF EXISTS marts;")
    op.execute("DROP SCHEMA IF EXISTS staging;")
    op.execute("DROP SCHEMA IF EXISTS raw;")
