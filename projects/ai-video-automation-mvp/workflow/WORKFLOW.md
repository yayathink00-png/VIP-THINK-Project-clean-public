# Workflow

## High-Level Flow

```text
new video requirement
  -> create guarded run
  -> bind Name Gate
  -> prompt approval package
  -> dedicated Jimeng browser preflight
  -> explicit human confirmation
  -> AI video segment generation
  -> segment review and rerun/take decision
  -> state reconciliation
  -> smart edit / stitching
  -> delivery package and teammate handoff
```

## Key Control Point

The workflow is intentionally not fully unattended. Generation should only start after explicit human confirmation of the current video identity, Jimeng dialogue, final output name, workspace, and prompt package. This protects budget, brand quality, and responsibility boundaries.

## Name Gate Rule

```text
One video project = one bound Jimeng dialogue.
All segments, reruns, and takes for that video stay in that dialogue.
The next video project creates and binds a new dialogue.
```

The dedicated browser can be reused. The production dialogue cannot be reused across unrelated videos.

## Work Details Worth Reporting

- The pipeline treats AI generation as a controlled production process, not a one-click black box.
- Segment generation is allowed to pause, rerun, or move forward based on explicit review.
- The process identified practical AI-video risks: wrong conversation selection, embedded subtitle leakage, inconsistent口播, visual identity drift, and unstable page automation.
- The stable operating model is guarded semi-automation: Codex prepares and checks the workflow, while the user approves high-risk generation and quality decisions.
- The next engineering step is quality automation, including visual identity checks, black/green screen detection, OCR risk checks, and final subtitle/CTA automation.

## Governance Gates

- No source videos in public Git.
- No generated videos in public Git.
- No extracted frames in public Git.
- No private prompt packs in public Git.
- No webhook secrets in public Git.
- No real platform workspace URLs, dialogue identifiers, or account state in public Git.
- No imitation or adaptation notes are public without review.
