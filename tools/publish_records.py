#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS_PATH = ROOT / "generated" / "publish-records.jsonl"


def log_publish_record(record):
    RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        **record,
    }
    with RECORDS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


def recent_publish_records(limit=10):
    if not RECORDS_PATH.exists():
        return []
    lines = RECORDS_PATH.read_text(encoding="utf-8").splitlines()
    records = []
    for line in reversed(lines[-limit:]):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records
