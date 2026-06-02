#!/usr/bin/env python3
"""Near-real-time CDC sink: Debezium ``cdc.jobs`` (Redpanda) -> Snowflake.

Reads row-level changes that Debezium captures from Postgres ``staging.jobs``
and applies them to the Snowflake landing table
``JOBATLAS.CDC.JOBS_STREAM`` via batched MERGE (upserts) and DELETE
(tombstones). This is the streaming sink for the JobAtlas warehouse layer.

The BigQuery sink is intentionally not wired here: it is gated on the GCP
setup (budget alerts + ADC quota project). The ``apply_batch`` seam is where a
``BigQuerySink`` slots in once GCP is configured.
"""

from __future__ import annotations

import json
import os
import signal
import sys
from datetime import UTC, date, datetime, timedelta

import snowflake.connector
from confluent_kafka import Consumer, KafkaError

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:19092")
TOPIC = os.environ.get("CDC_TOPIC", "cdc.jobs")
GROUP_ID = os.environ.get("CDC_GROUP", "jobatlas-cdc-sink")
SF_SCHEMA = "CDC"
SF_TABLE = "JOBS_STREAM"

# Columns kept in the warehouse stream table. We deliberately drop the large /
# non-analytic source columns (description, skills, minhash_signature, the
# embedding) -- this table is a change-tracking landing zone, not a mirror.
COLUMNS = [
    "ID",
    "SOURCE",
    "SOURCE_URL",
    "TITLE",
    "COMPANY",
    "CITY",
    "STATE",
    "COUNTRY",
    "SALARY_MIN",
    "SALARY_MAX",
    "CURRENCY",
    "POSTED_DATE",
    "IS_ACTIVE",
    "IS_DUPLICATE",
    "SCRAPED_AT",
    "UPDATED_AT",
    "CDC_OP",
    "CDC_TS_MS",
    "SYNCED_AT",
]

DDL_SCHEMA = f"CREATE SCHEMA IF NOT EXISTS {SF_SCHEMA}"
DDL_TABLE = f"""
CREATE TABLE IF NOT EXISTS {SF_SCHEMA}.{SF_TABLE} (
    ID NUMBER PRIMARY KEY,
    SOURCE VARCHAR, SOURCE_URL VARCHAR, TITLE VARCHAR, COMPANY VARCHAR,
    CITY VARCHAR, STATE VARCHAR, COUNTRY VARCHAR,
    SALARY_MIN FLOAT, SALARY_MAX FLOAT, CURRENCY VARCHAR,
    POSTED_DATE DATE, IS_ACTIVE BOOLEAN, IS_DUPLICATE BOOLEAN,
    SCRAPED_AT TIMESTAMP_TZ, UPDATED_AT TIMESTAMP_TZ,
    CDC_OP VARCHAR, CDC_TS_MS NUMBER, SYNCED_AT TIMESTAMP_TZ
)
"""
DDL_STG = (
    f"CREATE TRANSIENT TABLE IF NOT EXISTS {SF_SCHEMA}.{SF_TABLE}_STG LIKE {SF_SCHEMA}.{SF_TABLE}"
)
TRUNCATE_STG = f"TRUNCATE TABLE {SF_SCHEMA}.{SF_TABLE}_STG"

_update_set = ", ".join(f"{c} = src.{c}" for c in COLUMNS if c != "ID")
_insert_cols = ", ".join(COLUMNS)
_insert_vals = ", ".join(f"src.{c}" for c in COLUMNS)
MERGE_SQL = f"""
MERGE INTO {SF_SCHEMA}.{SF_TABLE} tgt
USING {SF_SCHEMA}.{SF_TABLE}_STG src ON tgt.ID = src.ID
WHEN MATCHED THEN UPDATE SET {_update_set}
WHEN NOT MATCHED THEN INSERT ({_insert_cols}) VALUES ({_insert_vals})
"""
INSERT_STG = (
    f"INSERT INTO {SF_SCHEMA}.{SF_TABLE}_STG ({_insert_cols}) "
    f"VALUES ({', '.join(['%s'] * len(COLUMNS))})"
)


