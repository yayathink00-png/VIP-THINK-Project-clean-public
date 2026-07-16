#!/usr/bin/env python3
"""Render brand-consistent Xiaohongshu carousel PNGs from daily loop drafts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    raise RuntimeError("No Chinese-capable font found for image rendering")


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        if draw.textbbox((0, 0), trial, font=font)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines or [""]


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont, color: str, width: int, spacing: int = 18) -> int:
    x, y = xy
    for line in wrap_text(draw, text, font, width):
        draw.text((x, y), line, fill=color, font=font)
        box = draw.textbbox((x, y), line, font=font)
        y = box[3] + spacing
    return y


def fitted_lines(draw: ImageDraw.ImageDraw, text: str, start_size: int, min_size: int, width: int) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Shrink cover copy until a final line cannot be stranded by itself."""
    for size in range(start_size, min_size - 1, -4):
        font = load_font(size)
        lines = wrap_text(draw, text, font, width)
        if len(lines[-1]) >= 3 or len(lines) == 1:
            return font, lines
    font = load_font(min_size)
    return font, wrap_text(draw, text, font, width)


def draw_lines(draw: ImageDraw.ImageDraw, xy: tuple[int, int], lines: list[str], font: ImageFont.FreeTypeFont, color: str, spacing: int) -> int:
    x, y = xy
    for line in lines:
        draw.text((x, y), line, fill=color, font=font)
        y = draw.textbbox((x, y), line, font=font)[3] + spacing
    return y


def asset_paths(asset_index: dict[str, Any], source_id: str) -> list[Path]:
    return [Path(item["path"]) for item in asset_index.get("items", []) if item.get("source_id") == source_id and Path(item["path"]).exists()]


def choose_asset(asset_index: dict[str, Any], source_id: str, key: str, marker: str = "") -> Path | None:
    options = asset_paths(asset_index, source_id)
    if marker:
        marked = [path for path in options if marker in path.name]
        if marked:
            options = marked
    if not options:
        return None
    position = int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % len(options)
    return options[position]


