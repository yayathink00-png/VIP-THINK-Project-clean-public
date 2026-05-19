# Workflow

## High-Level Flow

```text
account positioning
  -> account DNA and manual patch
  -> Codex skill-based content generation
  -> result import and quality reminders
  -> Notion content sync
  -> Codex image workflow
  -> image preview and archive sync
  -> publish gate checks
  -> single-item publish payload preview
  -> safe handoff
```

## Control Points

- Do not expose platform credentials or token names as operational instructions.
- Do not publish generated images without review.
- Keep account strategy and private positioning details inside approved internal spaces.
- Use checklists before release or handoff.

## Work Details Worth Reporting

- Step 2 was not left as static form filling; it became the structured source of truth for downstream generation.
- Step 4 reduced manual prompt copying by letting the local backend start Codex generation and import results.
- Step 4 Notion sync turned generated content into managed documents rather than loose exports.
- Step 5 turned image generation into a trackable queue with status polling and preview.
- Step 6 intentionally stops before publishing: it prepares and validates, but does not call the real publish action without final confirmation.

## Governance Gates

- No raw checkpoint folder migration by default.
- No private agent prompt migration by default.
- No local login/cookie state in Git.
- No generated content exports in public Git.

