from __future__ import annotations

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jobatlas.db.base import Base

EMBED_DIM = 384


class JobRaw(Base):
    """Postgres landing of raw scraped payloads (Mongo is the bulk raw zone).

    Lives here so Debezium can CDC it (Day 11) and to keep lineage for staging.
    """

    __tablename__ = "jobs_raw"
    __table_args__ = (
        Index("ix_jobs_raw_source", "source"),
        Index("ix_jobs_raw_content_hash", "content_hash"),
        {"schema": "raw"},
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_job_id: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    mongo_object_id: Mapped[str | None] = mapped_column(String(24))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Job(Base):
    """Normalized job (normalizer writes here, Day 5). dbt reads from this."""

    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "source_url", name="uq_jobs_source_url"),
        Index("ix_jobs_posted_date", "posted_date"),
        Index("ix_jobs_content_hash", "content_hash"),
        Index("ix_jobs_dedup_group_id", "dedup_group_id"),
        {"schema": "staging"},
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    raw_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("raw.jobs_raw.id", ondelete="SET NULL")
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_job_id: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str] = mapped_column(String(2), nullable=False, server_default=text("'IN'"))
    salary_min: Mapped[float | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'INR'"))
    posted_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    minhash_signature: Mapped[list[int] | None] = mapped_column(ARRAY(BigInteger))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    is_duplicate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    dedup_group_id: Mapped[int | None] = mapped_column(BigInteger)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class JobEmbedding(Base):
    """BGE-small (384-dim) embedding per job; HNSW cosine index for /match."""

    __tablename__ = "jobs_embeddings"
    __table_args__ = (
        Index(
            "ix_jobs_embeddings_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        {"schema": "staging"},
    )

    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("staging.jobs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM), nullable=False)
    model_name: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'BAAI/bge-small-en-v1.5'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
