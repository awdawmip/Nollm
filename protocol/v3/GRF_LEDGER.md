# GRF Ledger

GRF1-FH uses an append-only JSONL ledger for file-first prototype evidence.

Event fields:

```text
event_id
event_type
object_type
object_id
object_path
object_sha256
recorded_at
previous_event_id
```

Event types:

```text
object_written
object_reopened_same_bytes
object_write_rejected_different_bytes
relation_field_rebuilt
recall_digest_written
stitch_rejected_recorded
```

The ledger is not a database and not a cache. Source object files remain
authoritative for replay.
