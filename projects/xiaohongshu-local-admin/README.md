# Xiaohongshu Local Admin

## One-Line Summary

支撑 VIP THINK 小红书内容运营的本地后台：账号 DNA、Codex 内容生成、Notion 同步、图片工作流、发布门禁和安全交接体系。

## Business Problem

内容运营项目包含账号定位、选题、内容生成、图片生成、素材归档、Notion 同步和小红书发布准备。如果没有统一工作台，内容容易散落在本地文件、聊天记录、Notion 页面和导出包里；如果没有发布门禁，又容易把未确认内容、图片或登录态带入发布动作。

## Delivered Capability

- Step 2：稳定账号定位工作台，形成账号 DNA 和手动补位状态。
- Step 4：将本地固定规则内容生成升级为 Codex 技能生成，并能轮询状态、导入结果。
- Step 4：将主动作从导出 Excel 转为同步 Notion，按命名规则创建内容文档。
- Step 5：将复制生图指令升级为自动调用 Codex CLI 生图，支持状态轮询、本地预览、素材包导出和综合 Notion 归档。
- Step 5：修复图片文案重复，让轻广告/硬广告画面文字更可控。
- Step 6：把最终输出检查升级为小红书发布门禁，加入单条选择、可见性选择、人工确认、payload 预览和只读 MCP 状态检查。
- 建立安全转移规则：不提交 `.env`、generated、exports、图片、ZIP、Excel、cookies、token/key。

## Project Folder

- [Overview](./overview/PROJECT_OVERVIEW.md)
- [Deliverables](./deliverables/DELIVERABLES.md)
- [Workflow](./workflow/WORKFLOW.md)
- [Evidence](./evidence/EVIDENCE_SUMMARY.md)
- [Next Steps](./next-steps/NEXT_STEPS.md)

## Current Clean Repository Status

This clean repository includes only the leadership-facing project package.

The original checkpoint folders contain useful delivery evidence but may include private workflow, account positioning, prompt, token-name references, local paths, and operational context, so they are excluded until reviewed.

## Excluded For Safety

- dated checkpoint folders
- detailed handoff prompts
- account positioning internals
- local runtime paths
- Notion/TikHub/Jimeng token references
- generated images and exports
- cookies and local login state

## Recommended Next Step

Create a sanitized milestone report that summarizes Step 4/Step 5/Step 6 outcomes without copying raw checkpoint text or private operational details.

