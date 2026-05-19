# Audio BI Transcription

## One-Line Summary

将 BI 通话明细、录音下载、Whisper 转写、飞书多维表格同步、批次报告和失败重试整合成一条可复盘的自动化流水线。

## Business Problem

销售和运营团队有大量通话记录，但原始形态通常是导出表、通话链接和分散录音。人工下载、转写、整理、同步不仅慢，还容易漏记录、重复处理、无法解释失败原因。这个项目把“听录音复盘”升级为“批次化处理 + 状态追踪 + 可重试”的数据流水线。

## Delivered Capability

- 两个入口：手动 BI 导出表入口、Smartbi 抓包导出入口。
- 一条主流水线：读取通话表、按日期和接通状态筛选、下载录音、转写、同步结构化结果。
- 批次目录：每次运行生成独立 run，保存状态库、导出归档、下载目录、报告和 manifest。
- 断点续跑：用状态库记录每条沟通记录的下载、转写、同步状态。
- 失败重试：支持按 download、transcribe、feishu 阶段定向重试。
- 预检与安全检查：先估算处理量、检查风险项，再决定是否正式跑批。
- 交互向导：不手写长命令，也能生成运行计划。
- 飞书同步：支持新表、新文档、新文件夹、附件上传、上传后删除本地音频等运行模式。

## Project Folder

- [Overview](./overview/PROJECT_OVERVIEW.md)
- [Deliverables](./deliverables/DELIVERABLES.md)
- [Workflow](./workflow/WORKFLOW.md)
- [Evidence](./evidence/EVIDENCE_SUMMARY.md)
- [Next Steps](./next-steps/NEXT_STEPS.md)

## Current Clean Repository Status

This clean repository currently includes the leadership-facing project package only.

The original implementation contains source code, templates, tests, command docs, and sample structure that can be migrated later after maintainer review. Raw BI exports, downloaded audio, run folders, cookies, session state, credentials, generated reports, and real user data are excluded by default.

## Excluded For Safety

- real BI export files
- downloaded audio files
- generated transcripts from real users
- local run state and SQLite databases
- Feishu credentials or resource identifiers
- cookies and browser session state
- generated CSV/XLSX/HTML reports

## Recommended Next Step

Create a sanitized source-code PR that includes only:
- `src/`
- tests
- dependency manifest
- `.env.example` with fake placeholders
- synthetic sample data
- README rewritten without internal resource references

