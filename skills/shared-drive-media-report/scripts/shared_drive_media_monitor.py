#!/usr/bin/env python3
"""
Scan a shared-drive folder for newly added images/videos and notify DingTalk via dws bot.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".heic",
    ".heif",
    ".avif",
    ".svg",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".mpeg",
    ".mpg",
    ".3gp",
    ".ts",
    ".m2ts",
}


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def local_tz() -> dt.tzinfo:
    return dt.datetime.now().astimezone().tzinfo or dt.timezone.utc


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def parse_report_date(value: str | None) -> dt.date:
    if value:
        return dt.date.fromisoformat(value)
    return dt.datetime.now().astimezone().date()


def resolve_report_window(args: argparse.Namespace) -> tuple[dt.datetime | None, dt.datetime | None, str]:
    tz = local_tz()
    if args.window_start or args.window_end:
        if not args.window_start or not args.window_end:
            raise ValueError("--window-start and --window-end must be used together")
        start_date = dt.date.fromisoformat(args.window_start)
        end_date = dt.date.fromisoformat(args.window_end)
        start = dt.datetime.combine(start_date, dt.time.min, tzinfo=tz)
        end = dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time.min, tzinfo=tz)
        return start, end, f"{start_date.isoformat()} 至 {end_date.isoformat()}"

    if args.report_schedule != "wed_fri":
        return None, None, "全部时间"

    today = parse_report_date(args.report_date)
    weekday = today.weekday()
    if weekday == 2:
        start_date = today - dt.timedelta(days=2)
        end_date = today
        label = "本周周一至周三"
    elif weekday == 4:
        start_date = today - dt.timedelta(days=1)
        end_date = today
        label = "本周周四至周五"
    else:
        raise ValueError("wed_fri schedule only runs on Wednesday or Friday; use --window-start/--window-end for manual runs")

    start = dt.datetime.combine(start_date, dt.time.min, tzinfo=tz)
    end = dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time.min, tzinfo=tz)
    return start, end, f"{label}（{start_date.isoformat()} 至 {end_date.isoformat()}）"


def month_starts_between(start: dt.datetime | None, end: dt.datetime | None) -> list[dt.date]:
    if not start or not end:
        return []
    current = dt.date(start.year, start.month, 1)
    end_date = (end - dt.timedelta(seconds=1)).date()
    last = dt.date(end_date.year, end_date.month, 1)
    months = []
    while current <= last:
        months.append(current)
        if current.month == 12:
            current = dt.date(current.year + 1, 1, 1)
        else:
            current = dt.date(current.year, current.month + 1, 1)
    return months


def format_month_pattern(pattern: str, month_start: dt.date) -> str:
    return pattern.format(
        year=month_start.year,
        month=month_start.month,
        month02=f"{month_start.month:02d}",
    )


def dates_in_window(window_start: dt.datetime | None, window_end: dt.datetime | None) -> list[dt.date]:
    if not window_start or not window_end:
        return []
    current = window_start.date()
    last = (window_end - dt.timedelta(seconds=1)).date()
    dates = []
    while current <= last:
        dates.append(current)
        current += dt.timedelta(days=1)
    return dates


def extract_dates_from_name(name: str, years: set[int]) -> set[dt.date]:
    found: set[dt.date] = set()
    for match in re.finditer(r"(20\d{2})(\d{2})(\d{2})", name):
        year, month, day = map(int, match.groups())
        add_valid_date(found, year, month, day)
    for match in re.finditer(r"(20\d{2})[.\-_/年](\d{1,2})[.\-_/月](\d{1,2})", name):
        year, month, day = map(int, match.groups())
        add_valid_date(found, year, month, day)
    for match in re.finditer(r"(?<!\d)(\d{2})(\d{2})(?!\d)", name):
        month, day = map(int, match.groups())
        for year in years:
            add_valid_date(found, year, month, day)
    return found


def add_valid_date(target: set[dt.date], year: int, month: int, day: int) -> None:
    try:
        target.add(dt.date(year, month, day))
    except ValueError:
        return


def name_matches_date_window(name: str, window_dates: set[dt.date], years: set[int]) -> bool:
    return bool(extract_dates_from_name(name, years) & window_dates)


def week_index_for_date(value: dt.date) -> int:
    return min(((value.day - 1) // 7) + 1, 5)


def week_labels_for_dates(values: list[dt.date]) -> set[str]:
    numerals = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五"}
    labels: set[str] = set()
    for value in values:
        week = week_index_for_date(value)
        zh = numerals[week]
        labels.update({f"{zh}周", f"第{zh}周", f"第{week}周", f"{week}周"})
    return labels


def classify(path: Path) -> tuple[str | None, str]:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image", ext.lstrip(".") or "unknown"
    if ext in VIDEO_EXTENSIONS:
        return "video", ext.lstrip(".") or "unknown"

    guessed, _ = mimetypes.guess_type(str(path))
    if guessed and guessed.startswith("image/"):
        return "image", guessed.split("/", 1)[1]
    if guessed and guessed.startswith("video/"):
        return "video", guessed.split("/", 1)[1]
    return None, ext.lstrip(".") or "unknown"


def file_id(path: Path, root: Path, root_key: str, stat: os.stat_result | None) -> str:
    rel = path.relative_to(root).as_posix()
    if stat is None:
        raw = f"{root_key}|{rel}"
    else:
        raw = f"{root_key}|{rel}|{stat.st_size}|{int(stat.st_mtime)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def scan_media(
    root_info: dict[str, str],
    ignore_prefixes: list[str],
    max_depth: int | None,
    changed_within_days: int | None,
    window_start: dt.datetime | None,
    window_end: dt.datetime | None,
) -> list[dict[str, Any]]:
    root = Path(root_info["path"]).expanduser().resolve()
    label = root_info.get("label") or root.name
    root_key = f"{label}|{root}"
    fast_scan = bool(root_info.get("fast_scan", False))
    cutoff_ts = None
    if changed_within_days is not None and changed_within_days > 0:
        cutoff_ts = dt.datetime.now().timestamp() - changed_within_days * 86400
    items: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)
        depth = len(current_dir.relative_to(root).parts)
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                d for d in dirnames if not any(d.startswith(prefix) for prefix in ignore_prefixes)
            ]
        for filename in filenames:
            if any(filename.startswith(prefix) for prefix in ignore_prefixes):
                continue
            path = current_dir / filename
            media_type, subtype = classify(path)
            if media_type is None:
                continue
            stat = None
            if not fast_scan:
                try:
                    stat = path.stat()
                except OSError:
                    continue
                if window_start is not None and stat.st_mtime < window_start.timestamp():
                    continue
                if window_end is not None and stat.st_mtime >= window_end.timestamp():
                    continue
                if cutoff_ts is not None and stat.st_mtime < cutoff_ts:
                    continue
            items.append(
                {
                    "id": file_id(path, root, root_key, stat),
                    "root_label": label,
                    "root": str(root),
                    "path": str(path),
                    "relative_path": path.relative_to(root).as_posix(),
                    "asset_group": path.parent.relative_to(root).as_posix(),
                    "media_type": media_type,
                    "subtype": subtype,
                    "extension": path.suffix.lower().lstrip(".") or "unknown",
                    "size_bytes": stat.st_size if stat else None,
                    "mtime": dt.datetime.fromtimestamp(
                        stat.st_mtime, tz=dt.datetime.now().astimezone().tzinfo
                    ).isoformat(timespec="seconds") if stat else None,
                }
            )
    return sorted(items, key=lambda row: (row["root_label"], row["relative_path"]))


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    groups_by_media_type: dict[str, set[str]] = {}
    groups_by_root: dict[str, set[str]] = {}
    summary: dict[str, Any] = {
        "total": len(items),
        "by_media_type": {},
        "by_subtype": {},
        "by_root": {},
        "asset_groups_total": 0,
        "asset_groups_by_media_type": {},
        "asset_groups_by_root": {},
    }
    for item in items:
        media_type = item["media_type"]
        subtype_key = f"{media_type}/{item['subtype']}"
        root_label = item.get("root_label", "未命名目录")
        group_key = f"{root_label}/{item.get('asset_group') or '.'}"
        summary["by_media_type"][media_type] = summary["by_media_type"].get(media_type, 0) + 1
        summary["by_subtype"][subtype_key] = summary["by_subtype"].get(subtype_key, 0) + 1
        summary["by_root"][root_label] = summary["by_root"].get(root_label, 0) + 1
        groups_by_media_type.setdefault(media_type, set()).add(group_key)
        groups_by_root.setdefault(root_label, set()).add(group_key)
    summary["asset_groups_total"] = len({group for groups in groups_by_media_type.values() for group in groups})
    summary["asset_groups_by_media_type"] = {
        key: len(value) for key, value in sorted(groups_by_media_type.items())
    }
    summary["asset_groups_by_root"] = {
        key: len(value) for key, value in sorted(groups_by_root.items())
    }
    return summary


def format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "大小未读取"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size_bytes} B"


def clean_direction_text(value: str) -> str:
    text = Path(value).stem
    text = re.sub(r"^\d{8}[-_\s]*", "", text)
    text = re.sub(r"^\d{4}[.\-]\d{1,2}[.\-]\d{1,2}[（(].*?[）)]\s*", "", text)
    text = re.sub(r"[-_\s]*图\s*[（(]\d+[）)]$", "", text)
    text = re.sub(r"[-_\s]*20\d{4}$", "", text)
    text = re.sub(r"[-_\s]*20\d{6}$", "", text)
    text = re.sub(r"[_]+", " / ", text)
    text = re.sub(r"\s+", " ", text).strip(" -_")
    return text or value


def compact_direction_parts(*parts: str | None) -> str:
    cleaned = [clean_direction_text(part) for part in parts if part]
    cleaned = [part for part in cleaned if part and part not in {"."}]
    return "-".join(cleaned) if cleaned else "未识别"


def normalize_region(value: str) -> str:
    cleaned = clean_direction_text(value).upper()
    if cleaned in {"HK", "香港", "港澳", "澳门", "MO"}:
        return "港澳"
    if cleaned in {"TW", "台湾"}:
        return "台湾"
    return clean_direction_text(value)


def display_direction_text(value: str) -> str:
    text = value.replace(" / ", "-")
    text = re.sub(r"（([^）]+)）", r"-\1", text)
    text = re.sub(r"\(([^)]+)\)", r"-\1", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def image_region_direction_from_name(name: str) -> tuple[str, str] | None:
    stem = Path(name).stem
    stem = re.sub(r"[-_\s]*图\s*[（(]\d+[）)]$", "", stem)
    parts = [part.strip() for part in stem.split("-") if part.strip()]
    if len(parts) >= 3 and re.fullmatch(r"20\d{6}", parts[0]):
        region_values = {"港澳", "台湾", "香港", "澳门"}
        for index, part in enumerate(parts[1:], start=1):
            if part in region_values and index > 1:
                return normalize_region(part), clean_direction_text(parts[index - 1])
        for index, part in enumerate(parts[1:], start=1):
            if part.upper() in {"HK", "TW", "MO"} and index > 1:
                return normalize_region(part), clean_direction_text(parts[index - 1])
    return None


def video_region_direction_from_name(name: str) -> tuple[str, str] | None:
    stem = Path(name).stem
    parts = [part.strip() for part in stem.split("_") if part.strip()]
    if len(parts) >= 4:
        region = parts[3]
        if region in {"繁体", "简体"} and len(parts) >= 5:
            region = parts[4]
        return normalize_region(region), compact_direction_parts(parts[1], parts[2])
    return None


def item_region_direction(item: dict[str, Any]) -> tuple[str, str]:
    filename = Path(item["relative_path"]).name
    if item["media_type"] == "video":
        parsed = video_region_direction_from_name(filename)
        if parsed:
            return parsed
        return "未识别地区", clean_direction_text(Path(item["relative_path"]).stem)

    parsed = image_region_direction_from_name(filename)
    if parsed:
        return parsed

    asset_group = item.get("asset_group") or ""
    parts = [part for part in Path(asset_group).parts if part not in {"", "."}]
    if not parts:
        return "未识别地区", clean_direction_text(Path(item["relative_path"]).stem)

    leaf = clean_direction_text(parts[-1])
    generic_leafs = {"台湾", "港澳", "香港", "澳门", "改（台湾）", "改(台湾)"}
    if leaf in generic_leafs and len(parts) >= 2:
        return normalize_region(leaf), clean_direction_text(parts[-2])
    return "未识别地区", leaf


def item_direction(item: dict[str, Any]) -> str:
    region, direction = item_region_direction(item)
    if region == "未识别地区":
        return direction
    return f"{region} / {direction}"


def summarize_directions_by_region(
    items: list[dict[str, Any]],
    media_type: str,
    region_limit: int = 4,
    direction_limit: int = 5,
    unit: str = "个",
) -> list[str]:
    grouped: dict[str, dict[str, int]] = {}
    for item in items:
        if item["media_type"] != media_type:
            continue
        region, direction = item_region_direction(item)
        grouped.setdefault(region, {})
        grouped[region][direction] = grouped[region].get(direction, 0) + 1
    if not grouped:
        return ["- 无"]

    def region_total(region_item: tuple[str, dict[str, int]]) -> int:
        return sum(region_item[1].values())

    lines: list[str] = []
    ranked_regions = sorted(grouped.items(), key=lambda row: (-region_total(row), row[0]))
    for region, direction_counts in ranked_regions[:region_limit]:
        total = sum(direction_counts.values())
        ranked_directions = sorted(direction_counts.items(), key=lambda row: (-row[1], row[0]))
        lines.append(f"- 地区：{region}（{total}{unit}）")
        for name, count in ranked_directions[:direction_limit]:
            lines.append(f"  - {display_direction_text(name)}（{count}{unit}）")
        remaining = len(ranked_directions) - direction_limit
        if remaining > 0:
            lines.append(f"  - 其他 {remaining} 类")
    remaining_regions = len(ranked_regions) - region_limit
    if remaining_regions > 0:
        lines.append(f"- 其他地区：{remaining_regions} 类")
    return lines


def report_date_label() -> str:
    return dt.datetime.now().astimezone().strftime("%Y-%m-%d")


def window_date_label(window_label: str) -> str:
    match = re.search(r"(20\d{2}-\d{2}-\d{2})\s*至\s*(20\d{2}-\d{2}-\d{2})", window_label)
    if match:
        return f"{match.group(1)} 至 {match.group(2)}"
    return window_label


def window_scope_label(window_label: str) -> str:
    return re.sub(r"（20\d{2}-\d{2}-\d{2}\s*至\s*20\d{2}-\d{2}-\d{2}）", "", window_label)


def format_markdown(
    title: str,
    roots: list[dict[str, str]],
    new_items: list[dict[str, Any]],
    current_items: list[dict[str, Any]],
    limit: int,
    window_label: str,
) -> str:
    new_summary = summarize(new_items)
    new_image_count = new_summary["by_media_type"].get("image", 0)
    new_video_count = new_summary["by_media_type"].get("video", 0)
    return "\n".join([
        f"## {title}",
        "",
        f"- 播报日期：{report_date_label()}",
        f"- 检索日期：{window_date_label(window_label)}",
        f"- 检索口径：{window_scope_label(window_label)}",
        f"- 检索结果：新增图片 {new_image_count} 张，新增视频 {new_video_count} 条",
        "",
        "### 图片新增方向",
        *summarize_directions_by_region(new_items, "image", unit="张"),
        "",
        "### 视频新增方向",
        *summarize_directions_by_region(new_items, "video", unit="条"),
    ])


def send_dingtalk_bot(
    robot_code: str,
    title: str,
    text: str,
    dry_run: bool,
    group: str | None,
    users: str | None,
) -> subprocess.CompletedProcess[str] | None:
    cmd = [
        "dws",
        "chat",
        "message",
        "send-by-bot",
        "--format",
        "json",
        "--robot-code",
        robot_code,
        "--title",
        title,
        "--text",
        text,
    ]
    if users:
        cmd.extend(["--users", users])
    if group:
        cmd.extend(["--group", group])
    if dry_run:
        print(json.dumps({"dry_run_command": hide_secret(cmd), "text": text}, ensure_ascii=False, indent=2))
        return None
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def resolve_group_id(group_id: str) -> str:
    cmd = [
        "dws",
        "chat",
        "group",
        "get-by-group-id",
        "--group-id",
        group_id,
        "--format",
        "json",
    ]
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout, file=sys.stdout)
        print(completed.stderr, file=sys.stderr)
        raise RuntimeError("failed to resolve DingTalk group_id; run dws auth login first if not authenticated")
    data = json.loads(completed.stdout)
    found = find_conversation_id(data)
    if not found:
        raise RuntimeError(f"could not find openConversationId in dws response: {completed.stdout}")
    return found


def find_conversation_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.replace("_", "").lower()
            if normalized in {"openconversationid", "conversationid"} and isinstance(item, str):
                return item
        for item in value.values():
            found = find_conversation_id(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_conversation_id(item)
            if found:
                return found
    return None


def hide_secret(cmd: list[str]) -> list[str]:
    safe = list(cmd)
    for index, part in enumerate(safe):
        if part == "--robot-code" and index + 1 < len(safe):
            safe[index + 1] = "***"
    return safe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a folder for new image/video files and notify DingTalk via dws bot."
    )
    parser.add_argument("--config", type=Path, help="Path to config JSON.")
    parser.add_argument("--root", type=Path, help="Shared-drive folder to scan.")
    parser.add_argument("--state", type=Path, help="State JSON path.")
    parser.add_argument(
        "--robot-code",
        help="DingTalk bot robotCode. Can also use DINGTALK_ROBOT_CODE.",
    )
    parser.add_argument("--group", help="Target openConversationId for group bot message.")
    parser.add_argument("--group-id", help="DingTalk numeric group id; resolved to openConversationId before sending.")
    parser.add_argument("--users", help="Comma-separated userIds for direct bot message.")
    parser.add_argument("--title", default="共享盘新增媒体播报", help="DingTalk message title.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum file rows shown in one message.")
    parser.add_argument("--output-limit", type=int, default=50, help="Maximum file rows printed to terminal JSON.")
    parser.add_argument("--ignore-prefix", action="append", default=[], help="Ignore files/folders with prefix.")
    parser.add_argument("--max-depth", type=int, help="Maximum folder depth to scan from each root.")
    parser.add_argument("--changed-within-days", type=int, help="Only include files modified within recent N days.")
    parser.add_argument("--report-schedule", default="none", choices=["none", "wed_fri"], help="Automatic report window.")
    parser.add_argument("--report-date", help="YYYY-MM-DD date used to calculate the automatic report window.")
    parser.add_argument("--window-start", help="Manual report window start date, YYYY-MM-DD.")
    parser.add_argument("--window-end", help="Manual report window end date, YYYY-MM-DD.")
    parser.add_argument("--init-only", action="store_true", help="Create/update baseline without sending.")
    parser.add_argument("--no-send-when-empty", action="store_true", help="Do not send if no new media.")
    parser.add_argument("--list-roots-only", action="store_true", help="Print expanded scan roots and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print result without sending.")
    return parser.parse_args()


def merge_config(args: argparse.Namespace) -> argparse.Namespace:
    config = load_json(args.config, {}) if args.config else {}
    defaults = parse_args_defaults()
    for key, value in config.items():
        attr = key.replace("-", "_")
        if hasattr(args, attr):
            current = getattr(args, attr)
            if current in (None, [], False) or (attr in defaults and current == defaults[attr]):
                setattr(args, attr, value)
    return args


def parse_args_defaults() -> dict[str, Any]:
    return {
        "title": "共享盘新增媒体播报",
        "limit": 50,
        "output_limit": 50,
        "report_schedule": "none",
    }


def normalize_roots(args: argparse.Namespace) -> list[dict[str, Any]]:
    config = load_json(args.config, {}) if args.config else {}
    roots = config.get("roots")
    if roots:
        normalized = []
        for index, root_info in enumerate(roots, start=1):
            if isinstance(root_info, str):
                path = root_info
                label = Path(root_info).name or f"目录{index}"
            else:
                path = root_info.get("path")
                label = root_info.get("label") or Path(path or "").name or f"目录{index}"
            if not path:
                raise ValueError(f"roots[{index}] is missing path")
            normalized.append(
                {
                    "label": label,
                    "path": str(Path(path).expanduser().resolve()),
                    "month_folder_patterns": root_info.get("month_folder_patterns", []) if isinstance(root_info, dict) else [],
                    "date_folder_prune": bool(root_info.get("date_folder_prune", False)) if isinstance(root_info, dict) else False,
                    "week_folder_prune": bool(root_info.get("week_folder_prune", False)) if isinstance(root_info, dict) else False,
                    "fast_scan": bool(root_info.get("fast_scan", False)) if isinstance(root_info, dict) else False,
                }
            )
        return normalized

    if args.root:
        path = str(args.root.expanduser().resolve())
        return [{"label": Path(path).name, "path": path}]

    raise ValueError("set --root or config roots")


def expand_roots_for_window(
    roots: list[dict[str, Any]],
    window_start: dt.datetime | None,
    window_end: dt.datetime | None,
) -> list[dict[str, str]]:
    expanded: list[dict[str, str]] = []
    months = month_starts_between(window_start, window_end)
    window_dates_list = dates_in_window(window_start, window_end)
    window_dates = set(window_dates_list)
    years = {value.year for value in window_dates_list}
    for root in roots:
        patterns = root.get("month_folder_patterns") or []
        if not patterns or not months:
            expanded.append({"label": root["label"], "path": root["path"]})
            continue
        for month_start in months:
            for pattern in patterns:
                folder_name = format_month_pattern(pattern, month_start)
                candidate = Path(root["path"]) / folder_name
                if candidate.exists() and candidate.is_dir():
                    month_window_dates = [
                        value for value in window_dates_list
                        if value.year == month_start.year and value.month == month_start.month
                    ]
                    expanded.extend(
                        expand_month_candidate(
                            root,
                            candidate,
                            folder_name,
                            set(month_window_dates),
                            {value.year for value in month_window_dates},
                            week_labels_for_dates(month_window_dates),
                        )
                    )
    return expanded


def expand_month_candidate(
    root: dict[str, Any],
    candidate: Path,
    folder_name: str,
    window_dates: set[dt.date],
    years: set[int],
    week_labels: set[str],
) -> list[dict[str, str]]:
    if root.get("date_folder_prune") or root.get("week_folder_prune"):
        matched = []
        try:
            children = [child for child in candidate.iterdir() if child.is_dir()]
        except OSError:
            children = []
        for child in children:
            name = child.name
            date_match = root.get("date_folder_prune") and name_matches_date_window(name, window_dates, years)
            week_match = root.get("week_folder_prune") and any(label in name for label in week_labels)
            if date_match or week_match:
                matched.append(
                    {
                        "label": f"{root['label']}/{folder_name}/{name}",
                        "path": str(child.resolve()),
                        "fast_scan": bool(root.get("fast_scan", False)),
                    }
                )
        return matched

    return [
        {
            "label": f"{root['label']}/{folder_name}",
            "path": str(candidate.resolve()),
            "fast_scan": bool(root.get("fast_scan", False)),
        }
    ]


def main() -> int:
    args = merge_config(parse_args())
    try:
        base_roots = normalize_roots(args)
        window_start, window_end, window_label = resolve_report_window(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    missing_base_roots = [
        root for root in base_roots
        if not Path(root["path"]).exists() or not Path(root["path"]).is_dir()
    ]
    if missing_base_roots:
        print("ERROR: these base roots do not exist or are not folders. Is the SMB share mounted?", file=sys.stderr)
        for root in missing_base_roots:
            print(f"- {root['label']}: {root['path']}", file=sys.stderr)
        return 2

    roots = expand_roots_for_window(base_roots, window_start, window_end)
    if not roots:
        print("ERROR: no scan roots matched the report window.", file=sys.stderr)
        print(f"- window: {window_label}", file=sys.stderr)
        for root in base_roots:
            print(f"- base root: {root['label']}: {root['path']}", file=sys.stderr)
        return 2

    missing_roots = [root for root in roots if not Path(root["path"]).exists() or not Path(root["path"]).is_dir()]
    if missing_roots:
        print("ERROR: these roots do not exist or are not folders:", file=sys.stderr)
        for root in missing_roots:
            print(f"- {root['label']}: {root['path']}", file=sys.stderr)
        return 2

    if args.list_roots_only:
        print(
            json.dumps(
                {
                    "base_roots": base_roots,
                    "scan_roots": roots,
                    "window": {
                        "label": window_label,
                        "start": window_start.isoformat() if window_start else None,
                        "end_exclusive": window_end.isoformat() if window_end else None,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    state_path = (
        Path(args.state).expanduser().resolve()
        if args.state
        else Path.cwd() / ".shared_drive_media_state.json"
    )
    robot_code = args.robot_code or os.environ.get("DINGTALK_ROBOT_CODE")
    ignore_prefixes = list(args.ignore_prefix or [])

    previous_state = load_json(state_path, {"files": {}})
    previous_files = previous_state.get("files", {})
    current_items = []
    for root_info in roots:
        current_items.extend(
            scan_media(
                root_info,
                ignore_prefixes,
                args.max_depth,
                args.changed_within_days,
                window_start,
                window_end,
            )
        )
    new_items = [item for item in current_items if item["id"] not in previous_files]
    current_state = {
        "base_roots": base_roots,
        "scan_roots": roots,
        "window": {
            "label": window_label,
            "start": window_start.isoformat() if window_start else None,
            "end_exclusive": window_end.isoformat() if window_end else None,
        },
        "updated_at": now_iso(),
        "files": {item["id"]: item for item in current_items},
    }

    result = {
        "base_roots": base_roots,
        "scan_roots": roots,
        "window": {
            "label": window_label,
            "start": window_start.isoformat() if window_start else None,
            "end_exclusive": window_end.isoformat() if window_end else None,
        },
        "state": str(state_path),
        "new_summary": summarize(new_items),
        "scanned_summary": summarize(current_items),
        "new_files": new_items[: args.output_limit],
        "new_files_truncated": max(len(new_items) - args.output_limit, 0),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.init_only:
        save_json(state_path, current_state)
        return 0

    if not new_items and args.no_send_when_empty:
        save_json(state_path, current_state)
        return 0

    text = format_markdown(args.title, roots, new_items, current_items, args.limit, window_label)

    target_count = len([value for value in (args.group, args.group_id, args.users) if value])
    if target_count != 1:
        print("ERROR: set exactly one target: --group, --group-id, or --users.", file=sys.stderr)
        return 2

    if not robot_code and not args.dry_run:
        print(
            "ERROR: DingTalk robot code is missing. Set --robot-code or DINGTALK_ROBOT_CODE.",
            file=sys.stderr,
        )
        return 2

    if robot_code:
        group = args.group
        if args.group_id:
            if args.dry_run:
                group = f"<resolved from group_id {args.group_id}>"
            else:
                try:
                    group = resolve_group_id(str(args.group_id))
                except RuntimeError as exc:
                    print(f"ERROR: {exc}", file=sys.stderr)
                    return 2
        completed = send_dingtalk_bot(
            robot_code=robot_code,
            title=args.title,
            text=text,
            dry_run=args.dry_run,
            group=group,
            users=args.users,
        )
        if completed and completed.returncode != 0:
            print(completed.stdout, file=sys.stdout)
            print(completed.stderr, file=sys.stderr)
            return completed.returncode
    else:
        print(text)

    if not args.dry_run:
        save_json(state_path, current_state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
