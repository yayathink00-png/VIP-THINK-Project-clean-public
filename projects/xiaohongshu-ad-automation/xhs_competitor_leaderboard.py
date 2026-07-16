#!/usr/bin/env python3
"""Build one honest, interaction-ranked competitor leaderboard."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any


def number(value: Any) -> int | None:
    text = str(value or "").replace(",", "").strip()
    if not text:
        return None
    try:
        return int(float(text[:-1]) * 10_000) if text.endswith("万") else int(float(text))
    except ValueError:
        return None


def source_files(root: Path) -> list[Path]:
    return sorted(root.rglob("notes_details.json"))


def image_summary(note: dict[str, Any]) -> tuple[str, str]:
    images = note.get("image_list") or note.get("imageList") or []
    first = next((item for item in images if isinstance(item, dict)), {})
    url = str(first.get("url_pre") or first.get("url_default") or first.get("url") or "")
    return f"{len(images)}张", url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("inputs/competitor_data/compat"))
    parser.add_argument("--output", type=Path, default=Path("outputs/competitor_content_ranking.md"))
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for file_path in source_files(args.input_root):
        try:
            entries = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for entry in entries:
            if entry.get("_error"):
                continue
            note = entry.get("note") or {}
            interact = note.get("interact_info") or note.get("interactInfo") or {}
            metrics = [
                number(interact.get("liked_count") or interact.get("likedCount")),
                number(interact.get("collected_count") or interact.get("collectedCount")),
                number(interact.get("comment_count") or interact.get("commentCount")),
                number(interact.get("share_count") or interact.get("sharedCount")),
            ]
            available = [metric for metric in metrics if metric is not None]
            image_count, image_url = image_summary(note)
            tags = [str(tag.get("name") or "") for tag in note.get("tag_list", []) if isinstance(tag, dict)]
            rows.append(
                {
                    "blogger": str((note.get("user") or {}).get("nickname") or file_path.parent.name),
                    "content": str(note.get("title") or note.get("desc") or "")[:80],
                    "image": image_count,
                    "image_url": image_url,
                    "interaction": sum(available) if len(available) == 4 else None,
                    "tags": " ".join(f"#{tag}" for tag in tags[:8]),
                    "source": str(file_path),
                }
            )

    ranked = sorted(rows, key=lambda row: (row["interaction"] is not None, row["interaction"] or 0), reverse=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.output.with_suffix(".csv")
    html_path = args.output.with_suffix(".html")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["排名", "博主", "内容", "配图", "互动数", "标签", "首图链接", "数据来源"])
        writer.writeheader()
        for index, row in enumerate(ranked, start=1):
            rank = index if row["interaction"] is not None else "待补"
            writer.writerow({"排名": rank, "博主": row["blogger"], "内容": row["content"], "配图": row["image"], "互动数": row["interaction"] if row["interaction"] is not None else "待补", "标签": row["tags"], "首图链接": row["image_url"], "数据来源": row["source"]})

    lines = ["# 竞品内容综合排行", "", "互动数 = 点赞 + 收藏 + 评论 + 分享；无完整数据的内容不参与有效排名，统一排在表尾。", "", "| 排名 | 博主 | 内容 | 配图 | 互动数 | 标签 |", "|---:|---|---|---|---:|---|"]
    for index, row in enumerate(ranked, start=1):
        image = f'<img src="{row["image_url"]}" alt="首图" width="120" />' if row["image_url"] else row["image"]
        interaction = str(row["interaction"]) if row["interaction"] is not None else "待补"
        rank = str(index) if row["interaction"] is not None else "待补"
        lines.append(f"| {rank} | {row['blogger']} | {row['content'].replace('|', ' ')} | {image} | {interaction} | {row['tags'].replace('|', ' ')} |")
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    html_rows = []
    for index, row in enumerate(ranked, start=1):
        rank = str(index) if row["interaction"] is not None else "待补"
        interaction = str(row["interaction"]) if row["interaction"] is not None else "待补"
        image = f'<img src="{html.escape(row["image_url"], quote=True)}" alt="首图" />' if row["image_url"] else "无"
        html_rows.append(
            "<tr>"
            f"<td>{rank}</td><td>{html.escape(row['blogger'])}</td><td>{html.escape(row['content'])}</td>"
            f"<td>{image}</td><td>{interaction}</td><td>{html.escape(row['tags'])}</td>"
            "</tr>"
        )
    html_path.write_text(
        "<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\"><title>竞品内容综合排行</title>"
        "<style>body{font:14px Arial,sans-serif;margin:24px;color:#202124}table{border-collapse:collapse;width:100%}"
        "th,td{border-bottom:1px solid #ddd;padding:10px;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#fff}"
        "td:nth-child(4){width:140px}td img{width:120px;max-height:160px;object-fit:cover;border-radius:4px}"
        ".missing{color:#a65d00}</style><h1>竞品内容综合排行</h1>"
        "<p>互动数 = 点赞 + 收藏 + 评论 + 分享。待补不参与有效排名。</p>"
        "<table><thead><tr><th>排名</th><th>博主</th><th>内容</th><th>配图</th><th>互动数</th><th>标签</th></tr></thead><tbody>"
        + "".join(html_rows)
        + "</tbody></table></html>",
        encoding="utf-8",
    )
    print(f"rows={len(ranked)} output={args.output} html={html_path} csv={csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
