# VIP THINK Project Portfolio

This repository is the clean, leadership-facing project portfolio for VIP THINK automation work.

It keeps the project structure and delivery evidence visible, while excluding raw data, exports, generated media, private prompts, platform resource identifiers, cookies, session files, and secrets.

## Executive Summary

The original work has been整理成四个可汇报项目方向：

| Project | Business Value | Current Clean Status |
| --- | --- | --- |
| [Audio BI Transcription](./projects/audio-bi-transcription/) | 将 BI 通话数据、录音下载、Whisper 转写、飞书同步串成自动化流水线 | 保留公开安全项目说明，源代码待脱敏后分批迁入 |
| [AI Video Automation MVP](./projects/ai-video-automation-mvp/) | 建立 AI 视频生成、下载、剪辑、质检和通知的半自动流程 | 保留 MVP 说明与安全边界，生成视频和 prompts 暂不公开 |
| [Math Asset Automation](./projects/math-asset-automation/) | 将数学思维素材需求转成图片生成、状态管理和回填流程 | 保留流程说明，图片产物和飞书资源标识暂不公开 |
| [Xiaohongshu Local Admin](./projects/xiaohongshu-local-admin/) | 支撑小红书内容运营、Notion 同步、图片工作流和发布门禁 | 保留交付说明，checkpoint/handoff 原文暂不公开 |

## Why This Repository Is Clean

The source repository contained useful project work, but also included items unsuitable for public or broad leadership circulation:

- exported files such as ZIP, PDF, HTML, and CSV
- generated PNG batches and packaged image assets
- dated checkpoint and handoff folders
- platform workflow references and possible internal resource identifiers
- cookie/session/token-related implementation context
- private prompt and source-media adaptation context

This clean repository therefore presents the project value and governance evidence without copying risky assets.

## Repository Structure

```text
projects/
  audio-bi-transcription/
  ai-video-automation-mvp/
  math-asset-automation/
  xiaohongshu-local-admin/
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

