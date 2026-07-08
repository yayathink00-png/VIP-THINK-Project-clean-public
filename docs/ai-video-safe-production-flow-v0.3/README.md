# AI 视频安全生产流 V0.3｜安全版

版本日期：2026-05-22

## 这是什么

这是一套用于生产付费 AI 视频素材的安全流程。它适用于根据参考视频拆解剧情、台词、镜头和拍摄角度后，用文生视频或图生视频重新生成新片的工作流。

本版本为外发安全版，只包含 SOP、模板和排障规则，不包含真实项目 submit_id、本地路径、内部脚本快照或完整案例明细。

V0.3 的重点是：

- 每次扣点前都必须明确确认。
- 新 Dreamina 对话必须先创建、放入内容、重命名，再绑定到本地 run。
- 默认使用短提示词，减少 pre-TNS 风险。
- 人物连续段优先使用上一段清晰人物参考图做 image2video。
- 自动复核只作为风险提示，最终由人工审片决定。
- 积分按“最终采用”和“试错”分开记录。

## 包内文件

| 文件 | 用途 |
|---|---|
| `SOP_AI_VIDEO_SAFE_PRODUCTION_FLOW_V0_3.md` | 给操作员看的完整生产流程 |
| `templates/NEXT_RUN_PREFLIGHT_TEMPLATE_V0_3.md` | 新片启动前复制使用的预检模板 |
| `templates/PRODUCTION_SUMMARY_TEMPLATE_V0_3.md` | 成片后复盘文档模板 |
| `templates/PROMPT_GATE_TEMPLATE_V0_3.md` | 每段提交前展示给用户的提示词门模板 |
| `FAILURE_TAGS_AND_FIXES_V0_3.md` | 常见失败标签和修复策略 |
| `CHANGELOG_V0_3.md` | V0.3 相比 V0.2 的变化 |
| `MANIFEST.md` | 对外交付清单 |

## 最短使用方式

1. 复制 `templates/NEXT_RUN_PREFLIGHT_TEMPLATE_V0_3.md`，填入新片信息。
2. 先在 Dreamina 创建新对话，放入安全占位内容，再重命名。
3. 创建本地 run，并把已重命名的 Dreamina 对话绑定到 Name Gate。
4. 每段生成前使用 `PROMPT_GATE_TEMPLATE_V0_3.md` 给用户确认。
5. 用户回复 `确认生成 Segment XX` 后，才允许提交。
6. 返回后跑自动复核，再等用户回复：

```text
Segment XX 可进入下一段
Segment XX 建议重跑
Segment XX 必须重跑
```

7. 最后一段人工通过后，进入 Final Gate 合成，不再准备不存在的新段落。

## V0.3 的硬规则

- 不要把“Dreamina 对话名”作为新片初始输入。新对话一开始没有名字，必须先创建并放入内容，再重命名。
- 每个视频项目只使用一个 Dreamina 对话；同一项目内所有分段、重跑和 take 都留在同一对话。
- 参考素材路径在提交前必须能解析为绝对路径。
- 人物连续段默认考虑 image2video，不优先纯 text2video。
- 没有用户确认，不提交、不扣点。
- 自动 blocked 不等于必须重跑；必须结合人工听看。
