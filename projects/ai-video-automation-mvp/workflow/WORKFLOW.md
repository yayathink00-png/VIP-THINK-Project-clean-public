# Workflow

## High-Level Flow

```text
human segment approval
  -> AI video generation
  -> generated segment download
  -> FFmpeg trial edit
  -> QC notes
  -> review notification
```

## Key Control Point

The workflow is intentionally not fully unattended. Generation should only start after an explicit human confirmation. This protects budget, brand quality, and responsibility boundaries.

## Governance Gates

- No source videos in public Git.
- No generated videos in public Git.
- No extracted frames in public Git.
- No private prompt packs in public Git.
- No webhook secrets in public Git.
- No imitation or adaptation notes are public without review.

