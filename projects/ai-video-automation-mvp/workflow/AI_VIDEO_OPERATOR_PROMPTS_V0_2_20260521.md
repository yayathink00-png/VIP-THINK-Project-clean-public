# AI Video Operator Prompts v0.2

These are copy-ready operator prompts for handing the AI video workflow to another person or another Codex thread.

## 1. New Operator Start Prompt

Use this when a new operator takes over:

```text
你现在接手 AI 视频安全生产流程。请先阅读：

1. docs/AI_VIDEO_SAFE_PIPELINE_HANDOFF_INDEX_20260521.md
2. docs/AI_VIDEO_OPERATOR_RUNBOOK_V0_2_20260521.md
3. docs/AI_VIDEO_SAFE_PIPELINE_V0_2_20260521.md
4. docs/reports/AI_VIDEO_SAFE_PIPELINE_CHECKLIST_V0_2_20260521.xlsx

你的目标不是快速生成，而是按安全流程推进：
- 不经用户明确确认，不提交 Dreamina 生成；
- 任何消耗积分的动作前，必须先给用户看完整提示词和风险审计；
- 每个 Gate 都必须有钉钉通知和本地通知 manifest；
- 每段回传后必须运行 safe-review-segment；
- 自动检查结果不能替代用户审核；
- 未通过片段不能进入下一段或最终成片。

请先运行：
python3 scripts/ai_video_trial.py --help

然后向用户汇报你理解的当前流程和下一步，不要直接提交生成。
```

## 2. New Video Kickoff Prompt

Use this when starting a fresh AI video:

```text
我会按安全链路开新 AI 视频。开始前需要确认 6 个信息：

1. 源视频路径
2. 最终成片名字
3. Dreamina/即梦对话名
4. 比例和分辨率
5. 固定角色图/品牌 Logo 路径
6. 语言、字幕、旁白规则

确认后我会先创建 run，并绑定 Name Gate。之后每个片段都会先给你看提示词和风险审计，只有你回复对应的“确认生成 Segment XX”后才会提交。
```

## 3. Prompt Preview Message

Use this before asking for generation approval:

```text
这是 Segment XX 的生成前审核包。

请你重点看：
- 片段目标是否对
- 台词是否逐字正确
- 时长是否符合台词长度
- 参考素材是否合适
- 是否禁止字幕、可读文字、假 Logo、水印
- 风格是否符合要求

我已经/将会运行：
python3 scripts/ai_video_trial.py audit-generation-plan ...

我也会发送 Prompt Gate 钉钉提醒：
python3 scripts/ai_video_trial.py notify-safety-gate ...

如果你确认无误，请回复：
确认生成 Segment XX

未收到这句确认前，我不会提交 Dreamina，也不会消耗积分。
```

For reruns:

```text
如果你确认这版重跑提示词无误，请回复：
确认生成 Segment XX 重跑A

未收到这句确认前，我不会提交。
```

## 4. Generation Submitted Message

Use after submit succeeds:

```text
已按你确认的版本提交 Dreamina。

- Segment：XX
- 版本：重跑X
- submit_id：<submit_id>
- 请求时长：<duration>s
- 积分：<credit_count>

接下来我只会查询这个 submit_id，不会自动重提。回传后会运行 safe-review-segment，并发你审核重点。
我也会发送 Submit Gate 钉钉提醒，记录 submit_id 和本次提交报告。
```

## 5. Still Generating Message

Use during polling:

```text
Segment XX 仍在生成中。

我只查询了同一个 submit_id：<submit_id>。
当前状态：Generating / querying。
没有失败原因，也没有下载文件。
我会继续等待，不会重新提交。
我会按 Query Gate 发送钉钉状态提醒。
```

## 6. Returned Review Message

Use after `safe-review-segment`:

```text
Segment XX 已回传，并已完成安全审核包。

请审核：
- 视频文件：<video path>
- 安全审核总结：<safe_review_summary.md>
- 台词核验：<voiceover_verification.md>
- 视觉风险：<visual_artifact_audit.md>

当前自动检查状态：<safe_status>
我已经发送/会发送 Review Gate 钉钉提醒。

注意：自动检查不等于通过。请你决定：
Segment XX 可进入下一段
Segment XX 建议重跑
Segment XX 必须重跑
```

## 7. Rejection / Rerun Message

Use when user rejects a segment:

```text
收到，Segment XX 不进入下一段。

我会把这次问题记录为：
- 失败标签：<VO_ERROR / TEXT_ARTIFACT / STYLE_ERROR / ...>
- 主要原因：<reason>
- 本次 submit_id：<submit_id>

下一步我会先整理重跑提示词预览给你审核；未确认前不会重新生成。
```

## 8. Final Splice Message

Use before/after final export:

```text
我会只使用已通过片段拼接正式版：
- Segment 01：<version>
- Segment 02：<version>
- Segment 03：<version>
- Segment 04：<version>

如果其中有任何片段仍是待审核，我只能生成 review_splice 审核拼接版，不能标为最终通过成片。
```

After export:

```text
已生成拼接版。

- 视频：<final path>
- QC 报告：<qc report>
- 抽帧图：<contact sheet>

请最终检查台词、画面文字、Logo 位置和片段衔接。
```

## 9. Strict Stop Message

Use when the workflow must stop:

```text
这里需要先停一下，原因是：
<blocker>

按安全流程，这一步不能继续生成/拼接/交付。需要你确认下一步：
- 修改提示词
- 接受风险继续
- 重跑当前片段
- 只生成 review_splice 审核版
```

## 10. Handoff Prompt To Another Codex Thread

Use this when moving the work to a fresh Codex thread:

```text
请接手这个 AI 视频安全生产项目。当前工作目录是：
<local-workspace>

请先阅读：
docs/AI_VIDEO_SAFE_PIPELINE_HANDOFF_INDEX_20260521.md
docs/AI_VIDEO_OPERATOR_RUNBOOK_V0_2_20260521.md
docs/AI_VIDEO_SAFE_PIPELINE_V0_2_20260521.md
docs/AI_VIDEO_OPERATOR_PROMPTS_V0_2_20260521.md

关键原则：
- 不经用户明确确认，不提交 Dreamina；
- 提交前必须 audit-generation-plan；
- dreamina-submit-video 已自动接入风险审计；
- 回传后必须 safe-review-segment；
- 自动检查只是风险信号，不能替代用户决策；
- 未通过片段不能进入最终版。

请先运行：
python3 scripts/ai_video_trial.py --help
python3 scripts/ai_video_trial.py gate-status --run-dir "<run-dir>"

然后用中文汇报当前状态和下一步，不要擅自生成。
```
