# AI Video Automation MVP

## One-Line Summary

建立 VIP THINK AI 视频生产的半自动 MVP，把人工确认、AI 生成辅助、自动下载、FFmpeg 剪辑试跑、QC 报告和钉钉审核提醒串起来。

## Business Problem

AI 视频生产涉及多平台、多步骤和人工判断。没有流程门禁时，容易出现错对话、错模式、错比例、错时长、误点生成、素材版本混乱和质检不可追踪。这个 MVP 的重点不是让系统无人值守乱跑，而是把关键动作变成“人工确认 + 自动执行 + 可追踪状态”。

## Delivered Capability

- 跑通 `Codex 中控 + 人工 Gate + 即梦生成辅助 + 自动下载 + FFmpeg 剪辑` 的 MVP。
- 建立分段视频生成流程，按 Segment 和 take 管理版本。
- Segment 01/02 已通过流程验证，后续 Segment 03-05 暂停在安全节点。
- 自动从页面视频源下载生成片段，减少手动找文件。
- 用 FFmpeg 拼接已通过片段，叠加 Logo，生成剪辑试跑版本。
- 生成 QC 报告，辅助人工判断画面、Logo、安全区和口播问题。
- 钉钉通知只做审核提醒，不直接发送视频文件，避免素材外扩散。
- 明确下一步优先做 `preflight-jimeng`，把生成前检查固化。

## Project Folder

- [Overview](./overview/PROJECT_OVERVIEW.md)
- [Deliverables](./deliverables/DELIVERABLES.md)
- [Workflow](./workflow/WORKFLOW.md)
- [Evidence](./evidence/EVIDENCE_SUMMARY.md)
- [Next Steps](./next-steps/NEXT_STEPS.md)

## Current Clean Repository Status

This clean repository keeps only the leadership-facing project package.

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

