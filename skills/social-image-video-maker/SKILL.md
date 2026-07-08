---
name: social-image-video-maker
description: Create short social-media videos from folders of static images with optional random background music and animated sticker overlays. Use when the user asks to convert image folders, Xiaohongshu assets, education ad creatives, posters, covers, or social-media graphics into MP4 videos; when they mention "图片转视频", "社媒短视频", "配乐", "动态贴纸", "800x960", "按文件夹批量生成", or filename/date-based output automation.
---

# Social Image Video Maker

## Quick Start

Use `scripts/social_image_video_maker.py` for production work. Prefer this script over hand-written `ffmpeg` commands because it handles sorting, naming, date folders, random music, looping GIF stickers, and validation consistently.

```bash
python3 /path/to/social-image-video-maker/scripts/social_image_video_maker.py \
  --input-dir "/path/to/images" \
  --output-root "/path/to/output"
```

Default behavior:
- Output format: MP4, `800x960`, 30 fps
- Duration: `7.5` seconds per image
- Canvas: black background, no blurred fill
- Color: do not adjust image brightness, saturation, or tone
- Image placement: preserve original aspect ratio and center on canvas
- Stickers: randomly choose GIF/PNG/WebP, loop animated GIFs, place in the top safe area
- Music: randomly choose MP3/WAV/M4A/AAC, trim a random segment, add short fade in/out
- Naming: `社媒-图片转视频-YYYYMMDD-原素材<source-stem>.mp4`
- Folder: create an output subfolder named `YYYY-MM-DD`

Recorded local defaults:
- Music folder: `~/Desktop/常用音乐`
- Sticker folder: `~/Desktop/常用贴纸`

If these folders exist, the script uses them automatically. If they do not exist on a colleague's machine, pass `--music-dir` and `--sticker-dir` explicitly or run without music/stickers.

## Workflow

1. Inspect the input folder and count supported image files.
2. Confirm music and sticker folders exist when the user requests music/stickers.
3. Use non-recursive mode by default unless the user explicitly asks to include subfolders.
4. Generate a 3-item sample first when the user asks to test the look.
5. Ask for confirmation before scaling to all images if visual style is still being tuned.
6. After generation, verify at least one output with `ffprobe` for size, duration, and audio.

## Common Commands

Generate the first 3 images only:

```bash
python3 scripts/social_image_video_maker.py \
  --input-dir "/path/to/images" \
  --output-root "/path/to/output" \
  --limit 3
```

Generate all images in the current folder:

```bash
python3 scripts/social_image_video_maker.py \
  --input-dir "/path/to/images" \
  --output-root "/path/to/output"
```

Override music and sticker folders:

```bash
python3 scripts/social_image_video_maker.py \
  --input-dir "/path/to/images" \
  --output-root "/path/to/output" \
  --music-dir "/path/to/music" \
  --sticker-dir "/path/to/stickers"
```

Use a larger or smaller sticker:

```bash
--sticker-width 520
```

Use a different output size:

```bash
--size 720x1280
```

Change video duration:

```bash
--duration 8
```

Use the current date automatically, or force a date:

```bash
--date 2026-06-25
```

Include nested folders:

```bash
--recursive
```

## Style Rules

- Do not use blurred background fill unless the user explicitly requests it.
- Do not apply brightness, saturation, contrast, or color grading unless requested.
- Keep the original image fully visible.
- Put stickers in black/top safe space first; avoid covering titles, question text, answer areas, CTAs, and QR codes.
- If the source image nearly fills the canvas, reduce sticker size or move the sticker to an existing blank corner.

## Validation

Check one output file:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 "/path/to/output.mp4"
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,channels,duration -of csv=p=0 "/path/to/output.mp4"
```

Expected result:
- Video: `800,960,7.500000` unless custom options were used
- Audio: `aac,2,7.500000` when music was provided

## Failure Handling

If `ffmpeg` or `ffprobe` is missing, install FFmpeg:

```bash
brew install ffmpeg
```

If the sticker looks too small, increase `--sticker-width`. GIF files often include transparent padding, so visible sticker size can be much smaller than the GIF canvas.

If music is too repetitive, randomize with more source tracks or run again with a different `--seed`.
