# Project Overview

## Goal

Build a repeatable pipeline for BI call records: ingest exported call tables, download recordings, transcribe audio, sync structured results, and preserve run-level accountability.

## User Value

This project turns scattered call recordings into reviewable text assets. It helps sales, operations, and management inspect conversations, identify failure patterns, and build a reusable data foundation for coaching, quality control, and follow-up analysis.

## Scope

Included in the working project:
- manual export-table ingestion
- Smartbi captured-export ingestion
- latest-export detection from a download folder
- recording download orchestration
- Whisper/faster-whisper transcription
- connected-call-only filtering
- preflight and safety checks
- batch state tracking through a local state database
- failure retry by processing stage
- sync to a structured collaboration table
- optional audio attachment upload
- optional local audio cleanup after upload
- run reports, failure CSVs, and manifest output
- interactive run wizard for non-command-line users

Excluded from this clean repo:
- real BI exports
- audio files
- customer/user rows
- cookies or browser session state
- platform credentials and resource identifiers

## Leadership Message

This work demonstrates the move from manual call review to a governed automation workflow: fewer repeated manual steps, clearer failure recovery, better batch evidence, and a foundation for sales/operations quality review.

