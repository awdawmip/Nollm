# Ledger

The ledger is an append-only JSONL record of memory events.

## Purpose

The ledger makes Nollm auditable. It records what changed, when it changed, and which Core object was affected.

## Event Shape

Each line is one JSON object.

Required fields:

- `event_id`
- `op`
- `actor`
- `actor_type`
- `from_status`
- `to_status`
- `reason`
- `timestamp`
- `object_type`
- `object_id`
- `address`

Recommended fields:

- `action`: Backward-compatible human label for `op`.
- `supersedes`
- `replaces`

## Append-Only Invariants

- Ledger events are appended, not rewritten.
- Each event ID is unique within a notebook.
- Each event records the affected object and canonical address.
- Status changes must record `from_status` and `to_status`.
- Operator approval must be visible when promoting to `confirmed` in v0.1.
- Correction events should append a new event rather than editing history.
- Derived indexes must be rebuildable from ledger and source files.

## Core Boundary

Core may validate and append ledger events. Cortex may explain why an event should exist, but the ledger remains the audit trail.
