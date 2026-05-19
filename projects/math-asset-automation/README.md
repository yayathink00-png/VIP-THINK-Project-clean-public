# Math Asset Automation

## One-Line Summary

将数学思维投放素材需求整理为“任务读取、图片生成、状态跟踪、附件上传、结果回填”的半自动化流程。

## Business Problem

投放素材生产通常从 Excel、聊天记录和临时图片开始，容易出现需求字段不统一、图片版本混乱、附件回填失败、状态没人更新、素材是否可投放说不清。这个项目把素材需求改造成可读、可上传、可验证、可交接的任务流。

## Delivered Capability

- 明确旧横表不适合附件回填，改用“一行一个素材方向”的转列主表。
- 梳理素材字段：数量、主标题、副标题、核心卖点、CTA、画面内容、类型、比例、字体、投放区域、平台、参考、代言人、产出附件、状态。
- 跑通多维表格读取、云空间文件上传、附件字段写入和状态更新。
- 验证 `卖点5张` 从生成到 5 张附件回填的闭环。
- 建立脚本命令：list、get、upload、status。
- 建立图片生成协作 SOP：先每组 1 张测试图，通过后扩展到 5 张。
- 明确合规文案规则，避免“保证提分、100%有效、顶级名师”等风险表达。
- 提出下一阶段 `next`、`validate`、`prepare-dir`、`upload-dir`、`export-task` 命令规划。

## Project Folder

- [Overview](./overview/PROJECT_OVERVIEW.md)
- [Deliverables](./deliverables/DELIVERABLES.md)
- [Workflow](./workflow/WORKFLOW.md)
- [Evidence](./evidence/EVIDENCE_SUMMARY.md)
- [Next Steps](./next-steps/NEXT_STEPS.md)

## Current Clean Repository Status

This clean repository keeps only the leadership-facing project package and governance boundary.

The original folder contains generated PNG assets, packaged ZIP output, platform resource references, handoff notes, and scripts that require sanitization before migration.

## Excluded For Safety

- generated PNG images
- packaged ZIP outputs
- app/table/spreadsheet identifiers
- real platform URLs
- private handoff notes
- production attachment records

## Recommended Next Step

Replace all platform resource identifiers with placeholders, then migrate only sanitized scripts and public-safe templates. Keep all generated images private until asset rights are approved.

