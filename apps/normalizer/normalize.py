"""Normalizer (Day 5): raw.jobs_raw + Mongo minhash -> staging.jobs (UPSERT).

Run from repo root, .venv active, docker stack up:
    python -m apps.normalizer.normalize
    python -m apps.normalizer.normalize --source adzuna --limit 10
"""

from __future__ import annotations

import argparse
import logging
import os

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker

from apps.normalizer.parsers import PARSERS
from jobatlas.db.models import Job, JobRaw
from jobatlas.urls import canonicalize_url

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("normalizer")

# Columns refreshed on conflict (all except id/source/source_url/created_at).
_UPDATE_COLS = (
    "raw_id",
    "source_job_id",
    "title",
    "company",
    "city",
    "state",
    "country",
    "salary_min",
    "salary_max",
    "currency",
    "posted_date",
    "description",
    "skills",
    "minhash_signature",
    "content_hash",
    "scraped_at",
)


def _minhash_map(mongo_db, object_ids: list[str | None]) -> dict[str, list[int]]:
    oids = [ObjectId(o) for o in object_ids if o]
    if not oids:
        return {}
    out: dict[str, list[int]] = {}
    for coll in ("raw_api_responses", "raw_html"):
        for d in mongo_db[coll].find({"_id": {"$in": oids}}, {"minhash_signature": 1}):
            sig = d.get("minhash_signature")
            if sig:
                out[str(d["_id"])] = [int(x) for x in sig]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", action="append", help="limit to source(s); repeatable")
    ap.add_argument("--limit", type=int, help="max raw rows to read")
    args = ap.parse_args()

    load_dotenv()
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    session_factory = sessionmaker(bind=engine)
    mongo = MongoClient(os.environ["MONGO_URI"])
    mongo_db = mongo[os.environ.get("MONGO_DB", "jobatlas")]

    with session_factory() as session:
        stmt = select(JobRaw).order_by(JobRaw.id)
        if args.source:
            stmt = stmt.where(JobRaw.source.in_(args.source))
        if args.limit:
            stmt = stmt.limit(args.limit)
        raws = session.scalars(stmt).all()
        log.info("read %d raw rows", len(raws))

        sig_map = _minhash_map(mongo_db, [r.mongo_object_id for r in raws])

        # Dedupe within the batch by (source, canonical source_url); last (highest id)
        # wins. Prevents "ON CONFLICT cannot affect row twice" when jobs_raw has dups,
        # and collapses re-fetched param-variants (Adzuna se=/v=) onto one row.
        dedup: dict[tuple[str, str], dict] = {}
        skipped = 0
        for r in raws:
            parser = PARSERS.get(r.source)
            if parser is None:
                skipped += 1
                continue  # wellfound/naukri: no parser yet (Day-5 scope)
            fields = parser(r.payload or {})
            if not fields.get("title") or not r.source_url:
                skipped += 1
                log.warning("skip raw id=%s (%s): missing title/url", r.id, r.source)
                continue
            canon_url = canonicalize_url(r.source_url)
            dedup[(r.source, canon_url)] = {
                "raw_id": r.id,
                "source": r.source,
                "source_job_id": r.source_job_id,
                "source_url": canon_url,
                "content_hash": r.content_hash,
                "scraped_at": r.scraped_at,
                "minhash_signature": sig_map.get(r.mongo_object_id or ""),
                **fields,
            }

        rows = list(dedup.values())
        if not rows:
            log.info("nothing to upsert (skipped=%d)", skipped)
            return

        # Postgres caps one statement at 65535 bound params; at ~18 cols
        # per row that is ~3600 rows, so chunk well under it for big harvests.
        chunk_size = 1000
        for start in range(0, len(rows), chunk_size):
            chunk = rows[start : start + chunk_size]
            ins = pg_insert(Job).values(chunk)
            update_set = {c: getattr(ins.excluded, c) for c in _UPDATE_COLS}
            update_set["updated_at"] = func.now()
            ins = ins.on_conflict_do_update(constraint="uq_jobs_source_url", set_=update_set)
            session.execute(ins)
        session.commit()

    engine.dispose()
    mongo.close()
    log.info("upserted %d jobs (skipped=%d)", len(rows), skipped)


if __name__ == "__main__":
    main()
