# AI Video Safe Pipeline v0.2 - 2026-05-21

Purpose: turn the latest Dreamina CLI production run into a safer, repeatable AI video production mechanism.

This document supersedes the softer v0.1 runbook when producing paid-credit AI video segments.

## Non-Negotiable Rule

Codex may prepare prompts, inspect local state, submit only after explicit user confirmation, query results, download, review, notify, log, and splice.

Codex must not:

- submit a generation without the user's exact confirmation for that segment or rerun
- reuse a previous video's Dreamina dialogue for a new video
- continue to the next segment before the current segment is reviewed
- treat a generated segment as accepted just because it downloaded successfully
- mark a spliced cut as final if any segment is still pending review

## Production Gates

| Gate | Required before | Must show or verify | Blocking condition |
|---|---|---|---|
| Name Gate | Any prompt filling or submit | local run id, Dreamina dialogue name/id, final output name | any name missing, stale, or reused from another video |
| Prompt Gate | Any submit | full prompt, model, ratio, duration, references, expected confirmation phrase | prompt not reviewed by user |
| Submit Gate | Dreamina submit | user's exact confirmation text, e.g. `确认生成 Segment 04 重跑E` | confirmation absent or for another version |
| Query Gate | Result follow-up | only existing submit_id, no resubmit | submit_id unclear or user did not authorize rerun |
| Review Gate | Next segment | returned video, review file, contact sheet, DingTalk notification | segment not explicitly accepted |
| Export Gate | Splicing/final export | accepted segment list, logo asset, output path, QC sheet | any segment pending unless creating a clearly labeled review splice |

## DingTalk Notification Policy

Every gate must produce a DingTalk notification manifest. Do not rely on chat-only updates.

| Gate | DingTalk requirement |
|---|---|
| Name Gate | notify bound project name, final name, Dreamina dialogue/session before generation work starts |
| Prompt Gate | notify full prompt preview or prompt file, risk audit status, exact confirmation phrase |
| Submit Gate | notify submit_id, version, duration, credit_count if available |
| Query Gate | notify long-running / failed / successful return states; never silently wait when user expects follow-up |
| Review Gate | notify safe review summary, voiceover report, visual artifact report |
| Export Gate | notify final/review splice path, QC report, known caveats |
| Handoff Gate | notify handoff index, runbook, current run state, next action |

Use the generic gate notifier when a specialized command does not send DingTalk:

```bash
python3 scripts/ai_video_trial.py notify-safety-gate \
  --run-dir "data/runs/<run-id>" \
  --gate "Prompt Gate" \
  --segment 4 \
  --status "待用户审核" \
  --action "请审核提示词和风险审计；确认后回复：确认生成 Segment 04 重跑E" \
  --gate-file "preflight/segment_04_generation_risk_audit.md"
```

Each notification writes:

```text
notifications/YYYYMMDD_HHMMSS_segment_XX_<gate>_safety_gate_dingtalk.json
```

## Segment Prompt Priority Contract

Every segment prompt must begin with a priority contract. Do not leave all requirements at equal priority.

Recommended order examples:

| Segment type | Priority 1 | Priority 2 | Priority 3 | Priority 4 |
|---|---|---|---|---|
| Opening/hook | visual clarity | character consistency | voiceover correctness | continuity |
| Continuity scene | continuity from prior segment | character consistency | voiceover tone | props/background |
| Exact narration CTA | exact voiceover text | no extra voiceover | brand/layout constraints | voice continuity |
| Final splice | accepted files only | logo placement | audio/video specs | QC record |

For exact CTA voiceover, do not upload voice reference audio unless the user explicitly accepts the risk that voice continuity can reduce text accuracy.

Before sending a production prompt to the user for final approval, run the automatic risk audit:

```bash
python3 scripts/ai_video_trial.py audit-generation-plan \
  --run-dir "data/runs/<run-id>" \
  --segment 4 \
  --prompt-file "run_docs/planning/segment_04_rerunE_dreamina_preview.md" \
  --duration 12 \
  --image-count 1 \
  --video-count 0 \
  --audio-count 0 \
  --exact-cta \
  --strict
```

Use `--exact-cta` when exact CTA wording is the pass/fail condition. In this mode, audio references are treated as blocking risk because this run showed they can improve voice continuity while increasing wording errors.

## Duration Policy

Do not default to 15 seconds.

| Narration length | Suggested duration | Notes |
|---:|---:|---|
| 8-15 Chinese characters | 4-6s | usually one short beat |
| 16-30 Chinese characters | 6-8s | short sentence |
| 31-45 Chinese characters | 8-10s | one medium sentence |
| 46-65 Chinese characters | 10-12s | CTA or explanatory sentence |
| 65+ Chinese characters | split segment | high error and credit-waste risk |

If a prompt requests a duration longer than the narration needs, record the reason in the preflight. If no reason exists, shorten it before asking for user approval.

The automatic audit writes:

```text
preflight/segment_XX_generation_risk_audit.md
preflight/segment_XX_generation_risk_audit.json
```

If the audit status is `blocked`, do not ask the user to confirm generation yet.

`dreamina-submit-video` now runs this audit automatically after `--user-confirmed` and before any real Dreamina submit. A blocked audit stops the submit before credits are spent.

