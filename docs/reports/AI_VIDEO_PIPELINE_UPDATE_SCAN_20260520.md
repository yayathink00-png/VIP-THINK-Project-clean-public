# AI Video Pipeline Update Scan - 2026-05-20

## Summary

This update records the next production-cycle validation of the AI video automation workflow. The work moved beyond a single handoff/runbook milestone and tested a real segmented production loop with prompt previews, human approval gates, automated generation submission, async result checks, returned-video review, and leadership reporting.

## What Advanced Today

- Validated a four-segment AI video production structure using a guarded semi-automation process.
- Completed human-reviewed production for the first three story segments.
- Ran multiple final CTA segment strategies and isolated the main unresolved quality issue: long-form multilingual narration can still drift in the latter half of the line.
- Confirmed that a lighter reference strategy can improve generation stability compared with overloading the model with multiple source references.
- Produced a daily progress report and handoff-style evidence package suitable for leadership review without exposing private assets.

## Current Segment Status

| Segment | Status | Public-Safe Summary |
|---|---|---|
| Segment 01 | Accepted | Establishes the opening learning-result contrast. |
| Segment 02 | Accepted | Continues the proof/verification moment. |
| Segment 03 | Accepted | Explains the method behind the improvement. |
| Segment 04 | Needs more iteration | CTA structure is close, but narration accuracy still needs stabilization. |

## Workflow Chain Confirmed

1. Requirement and output naming are confirmed first.
2. Source structure is broken into safe production beats.
3. Segment-level prompts are drafted and stored before generation.
4. A human approval gate is required before any generation action.
5. Automation submits the approved generation package and records the run state.
6. Async generation status is queried by the automation layer.
7. Returned videos are downloaded and named consistently.
8. Review records and frame summaries are created for decision-making.
9. Review notifications are sent through the team workflow.
10. The next segment only proceeds after an explicit accept/rerun decision.
11. Daily progress is summarized for leadership and future operators.

## Quality Lessons

- Video generation quality depends on the full package: prompt, references, narration length, review criteria, and state tracking.
- Too many references can make the model less stable, even when the visual target is clearer.
- Narration accuracy needs its own pass/fail gate, especially for multilingual or longer CTA lines.
- A production workflow needs rollback and rerun records, not only final outputs.
- Public reporting should summarize the workflow and outcomes without exposing raw media, prompt packs, platform state, or operational identifiers.

## Current Risk

The workflow is functioning, but final CTA narration reliability remains the key quality blocker. The next production attempt should reduce narration complexity or separate precise audio control from visual generation if needed.

## Public Repository Boundary

This report intentionally excludes generated videos, source media, private prompts, platform identifiers, notification details, local paths, and account/session information.
