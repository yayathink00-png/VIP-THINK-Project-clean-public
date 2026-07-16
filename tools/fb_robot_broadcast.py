#!/usr/bin/env python3
"""
fb_robot_broadcast.py

Send the local FB new/scheduled ads broadcast to a chat robot webhook.

Supported webhooks:
- WeCom / 企业微信 group robot
- Feishu/Lark group robot
- DingTalk robot

It reads fb_new_creative_monitor.sqlite3 created by fb_new_creative_broadcast.py.
It does not call Meta API and does not change ads.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DB = SCRIPT_DIR / "fb_new_creative_monitor.sqlite3"
DEFAULT_ENV = SCRIPT_DIR / ".env"
DEFAULT_IMAGE_LIBRARY_ROOT = Path("/Volumes/海外投放素材库/图片素材/思维")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}

ACCOUNT_NAMES = {
    "act_468253789344241": "飞书7户-港澳-KOL-post",
    "act_442457935507062": "飞书9户-优质-表单",
    "act_366864216464093": "飞书8户-混投-表单",
    "act_1816783745480753": "飞书3户-港澳-WA",
    "act_627543006449377": "飞书18户-台湾-KOL",
    "act_1158469106256042": "飞书27户-台湾-H5",
    "act_2107766700052928": "飞书23户-新加坡-表单",
    "act_1416198419836342": "飞书31户-新加坡-KOL",
}

ACCOUNT_ALIASES = {
    "7": "act_468253789344241",
    "8": "act_366864216464093",
    "9": "act_442457935507062",
    "27": "act_1158469106256042",
    "18": "act_627543006449377",
    "23": "act_2107766700052928",
    "3": "act_1816783745480753",
    "31": "act_1416198419836342",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send FB new/scheduled ads broadcast to robot webhook.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite DB path. Default: fb_new_creative_monitor.sqlite3")
    parser.add_argument("--days", type=int, default=14, help="Window ending today. Default: 14.")
    parser.add_argument("--since", help="Start date YYYY-MM-DD. Overrides --days.")
    parser.add_argument("--until", help="End date YYYY-MM-DD. Default: today.")
    parser.add_argument(
        "--future-scheduled-days",
        type=int,
        default=14,
        help="Also include adsets scheduled in the next N days. Default: 14.",
    )
    parser.add_argument("--webhook", default="", help="Robot webhook URL. Defaults to FB_BROADCAST_WEBHOOK_URL.")
    parser.add_argument(
        "--robot-type",
        choices=["auto", "wecom", "feishu", "dingtalk"],
        default="auto",
        help="Webhook type. Default: auto.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print message only; do not send.")
    parser.add_argument("--max-lines", type=int, default=16, help="Max account/detail lines in robot message.")
    parser.add_argument("--sla-days", type=int, default=7, help="Newly made creatives should launch/schedule within N days. Default: 7.")
    parser.add_argument(
        "--material-lookback-days",
        type=int,
        default=7,
        help="Material production/final-date lookback window ending at --until. Default: 7.",
    )
    parser.add_argument(
        "--account-aliases",
        default="",
        help="Comma-separated account aliases/IDs to include, e.g. 7,8,9,27,18,23. Defaults to FB_BROADCAST_ACCOUNT_ALIASES or all.",
    )
    parser.add_argument(
        "--include-month-only",
        action="store_true",
        help="Also count ad-name dates like 202606. Default only counts full dates like 20260623.",
    )
    parser.add_argument(
        "--image-library-root",
        default=os.getenv("FB_IMAGE_LIBRARY_ROOT", str(DEFAULT_IMAGE_LIBRARY_ROOT)),
        help="Image material library root. Default: /Volumes/海外投放素材库/图片素材/思维",
    )
    parser.add_argument(
        "--image-library-start-month",
        default=os.getenv("FB_IMAGE_LIBRARY_START_MONTH", "2026-07"),
        help="Only scan image-library month folders from this month. Default: 2026-07.",
    )
    parser.add_argument("--disable-image-library", action="store_true", help="Disable image-library final/pending checks.")
    return parser.parse_args()


def load_env(path: Path = DEFAULT_ENV) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def resolve_window(args: argparse.Namespace) -> tuple[date, date, date]:
    until = parse_day(args.until) if args.until else date.today()
    since = parse_day(args.since) if args.since else until - timedelta(days=max(args.days, 1) - 1)
    future_until = until + timedelta(days=max(args.future_scheduled_days, 0))
    return since, until, future_until


def parse_day(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        sys.exit(f"[ERR] Invalid date: {value}. Use YYYY-MM-DD.")


def parse_meta_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip().replace("+0000", "+00:00").replace("-0000", "+00:00")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def in_report_window(row: dict[str, Any], since: date, until: date, future_until: date, include_month_only: bool) -> bool:
    report_date = row.get("report_date") or row.get("material_date")
    report_precision = row.get("report_date_precision") or row.get("material_date_precision")
    if report_date and report_precision == "full":
        return since <= report_date <= until
    if report_date and report_precision == "month":
        if not include_month_only:
            return False
        month_start = report_date.replace(day=1)
        if report_date.month == 12:
            month_end = report_date.replace(year=report_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = report_date.replace(month=report_date.month + 1, day=1) - timedelta(days=1)
        if month_start <= until and month_end >= since:
            return True
    return False


def is_launched_or_scheduled_in_window(row: dict[str, Any], since: date, until: date, future_until: date) -> bool:
    created = row.get("created_date")
    if created and since <= created <= until:
        return True
    adset_start = row.get("adset_start_date")
    if adset_start and since <= adset_start <= future_until:
        return True
    return False


def parse_account_filter(raw: str) -> list[str]:
    accounts: list[str] = []
    for item in re.split(r"[,，;；\s]+", raw.strip()):
        if not item:
            continue
        account_id = ACCOUNT_ALIASES.get(item, item)
        if account_id.isdigit():
            account_id = "act_" + account_id
        if account_id and account_id not in accounts:
            accounts.append(account_id)
    return accounts


def load_rows(
    db_path: Path,
    since: date,
    until: date,
    future_until: date,
    include_month_only: bool,
    sla_days: int,
    selected_accounts: list[str],
    image_library_root: Path | None = None,
    image_library_start_month: str = "2026-07",
    material_lookback_days: int = 7,
) -> list[dict[str, Any]]:
    if not db_path.exists():
        sys.exit(f"[ERR] DB not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        """
        SELECT ad_id, account_id, creative_key, ad_name, campaign_name, adset_name,
               created_time, updated_time, adset_start_time, campaign_start_time,
               schedule_reason, effective_status
        FROM ads_seen
        ORDER BY account_id, created_time, adset_start_time, ad_id
        """
    )]
    conn.close()
    selected = set(selected_accounts)
    if selected:
        rows = [r for r in rows if r.get("account_id") in selected]
    image_library = load_image_library(image_library_root, image_library_start_month) if image_library_root else {}
    enriched = [enrich_row(r, sla_days, image_library) for r in rows]
    material_since = until - timedelta(days=max(material_lookback_days, 1) - 1)
    rows = [
        r
        for r in enriched
        if in_report_window(r, material_since, until, future_until, include_month_only)
    ]
    materials = group_rows_by_material(rows, sla_days, image_library, since, until)
    materials = [
        r
        for r in materials
        if r.get("first_action_date")
        and since <= r["first_action_date"] <= until
        and int(r.get("material_ad_count") or 0) > 0
    ]
    materials.sort(
        key=lambda r: (
            r.get("material_date") or date.min,
            r.get("first_action_date") or date.min,
            r.get("account_name") or "",
        ),
        reverse=True,
    )
    return materials


def enrich_row(row: dict[str, Any], sla_days: int, image_library: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    text = " ".join(str(row.get(k) or "") for k in ("ad_name", "campaign_name", "adset_name"))
    row["account_name"] = ACCOUNT_NAMES.get(row.get("account_id", ""), row.get("account_id", ""))
    row["region"] = infer_region(text + " " + row["account_name"])
    row["material_type"] = infer_material_type(text)
    material_date, precision, raw = extract_material_date(row.get("ad_name") or "")
    row["material_date"] = material_date
    row["material_date_precision"] = precision
    row["material_date_raw"] = raw
    row["report_date"] = material_date
    row["report_date_precision"] = precision
    created = parse_meta_datetime(row.get("created_time"))
    adset_start = parse_meta_datetime(row.get("adset_start_time"))
    row["created_date"] = created.date() if created else None
    row["adset_start_date"] = adset_start.date() if adset_start else None
    apply_image_library_metadata(row, image_library or {})
    base_date = comparison_date(row)
    row["created_delta_days"] = delta_days(base_date, row["created_date"])
    row["adset_delta_days"] = delta_days(base_date, row["adset_start_date"])
    row["date_check"] = classify_date_check(row, sla_days)
    row["sla_status"] = classify_sla_status(row, sla_days)
    row["days_to_first_action"] = days_to_first_action(row)
    return row


def group_rows_by_material(
    rows: list[dict[str, Any]],
    sla_days: int,
    image_library: dict[str, dict[str, Any]] | None = None,
    action_since: date | None = None,
    action_until: date | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = material_group_key(row)
        grouped.setdefault(key, []).append(row)

    materials: list[dict[str, Any]] = []
    for material_rows in grouped.values():
        material_rows.sort(key=material_sort_key)
        first = dict(material_rows[0])
        apply_image_library_metadata(first, image_library or {})
        material_date = comparison_date(first)
        report_rows = [
            row
            for row in material_rows
            if action_since
            and action_until
            and is_launched_or_scheduled_in_window(row, action_since, action_until, action_until)
        ]
        action_candidates: list[tuple[date, dict[str, Any], str]] = []
        early_candidates: list[tuple[date, dict[str, Any], str]] = []
        for row in material_rows:
            for field_name, source_name in (("created_date", "广告创建"), ("adset_start_date", "广告组排期")):
                action_date = row.get(field_name)
                if not action_date:
                    continue
                item = (action_date, row, source_name)
                if material_date and action_date >= material_date:
                    action_candidates.append(item)
                else:
                    early_candidates.append(item)

        if action_candidates:
            first_action_date, first_action_row, first_action_source = min(action_candidates, key=lambda item: item[0])
        elif early_candidates:
            first_action_date, first_action_row, first_action_source = min(early_candidates, key=lambda item: item[0])
        else:
            first_action_date, first_action_row, first_action_source = None, first, ""

        first.update(first_action_row)
        first["material_group_key"] = material_group_key(first)
        counted_rows = report_rows if action_since and action_until else material_rows
        first["material_ad_count"] = len(counted_rows)
        first["material_account_count"] = len({r.get("account_id") for r in counted_rows if r.get("account_id")})
        first["material_accounts"] = "、".join(
            ACCOUNT_NAMES.get(account_id, account_id)
            for account_id in sorted({r.get("account_id") for r in counted_rows if r.get("account_id")})
        )
        first["report_account_counts"] = Counter(
            ACCOUNT_NAMES.get(r.get("account_id", ""), r.get("account_id", "")) for r in counted_rows
        )
        first["report_account_ids"] = sorted({r.get("account_id") for r in counted_rows if r.get("account_id")})
        first["report_status_counts"] = Counter(r.get("effective_status") or "未识别" for r in counted_rows)
        first["first_action_date"] = first_action_date
        first["first_action_source"] = first_action_source
        first["created_date"] = first_action_row.get("created_date")
        first["adset_start_date"] = first_action_row.get("adset_start_date")
        first["created_delta_days"] = delta_days(material_date, first.get("created_date"))
        first["adset_delta_days"] = delta_days(material_date, first.get("adset_start_date"))
        first["days_to_first_action"] = delta_days(material_date, first_action_date)
        first["date_check"] = classify_date_check(first, sla_days)
        first["sla_status"] = classify_sla_status(first, sla_days)
        materials.append(first)

    return materials


def load_image_library(root: Path | None, start_month: str) -> dict[str, dict[str, Any]]:
    if not root or not root.exists():
        return {}
    start_date = parse_month_start(start_month)
    index: dict[str, dict[str, Any]] = {}
    for month_dir in sorted(p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"20\d{2}-\d{2}", p.name)):
        if month_dir.name < start_month:
            continue
        for file_path in month_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            batch = image_library_batch_for(file_path, month_dir)
            if not batch:
                continue
            if start_date and batch.get("library_production_date") and batch["library_production_date"] < start_date:
                continue
            key = normalized_material_name(file_path.stem)
            meta = {**batch, "library_file_path": str(file_path), "library_month": month_dir.name}
            current = index.get(key)
            if not current or image_library_rank(meta) > image_library_rank(current):
                index[key] = meta
    return index


def image_library_rank(meta: dict[str, Any]) -> int:
    if meta.get("library_status") == "final":
        return 3
    if meta.get("library_status") == "pending":
        return 2
    return 1


def image_library_batch_for(file_path: Path, month_dir: Path) -> dict[str, Any] | None:
    current = file_path.parent
    while current != month_dir.parent:
        meta = parse_image_library_batch_name(current.name)
        if meta:
            return meta
        if current == current.parent:
            break
        current = current.parent
    return None


def parse_image_library_batch_name(name: str) -> dict[str, Any] | None:
    if "制作" not in name:
        return None
    production_match = re.search(r"制作\s*(20\d{6})", name)
    if not production_match:
        return None
    production_date = parse_compact_day(production_match.group(1))
    if not production_date:
        return None
    final_match = re.search(r"定稿\s*(20\d{6})", name)
    final_date = parse_compact_day(final_match.group(1)) if final_match else None
    status = "final" if final_date else "pending" if "待确认" in name else "unknown"
    owner_match = re.search(r"[（(]([^（）()]+)[）)]", name)
    return {
        "library_status": status,
        "library_production_date": production_date,
        "library_final_date": final_date,
        "library_owner": owner_match.group(1).strip() if owner_match else "",
        "library_batch_name": name,
    }


def parse_compact_day(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError:
        return None


def parse_month_start(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)
    except ValueError:
        return None


def apply_image_library_metadata(row: dict[str, Any], image_library: dict[str, dict[str, Any]]) -> None:
    if row.get("material_type") != "图片":
        row.setdefault("library_status", "not_image")
        row.setdefault("sla_base_source", "素材制作日期")
        return
    meta = image_library.get(normalized_material_name(row.get("ad_name") or ""))
    if not meta:
        row.setdefault("library_status", "unmatched")
        row.setdefault("sla_base_source", "素材制作日期")
        return
    row.update(meta)
    if meta.get("library_status") == "final" and meta.get("library_final_date"):
        row["report_date"] = meta["library_final_date"]
        row["report_date_precision"] = "full"
        row["sla_base_source"] = "素材定稿日期"
    elif meta.get("library_status") == "pending":
        row["sla_base_source"] = "素材待确认"
    else:
        row["sla_base_source"] = "素材制作日期"


def comparison_date(row: dict[str, Any]) -> date | None:
    if row.get("library_status") == "final" and row.get("library_final_date"):
        return row.get("library_final_date")
    return row.get("material_date")


def material_group_key(row: dict[str, Any]) -> str:
    ad_name = normalized_material_name(row.get("ad_name") or "")
    if ad_name:
        return f"adname:{ad_name}"
    creative_key = str(row.get("creative_key") or "").strip()
    if creative_key:
        return f"creative:{creative_key}"
    fallback = "|".join(
        str(row.get(key) or "").strip()
        for key in ("account_id", "material_date_raw", "ad_name", "campaign_name", "adset_name")
    )
    return f"adname:{fallback}"


def normalized_material_name(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def material_sort_key(row: dict[str, Any]) -> tuple[date, date, str]:
    material_date = comparison_date(row) or date.max
    first_action = first_action_date_for_sort(row) or date.max
    return material_date, first_action, str(row.get("ad_id") or "")


def first_action_date_for_sort(row: dict[str, Any]) -> date | None:
    material_date = comparison_date(row)
    candidates = []
    early = []
    for value in (row.get("created_date"), row.get("adset_start_date")):
        if not value:
            continue
        if material_date and value >= material_date:
            candidates.append(value)
        else:
            early.append(value)
    if candidates:
        return min(candidates)
    return min(early) if early else None


def extract_material_date(name: str) -> tuple[date | None, str, str]:
    text = str(name or "")
    patterns = [
        r"(?<!\d)(20\d{2})[-_./年]?(0[1-9]|1[0-2])[-_./月]?(0[1-9]|[12]\d|3[01])(?:日)?(?!\d)",
        r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])([0-2]\d|3[01])(?!\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        year, month, day = [int(x) for x in match.groups()]
        try:
            return date(year, month, day), "full", match.group(0)
        except ValueError:
            continue

    month_match = re.search(r"(?<!\d)(20\d{2})[-_./年]?(0[1-9]|1[0-2])(?!\d)", text)
    if month_match:
        year, month = [int(x) for x in month_match.groups()]
        return date(year, month, 1), "month", month_match.group(0)
    return None, "", ""


def delta_days(left: date | None, right: date | None) -> int | None:
    if not left or not right:
        return None
    return (right - left).days


def classify_date_check(row: dict[str, Any], sla_days: int) -> str:
    if row.get("library_status") == "pending" and has_action(row):
        return "待确认素材已上线/排期"
    material_date = comparison_date(row)
    if not material_date:
        return "无素材日期"
    precision = row.get("material_date_precision")
    if precision == "month":
        return "素材日期只有月份"
    days = row.get("days_to_first_action")
    if days is None:
        return "缺少上新/排期时间"
    if days < -1:
        return f"上新/排期早于{base_source(row)}"
    if days > sla_days:
        return f"超过{sla_days}天才上新/排期"
    if days < 0:
        return "上新/排期早于素材日期"
    return f"{sla_days}天内已上新/排期"


def days_to_first_action(row: dict[str, Any]) -> int | None:
    material_date = comparison_date(row)
    if not material_date:
        return None
    candidates: list[int] = []
    early: list[int] = []
    for value in (row.get("created_date"), row.get("adset_start_date")):
        if value:
            delta = (value - material_date).days
            if delta >= 0:
                candidates.append(delta)
            else:
                early.append(delta)
    if candidates:
        return min(candidates)
    return min(early) if early else None


def classify_sla_status(row: dict[str, Any], sla_days: int) -> str:
    if row.get("library_status") == "pending" and has_action(row):
        return "素材库待确认但Meta已有广告记录"
    days = days_to_first_action(row)
    if days is None:
        return "缺少上新/排期时间"
    if days < 0:
        return f"上新/排期早于{base_source(row)}"
    if days <= sla_days:
        return f"达标：{sla_days}天内"
    return f"超时：超过{sla_days}天"


def has_action(row: dict[str, Any]) -> bool:
    return bool(row.get("created_date") or row.get("adset_start_date") or row.get("first_action_date"))


def base_source(row: dict[str, Any]) -> str:
    source = row.get("sla_base_source") or "素材制作日期"
    return str(source).replace("素材", "")


def infer_region(text: str) -> str:
    lowered = text.lower()
    if re.search(r"台湾|台灣|taiwan|\btw\b", lowered):
        return "台湾"
    if re.search(r"香港|港澳|hong\s*kong|\bhk\b|澳门|澳門|macau", lowered):
        return "香港/港澳"
    if re.search(r"新加坡|singapore|\bsg\b", lowered):
        return "新加坡"
    return "未识别"


def infer_material_type(text: str) -> str:
    lowered = text.lower()
    if "ai视频" in lowered or "ai video" in lowered or "ai_video" in lowered:
        return "AI视频"
    if "sl视频" in lowered or "sl video" in lowered or "sl_video" in lowered:
        return "SL视频"
    if any(token in lowered for token in (".mp4", ".mov", "视频", "video")):
        return "视频"
    if any(token in lowered for token in (".jpg", ".jpeg", ".png", "800x800", "图")):
        return "图片"
    return "未识别"


def build_message(
    rows: list[dict[str, Any]],
    since: date,
    until: date,
    future_until: date,
    max_lines: int,
    sla_days: int,
    selected_accounts: list[str],
    material_lookback_days: int,
) -> str:
    creatives = {r.get("creative_key") for r in rows if r.get("creative_key")}
    by_account: Counter[str] = Counter()
    for row in rows:
        by_account.update(row.get("report_account_counts") or {row["account_name"]: int(row.get("material_ad_count") or 1)})
    by_region = Counter(r["region"] for r in rows)
    by_type = Counter(r["material_type"] for r in rows)
    by_status: Counter[str] = Counter()
    for row in rows:
        by_status.update(row.get("report_status_counts") or {row.get("effective_status") or "未识别": int(row.get("material_ad_count") or 1)})
    by_precision = Counter(r.get("material_date_precision") or "未识别" for r in rows)
    by_check = Counter(r.get("date_check") or "未识别" for r in rows)
    by_sla = Counter(r.get("sla_status") or "未识别" for r in rows)
    by_library = Counter(r.get("library_status") or "未识别" for r in rows)
    paused = sum(v for k, v in by_status.items() if "PAUSED" in k)
    active = sum(v for k, v in by_status.items() if "ACTIVE" in k)

    lines: list[str] = []
    lines.append(f"**FB新素材上新/排期情况播报｜{since.isoformat()} 至 {until.isoformat()}**")
    lines.append("")
    total_ads = sum(int(r.get("material_ad_count") or 1) for r in rows)
    monitored_accounts = selected_accounts or sorted({r.get("account_id", "") for r in rows if r.get("account_id")})
    hit_account_ids = {
        account_id
        for row in rows
        for account_id in (row.get("report_account_ids") or ([row.get("account_id")] if row.get("account_id") else []))
    }
    no_hit_accounts = [acct for acct in monitored_accounts if acct not in hit_account_ids]
    lines.append(f"- 监控账户：{len(monitored_accounts)} 个")
    lines.append(f"- 本期有上新或排期素材账户：{len(hit_account_ids)} 个")
    lines.append(f"- 本期无上新或排期素材账户：{len(no_hit_accounts)} 个")
    lines.append(f"- 新制作素材广告：{total_ads} 条")
    lines.append(f"- 涉及素材：{len(rows)} 个")
    lines.append(f"- 状态：ACTIVE相关 {active} 条；PAUSED相关 {paused} 条")
    material_since = until - timedelta(days=max(material_lookback_days, 1) - 1)
    if since == until:
        action_window_text = f"{since.isoformat()} 当天新建，或广告组排期时间在 {until.isoformat()} 的广告"
    else:
        action_window_text = f"{since.isoformat()} 至 {until.isoformat()} 期间新建，或广告组排期时间在本期内的广告"
    lines.append(
        f"- 广告口径：本期统计 {action_window_text}；同一素材只统计首次上新/排期对应的广告，后续复制、加投、换广告组不重复计入。"
    )
    lines.append(
        f"- 素材口径：素材按名称去重；图片看素材库定稿日期，视频看文件名日期；本期只看素材日期在 {material_since.isoformat()} 至 {until.isoformat()} 的素材。"
    )
    lines.append(f"**{sla_days}天上新/排期监控**")
    lines.append("；".join(f"{k} {v}" for k, v in by_sla.most_common()) or "无")
    if by_sla:
        lines.append("提醒：超时可能与素材审核时间有关，建议结合实际审核节奏判断。")
    lines.append("")

    if by_precision.get("month"):
        lines.append(f"**注意**：有 {by_precision['month']} 条只识别到月份日期，建议后续命名补到日。")
        lines.append("")

    lines.append("**按账户**")
    if monitored_accounts:
        for account_id in monitored_accounts:
            lines.append(f"- {ACCOUNT_NAMES.get(account_id, account_id)}：{by_account.get(ACCOUNT_NAMES.get(account_id, account_id), 0)} 条")
    else:
        for name, count in by_account.most_common(max_lines):
            lines.append(f"- {name}：{count} 条")
        if len(by_account) > max_lines:
            lines.append(f"- 其余账户：{sum(c for _, c in by_account.most_common()[max_lines:])} 条")
    lines.append("")

    lines.append("**按地区**")
    lines.append("；".join(f"{k} {v}" for k, v in by_region.most_common()) or "无")
    lines.append("")

    lines.append("**按素材类型**")
    lines.append("；".join(f"{k} {v}" for k, v in by_type.most_common()) or "无")
    lines.append("")

    if max_lines > 0:
        lines.append("**代表广告**")
        for row in rows[:max_lines]:
            material_date = row["material_date"].isoformat() if row.get("material_date") else "无"
            base_date = comparison_date(row)
            base_date_text = base_date.isoformat() if base_date else "无"
            first_action_date = row["first_action_date"].isoformat() if row.get("first_action_date") else "无"
            days = row.get("days_to_first_action")
            days_text = "无" if days is None else f"{days}天"
            lines.append(
                f"- {row['account_name']}｜{row['region']}｜{row['material_type']}｜"
                f"素材{material_date}｜考核{row.get('sla_base_source') or '素材制作日期'}{base_date_text}｜"
                f"首次{row.get('first_action_source') or '无'}{first_action_date}｜"
                f"{row.get('sla_status') or '未识别'}｜用时{days_text}｜"
                f"含{row.get('material_ad_count') or 1}条广告｜"
                f"{short(row.get('ad_name'), 26)}"
            )
        if len(rows) > max_lines:
            lines.append(f"- 其余 {len(rows) - max_lines} 个素材见本地明细库")

    return "\n".join(lines)


def short(value: Any, length: int) -> str:
    text = str(value or "").replace("\n", " ")
    return text if len(text) <= length else text[: length - 1] + "…"


def detect_robot_type(webhook: str, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    lowered = webhook.lower()
    if "qyapi.weixin.qq.com" in lowered:
        return "wecom"
    if "open.feishu.cn" in lowered or "open.larksuite.com" in lowered:
        return "feishu"
    if "oapi.dingtalk.com" in lowered:
        return "dingtalk"
    sys.exit("[ERR] Cannot auto-detect robot type. Pass --robot-type wecom|feishu|dingtalk.")


def payload_for(robot_type: str, message: str) -> dict[str, Any]:
    if robot_type == "wecom":
        return {"msgtype": "markdown", "markdown": {"content": message[:3900]}}
    if robot_type == "feishu":
        return {"msg_type": "text", "content": {"text": strip_markdown(message[:3900])}}
    if robot_type == "dingtalk":
        return {"msgtype": "markdown", "markdown": {"title": "FB新素材上新/排期情况播报", "text": message[:3900]}}
    raise ValueError(robot_type)


def prepare_webhook_url(webhook: str, robot_type: str) -> str:
    if robot_type != "dingtalk":
        return webhook
    secret = os.getenv("FB_BROADCAST_DINGTALK_SECRET", "").strip()
    if not secret:
        return webhook
    timestamp = str(round(time.time() * 1000))
    sign_raw = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), sign_raw, hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(digest))
    separator = "&" if "?" in webhook else "?"
    return f"{webhook}{separator}timestamp={timestamp}&sign={sign}"


def strip_markdown(text: str) -> str:
    return text.replace("**", "")


def send_webhook(webhook: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "fb-robot-broadcast/0.1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"raw": raw}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Webhook HTTP {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Webhook connection failed: {exc.reason}") from exc


def main() -> int:
    args = parse_args()
    load_env()
    since, until, future_until = resolve_window(args)
    account_filter_raw = args.account_aliases or os.getenv("FB_BROADCAST_ACCOUNT_ALIASES", "").strip()
    selected_accounts = parse_account_filter(account_filter_raw)
    image_library_root = None if args.disable_image_library else Path(args.image_library_root)
    rows = load_rows(
        Path(args.db),
        since,
        until,
        future_until,
        args.include_month_only,
        args.sla_days,
        selected_accounts,
        image_library_root,
        args.image_library_start_month,
        args.material_lookback_days,
    )
    message = build_message(
        rows,
        since,
        until,
        future_until,
        args.max_lines,
        args.sla_days,
        selected_accounts,
        args.material_lookback_days,
    )

    if args.dry_run:
        print(message)
        return 0

    webhook = args.webhook or os.getenv("FB_BROADCAST_WEBHOOK_URL", "").strip()
    if not webhook:
        sys.exit("[ERR] Missing webhook. Put FB_BROADCAST_WEBHOOK_URL=... in .env or pass --webhook.")

    robot_type_setting = args.robot_type
    if robot_type_setting == "auto":
        robot_type_setting = os.getenv("FB_BROADCAST_ROBOT_TYPE", "auto").strip() or "auto"
    robot_type = detect_robot_type(webhook, robot_type_setting)
    payload = payload_for(robot_type, message)
    result = send_webhook(prepare_webhook_url(webhook, robot_type), payload)
    print(f"[OK] sent to {robot_type}: {json.dumps(result, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
