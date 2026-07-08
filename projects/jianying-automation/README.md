# JianYing Automation Workflow

This folder contains a tested JianYing draft-generation workflow for assembling AI video clips with review subtitles.

## Current Capability

- Reads a storyboard Excel file.
- Uses local vertical video clips.
- Creates a JianYing draft.
- Adds subtitle tracks.
- Supports an enhanced mode with keyword highlights and a final CTA overlay.
- Writes an `.srt` file for review.

## Tested Drafts

Generated locally:

```text
VIPTHINK_SUB_V3
VIPTHINK_SUB_V4_SMALL
```

The latest smaller-subtitle test is:

```text
VIPTHINK_SUB_V4_SMALL
```

## Run Command

From `/Users/yangyi/Documents/自动化剪辑`:

```bash
.venv/bin/python scripts/create_caiyong_subtitled_draft.py \
  --enhanced \
  --project VIPTHINK_SUB_V4_SMALL \
  --srt /Users/yangyi/Documents/自动化剪辑/output/VIPTHINK_SUB_V4_SMALL.srt
```

## Default Inputs

```text
/Users/yangyi/Downloads/caiyong
/Users/yangyi/Downloads/7_AI视频真人_台湾腔_分镜表.xlsx
```

Default clip order:

```text
1.mp4, 2.1.mp4, 3.mp4, 4.mp4, 5.mp4, 6.mp4
```

## Notes

- Source videos are not committed.
- The local third-party `jianying-editor-skill` runtime is not committed.
- If JianYing prompts to relink media, select `/Users/yangyi/Downloads/caiyong`.
