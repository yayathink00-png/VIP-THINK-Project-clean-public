# AI Video Operator Runbook v0.2

This is the handoff runbook for an operator who needs to continue the AI video workflow safely.

## Core Rule

Never spend Dreamina credits unless the user has reviewed the current prompt and explicitly confirmed the current segment/version.

Every key gate must send DingTalk. A local report without DingTalk is not enough for production.

## 0. Start A New Run

```bash
python3 scripts/ai_video_trial.py new-video-run \
  --video "<source-video>" \
  --final-video-name "<final-video-name>" \
  --jimeng-dialogue "<one-dialogue-for-this-video>" \
  --workspace-url "<dreamina-workspace-url>"
```

Expected state:

- `gate_status.json` exists
- `Name Gate` is bound
- `segments.json` exists
- `creative_requirements.json` exists

## 1. Prepare Prompt

Each segment prompt must include:

- priority hierarchy
- exact narration when narration is required
- duration based on narration length
- no generated subtitles/text/Logo/watermark
- reference strategy and reference count
- expected confirmation phrase

Before asking for approval, audit the prompt:

```bash
python3 scripts/ai_video_trial.py audit-generation-plan \
  --run-dir "data/runs/<run-id>" \
  --segment <N> \
  --prompt-file "<prompt-file>" \
  --duration <seconds> \
  --image-count <n> \
  --video-count <n> \
  --audio-count <n> \
  --exact-cta \
  --strict
```

If it is blocked, fix the prompt before showing it to the user.

Notify DingTalk for Prompt Gate:

```bash
python3 scripts/ai_video_trial.py notify-safety-gate \
  --run-dir "data/runs/<run-id>" \
  --gate "Prompt Gate" \
  --segment <N> \
  --status "待用户审核" \
  --action "请审核完整提示词和风险审计；确认后回复指定确认语" \
  --gate-file "<risk-audit-or-prompt-file>"
```

## 2. Ask User For Approval

Show the user:

- full prompt
- model
- duration
- ratio
- references
- risk audit report
- exact confirmation phrase

Accepted confirmation format:

```text
确认生成 Segment XX
确认生成 Segment XX 重跑A
确认生成 Segment XX 重跑E
```

Do not infer confirmation from casual approval if the version is unclear.

## 3. Submit To Dreamina

Use `dreamina-submit-video`; it automatically runs the risk audit before submitting.

```bash
python3 scripts/ai_video_trial.py dreamina-submit-video \
  --run-dir "data/runs/<run-id>" \
  --segment <N> \
  --mode multimodal2video \
  --image "<character-image>" \
  --prompt "<prompt>" \
  --session <dreamina-session-id> \
  --duration <seconds> \
  --ratio 9:16 \
  --model-version seedance2.0fast_vip \
  --video-resolution 720p \
  --poll 0 \
  --user-confirmed
```

For exact CTA segments, add:

```bash
--exact-cta
```

After submit succeeds, notify Submit Gate:

```bash
python3 scripts/ai_video_trial.py notify-safety-gate \
  --run-dir "data/runs/<run-id>" \
  --gate "Submit Gate" \
  --segment <N> \
  --status "已提交" \
  --action "只查询当前 submit_id，不自动重提" \
  --gate-file "run_docs/state/<dreamina-submit-report>.json"
```

Only skip audit with explicit user approval:

```bash
--skip-risk-audit
```

## 4. Query Existing Submit ID

Only query the known submit id. Do not resubmit unless the user confirms a rerun.

```bash
python3 scripts/ai_video_trial.py dreamina-query-result \
  --submit-id "<submit-id>" \
  --download-dir "data/runs/<run-id>/returned"
```

If still generating, report status and keep waiting.

For long-running generation, notify Query Gate:

```bash
python3 scripts/ai_video_trial.py notify-safety-gate \
  --run-dir "data/runs/<run-id>" \
  --gate "Query Gate" \
  --segment <N> \
  --status "仍在生成" \
  --action "继续等待同一个 submit_id；不重新提交"
```

## 5. Stable File Name

Copy the returned video to a stable segment name:

```bash
cp "returned/<submit-id>_video_1.mp4" "returned/SegmentXX_rerunY.mp4"
```

## 6. One-Command Safe Review

Run this before asking the user to accept the segment:

```bash
python3 scripts/ai_video_trial.py safe-review-segment \
  --run-dir "data/runs/<run-id>" \
  --segment <N> \
  --video "returned/SegmentXX_rerunY.mp4" \
  --target-text "<target-narration>" \
  --must-include "<term|alias,term|alias>" \
  --strict-terms
```

This creates:

- segment review
- voiceover verification
- visual artifact audit
- safe review summary

If no narration is required, omit `--target-text` and `--must-include`.

## 7. Notify DingTalk

Use `--notify-dingtalk` with `safe-review-segment` whenever possible. If a separate notification is needed:

```bash
set -a; source ./.env; set +a

python3 scripts/ai_video_trial.py notify-dingtalk \
  --run-dir "data/runs/<run-id>" \
  --segment <N> \
  --stage review \
  --review-file "reviews/segment_XX/safe_review_summary.md" \
  --decision "待用户审核" \
  --reviewer "请审核台词、画面文字、Logo/水印风险；未通过前不继续"
```

## 8. Wait For User Decision

Only these decisions move the state:

```text
Segment XX 可进入下一段
Segment XX 建议重跑
Segment XX 必须重跑
```

Record approved decisions:

```bash
python3 scripts/ai_video_trial.py record-review-decision \
  --run-dir "data/runs/<run-id>" \
  --segment <N> \
  --decision 可进入下一段 \
  --reviewer user
```

## 9. Final Export

Only use accepted segments for final export.

```bash
python3 scripts/ai_video_trial.py final-export \
  --run-dir "data/runs/<run-id>" \
  --segments 1,2,3,4 \
  --logo "<official-logo-path>" \
  --name "<final-output-prefix>"
```

If any segment is pending but the user asks to see a splice, label it as `review_splice`, not final.

Notify Export Gate after export:

```bash
python3 scripts/ai_video_trial.py notify-safety-gate \
  --run-dir "data/runs/<run-id>" \
  --gate "Export Gate" \
  --status "已生成审核版/正式版" \
  --action "请审核完整成片、QC报告、抽帧图和已知风险" \
  --gate-file "edit/<qc-report>.md"
```

## 10. Delivery Log

At handoff, provide:

- final/review video path
- `safe_review_summary.md` for each segment
- full prompt log Excel
- Dreamina submit ids and credit counts
- known warnings and accepted caveats

## Stop Immediately If

- prompt was not shown to user
- confirmation phrase does not match current version
- risk audit is blocked
- submit_id is unclear
- DingTalk notification failed
- safe review is missing
- user has not accepted the current segment
- final export is requested with pending segments and not labeled review_splice
