# Workflow

## High-Level Flow

```text
creative requirement and source analysis
  -> segment prompt and generation gate
  -> human confirmation
  -> AI video generation
  -> generated segment download
  -> segment review and gate status update
  -> FFmpeg trial edit
  -> QC notes and review notification
```

## Key Control Point

The workflow is intentionally not fully unattended. Generation should only start after an explicit human confirmation. This protects budget, brand quality, and responsibility boundaries.

## Work Details Worth Reporting

- The MVP treats AI generation as a controlled production process, not a one-click black box.
- Segment generation is paused when the larger pipeline needs validation, instead of blindly producing more assets.
- The process identified practical AI-video risks: embedded subtitle leakage, inconsistent口播, and unstable page automation.
- The next engineering step is clear: preflight the generation page before any new segment is created.

## Governance Gates

- No source videos in public Git.
- No generated videos in public Git.
- No extracted frames in public Git.
- No private prompt packs in public Git.
- No webhook secrets in public Git.
- No imitation or adaptation notes are public without review.

