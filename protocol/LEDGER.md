# Ledger

The ledger is an append-only JSONL record of memory events.

## Purpose

The ledger makes Nollm auditable. It records what changed, when it changed, and which Core object was affected.

## Event Shape

Each line is one JSON object.

Required fields:

- `event_id`
- `timestamp`
- `action`
- `object_type`
- `object_id`
- `address`

Recommended fields:

- `actor`
- `reason`
- `supersedes`

## Core Boundary

Core may validate and append ledger events. Cortex may explain why an event should exist, but the ledger remains the audit trail.

