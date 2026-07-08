#!/usr/bin/env python3
"""Create a JianYing draft from the caiyong clips with review subtitles."""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "jianying-editor-skill-main"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from jy_wrapper import JyProject  # noqa: E402
import pyJianYingDraft as draft  # noqa: E402


NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "s":
        value = cell.find(f"{NS_MAIN}v")
        if value is None or value.text is None:
            return ""
        return shared_strings[int(value.text)]
    if cell_type == "inlineStr":
        text_node = cell.find(f".//{NS_MAIN}t")
        return "" if text_node is None or text_node.text is None else text_node.text
    value = cell.find(f"{NS_MAIN}v")
    return "" if value is None or value.text is None else value.text


def read_xlsx_first_sheet(path: Path) -> list[dict[str, str]]:
    """Read a small xlsx sheet using stdlib only."""
    with zipfile.ZipFile(path) as zf:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in ss_root.findall(f"{NS_MAIN}si"):
                parts = [node.text or "" for node in si.findall(f".//{NS_MAIN}t")]
                shared_strings.append("".join(parts))

        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        first_sheet = workbook.find(f".//{NS_MAIN}sheet")
        if first_sheet is None:
            raise RuntimeError("No worksheet found in workbook")
        rel_id = first_sheet.attrib[f"{NS_REL}id"]

        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels.findall(f"{NS_PKG_REL}Relationship"):
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib["Target"]
                break
        if not target:
            raise RuntimeError(f"Worksheet relationship not found: {rel_id}")
        target = target.lstrip("/")
        sheet_path = target if target.startswith("xl/") else "xl/" + target
        sheet = ET.fromstring(zf.read(sheet_path))

    rows: list[list[str]] = []
    for row in sheet.findall(f".//{NS_MAIN}sheetData/{NS_MAIN}row"):
        values: list[str] = []
        for cell in row.findall(f"{NS_MAIN}c"):
            values.append(_cell_text(cell, shared_strings))
        rows.append(values)

    if not rows:
        return []
    headers = rows[0]
    records = []
    for row in rows[1:]:
        if not any(str(v).strip() for v in row):
            continue
        records.append({headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))})
    return records


def parse_timecode(value: str) -> float:
    hh, mm, rest = value.split(":")
    return int(hh) * 3600 + int(mm) * 60 + float(rest)


def parse_range(value: str) -> tuple[float, float]:
    start, end = value.split("-")
    return parse_timecode(start), parse_timecode(end)


