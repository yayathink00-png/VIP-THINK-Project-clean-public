---
name: shared-drive-media-report
description: Scan a mounted shared drive for newly added image/video materials and send a concise DingTalk content-bot report. Use when the user asks to run, test, adjust, schedule, or troubleshoot a shared-drive new-material broadcast for image/video asset folders, DingTalk DWS content robots, or recurring “新增素材播报” workflows.
---

# Shared Drive Media Report

## Purpose

Use this skill to operate a shared-drive material scanner and DingTalk content-bot broadcaster.

The bundled script scans mounted SMB folders, counts image/video files for a configured reporting window, groups image directions by region and direction, groups video directions by language/region and direction, and sends Markdown via `dws chat message send-by-bot`.

## Files

- Script: `scripts/shared_drive_media_monitor.py`
- Example config: `scripts/config.example.json`

Do not invent robot codes, group IDs, paths, or command flags. Inspect the local config and DWS help when unsure.

## Setup

1. Copy `scripts/config.example.json` to a local private config file such as `scripts/config.local.json`.
2. Fill in the mounted shared-drive roots, DingTalk `robot_code`, and either `group_id`, `group`, or `users`.
3. Keep real tokens, webhook URLs, robot codes, and group IDs out of GitHub.

The script expects the SMB share to be mounted before scanning.

## Workflow

Run a dry-run first unless the user explicitly asks to send immediately:

```bash
python3 -B scripts/shared_drive_media_monitor.py --config scripts/config.local.json --dry-run
```

Check the dry-run text:

- title should match the configured report title
- message should contain the top summary, `图片新增方向`, and `视频新增方向`
- no extra debug sections should be present in the DingTalk text

Send only after confirmation or when the user clearly asks to send:

```bash
python3 -B scripts/shared_drive_media_monitor.py --config scripts/config.local.json
```

Use escalated execution when needed because sending uses local DWS login and network access.

## Manual Date Windows

Use manual dates for testing or backfills:

```bash
python3 -B scripts/shared_drive_media_monitor.py --config scripts/config.local.json --window-start 2026-06-29 --window-end 2026-07-01 --dry-run
```

Without manual dates, `wed_fri` only runs on Wednesday or Friday.

## Report Format

Keep the message concise:

```markdown
## 新增素材播报

- 播报日期：YYYY-MM-DD
- 检索日期：YYYY-MM-DD 至 YYYY-MM-DD
- 检索口径：本周周一至周三
- 检索结果：新增图片 X 张，新增视频 Y 条

### 图片新增方向
- 地区：港澳（379张）
  - 卖点设计-幼小衔接（45张）

### 视频新增方向
- 地区：粤语（1条）
  - 学习效果与成果类-速算技巧（1条）
```

Current parsing conventions:

- `HK`, `香港`, `澳门`, and `MO` normalize to `港澳`
- `TW` and `台湾` normalize to `台湾`
- Image filenames are parsed by finding a region token and using the preceding token as direction
- Video filenames are parsed from underscore fields; if the fourth field is `繁体` or `简体`, use the next field as language/region

## Common Failures

- `base root does not exist`: shared drive is not mounted or the configured root is wrong.
- `wed_fri schedule only runs on Wednesday or Friday`: use `--window-start` and `--window-end` for manual tests.
- `robotCode对应的机器人模板不存在`: wrong robot code for the target group; ask for the group’s usable content-bot `robot_code`.
- `无效的会话`: a numeric group id was passed as `--group`; use `group_id` so the script resolves `openConversationId`.
- DWS auth errors: run `dws auth login` outside the script, then retry.

## Safety

Do not use arbitrary webhook URLs for this workflow unless the user explicitly changes the requirement and approves the data exposure. The default production path is DWS content-bot sending, not webhook sending.
