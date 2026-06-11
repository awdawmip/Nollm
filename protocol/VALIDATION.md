# Validation

Validation keeps Nollm Core deterministic before runtime implementation exists.

## Minimum Invariants

- Card statuses must be valid according to `protocol/STATUS.md`.
- Card types must be valid according to `protocol/TYPES.md`.
- Card anchors must exist in the notebook anchor set.
- Aliases must target existing anchors.
- Ledger event IDs must be unique within a notebook.
- Every card must have a creation ledger event.
- Every status change must have a ledger event.
- `confirmed` transitions require explicit human approval in v0.1.
- Recall source addresses must resolve or be marked external.
- Derived indexes must be rebuildable from Markdown, YAML, JSON, and JSONL source files.

## Non-Goals

Validation must not infer ontology, generate anchors automatically, call external LLMs, build embeddings, or mutate memory autonomously.

