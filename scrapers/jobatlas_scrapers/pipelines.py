"""Item pipeline: compute content-hash + MinHash, land raw payloads.

Flow per item: hash + MinHash signature -> insert into the Mongo raw zone
(raw_api_responses for API sources, raw_html for scraped HTML) -> insert the
CDC-able landing copy into raw.jobs_raw with a back-reference to the Mongo
ObjectId. Full normalization into staging.jobs is the Day-5 normalizer's job;
the MinHash signature rides in the Mongo doc for it to carry forward.
"""

import hashlib
import json
import os
import re
from datetime import UTC, datetime

from datasketch import MinHash
from dotenv import find_dotenv, load_dotenv
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jobatlas.db.models import JobRaw

MINHASH_NUM_PERM = 128


def _shingles(text: str, k: int = 3) -> list[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    if len(words) < k:
        return [" ".join(words)] if words else []
    return [" ".join(words[i : i + k]) for i in range(len(words) - k + 1)]


def _compute_minhash(text: str) -> list[int]:
    m = MinHash(num_perm=MINHASH_NUM_PERM)
    for sh in _shingles(text):
        m.update(sh.encode("utf-8"))
    return [int(x) for x in m.hashvalues]


def _content_hash(payload) -> str:
    data = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class RawLandingPipeline:
    def open_spider(self, spider):
        load_dotenv(find_dotenv())  # walks up from scrapers/ to repo-root .env
        self.mongo = MongoClient(os.environ["MONGO_URI"])
        self.mongo_db = self.mongo[os.environ.get("MONGO_DB", "jobatlas")]
        self.engine = create_engine(os.environ["DATABASE_URL"], future=True)
        self.Session = sessionmaker(bind=self.engine)
        self.count = 0

    def close_spider(self, spider):
        self.engine.dispose()
        self.mongo.close()
        spider.logger.info("RawLandingPipeline: landed %d items", self.count)

    def process_item(self, item, spider):
        now = datetime.now(UTC)
        raw = item.get("raw_payload")
        payload_doc = {"html": raw} if isinstance(raw, str) else (raw or {})

        chash = _content_hash(raw)
        text = " ".join(
            str(item.get(f) or "") for f in ("title", "company", "location", "description")
        )
        sig = _compute_minhash(text)

        # 1) Mongo raw zone — collection chosen by raw_kind
        coll = "raw_api_responses" if item.get("raw_kind") == "api" else "raw_html"
        mongo_id = (
            self.mongo_db[coll]
            .insert_one(
                {
                    "source": item.get("source"),
                    "source_job_id": item.get("source_job_id"),
                    "source_url": item.get("source_url"),
                    "raw_kind": item.get("raw_kind"),
                    "content_hash": chash,
                    "fetched_at": now,
                    "minhash_signature": sig,
                    "payload": payload_doc,
                }
            )
            .inserted_id
        )

        # 2) Postgres CDC-able landing copy
        with self.Session() as session:
            session.add(
                JobRaw(
                    source=item["source"],
                    source_job_id=item.get("source_job_id"),
                    source_url=item.get("source_url"),
                    mongo_object_id=str(mongo_id),
                    payload=payload_doc,
                    content_hash=chash,
                    scraped_at=now,
                )
            )
            session.commit()

        item["content_hash"] = chash
        item["minhash_signature"] = sig
        item["fetched_at"] = now
        self.count += 1
        return item
