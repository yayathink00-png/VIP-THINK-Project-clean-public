# AI Video Automation MVP

## One-Line Summary

建立 VIP THINK AI 视频生产的半自动 MVP，把人工确认、AI 生成、下载、FFmpeg 剪辑、质检和通知串起来。

## Business Problem

AI 视频生产涉及多平台、多步骤和人工判断。没有流程门禁时，容易出现误生成、版本混乱、素材丢失和质检不可追踪。

## Delivered Capability

- 明确人工确认门禁，避免自动触发不可控生成
- 支持生成结果下载和本地剪辑试验
- 支持 Logo、字幕等后期层处理
- 支持质检报告和团队通知
- 建立下一阶段自动化命令设计方向

## Project Folder

- [Overview](./overview/PROJECT_OVERVIEW.md)
- [Deliverables](./deliverables/DELIVERABLES.md)
- [Workflow](./workflow/WORKFLOW.md)
- [Evidence](./evidence/EVIDENCE_SUMMARY.md)
- [Next Steps](./next-steps/NEXT_STEPS.md)

## Current Clean Repository Status

This clean repository keeps only the leadership-facing project summary.

Generated videos, extracted frames, source video breakdowns, private prompt packs, DingTalk secrets, browser session state, and handoff run-state are excluded by default.

## Excluded For Safety

- generated video files
- source videos and extracted frames
- private prompt packs
- source-media adaptation notes
- DingTalk webhooks or secrets
- browser/session state
- run-state metadata

## Recommended Next Step

After rights and prompt-boundary review, migrate only sanitized workflow code and public-safe CLI docs. Keep generation assets and prompt packs private unless explicitly approved.
