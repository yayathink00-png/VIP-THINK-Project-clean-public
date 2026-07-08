# AI Video Next Run Preflight Template

Copy this checklist into the next run before any Dreamina credit is spent.

## Identity

| Item | Value |
|---|---|
| Local run id |  |
| Final video name |  |
| Dreamina dialogue name |  |
| Dreamina session id/url |  |
| Character reference |  |
| Logo asset |  |
| Language/script |  |
| Aspect/resolution |  |

## Segment Plan

| Segment | Goal | Narration text | Narration chars | Suggested duration | Priority 1 | References | Approval phrase |
|---|---|---|---:|---:|---|---|---|
| 01 |  |  |  |  |  |  | 确认生成 Segment 01 |
| 02 |  |  |  |  |  |  | 确认生成 Segment 02 |
| 03 |  |  |  |  |  |  | 确认生成 Segment 03 |
| 04 |  |  |  |  |  |  | 确认生成 Segment 04 |

## Mandatory Prompt Header

Every prompt must start with:

```text
最高优先级：
第二优先级：
第三优先级：

本段只允许出现的旁白：
「」

不允许：
- 不要生成字幕、花字、可读文字、假 Logo、水印或角标
- 不要改写、漏读、重复、翻译旁白
- 不要把人物做成明显对口型完整说话，除非用户明确要求
```

## Reference Decision

| Need | Use | Do not use |
|---|---|---|
| Character consistency | character image | original human identity video |
| Continuity | prior tail frame | many full videos |
| Voice continuity | prior audio/video | if exact CTA text is priority 1 |
| Original structure | short reference or text structure | long/multiple references |
| Exact wording | minimal references | voice reference that can pull wording off-script |

## Stop Before Submit

Stop unless all are true:

- [ ] User has seen the full current prompt.
- [ ] Duration is justified by narration length.
- [ ] Reference set is minimal and intentional.
- [ ] Exact confirmation phrase matches current segment/version.
- [ ] DingTalk preflight notification was sent if this is a production run.
- [ ] Submitting will not reuse an old video project's Dreamina dialogue.

## After Return

- [ ] Copy returned video to stable segment file name.
- [ ] Run review-segment.
- [ ] Generate contact sheet.
- [ ] Send DingTalk review notification.
- [ ] Log submit_id, credit_count, duration, references, prompt, outcome.
- [ ] Wait for user decision before next segment.

## Failure Tags

Use one or more:

```text
VO_ERROR
VOICE_CONTINUITY_ERROR
STYLE_ERROR
VISUAL_STRUCTURE_ERROR
TEXT_ARTIFACT
LOGO_RISK
REFERENCE_OVERLOAD
DURATION_WASTE
PROCESS_BREAK
```
