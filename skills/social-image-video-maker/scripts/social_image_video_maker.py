#!/usr/bin/env python3
"""Batch-create short social videos from image folders."""

from __future__ import annotations

import argparse
import datetime as dt
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
MUSIC_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
STICKER_EXTENSIONS = {".gif", ".png", ".webp"}
DEFAULT_MUSIC_DIR = Path("~/Desktop/常用音乐")
DEFAULT_STICKER_DIR = Path("~/Desktop/常用贴纸")


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.stem.lower())]


def parse_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", value.strip().lower())
    if not match:
        raise argparse.ArgumentTypeError("size must look like 800x960")
    width = int(match.group(1))
    height = int(match.group(2))
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("size values must be positive")
    return width, height


def parse_date(value: str | None) -> dt.date:
    if not value:
        return dt.date.today()
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must look like YYYY-MM-DD") from exc


def run_capture(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.strip()


def media_duration(path: Path) -> float:
    output = run_capture(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ]
    )
    return float(output)


def collect_files(
    folder: Path | None,
    extensions: set[str],
    recursive: bool = False,
    *,
    required: bool = True,
) -> list[Path]:
    if folder is None:
        return []
    if not folder.is_dir():
        if not required:
            print(f"WARNING: optional folder not found, skipping: {folder}", file=sys.stderr)
            return []
        raise FileNotFoundError(f"Folder not found: {folder}")
    iterator = folder.rglob("*") if recursive else folder.iterdir()
    files = [p for p in iterator if p.is_file() and p.suffix.lower() in extensions]
    return sorted(files, key=natural_key)


def choose_music(rng: random.Random, music_files: list[Path], duration: float) -> tuple[Path | None, float]:
    if not music_files:
        return None, 0.0
    music = rng.choice(music_files)
    music_duration = media_duration(music)
    max_start = max(0.0, music_duration - duration - 0.5)
    start = rng.uniform(0.0, max_start) if max_start > 0 else 0.0
    return music, start


def choose_sticker(rng: random.Random, sticker_files: list[Path]) -> Path | None:
    if not sticker_files:
        return None
    return rng.choice(sticker_files)


def output_name(prefix: str, date_compact: str, source: Path) -> str:
    return f"{prefix}-{date_compact}-原素材{source.stem}.mp4"


def build_filter(args: argparse.Namespace, has_sticker: bool, has_music: bool) -> str:
    width, height = args.size
    parts = [
        f"color=c={args.background}:s={width}x{height}:d={args.duration}:r={args.fps}[bg]",
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,format=rgba[fg]",
    ]

    if has_sticker:
        parts.append(f"[1:v]scale={args.sticker_width}:-1,format=rgba[st]")
        parts.append("[bg][fg]overlay=(W-w)/2:(H-h)/2[base]")
        parts.append(
            "[base][st]overlay="
            f"x='{args.sticker_x}+{args.sticker_float}*sin(t*2.2)':"
            f"y='{args.sticker_y}+{args.sticker_float}*cos(t*2.0)',"
            "format=yuv420p[v]",
        )
    else:
        parts.append("[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")

    if has_music:
        audio_index = 2 if has_sticker else 1
        parts.append(
            f"[{audio_index}:a]atrim=0:{args.duration},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={args.audio_fade_in},"
            f"afade=t=out:st={max(0, args.duration - args.audio_fade_out)}:d={args.audio_fade_out}[a]"
        )

    return ";".join(parts)


