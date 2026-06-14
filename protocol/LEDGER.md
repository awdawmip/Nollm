# Ledger

The ledger is an append-only JSONL record of memory events.

## Purpose

The ledger makes Nollm auditable. It records what changed, when it changed, and which Core object was affected.

Ledger is an audit trail, not memory recall. Ledger/history do not prove truth. Ledger/history do not approve memory. Ledger/history do not change status or trust. Ledger/history are read-only unless an explicit write action such as annotate/status is used.

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
- `annotation_type`: Type of operator annotation when `op` is `annotate_card`.
- `annotation`: Operator note text when `op` is `annotate_card`.

## Append-Only Invariants

- Ledger events are appended, not rewritten.
- Each event ID is unique within a notebook.
- Each event records the affected object and canonical address.
- Status changes must record `from_status` and `to_status`.
- Annotation events must record equal `from_status` and `to_status`; annotations are not status transitions.
- Operator approval must be visible when promoting to `confirmed` in v0.1.
- Correction events should append a new event rather than editing history.
- Derived indexes must be rebuildable from ledger and source files.

## Annotation Events

Annotations are operator notes. Annotations are ledgered. Annotations do not modify card content, change status, change trust, prove truth, approve memory, block LLM usage, or create passive human review.

Annotation events use `op: annotate_card`. Listing annotations is a read action over ledger events.

## Query And History

Ledger queries may filter by object, operation, actor, actor type, and limit. History is object-level ledger inspection for one card or object.

Annotation text may appear in history because history is explicit audit inspection, but annotation text is still not recall content.

## Core Boundary

Core may validate and append ledger events. Cortex may explain why an event should exist, but the ledger remains the audit trail.
