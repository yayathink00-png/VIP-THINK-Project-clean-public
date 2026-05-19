# VIP THINK Automation Project Portfolio

This repository is the clean, leadership-facing portfolio for VIP THINK automation work.

It keeps the project structure, work scope, delivery evidence, and governance boundary visible, while excluding raw data, exports, generated media, private prompts, platform resource identifiers, cookies, session files, and secrets.

## Executive Summary

This portfolio summarizes four automation workstreams completed or advanced for VIP THINK. The goal is not to dump raw working files into GitHub. The goal is to show what was built, what business problem it solves, what has already been validated, and which materials are intentionally kept private.

| Project | What Was Built | Business Value |
| --- | --- | --- |
| [Audio BI Transcription](./projects/audio-bi-transcription/) | BI 导出、录音下载、Whisper 转写、飞书同步、批次报告、失败重试 | 把通话复盘从手工整理变成可追踪的批处理流水线 |
| [AI Video Automation Pipeline](./projects/ai-video-automation-mvp/) | Codex 中控、Name Gate、专用即梦浏览器、人工审核、分段重跑、智能剪辑、交付归档 | 把一次性 AI 视频制作升级为带安全闸口的半自动生产线 |
| [Math Asset Automation](./projects/math-asset-automation/) | 素材需求转列、多维表格任务读取、图片产物上传、状态回填、协作 SOP | 把投放素材生产从聊天驱动变成任务驱动 |
| [Xiaohongshu Local Admin](./projects/xiaohongshu-local-admin/) | 账号 DNA、Codex 内容生成、Notion 同步、图片工作流、发布门禁、MCP 检查 | 把小红书内容运营从分散步骤变成有检查点的本地工作台 |

## What This Shows

This clean portfolio shows the real work without exposing sensitive operational assets:

- workflow design and implementation scope
- delivery checkpoints and validated capabilities
- business value and operational leverage
- safety boundaries for data, media, credentials, and prompts
- next steps for migrating sanitized source code later

## What It Does Not Expose

The source repository included working materials that should not be circulated broadly:

- BI exports, audio files, generated transcripts, and run databases
- generated images, videos, frames, previews, ZIP packages, PDF/HTML/CSV exports
- private prompts, source-media breakdowns, account strategy details
- local paths, platform resource identifiers, cookies, session files, API keys, and webhooks
- raw checkpoint folders that mix delivery evidence with private operational context

This repository therefore presents a clean project narrative first, and keeps risky implementation artifacts out until each project owner approves a sanitized migration.

## Repository Structure

```text
projects/
  audio-bi-transcription/
    overview/
    deliverables/
    workflow/
    evidence/
    next-steps/
  ai-video-automation-mvp/
    overview/
    deliverables/
    workflow/
    evidence/
    next-steps/
  math-asset-automation/
    overview/
    deliverables/
    workflow/
    evidence/
    next-steps/
  xiaohongshu-local-admin/
    overview/
    deliverables/
    workflow/
    evidence/
    next-steps/
docs/
  governance/
  reports/
```

## Governance Boundary

This repository is safe for controlled internal review. It does not certify historical commits, forks, clones, screenshots, caches, or third-party redistribution from the original repository.

Before making this repository public or adding source code, complete:

- [Publishing Checklist](./docs/governance/PUBLISHING_CHECKLIST.md)
- [Security Checklist](./docs/governance/SECURITY_CHECKLIST.md)
- [Maintainer Confirmation Template](./docs/governance/MAINTAINER_CONFIRMATION_TEMPLATE.md)

## Leadership Reporting Angle

Recommended framing:

> This is no longer a raw working repository. It is a clean portfolio showing project ownership, delivery scope, reusable workflow design, and governance maturity. Sensitive working materials remain protected, while the value of the work is visible and easy to review.
