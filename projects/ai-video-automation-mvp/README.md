# AI Video Automation Pipeline

## One-Line Summary

建立 VIP THINK AI 视频生产的半自动流水线，把项目命名、即梦对话绑定、人工审核、分段生成、重跑决策、智能剪辑、状态校验和交付归档串成可复用流程。

## Business Problem

AI 视频生产涉及多平台、多步骤和人工判断。没有流程门禁时，容易出现错对话、错模式、错比例、错时长、误点生成、人物形象漂移、素材版本混乱和质检不可追踪。这个项目的重点不是让系统无人值守乱跑，而是把关键动作变成“人工确认 + 自动执行 + 可追踪状态”。

## Delivered Capability

- 跑通 `Codex 中控 + 人工 Gate + 即梦生成辅助 + 分段审核 + 智能剪辑 + 交付归档` 的完整首条视频流程。
- 建立每条视频专属的 Name Gate：本地项目名、即梦对话名、最终成片名、workspace 在生成前必须一致。
- 建立“一个视频项目绑定一个即梦对话”的规则，避免不同视频混进同一个对话。
- 建立专用即梦浏览器方案，减少自动化操作占用日常浏览器和误操作风险。
- 建立 `continue-safe` 阶段检查，未获得用户明确确认时阻断生成动作。
- 建立 `reconcile-state` 状态校验，减少文件、审核记录和当前决策不一致。
- 完成 Segment 01-05 的人工审核/重跑流程验证，其中 Segment 05 经 TakeC 后进入剪辑。
- 生成智能剪辑版本并完成交付包归档，不把真实素材和生成视频放进 clean public repo。
- 形成可给同事接手的稳定版 handoff 结构和启动提示词。

## Project Folder

- [Overview](./overview/PROJECT_OVERVIEW.md)
- [Deliverables](./deliverables/DELIVERABLES.md)
- [Workflow](./workflow/WORKFLOW.md)
- [Evidence](./evidence/EVIDENCE_SUMMARY.md)
- [Next Steps](./next-steps/NEXT_STEPS.md)

## Current Clean Repository Status

This clean repository keeps only the leadership-facing project package and sanitized progress narrative.

Generated videos, extracted frames, source video breakdowns, private prompt packs, real platform URLs, DingTalk secrets, browser session state, and handoff run-state are excluded by default.

## Excluded For Safety

- generated video files
- source videos and extracted frames
- private prompt packs
- source-media adaptation notes
- real platform workspace URLs and dialogue identifiers
- DingTalk webhooks or secrets
- browser/session state
- run-state metadata

## Recommended Next Step

After rights and prompt-boundary review, migrate only sanitized workflow code and synthetic examples. Keep generation assets, real prompt packs, browser automation state, and platform-specific identifiers private unless explicitly approved.
