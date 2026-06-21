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

## Default State

Legacy shards use:

- `origin_kind: legacy_import`
- `operational_state: loose`
- `epistemic_state`: from source policy, usually `legacy_recorded` or `tentative`

Legacy text is not automatically confirmed.
