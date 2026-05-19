# Leadership Brief

## Summary

本次治理不是“把项目删空”，而是先把原仓库中不适合公开或广泛流转的内容隔离，再建立一个可安全汇报、可逐步迁移的 clean portfolio。

当前 clean 仓库已经保留四个项目方向和治理边界：

- Audio BI Transcription
- AI Video Automation MVP
- Math Asset Automation
- Xiaohongshu Local Admin

## What Was Protected

原仓库中存在导出物、生成图片、checkpoint/handoff、平台资源标识、cookie/session/token 相关上下文和私有 prompt 边界问题。为了保护成员责任边界和公司资料，本次没有把这些内容直接放入 clean 仓库。

## How To Explain To Leadership

建议汇报口径：

> 我们已经把 VIP THINK 项目从“工作过程仓库”整理成“可治理、可汇报、可逐步公开”的 clean portfolio。当前版本保留了项目结构、业务价值、交付能力和治理规则，但暂时不迁移原始素材、导出物、私有 prompt、平台资源标识和未审核图片。这样既能展示项目成果，也不会把历史过程资料和敏感资产扩大传播。

## Current Status

- 新仓库已创建为 private
- 项目按四个方向重新分组
- 已加入 public release governance 文档
- 未迁移风险资产
- 后续可按项目逐步提交脱敏源码和公开安全 demo

## Suggested Next Milestones

1. 项目负责人确认每个项目允许公开的范围。
2. 先迁移 `audio-bi-transcription` 的脱敏源码和测试。
3. 再迁移 `ai-video-automation-mvp` 的安全 CLI 骨架。
4. 对图片和小红书项目只迁移流程说明，不迁移生成资产。
5. 每次迁移都走 PR、扫描和负责人确认。

