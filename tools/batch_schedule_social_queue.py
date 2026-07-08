#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.meta_publish_server import schedule_facebook_photo
from tools.social_publish_core import ACCOUNT_PRESETS, prepare_image


DEFAULT_QUEUE = ROOT / "generated" / "schedules" / "global_2026-07-07_2026-07-10" / "queue.scheduled.json"
DEFAULT_PREVIEW = ROOT / "generated" / "schedules" / "global_2026-07-07_2026-07-10" / "preview.md"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_time(value):
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=8)))
    return parsed


def unix_time(value):
    return int(parse_time(value).timestamp())


def extract_caption(preview_text, caption_file_section):
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


def section_for(item, platform):
    for post in item.get("posts", []):
        if post.get("platform") == platform:
            return post["caption_file_section"]
    raise ValueError(f"Queue item {item.get('date')} #{item.get('sequence')} has no {platform} post")


def result_path_for(queue_path):
    path = Path(queue_path)
    return path.with_name(path.stem + ".batch-result.json")


def main():
    parser = argparse.ArgumentParser(description="Batch submit VIP THINK scheduled social queue.")
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE))
    parser.add_argument("--preview-md", default=str(DEFAULT_PREVIEW))
    parser.add_argument("--preset", default="global", choices=["hk", "global", "both"])
    parser.add_argument("--yes", action="store_true", help="Actually submit future Facebook posts. Without this, dry-run only.")
    args = parser.parse_args()

    queue_path = Path(args.queue)
    preview_text = Path(args.preview_md).read_text(encoding="utf-8")
    queue = load_json(queue_path)
    page_ids = ACCOUNT_PRESETS[args.preset]["page_ids"]

    payload = {
        "dry_run": not args.yes,
        "preset": args.preset,
        "queue": str(queue_path),
        "result_file": str(result_path_for(queue_path)),
        "facebook": [],
        "instagram": [],
    }

    for item in queue.get("items", []):
        image_url = None
        if args.yes:
            image_url, _ = prepare_image(item["image"])

        fb_caption = extract_caption(preview_text, section_for(item, "facebook"))
        ig_caption = extract_caption(preview_text, section_for(item, "instagram"))
        scheduled_unix = unix_time(item["scheduled_at"])

        for page_id in page_ids:
            if args.yes:
                result = schedule_facebook_photo(page_id, image_url, fb_caption, scheduled_unix)
            else:
                result = {
                    "would_schedule": True,
                    "scheduled_publish_time": scheduled_unix,
                    "image": item["image"],
                }
            payload["facebook"].append(
                {
                    "date": item["date"],
                    "time": item["time"],
                    "sequence": item["sequence"],
                    "topic": item["topic"],
                    "page_id": page_id,
                    "image": item["image"],
                    "image_url": image_url,
                    "scheduled_at": item["scheduled_at"],
                    "result": result,
                }
            )

        payload["instagram"].append(
            {
                "date": item["date"],
                "time": item["time"],
                "sequence": item["sequence"],
                "topic": item["topic"],
                "ig_user_ids": ACCOUNT_PRESETS[args.preset]["ig_user_ids"],
                "image": item["image"],
                "scheduled_at": item["scheduled_at"],
                "caption_preview": ig_caption,
                "status": "not_submitted",
                "reason": "Instagram Graph API publishing is immediate; this local tool does not have an official future scheduling endpoint to submit multi-day Instagram posts all at once.",
            }
        )

    save_json(result_path_for(queue_path), payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