Only use this bypass after explicit user approval:

```bash
--skip-risk-audit
```

Skipping the audit must be recorded in the submit JSON report and explained to the user.

## Reference Strategy

Use the smallest reference set that solves the current problem.

| Problem to solve | Preferred references | Avoid |
|---|---|---|
| character consistency | fixed character image | source video identity reference |
| scene continuity | prior segment tail frame | multiple full videos |
| voice continuity | prior segment audio or prior segment video | using voice reference when exact wording is top priority |
| original CTA structure | short structure reference or text description | long/multiple original clips |
| exact voiceover | prompt-only or minimal image reference | audio/video references that can pull wording off-script |

Reference overload is a real failure mode. If a generation fails after adding references, remove references before adding more.

## Required Failure Tags

Every rejected or failed take must be tagged.

| Tag | Meaning |
|---|---|
| `VO_ERROR` | voiceover text wrong, omitted, repeated, translated, or added |
| `VOICE_CONTINUITY_ERROR` | speaker/voice does not connect to previous segment |
| `STYLE_ERROR` | wrong style, e.g. 2D instead of 3D cartoon |
| `VISUAL_STRUCTURE_ERROR` | scene does not match required structure or original reference |
| `TEXT_ARTIFACT` | readable/gibberish/simplified/English text appears in video |
| `LOGO_RISK` | fake logo, watermark, AI mark, or unwanted corner mark |
| `REFERENCE_OVERLOAD` | generation failed or degraded after too many references |
| `DURATION_WASTE` | duration longer than narration requires |
| `PROCESS_BREAK` | missing notification, missing approval, wrong state, or untracked decision |

## Mandatory Review Package

After every successful return:

1. Copy the returned file to a stable segment name.
2. Run `safe-review-segment`.
3. Send DingTalk through `safe-review-segment --notify-dingtalk` or a separate `notify-dingtalk` call.
4. Report in the current thread with local video path, safe review summary, voiceover report, visual artifact report, and focus points.
5. Wait for the user's decision.

Do not proceed from "downloaded" to "accepted" automatically.

One-command safe review:

```bash
python3 scripts/ai_video_trial.py safe-review-segment \
  --run-dir "data/runs/<run-id>" \
  --segment 4 \
  --video "returned/Segment04_rerunE.mp4" \
  --target-text "<target narration text>" \
  --must-include "<required-term|alias,...>" \
  --strict-terms
```

The command creates:

```text
reviews/segment_XX/segment_review.md
reviews/segment_XX/voiceover_check/voiceover_verification.md
reviews/segment_XX/visual_artifact_check/visual_artifact_audit.md
reviews/segment_XX/safe_review_summary.md
```

The safe review status is not an acceptance decision. It is a production safety signal.

Voiceover verification command:

```bash
python3 scripts/ai_video_trial.py verify-voiceover \
  --run-dir "data/runs/<run-id>" \
  --segment 4 \
  --video "returned/Segment04_rerunE.mp4" \
  --target-text "<target narration text>" \
  --must-include "<required-term|alias,...>" \
  --model tiny \
  --language Chinese \
  --strict-terms
```

`--must-include` supports aliases with `|` because Cantonese ASR may output standard written Chinese or numeric variants. Treat `pass` as a helper signal, not full acceptance; the user still makes the final review decision.

Visual artifact audit command:

```bash
python3 scripts/ai_video_trial.py audit-visual-artifacts \
  --run-dir "data/runs/<run-id>" \
  --segment 4 \
  --video "returned/Segment04_rerunE.mp4" \
  --frame-interval 1
```

This is not true OCR. It deliberately uses sensitive heuristics to flag frames and crop high-risk regions:

- top-left / top-right: fake logo, watermark, AI mark, corner badge
- bottom: subtitles or bottom text
- center: readable course card, worksheet, screen text, gibberish

`warning` means the crop sheets must be manually reviewed before the segment can be accepted.

## Logging Requirements

For each submit, preserve:

- segment number and version/take
- exact submit_id
- full prompt actually submitted
- prompt preview shown to the user
- model, ratio, resolution, duration
- reference count and reference types
- credit_count if returned by Dreamina
- returned file path
- wait time from submit to downloaded file
- DingTalk notification manifest
- user decision
- failure tags

The latest production run established the Excel log format:

```text
reports/<private-generation-log>.xlsx
```

Future runs should create the same workbook structure before final handoff.

## Segment 04 Lesson

Segment 04 proved the most important rule:

```text
When exact CTA wording is the pass/fail condition, prioritize text accuracy over voice continuity.
```

For final CTA segments:

- keep duration close to the narration length
- keep references minimal
- write "only this narration, read once, no extra lines" at the top
- avoid voice reference audio unless user explicitly approves that tradeoff
- check generated screens/cards for readable text risk

## Stop Conditions

Stop and ask the user before proceeding if:

- the user has not seen the current prompt
- the requested confirmation phrase and actual user phrase differ
- the task would spend credits
- current submit_id is not the one being queried
- DingTalk notification fails or is unconfirmed
- a segment has not been accepted but the next segment/final export is requested
- a model-generated screen contains readable text that could violate the no-text rule

If the user still asks to splice with a pending segment, label the output as `review_splice`, not final approved delivery.
