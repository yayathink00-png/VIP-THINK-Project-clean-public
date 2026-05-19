# Audio BI Transcription

## One-Line Summary

将 BI 导出的通话数据、录音下载、Whisper 转写和飞书同步整合成一条可复盘的自动化流水线。

## Business Problem

销售和运营团队需要从大量通话记录中快速获得可检索、可分析、可沉淀的文本内容。手工下载录音、转写、整理和同步成本高，且过程难以追踪。

## Delivered Capability

- 支持从 BI 导出表进入批处理流程
- 支持根据通话链接下载录音
- 支持 Whisper/faster-whisper 转写
- 支持批次状态、失败重试、预检和安全检查
- 支持将结果同步到飞书多维表格
- 支持生成批次报告和失败明细，便于复盘

## Project Folder

- [Overview](./overview/PROJECT_OVERVIEW.md)
- [Deliverables](./deliverables/DELIVERABLES.md)
- [Workflow](./workflow/WORKFLOW.md)
- [Evidence](./evidence/EVIDENCE_SUMMARY.md)
- [Next Steps](./next-steps/NEXT_STEPS.md)

## Current Clean Repository Status

This clean repository currently includes the project description only.

The original implementation contains source code, templates, and tests that may be migrated later after maintainer review. Raw BI exports, downloaded audio, run folders, cookies, session state, credentials, and generated reports are excluded by default.

## Excluded For Safety

- real BI export files
- downloaded audio files
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
- README rewritten without internal resource references
