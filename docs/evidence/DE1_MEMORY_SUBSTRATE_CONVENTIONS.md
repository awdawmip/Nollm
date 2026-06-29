# DE1 Memory Substrate Conventions

Memory Substrate records are deliberately narrow.

Dream Shards preserve original expression, origin, and temporal context.
Interpretations are separately stored statements supplied by callers. Revision
Threads are explicit relations and do not choose a single truth. Usage State is
current use posture only.

The store is single-process, single-writer, and file-first. It uses canonical
JSON and JSONL ledger events for deterministic replay in synthetic and local
tests. It does not provide concurrency, migration, external verification,
authorization, redaction, or deletion workflows.