def paste_contain(canvas: Image.Image, path: Path | None, box: tuple[int, int, int, int]) -> None:
    if path is None:
        return
    try:
        with Image.open(path) as raw:
            image = raw.convert("RGBA")
            image.thumbnail((box[2], box[3]), Image.Resampling.LANCZOS)
            x = box[0] + max((box[2] - image.width) // 2, 0)
            y = box[1] + max((box[3] - image.height) // 2, 0)
            canvas.alpha_composite(image, (x, y))
    except OSError:
        return


def logo_badge(canvas: Image.Image, logo: Path | None, dark: bool, width: int, height: int) -> None:
    if logo is None:
        return
    badge_w, badge_h = 270, 110
    x, y = width - badge_w - 56, height - badge_h - 56
    draw = ImageDraw.Draw(canvas)
    if not dark:
        draw.rounded_rectangle((x, y, x + badge_w, y + badge_h), radius=26, fill="#ffffff")
    paste_contain(canvas, logo, (x + 24, y + 20, badge_w - 48, badge_h - 40))


def cover_page(draft: dict[str, Any], visual: dict[str, Any], asset_index: dict[str, Any]) -> Image.Image:
    canvas_info = visual["canvas"]
    colors = visual["colors"]
    width, height = canvas_info["xiaohongshu_width"], canvas_info["xiaohongshu_height"]
    canvas = Image.new("RGBA", (width, height), colors["primary_green"])
    draw = ImageDraw.Draw(canvas)
    eyebrow_font = load_font(38)
    white_logo = choose_asset(asset_index, "vipthink_logo", draft["content_id"], "白彩")
    ip = choose_asset(asset_index, "vipthink_ip", draft["content_id"])

    draw.rounded_rectangle((70, 98, 342, 166), radius=34, fill=colors["accent_yellow"])
    draw.text((104, 110), "VIPTHINK 思维小课", fill=colors["text_black"], font=eyebrow_font)
    title_font, title_lines = fitted_lines(draw, draft["cover_text"], 112, 76, 1010)
    draw_lines(draw, (76, 320), title_lines, title_font, "#ffffff", 24)
    support_font, support_lines = fitted_lines(draw, draft["title_options"][0], 52, 38, 1010)
    draw_lines(draw, (80, 760), support_lines, support_font, "#ffffff", 16)
    draw.rounded_rectangle((76, 1370, 620, 1458), radius=44, fill="#ffffff")
    draw.text((112, 1392), "把复杂问题拆成孩子能做到的一步", fill=colors["text_black"], font=eyebrow_font)
    paste_contain(canvas, ip, (690, 960, 470, 530))
    logo_badge(canvas, white_logo, True, width, height)
    return canvas


def content_page(draft: dict[str, Any], page_number: int, visual: dict[str, Any], asset_index: dict[str, Any]) -> Image.Image:
    canvas_info = visual["canvas"]
    colors = visual["colors"]
    width, height = canvas_info["xiaohongshu_width"], canvas_info["xiaohongshu_height"]
    background = colors["background_gray"] if page_number % 2 else "#ffffff"
    canvas = Image.new("RGBA", (width, height), background)
    draw = ImageDraw.Draw(canvas)
    label_font = load_font(36)
    heading_font = load_font(80)
    small_font = load_font(42)
    full_logo = choose_asset(asset_index, "vipthink_logo", draft["content_id"], "全彩")
    ip = choose_asset(asset_index, "vipthink_ip", draft["content_id"])
    text = draft["carousel_pages"][page_number - 1]

    draw.rectangle((0, 0, 28, height), fill=colors["primary_green"])
    draw.rounded_rectangle((78, 92, 336, 158), radius=32, fill=colors["secondary_green"])
    draw.text((108, 102), f"{draft['content_type']}  {page_number}/7", fill=colors["text_black"], font=label_font)
    if page_number == 7:
        canvas = Image.new("RGBA", (width, height), colors["primary_green"])
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((78, 94, 378, 164), radius=35, fill=colors["accent_yellow"])
        draw.text((112, 105), "保存起来慢慢看", fill=colors["text_black"], font=label_font)
        draw_wrapped(draw, (84, 385), text, heading_font, "#ffffff", 850, spacing=30)
        draw_wrapped(draw, (88, 1040), "先在家试一次，观察孩子卡在哪一步。", small_font, "#ffffff", 780, spacing=18)
        paste_contain(canvas, ip, (720, 1060, 420, 430))
        logo_badge(canvas, choose_asset(asset_index, "vipthink_logo", draft["content_id"], "白彩"), True, width, height)
        return canvas

    draw_wrapped(draw, (82, 338), text, heading_font, colors["text_black"], 890, spacing=28)
    draw.rounded_rectangle((84, 1112, 1090, 1132), radius=10, fill=colors["accent_yellow"])
    draw_wrapped(draw, (84, 1194), "先理解，再表达，最后练习。", small_font, colors["primary_green"], 720, spacing=14)
    paste_contain(canvas, ip, (760, 1200, 330, 330))
    logo_badge(canvas, full_logo, False, width, height)
    return canvas


def ranked_drafts(drafts: list[dict[str, Any]], publish_count: int) -> list[dict[str, Any]]:
    eligible = [draft for draft in drafts if draft.get("publish_recommendation") != "reject"]
    ordered = sorted(eligible, key=lambda item: item.get("overall_score", 0), reverse=True)
    selected: list[dict[str, Any]] = []
    types: set[str] = set()
    for draft in ordered:
        if draft.get("content_type") in types:
            continue
        selected.append(draft)
        types.add(str(draft.get("content_type")))
        if len(selected) >= publish_count:
            return selected
    for draft in ordered:
        if draft not in selected:
            selected.append(draft)
        if len(selected) >= publish_count:
            break
    return selected


def render_drafts(drafts: list[dict[str, Any]], visual: dict[str, Any], asset_index: dict[str, Any], output_root: Path, publish_count: int) -> dict[str, list[str]]:
    output_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, list[str]] = {}
    for draft in ranked_drafts(drafts, publish_count):
        folder = output_root / draft["content_id"]
        folder.mkdir(parents=True, exist_ok=True)
        images = [cover_page(draft, visual, asset_index)]
        images.extend(content_page(draft, number, visual, asset_index) for number in range(2, 8))
        paths: list[str] = []
        for number, image in enumerate(images, start=1):
            path = folder / f"page_{number:02d}.png"
            image.convert("RGB").save(path, format="PNG", optimize=True)
            paths.append(str(path))
        result[draft["content_id"]] = paths
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Xiaohongshu PNG slides from a daily draft JSON file.")
    parser.add_argument("--drafts", required=True, help="Path to runs/YYYY-MM-DD/drafts.json")
    parser.add_argument("--visual", default="inputs/brand/visual_guidelines.json")
    parser.add_argument("--asset-index", default="memory/asset_index.json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--publish-count", type=int, default=3)
    args = parser.parse_args()
    with Path(args.drafts).open("r", encoding="utf-8") as handle:
        drafts = json.load(handle).get("drafts", [])
    with Path(args.visual).open("r", encoding="utf-8") as handle:
        visual = json.load(handle)
    with Path(args.asset_index).open("r", encoding="utf-8") as handle:
        asset_index = json.load(handle)
    result = render_drafts(drafts, visual, asset_index, Path(args.out), args.publish_count)
    print(json.dumps({"rendered_drafts": len(result), "output": args.out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
