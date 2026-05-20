# Project Overview

## Goal

Build a semi-automated AI video production workflow for VIP THINK that keeps human confirmation in control while reducing repetitive production work, wrong-dialogue generation, and file/version mistakes.

## User Value

The project creates a safer production loop for AI-generated video: each video binds to its own production identity, prompts and generation steps are gated, segment decisions are traceable, smart edits can be produced, and teammates can review the workflow without receiving raw private assets.

## Scope

Included in the working project:
- project-level Name Gate for video name, output name, Jimeng dialogue, and workspace
- generation confirmation gates that block unapproved generation
- dedicated Jimeng browser workflow
- generated segment lifecycle and rerun/take handling
- smart edit / stitching workflow
- logo and subtitle post-production direction
- QC report and review material direction
- team handoff package for controlled collaboration
- segment/take naming rules
- gate status tracking
- guidance to keep one video inside one bound Jimeng dialogue
- handling of known issues such as unwanted embedded subtitles and visual identity drift
- delivery package governance

Excluded from this clean repo:
- generated videos
- source videos
- extracted frames
- private prompts
- source-video breakdowns
- real Jimeng workspace URLs or account context
- browser session state
- webhook secrets
- local run-state files with operational context

## Leadership Message

This work shows a practical path from manual AI video experimentation to a governed production pipeline. It avoids unsafe fully unattended generation, keeps review responsibility clear, reduces repeated manual operations, and creates a reusable process for future AI video batches.

The latest production validation shows that the pipeline can move real segmented work forward while still exposing quality blockers early. The current bottleneck is not basic automation, but final CTA narration precision, which is a concrete next optimization target.
