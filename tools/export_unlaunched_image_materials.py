#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
DEFAULT_LIBRARY_ROOT = Path("/Volumes/海外投放素材库/图片素材/思维")
DEFAULT_DB = Path("/Users/yangyi/Desktop/03 批量上FB广告/fb_new_creative_monitor.sqlite3")
ACCOUNT_ALIASES = {
    "7": "act_468253789344241",
    "8": "act_366864216464093",
    "9": "act_442457935507062",
    "27": "act_1158469106256042",
    "18": "act_627543006449377",
    "23": "act_2107766700052928",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export finalized image materials not found in Meta ads.")
    parser.add_argument("--since", required=True, help="Final date start, YYYY-MM-DD.")
    parser.add_argument("--until", required=True, help="Final date end, YYYY-MM-DD.")
    parser.add_argument("--library-root", default=str(DEFAULT_LIBRARY_ROOT))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--account-aliases", default="7,8,9,27,18,23")
    parser.add_argument("--out-dir", default="/Users/yangyi/Documents/机器人播报")
    return parser.parse_args()


def parse_day(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_compact_day(value: str):
    return datetime.strptime(value, "%Y%m%d").date()


def normalize_name(value: str) -> str:
    text = str(value or "").strip()
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"图\s*\(\s*(\d+)\s*\)", r"图\1", text)
    text = re.sub(r"图\s+(\d+)$", r"图\1", text)
    return text.strip()


def infer_region(text: str) -> str:
    if "台湾" in text:
        return "台湾"
    if "新加坡" in text:
        return "新加坡"
    if "港澳" in text or "香港" in text or "澳门" in text:
        return "香港/港澳"
    if "欧美澳" in text:
        return "欧美澳"
    return "未识别"


def parse_batch_name(name: str) -> dict | None:
    if "制作" not in name or "定稿" not in name:
        return None
    production_match = re.search(r"制作[^\d]*(20\d{6})", name)
    final_match = re.search(r"定稿[^\d]*(20\d{6})", name)
    if not production_match or not final_match:
        return None
    owner_match = re.search(r"[（(]([^（）()0-9]+)[）)]", name)
    return {
        "production_date": parse_compact_day(production_match.group(1)),
        "final_date": parse_compact_day(final_match.group(1)),
        "owner": owner_match.group(1).strip() if owner_match else "",
        "batch_name": name,
    }


def batch_for_file(file_path: Path, month_dir: Path) -> dict | None:
    current = file_path.parent
    while current != month_dir.parent:
        meta = parse_batch_name(current.name)
        if meta:
            return meta
        if current == current.parent:
            break
        current = current.parent
    return None


def scan_library(root: Path, since, until) -> list[dict]:
    rows: list[dict] = []
    for month_dir in sorted(p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"20\d{2}-\d{2}", p.name)):
        if month_dir.name < f"{since:%Y-%m}" or month_dir.name > f"{until:%Y-%m}":
            continue
        for file_path in month_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            batch = batch_for_file(file_path, month_dir)
            if not batch or not (since <= batch["final_date"] <= until):
                continue
            stem = file_path.stem
            rows.append(
                {
                    "素材名称": stem,
                    "匹配Key": normalize_name(stem),
                    "制作日期": batch["production_date"].isoformat(),
                    "定稿日期": batch["final_date"].isoformat(),
                    "负责人": batch["owner"],
                    "地区": infer_region(str(file_path)),
                    "批次": batch["batch_name"],
                    "文件路径": str(file_path),
                }
            )
    return rows


def account_ids(raw: str) -> list[str]:
    result = []
    for item in re.split(r"[,，;；\s]+", raw.strip()):
        if not item:
            continue
        account_id = ACCOUNT_ALIASES.get(item, item)
        if account_id.isdigit():
            account_id = "act_" + account_id
        result.append(account_id)
    return result


def load_meta_ad_keys(db_path: Path, accounts: list[str]) -> set[str]:
    conn = sqlite3.connect(db_path)
    placeholders = ",".join("?" for _ in accounts)
    query = f"SELECT ad_name FROM ads_seen WHERE account_id IN ({placeholders})"
    keys = {normalize_name(row[0]) for row in conn.execute(query, accounts) if row[0]}
    conn.close()
    return keys


def write_csv(path: Path, rows: list[dict]) -> None:
    columns = ["定稿日期", "制作日期", "地区", "负责人", "批次", "素材名称", "文件路径"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def main() -> int:
    args = parse_args()
    since = parse_day(args.since)
    until = parse_day(args.until)
    library_rows = scan_library(Path(args.library_root), since, until)
    meta_keys = load_meta_ad_keys(Path(args.db), account_ids(args.account_aliases))
    unlaunched = [row for row in library_rows if row["匹配Key"] not in meta_keys]
    unlaunched.sort(key=lambda r: (r["定稿日期"], r["地区"], r["批次"], r["素材名称"]))

    out_dir = Path(args.out_dir) / f"fb_unlaunched_image_materials_{since:%Y%m%d}_{until:%Y%m%d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"上一周未上图片素材名单_{len(unlaunched)}.csv"
    write_csv(csv_path, unlaunched)

    by_final = Counter(row["定稿日期"] for row in unlaunched)
    by_region = Counter(row["地区"] for row in unlaunched)
    by_batch = Counter(row["批次"] for row in unlaunched)

    summary_path = out_dir / "名单说明.md"
    lines = [
        f"# 上一周未上图片素材名单｜{since} 至 {until}",
        "",
        f"- 素材库已定稿图片：{len(library_rows)} 个",
        f"- 未匹配到 Meta 广告记录：{len(unlaunched)} 个",
        "- 口径：素材库图片文件名与监控账户 Meta 广告名称归一化后匹配；匹配不到视为未上新/未排期。",
        "- 监控账户：7、8、9、27、18、23。",
        "",
        "## 按定稿日期",
        "；".join(f"{k} {v}" for k, v in sorted(by_final.items())) or "无",
        "",
        "## 按地区",
        "；".join(f"{k} {v}" for k, v in by_region.most_common()) or "无",
        "",
        "## 未上数量最多批次",
    ]
    lines.extend(f"- {batch}：{count} 个" for batch, count in by_batch.most_common(20))
    lines.extend(["", f"CSV：{csv_path}"])
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(summary_path)
    print(csv_path)
    print(f"library_final={len(library_rows)}")
    print(f"unlaunched={len(unlaunched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
