#!/usr/bin/env python3
"""Create a lightweight, filename-based index for VIPTHINK visual assets.

The script stores paths and tags only. It never copies the mounted asset
library, so daily content runs stay small and source updates remain visible.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCES = ROOT / "inputs" / "brand" / "asset_sources.json"
DEFAULT_OUTPUT = ROOT / "memory" / "asset_index.json"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}
TAG_RULES = {
    "用户痛点": "用户痛点",
    "学习效果": "学习效果和成果",
    "成果类": "学习效果和成果",
    "往期优秀": "往期优秀素材",
    "竞品广告": "竞品广告",
    "普通话": "普通话",
    "台湾腔": "台湾腔",
    "简体": "简体",
    "繁体": "繁体",
    "口播": "口播",
    "情景剧": "情景剧",
    "数学": "数学",
    "逻辑": "逻辑",
    "应用题": "应用题",
    "动画": "动画互动",
    "游戏": "游戏化",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def media_kind(path: Path, source_kind: str) -> str:
    if path.suffix.lower() in VIDEO_EXTENSIONS:
        return "video"
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return "image"
    return ""


def tags_for(path: Path, source_kind: str) -> list[str]:
    text = str(path).lower()
    tags = {source_kind}
    for marker, tag in TAG_RULES.items():
        if marker.lower() in text:
            tags.add(tag)
    return sorted(tags)


def build_index(sources: list[dict[str, Any]], max_files: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    for source in sources:
        root = Path(str(source["path"]))
        if not root.exists():
            warnings.append({"source": str(source.get("id", "unknown")), "warning": f"路径不可用：{root}"})
            continue
        for path in root.rglob("*"):
            if max_files and len(items) >= max_files:
                warnings.append({"source": str(source.get("id", "unknown")), "warning": f"达到索引上限：{max_files}"})
                return items, warnings
            if not path.is_file() or path.name.startswith("."):
                continue
            kind = media_kind(path, str(source.get("kind", "asset")))
            if kind not in {"image", "video"}:
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            items.append(
                {
                    "asset_id": hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12],
                    "source_id": source.get("id"),
                    "kind": kind,
                    "path": str(path),
                    "extension": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "tags": tags_for(path, str(source.get("kind", "asset"))),
                }
            )
    return items, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Index VIPTHINK visual assets without copying them.")
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-files", type=int, default=10000, help="0 means no limit")
    args = parser.parse_args()

    source_config = load_json(Path(args.sources))
    items, warnings = build_index(source_config.get("sources", []), args.max_files)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
                "sources": source_config.get("sources", []),
                "item_count": len(items),
                "items": items,
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Indexed {len(items)} assets")
    print(f"Output: {output}")
    for warning in warnings:
        print(f"Warning: {warning['warning']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
