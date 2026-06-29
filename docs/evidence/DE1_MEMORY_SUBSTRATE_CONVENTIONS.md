# DE1 Memory Substrate Conventions

Memory Substrate records are deliberately narrow.

Dream Shards preserve original expression, origin, and temporal context.
Interpretations are separately stored statements supplied by callers. Revision
Threads are explicit relations and do not choose a single truth. Usage State is
current use posture only.

An Interpretation subject is always a Dream Shard. DE1 does not model
interpretation-of-interpretation chains; relations among interpretations must be
represented explicitly through revision threads or later-stage objects, not by
changing the subject domain.

The store is single-process, single-writer, and file-first. It uses canonical
JSON and JSONL ledger events for deterministic replay in synthetic and local
tests. It does not provide concurrency, migration, external verification,
authorization, redaction, or deletion workflows.

Every durable record must have one matching ledger event, and every ledger event
must resolve back to one durable record. Reopen fails on orphan objects, orphan
events, duplicate events, filename/payload ID mismatch, or cross-bucket record
ID collision. These checks preserve the memory history spine; they do not claim
cryptographic protection against manual edits.
