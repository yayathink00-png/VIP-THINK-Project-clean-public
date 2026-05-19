# Leadership Brief

## Summary

本次治理不是“把项目删空”，而是把原来的工作过程仓库整理成一个可汇报、可审计、可继续扩展的 clean portfolio。

当前 clean 仓库保留四个项目方向：

- Audio BI Transcription
- AI Video Automation MVP
- Math Asset Automation
- Xiaohongshu Local Admin

Each project has a complete folder package:

- `overview/`
- `deliverables/`
- `workflow/`
- `evidence/`
- `next-steps/`

## What Was Protected

原仓库中存在导出物、生成图片、checkpoint/handoff、平台资源标识、cookie/session/token 相关上下文和私有 prompt 边界问题。为了保护成员责任边界和公司资料，本次没有把这些内容直接放入 clean 仓库。

## How To Explain To Leadership

建议汇报口径：

> 我们已经把 VIP THINK 项目从“工作过程仓库”整理成“可治理、可汇报、可逐步交付”的 clean portfolio。现在能看到四条真实工作线：BI 通话转写流水线、AI 视频自动化 MVP、数学素材自动化、小红书本地运营工作台。每条线都补充了业务问题、已交付能力、工作流、证据摘要和下一步计划。原始数据、导出物、生成图片/视频、私有 prompt、平台资源标识和 cookie/session/token 相关内容没有迁移，避免扩大敏感材料传播范围。

## Work Value By Project

### Audio BI Transcription

把 BI 通话明细、录音链接、Whisper 转写、飞书同步、批次报告和失败重试串成一条流水线。价值是减少人工下载和整理录音的重复劳动，让销售/运营复盘可以基于可追踪的批次结果推进。

### AI Video Automation MVP

跑通了“Codex 中控 + 人工确认 Gate + 即梦生成辅助 + 自动下载 + FFmpeg 剪辑 + QC + 钉钉提醒”的半自动流程。价值不是完全无人生成，而是把 AI 视频生产中的误点、错对话、错模式、文件散落和审核不可追踪问题降下来。

### Math Asset Automation

把数学思维投放素材从 Excel/聊天驱动，推进到多维表格任务化管理：素材方向、数量、标题、卖点、CTA、画面、平台、状态、附件回填都形成结构化流程。已验证一批卖点图的生成与附件字段回填，后续可以继续补 `next`、`validate`、`upload-dir` 等稳定命令。

### Xiaohongshu Local Admin

围绕小红书内容运营，完成账号 DNA、内容生成、Notion 同步、图片工作流和发布门禁的阶段性建设。价值是把内容从“生成完就散落”推进到可归档、可检查、可确认、可交接的本地工作台。

## Current Status

- 新仓库已创建为 private
- 项目按四个方向重新分组
- 每个项目已建立完整子文件夹，便于领导逐项查看
- 已加入 public release governance 文档
- 未迁移风险资产
- 后续可按项目逐步提交脱敏源码和公开安全 demo

## Suggested Next Milestones

1. 项目负责人确认每个项目允许公开的范围。
2. 先迁移 `audio-bi-transcription` 的脱敏源码和测试。
3. 再迁移 `ai-video-automation-mvp` 的安全 CLI 骨架。
4. 对图片和小红书项目只迁移流程说明，不迁移生成资产。
5. 每次迁移都走 PR、扫描和负责人确认。

