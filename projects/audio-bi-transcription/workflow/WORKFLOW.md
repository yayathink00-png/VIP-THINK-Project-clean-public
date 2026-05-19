# Workflow

## High-Level Flow

```text
BI export or captured Smartbi request
  -> latest file detection or explicit file input
  -> preflight count and safety check
  -> run folder and state database
  -> recording download
  -> optional Whisper transcription
  -> optional structured sync
  -> optional audio attachment upload
  -> report and failure summary
  -> targeted retry
```

## Operating Modes

- Download only: preserve recordings for later processing.
- Transcription trial: sample a limited number of calls.
- Full batch: download, transcribe, and sync reviewed results.
- Retry mode: continue from failed records instead of restarting the batch.
- Dry run: read inputs and print the plan without performing the risky steps.
- Wizard mode: guide the operator through date, model, sync, attachment, and cleanup choices.

## Work Details Worth Reporting

- The project does not assume one perfect path. It supports both clean exported files and captured Smartbi requests.
- The run directory design gives every batch a durable audit trail.
- Failed rows are not lost inside terminal output; they are recorded and can be retried.
- Audio retention is treated as a safety decision, not an accident.
- Sync is flexible enough for daily tables, separate documents, or folder-based organization.

## Governance Gates

- No raw exports in public Git.
- No downloaded audio in public Git.
- No credentials or cookies in public Git.
- Batch artifacts stay local or in approved private storage.
- Reports must be anonymized before broader sharing.