def fmt_srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    h, rem = divmod(millis, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def split_subtitle_text(text: str) -> list[str]:
    text = re.sub(r"\s+", "", str(text).strip())
    chunks = [part for part in re.split(r"(?<=[。！？!？，,])", text) if part]
    merged: list[str] = []
    pending = ""
    for chunk in chunks:
        if not pending:
            pending = chunk
        elif len(pending) + len(chunk) <= 24:
            pending += chunk
        else:
            merged.append(pending)
            pending = chunk
    if pending:
        merged.append(pending)
    return merged or [text]


def distribute_subtitles(text: str, start: float, end: float) -> list[tuple[float, float, str]]:
    chunks = split_subtitle_text(text)
    total_weight = sum(max(len(c), 6) for c in chunks)
    duration = end - start
    cursor = start
    result = []
    for idx, chunk in enumerate(chunks):
        if idx == len(chunks) - 1:
            chunk_end = end
        else:
            chunk_dur = duration * max(len(chunk), 6) / total_weight
            chunk_end = cursor + max(0.9, chunk_dur)
            chunk_end = min(chunk_end, end - 0.25 * (len(chunks) - idx - 1))
        result.append((cursor, chunk_end, chunk))
        cursor = chunk_end
    return result


def write_srt(items: list[tuple[float, float, str]], path: Path) -> None:
    blocks = []
    for idx, (start, end, text) in enumerate(items, 1):
        blocks.append(f"{idx}\n{fmt_srt_time(start)} --> {fmt_srt_time(end)}\n{text}\n")
    path.write_text("\n".join(blocks), encoding="utf-8")


def highlight_specs(text: str, base_size: float) -> list[dict]:
    highlight_size = base_size + 0.25
    specs = []
    keyword_groups = [
        (["VIPTHINK", "VIP THINK"], (1.0, 0.82, 0.18), highlight_size),
        (["数感", "思维", "逻辑", "理解能力", "专注力"], (0.25, 0.86, 1.0), highlight_size),
        (["半个小时", "二十种", "直播课", "报名"], (1.0, 0.48, 0.18), highlight_size),
        (["凑十法", "破十法", "速算技巧"], (0.55, 1.0, 0.48), highlight_size),
    ]
    for words, color, size in keyword_groups:
        for word in words:
            if word in text:
                specs.append({"word": word, "color": color, "size": size, "bold": True})
    return specs


def add_subtitle(project: JyProject, text: str, sub_start: float, sub_end: float, args: argparse.Namespace) -> None:
    subtitle_kwargs = {
        "start_time": f"{sub_start:.3f}s",
        "duration": f"{sub_end - sub_start:.3f}s",
        "track_name": "Subtitles",
        "style": draft.TextStyle(
            size=args.subtitle_size,
            bold=True,
            color=(1.0, 1.0, 1.0),
            align=1,
            auto_wrapping=True,
            max_line_width=0.92,
        ),
        "border": draft.TextBorder(color=(0.0, 0.0, 0.0), alpha=1.0, width=38.0),
        "clip_settings": draft.ClipSettings(transform_y=-0.82),
    }
    if args.enhanced:
        specs = highlight_specs(text, args.subtitle_size)
        if specs:
            project.add_rich_text(text, specs, **subtitle_kwargs)
            return
    project.add_text_simple(text, **subtitle_kwargs)


def add_enhanced_cta(project: JyProject) -> None:
    project.add_text_simple(
        "报名送一堂思维直播课",
        start_time="49.530s",
        duration="4.050s",
        track_name="CTA",
        style=draft.TextStyle(
            size=1.45,
            bold=True,
            color=(1.0, 0.86, 0.24),
            align=1,
            auto_wrapping=True,
            max_line_width=0.82,
        ),
        border=draft.TextBorder(color=(0.0, 0.0, 0.0), alpha=1.0, width=30.0),
        background=draft.TextBackground(
            color="#1F2933",
            alpha=0.72,
            round_radius=0.18,
            height=0.08,
            width=0.62,
            horizontal_offset=0.5,
            vertical_offset=0.68,
        ),
        clip_settings=draft.ClipSettings(transform_y=-0.50),
        anim_in="向上滑动",
    )


def build_draft(args: argparse.Namespace) -> None:
    excel_path = Path(args.excel)
    clips_dir = Path(args.clips_dir)
    records = read_xlsx_first_sheet(excel_path)
    if len(records) != 6:
        raise RuntimeError(f"Expected 6 storyboard rows, got {len(records)}")

    video_names = ["1.mp4", args.second_clip, "3.mp4", "4.mp4", "5.mp4", "6.mp4"]
    video_paths = [clips_dir / name for name in video_names]
    missing = [str(path) for path in video_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing video files: " + ", ".join(missing))

    project = JyProject(project_name=args.project, width=720, height=1280, overwrite=True)

    subtitle_items: list[tuple[float, float, str]] = []
    last_subtitle_end = -1.0
    for record, video_path in zip(records, video_paths):
        start, end = parse_range(record["时间段 (Time)"])
        duration = end - start
        project.add_media_safe(
            str(video_path),
            start_time=f"{start:.3f}s",
            duration=f"{duration:.3f}s",
            track_name="VideoTrack",
        )

        for sub_start, sub_end, text in distribute_subtitles(
            record["原视频完整台词（按字幕拆解）"], start, end
        ):
            sub_start = max(sub_start, last_subtitle_end + 0.03)
            if sub_end <= sub_start:
                sub_end = sub_start + 0.5
            subtitle_items.append((sub_start, sub_end, text))
            add_subtitle(project, text, sub_start, sub_end, args)
            last_subtitle_end = sub_end

    if args.enhanced:
        add_enhanced_cta(project)

    result = project.save()
    srt_path = Path(args.srt)
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    write_srt(subtitle_items, srt_path)

    print("Draft generated")
    print(f"Project: {args.project}")
    print(f"Draft path: {result['draft_path']}")
    print(f"SRT path: {srt_path}")
    print(f"Clips: {', '.join(video_names)}")
    print(f"Subtitle segments: {len(subtitle_items)}")
    print(f"Enhanced: {args.enhanced}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create caiyong subtitled JianYing draft")
    parser.add_argument("--project", default="VIPTHINK_TW_AI真人口播_带字幕_v1")
    parser.add_argument("--second-clip", default="2.1.mp4", choices=["2.mp4", "2.1.mp4"])
    parser.add_argument("--clips-dir", default="/Users/yangyi/Downloads/caiyong")
    parser.add_argument("--excel", default="/Users/yangyi/Downloads/7_AI视频真人_台湾腔_分镜表.xlsx")
    parser.add_argument("--srt", default=str(ROOT / "output" / "VIPTHINK_TW_AI真人口播_带字幕_v1.srt"))
    parser.add_argument("--subtitle-size", type=float, default=0.95)
    parser.add_argument("--enhanced", action="store_true", help="Add keyword highlights and final CTA overlay")
    args = parser.parse_args()
    build_draft(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
