#!/usr/bin/env python3
import datetime as dt
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = ROOT / "generated" / "image-videos"
SOCIAL_VIDEO_SCRIPT = Path("/Users/yangyi/Documents/Codex/2026-06-25/ze/work/social-image-video-maker/scripts/social_image_video_maker.py")
HOMEBREW_BIN = "/opt/homebrew/bin"


def tool_env():
    env = os.environ.copy()
    env["PATH"] = HOMEBREW_BIN + ":" + env.get("PATH", "")
    return env


def ffmpeg_available():
    env = tool_env()
    return shutil.which("ffmpeg", path=env["PATH"]) is not None and shutil.which("ffprobe", path=env["PATH"]) is not None


def save_uploaded_image(filename, data):
    folder = ROOT / "generated" / "uploaded-images" / dt.datetime.now().strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in ".-_" else "-" for ch in Path(filename).name)
    path = folder / safe_name
    if path.exists():
        path = folder / f"{path.stem}-{int(dt.datetime.now().timestamp())}{path.suffix}"
    path.write_bytes(data)
    return path


def download_image(image_url):
    suffix = Path(image_url.split("?", 1)[0]).suffix.lower() or ".jpg"
    folder = ROOT / "generated" / "downloaded-images" / dt.datetime.now().strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"image-{int(dt.datetime.now().timestamp())}{suffix}"
    req = urllib.request.Request(image_url, headers={"User-Agent": "CodexSocialPublisher/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        path.write_bytes(response.read())
    return path


def make_video_from_image(image_path, *, size="720x1280", duration=7.5, title_prefix="youtube"):
    if not SOCIAL_VIDEO_SCRIPT.is_file():
        raise FileNotFoundError(f"social video script not found: {SOCIAL_VIDEO_SCRIPT}")
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg/ffprobe not found. Expected /opt/homebrew/bin/ffmpeg and ffprobe.")
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    image_path = Path(image_path)
    with tempfile.TemporaryDirectory(prefix="codex-image-video-") as temp_dir:
        input_dir = Path(temp_dir) / "input"
        input_dir.mkdir()
        temp_image = input_dir / image_path.name
        shutil.copy2(image_path, temp_image)
        cmd = [
            "python3",
            str(SOCIAL_VIDEO_SCRIPT),
            "--input-dir",
            str(input_dir),
            "--output-root",
            str(GENERATED_ROOT),
            "--size",
            size,
            "--duration",
            str(duration),
            "--prefix",
            title_prefix,
        ]
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=tool_env())
        if result.returncode != 0:
            raise RuntimeError("image-to-video failed\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr)
    outputs = sorted(GENERATED_ROOT.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not outputs:
        raise RuntimeError("image-to-video finished but no mp4 output found")
    return outputs[0]