def _epoch_days(v):
    """Debezium io.debezium.time.Date -> python date (days since 1970-01-01)."""
    return None if v is None else date(1970, 1, 1) + timedelta(days=int(v))


def _ts(v):
    """ISO-8601 string (ZonedTimestamp) -> tz-aware datetime."""
    if v is None:
        return None
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


def _num(v):
    return None if v is None else float(v)


def _row_tuple(after: dict, op: str, ts_ms) -> tuple:
    return (
        after["id"],
        after.get("source"),
        after.get("source_url"),
        after.get("title"),
        after.get("company"),
        after.get("city"),
        after.get("state"),
        after.get("country"),
        _num(after.get("salary_min")),
        _num(after.get("salary_max")),
        after.get("currency"),
        _epoch_days(after.get("posted_date")),
        after.get("is_active"),
        after.get("is_duplicate"),
        _ts(after.get("scraped_at")),
        _ts(after.get("updated_at")),
        op,
        ts_ms,
        datetime.now(UTC),
    )


def connect_snowflake():
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
    )
    cur = conn.cursor()
    cur.execute(DDL_SCHEMA)
    cur.execute(DDL_TABLE)
    cur.execute(DDL_STG)
    cur.close()
    return conn


def apply_batch(conn, upserts: list[tuple], deletes: list[int]) -> None:
    cur = conn.cursor()
    try:
        if upserts:
            cur.execute(TRUNCATE_STG)
            cur.executemany(INSERT_STG, upserts)
            cur.execute(MERGE_SQL)
        if deletes:
            placeholders = ", ".join(["%s"] * len(deletes))
            cur.execute(
                f"DELETE FROM {SF_SCHEMA}.{SF_TABLE} WHERE ID IN ({placeholders})",
                deletes,
            )
        conn.commit()
    finally:
        cur.close()


def main() -> int:
    sf = connect_snowflake()
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([TOPIC])

    running = {"on": True}
    signal.signal(signal.SIGINT, lambda *_: running.__setitem__("on", False))
    signal.signal(signal.SIGTERM, lambda *_: running.__setitem__("on", False))

    total = 0
    print(
        f"[cdc-sink] consuming {TOPIC} from {KAFKA_BOOTSTRAP} -> "
        f"{os.environ['SNOWFLAKE_DATABASE']}.{SF_SCHEMA}.{SF_TABLE}",
        flush=True,
    )
    try:
        while running["on"]:
            msgs = consumer.consume(num_messages=500, timeout=2.0)
            if not msgs:
                continue
            upserts: list[tuple] = []
            deletes: list[int] = []
            for m in msgs:
                if m.error():
                    if m.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    print(f"[cdc-sink] kafka error: {m.error()}", file=sys.stderr, flush=True)
                    continue
                raw = m.value()
                if raw is None:  # Debezium tombstone after a delete
                    continue
                evt = json.loads(raw)
                op = evt.get("op")
                ts_ms = evt.get("ts_ms")
                if op == "d":
                    before = evt.get("before") or {}
                    if before.get("id") is not None:
                        deletes.append(before["id"])
                elif op in ("c", "u", "r"):
                    after = evt.get("after")
                    if after:
                        upserts.append(_row_tuple(after, op, ts_ms))
            if upserts or deletes:
                apply_batch(sf, upserts, deletes)
                consumer.commit(asynchronous=False)
                total += len(upserts) + len(deletes)
                print(
                    f"[cdc-sink] applied +{len(upserts)} upsert / "
                    f"-{len(deletes)} delete (running total {total})",
                    flush=True,
                )
    finally:
        print("[cdc-sink] shutting down", flush=True)
        consumer.close()
        sf.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
