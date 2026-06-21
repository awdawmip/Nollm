# Legacy Import Protocol

Status: MT1.

Legacy import converts sealed archive spans into native DreamShards with provenance. It does not confirm facts, place geometry, or create active recall fallback.

## Request

`LegacyImportRequest` includes:

- `schema`: `nollm.legacy_import_request.v1`
- `batch_id`
- `snapshot_id`
- `target_field_id`
- `source_policy_id`
- `dedupe_policy`
- `geometry_policy`
- `created_at`

## Idempotence

The idempotence key is SHA-256 over:

```text
nollm.legacy_import.idempotence.v1\0
normalized_shard_text\0
canonical ordered source-span refs\0
source_policy_id
```

Repeating the same commit must not create logical duplicate shards.

## Staging

Commit uses staging, validates archive, coverage, provenance, and shard records, then atomically publishes a field revision. Failure must not update `field/HEAD.json`.

## SourceSpanLink

MT1-R1 writes immutable relation records during commit:

```text
schema: nollm.source_span_link.v1
snapshot_id
batch_id
span_id
shard_id
source_ref
text_hash
field_revision_id
```

The relation is bidirectional: the SourceSpan lists `related_shard_ids`, and the DreamShard lists the same `span_id` in `continuity_refs`. Validation rejects either side if the other side is missing or if the archive URI does not exactly match the span byte range.

## Batch State

The batch state machine is monotonic:

```text
planned -> validated -> committed
planned -> failed | quarantined
validated -> failed | quarantined
```

Repeating plan after commit returns the committed state and preserves existing request and receipt bytes. Duplicate commit returns the existing receipt and revision without semantic change.

## Atomic Publish

Commit prepares shards, span links, a revision candidate, and a receipt candidate under staging. Staging validation must pass before any active field path is updated. `field/HEAD.json` is the final visibility point. Active shard indexes only consider shards listed by the published revision referenced by HEAD.

## Default State

Legacy shards use:

- `origin_kind: legacy_import`
- `operational_state: loose`
- `epistemic_state`: from source policy, usually `legacy_recorded` or `tentative`

Legacy text is not automatically confirmed.
