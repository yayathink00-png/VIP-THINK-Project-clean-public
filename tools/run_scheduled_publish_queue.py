#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.social_publish_core import publish_image_bundle


DEFAULT_QUEUE = ROOT / "generated" / "schedules" / "global_2026-07-07_2026-07-10" / "queue.scheduled.json"
DEFAULT_PREVIEW = ROOT / "generated" / "schedules" / "global_2026-07-07_2026-07-10" / "preview.md"


def parse_time(value):
    if value:
        parsed = dt.datetime.fromisoformat(value)
    else:
        parsed = dt.datetime.now().astimezone()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=8)))
    return parsed


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def state_path_for(queue_path):
    path = Path(queue_path)
    return path.with_suffix(".state.json")


def load_state(queue_path):
    path = state_path_for(queue_path)
    if not path.exists():
        return {"published": {}, "attempts": []}
    return load_json(path)


def item_key(item):
    return f"{item['date']}#{item['sequence']}"


def extract_facebook_caption(preview_text, caption_file_section):
    date_heading, platform_heading = [part.strip() for part in caption_file_section.split("/", 1)]
    section_start = preview_text.find(f"## {date_heading}")
    if section_start < 0:
        raise ValueError(f"Cannot find date section in preview.md: {date_heading}")
    next_section = preview_text.find("\n## ", section_start + 1)
    section = preview_text[section_start: next_section if next_section > 0 else len(preview_text)]
    platform_start = section.find(f"### {platform_heading}")
    if platform_start < 0:
        raise ValueError(f"Cannot find platform section in preview.md: {caption_file_section}")
    platform_section = section[platform_start:]
    match = re.search(r"```text\n(.*?)\n```", platform_section, re.S)
    if not match:
        raise ValueError(f"Cannot find caption code block in preview.md: {caption_file_section}")
    return match.group(1).strip()


def due_items(queue, state, now):
    items = []
    for item in queue.get("items", []):
        key = item_key(item)
        if key in state.get("published", {}):
            continue
        scheduled_at = parse_time(item["scheduled_at"])
        if scheduled_at <= now:
            items.append(item)
    return items


def main():
    parser = argparse.ArgumentParser(description="Run due VIP THINK scheduled social posts.")
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE))
    parser.add_argument("--preview-md", default=str(DEFAULT_PREVIEW))
    parser.add_argument("--now", help="Override current time, ISO format. For tests only.")
    parser.add_argument("--yes", action="store_true", help="Actually publish. Without this, dry-run only.")
    args = parser.parse_args()

    queue_path = Path(args.queue)
    preview_path = Path(args.preview_md)
    queue = load_json(queue_path)
    state = load_state(queue_path)
    now = parse_time(args.now)
    preview_text = preview_path.read_text(encoding="utf-8")
    items = due_items(queue, state, now)

    if not items:
        print(json.dumps({"status": "no_due_items", "now": now.isoformat()}, ensure_ascii=False, indent=2))
        return 0

    results = []
    for item in items:
        facebook_section = next(
            post["caption_file_section"]
            for post in item["posts"]
            if post["platform"] == "facebook"
        )
        caption = extract_facebook_caption(preview_text, facebook_section)
        result = publish_image_bundle(
            preset="global",
            image=item["image"],
            global_caption=caption,
            publish_facebook_enabled=True,
            publish_instagram_enabled=True,
            publish_youtube_enabled=False,
            dry_run=not args.yes,
        )
        payload = {
            "key": item_key(item),
            "scheduled_at": item["scheduled_at"],
            "topic": item["topic"],
            "image": item["image"],
            "dry_run": result.get("dry_run", True),
            "links": result.get("links", []),
            "results": result.get("results", {}),
        }
        results.append(payload)
        if args.yes:
            state.setdefault("published", {})[item_key(item)] = {
                "published_at": now.isoformat(),
                "topic": item["topic"],
                "image": item["image"],
                "links": result.get("links", []),
            }
    state.setdefault("attempts", []).append(
        {
            "run_at": now.isoformat(),
            "dry_run": not args.yes,
            "item_keys": [item_key(item) for item in items],
        }
    )
    if args.yes:
        save_json(state_path_for(queue_path), state)
    print(json.dumps({"status": "ok", "dry_run": not args.yes, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
