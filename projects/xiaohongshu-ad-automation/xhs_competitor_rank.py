#!/usr/bin/env python3
"""Rank competitor notes into a VIPTHINK remake-candidate list."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def number(value: Any) -> float:
    text = str(value or "0").replace(",", "").strip()
    if text.endswith("万"):
        text = str(float(text[:-1]) * 10000)
    try:
        return float(text)
    except ValueError:
        return 0.0


def percentile(values: list[float], value: float) -> float:
    if len(values) <= 1:
        return 1.0
    return sum(item <= value for item in values) / len(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("details", type=Path)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = json.loads(args.details.read_text(encoding="utf-8"))
    candidates: list[dict[str, Any]] = []
    for entry in records:
        if entry.get("_error"):
            continue
        note = entry.get("note") or {}
        interact = note.get("interact_info") or note.get("interactInfo") or {}
        candidates.append(
            {
                "note_id": str(note.get("note_id") or note.get("noteId") or ""),
                "title": str(note.get("title") or ""),
                "content_type": str(note.get("type") or ""),
                "publish_time": note.get("time"),
                "likes": number(interact.get("liked_count") or interact.get("liked")),
                "saves": number(interact.get("collected_count") or interact.get("collected")),
                "comments": number(interact.get("comment_count")),
                "shares": number(interact.get("share_count")),
                "content_excerpt": str(note.get("desc") or "")[:240],
                "tags": [str(item.get("name") or item.get("tag_name") or "") for item in (note.get("tag_list") or []) if isinstance(item, dict)],
            }
        )

    likes = [item["likes"] for item in candidates]
    saves = [item["saves"] for item in candidates]
    comments = [item["comments"] for item in candidates]
    shares = [item["shares"] for item in candidates]
    for item in candidates:
        score = (
            percentile(likes, item["likes"]) * 0.35
            + percentile(saves, item["saves"]) * 0.35
            + percentile(comments, item["comments"]) * 0.20
            + percentile(shares, item["shares"]) * 0.10
        )
        item["remake_priority_score"] = round(score * 100, 1)
        item["remake_rule"] = "复用选题、封面信息层级和内容结构；使用 VIPTHINK 自有证据、IP、素材和文案重新制作。"

    ranked = sorted(candidates, key=lambda item: item["remake_priority_score"], reverse=True)
    result = {
        "source_scope": "单账号内互动相对排名，不等同于曝光或转化效果。",
        "input_note_count": len(candidates),
        "selected_count": min(args.top, len(ranked)),
        "candidates": ranked[: args.top],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ranked={len(candidates)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
