#!/usr/bin/env python3
"""Adapt successful TikHub compatibility details for blogger-distiller analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = json.loads(args.source.read_text(encoding="utf-8"))
    adapted: list[dict[str, Any]] = []
    for row in rows:
        if row.get("_error"):
            continue
        note = row.get("note") or {}
        interact = note.get("interact_info") or {}
        adapted.append(
            {
                "note": {
                    "noteId": note.get("note_id") or row.get("_feed_id", ""),
                    "title": note.get("title", ""),
                    "desc": note.get("desc", ""),
                    "type": note.get("type", "normal"),
                    "time": note.get("time", 0),
                    "tagList": note.get("tag_list", []),
                    "interactInfo": {
                        "likedCount": interact.get("liked_count", ""),
                        "collectedCount": interact.get("collected_count", ""),
                        "commentCount": interact.get("comment_count", ""),
                        "sharedCount": interact.get("share_count", ""),
                    },
                },
                "comments": row.get("comments") or {"list": []},
                "_feed_id": row.get("_feed_id", ""),
                "_meta": {**(row.get("_meta", {}) or {}), "source": "xhs"},
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(adapted, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"adapted={len(adapted)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
