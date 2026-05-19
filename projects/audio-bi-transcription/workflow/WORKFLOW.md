# Workflow

## High-Level Flow

```text
BI export or captured export request
  -> preflight count and safety check
  -> recording download
  -> optional transcription
  -> optional structured sync
  -> batch report
  -> failure retry
```

## Operating Modes

- Download only: preserve recordings for later processing.
- Transcription trial: sample a limited number of calls.
- Full batch: download, transcribe, and sync reviewed results.
- Retry mode: continue from failed records instead of restarting the batch.

## Governance Gates

- No raw exports in public Git.
- No downloaded audio in public Git.
- No credentials or cookies in public Git.
- Batch artifacts stay local or in approved private storage.
- Reports must be anonymized before broader sharing.

