# AI Video Safe Pipeline Handoff Index - 2026-05-21

Use this file as the entry point when another operator continues the AI video workflow.

## Read First

1. `docs/AI_VIDEO_OPERATOR_RUNBOOK_V0_2_20260521.md`
2. `docs/AI_VIDEO_SAFE_PIPELINE_V0_2_20260521.md`
3. `docs/AI_VIDEO_NEXT_RUN_PREFLIGHT_TEMPLATE_20260521.md`
4. `docs/AI_VIDEO_OPERATOR_PROMPTS_V0_2_20260521.md`
5. `docs/reports/AI_VIDEO_SAFE_PIPELINE_CHECKLIST_V0_2_20260521.xlsx`

## Current Tooling Added

| Command | Purpose |
|---|---|
| `audit-generation-plan` | Checks prompt risk before spending Dreamina credits. |
| `dreamina-submit-video` | Now runs risk audit automatically after user confirmation. |
| `verify-voiceover` | Extracts audio, runs Whisper, compares generated narration to target text. |
| `audit-visual-artifacts` | Extracts frames/crops and flags text/logo/watermark risks. |
| `safe-review-segment` | Runs review package + voiceover check + visual audit + summary in one command. |

## Minimum Safe Segment Flow

```bash
# 1. Audit prompt before asking user to generate
python3 scripts/ai_video_trial.py audit-generation-plan ...

# 2. Submit only after exact user confirmation
python3 scripts/ai_video_trial.py dreamina-submit-video ... --user-confirmed

# 3. Query existing submit_id only
python3 scripts/ai_video_trial.py dreamina-query-result --submit-id "<submit-id>" --download-dir "data/runs/<run-id>/returned"

# 4. Run one-command safe review
python3 scripts/ai_video_trial.py safe-review-segment ...

# 5. Wait for user decision
python3 scripts/ai_video_trial.py record-review-decision ... --decision 可进入下一段
```

## Safety Meaning

Automation can produce:

- `pass`
- `warning`
- `blocked`
- `needs_human_review`

None of these equals final acceptance. Only the user's explicit decision accepts a segment.

## Operator Conversation Prompts

For copy-ready user-facing messages, use:

```text
docs/AI_VIDEO_OPERATOR_PROMPTS_V0_2_20260521.md
```

It contains start prompts, approval prompts, polling updates, returned-review messages, rejection messages, final splice messages, strict stop messages, and a handoff prompt for another Codex thread.

## Known Limitations

- Visual artifact audit is heuristic, not OCR.
- Whisper tiny is fast but can misrecognize Cantonese and English brand names.
- `--must-include` supports aliases to reduce false negatives.
- Exact CTA segments should not use audio reference unless user explicitly accepts wording risk.
- Pending segments can be spliced only as `review_splice`, not final.

## Next Recommended Improvements

1. Add real OCR when an OCR engine is available.
2. Add a delivery-package command that includes all safe review summaries automatically.
3. Add a prompt template generator that calculates duration from narration length.
4. Add a GitHub upload helper for public/private safe packaging.
