# Project Overview

## Goal

Build a repeatable pipeline for BI call records: ingest exported call tables, download recordings, transcribe audio, sync structured results, and preserve run-level accountability.

## User Value

This project turns scattered call recordings into reviewable text assets. It helps sales, operations, and management inspect conversations, identify failure patterns, and build a reusable data foundation for coaching and quality control.

## Scope

Included in the working project:
- export-table ingestion
- recording download orchestration
- Whisper/faster-whisper transcription
- preflight and safety checks
- batch state tracking
- failure retry
- sync to a structured collaboration table
- run reports and failure summaries

Excluded from this clean repo:
- real BI exports
- audio files
- customer/user rows
- cookies or browser session state
- platform credentials and resource identifiers

## Leadership Message

This work demonstrates the move from manual call review to a governed automation workflow: fewer repeated manual steps, clearer failure recovery, and better evidence for operations review.