def make_video(
    image: Path,
    output: Path,
    music: Path | None,
    music_start: float,
    sticker: Path | None,
    args: argparse.Namespace,
) -> None:
    cmd = [
        "ffmpeg",
        "-y" if args.overwrite else "-n",
        "-loop",
        "1",
        "-framerate",
        str(args.fps),
        "-t",
        str(args.duration),
        "-i",
        str(image),
    ]

    if sticker:
        if sticker.suffix.lower() == ".gif":
            cmd.extend(["-stream_loop", "-1"])
        else:
            cmd.extend(["-loop", "1"])
        cmd.extend(["-t", str(args.duration), "-i", str(sticker)])

    if music:
        cmd.extend(["-ss", f"{music_start:.3f}", "-t", str(args.duration), "-i", str(music)])

    filter_complex = build_filter(args, has_sticker=sticker is not None, has_music=music is not None)
    cmd.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
        ]
    )
    if music:
        cmd.extend(["-map", "[a]"])
    cmd.extend(
        [
            "-r",
            str(args.fps),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
        ]
    )
    if music:
        cmd.extend(["-c:a", "aac", "-b:a", args.audio_bitrate])
    cmd.extend(["-shortest", "-movflags", "+faststart", str(output)])
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create short social videos from image folders.")
    parser.add_argument("--input-dir", required=True, type=Path, help="Folder containing source images.")
    parser.add_argument("--output-root", required=True, type=Path, help="Root folder for dated output folder.")
    parser.add_argument("--music-dir", type=Path, default=DEFAULT_MUSIC_DIR, help="Folder containing music files.")
    parser.add_argument("--sticker-dir", type=Path, default=DEFAULT_STICKER_DIR, help="Folder containing GIF/PNG/WebP stickers.")
    parser.add_argument("--date", type=parse_date, default=parse_date(None), help="Output date, YYYY-MM-DD.")
    parser.add_argument("--limit", type=int, help="Only process the first N images.")
    parser.add_argument("--recursive", action="store_true", help="Include nested image folders.")
    parser.add_argument("--duration", type=float, default=7.5, help="Video duration per image.")
    parser.add_argument("--fps", type=int, default=30, help="Output frame rate.")
    parser.add_argument("--size", type=parse_size, default=parse_size("800x960"), help="Output size.")
    parser.add_argument("--background", default="black", help="Canvas background color.")
    parser.add_argument("--sticker-width", type=int, default=360, help="Sticker canvas width after scaling.")
    parser.add_argument("--sticker-x", type=int, default=395, help="Sticker overlay x position.")
    parser.add_argument("--sticker-y", type=int, default=45, help="Sticker overlay y position.")
    parser.add_argument("--sticker-float", type=int, default=14, help="Sticker floating movement in pixels.")
    parser.add_argument("--audio-fade-in", type=float, default=0.25, help="Audio fade-in seconds.")
    parser.add_argument("--audio-fade-out", type=float, default=0.35, help="Audio fade-out seconds.")
    parser.add_argument("--audio-bitrate", default="128k", help="AAC audio bitrate.")
    parser.add_argument("--prefix", default="社媒-图片转视频", help="Output filename prefix.")
    parser.add_argument("--seed", type=int, default=20260625, help="Random seed.")
    parser.add_argument("--no-overwrite", dest="overwrite", action="store_false", help="Do not overwrite outputs.")
    parser.set_defaults(overwrite=True)
    args = parser.parse_args()

    if args.duration <= 0:
        parser.error("--duration must be greater than 0")
    if args.fps <= 0:
        parser.error("--fps must be greater than 0")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be greater than 0")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        parser.error("ffmpeg and ffprobe are required. Install with: brew install ffmpeg")
    return args


def main() -> int:
    args = parse_args()
    images = collect_files(args.input_dir.expanduser(), IMAGE_EXTENSIONS, recursive=args.recursive)
    if args.limit:
        images = images[: args.limit]
    if not images:
        print(f"ERROR: no supported images found in {args.input_dir}", file=sys.stderr)
        return 2

    music_files = collect_files(args.music_dir.expanduser(), MUSIC_EXTENSIONS, required=False) if args.music_dir else []
    sticker_files = collect_files(args.sticker_dir.expanduser(), STICKER_EXTENSIONS, required=False) if args.sticker_dir else []

    output_dir = args.output_root.expanduser() / args.date.strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    date_compact = args.date.strftime("%Y%m%d")
    rng = random.Random(args.seed)

    for index, image in enumerate(images, start=1):
        music, music_start = choose_music(rng, music_files, args.duration)
        sticker = choose_sticker(rng, sticker_files)
        output = output_dir / output_name(args.prefix, date_compact, image)
        print(f"[{index}/{len(images)}] {image.name} -> {output.name}")
        if music:
            print(f"  music: {music.name} @ {music_start:.1f}s")
        if sticker:
            print(f"  sticker: {sticker.name}")
        make_video(image, output, music, music_start, sticker, args)

    print(f"\nCreated {len(images)} video(s) in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
