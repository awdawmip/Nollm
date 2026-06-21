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
source_range_hash
text_hash
```

The relation is bidirectional: the published SourceSpan projection lists `related_shard_ids`, and the DreamShard lists the same `span_id` in `continuity_refs`. Validation rejects either side if the other side is missing, if the archive URI does not exactly match the span byte range, or if any link field disagrees with the shard, receipt, publication package, snapshot, or revision.

## Text Normalization

Legacy import uses one canonical function:

```text
nollm.legacy_text_normalization.v1
```

Rules:

1. Decode the archive byte range as strict UTF-8.
2. Treat every Unicode whitespace run as one ASCII space.
3. Strip leading and trailing whitespace.

DreamShards store:

- `source_range_hash`: SHA-256 of the raw archive bytes selected by `source_ref`.
- `text`: canonical normalized text.
- `text_hash`: SHA-256 of UTF-8 bytes of `text`.
- `normalization_id`: `nollm.legacy_text_normalization.v1`.

The extractor, idempotence key, shard construction, and provenance validator must use this same function.

## Batch State

The batch state machine is monotonic:

```text
planned -> staged -> validated -> publishing -> committed
planned | staged | validated | publishing -> failed | quarantined
```

`failed`, `quarantined`, and `committed` are terminal for that batch. Repeating plan after commit returns the committed state and preserves existing request, receipt, and publication manifest bytes. Duplicate commit returns the existing receipt and revision without semantic change. Recovery that cannot finish a safe `publishing -> committed` transition must create a replacement batch rather than move `failed -> validated`.

## Atomic Publish

Commit prepares shards, span links, source-span projection, a revision candidate, receipt candidate, and artifact hash manifest under staging. Staged validation must pass before any active path is updated.

Publication is revision-scoped:

```text
field/publications/<field_revision_id>/
  revision.json
  shards/
  source-span-links.jsonl
  source-span-projection.jsonl
  receipt.json
  artifact-hashes.json
```

`field/HEAD.json` is the only active visibility pointer and must be written last. Active readers, dedupe, coverage, provenance, and reports read from the HEAD publication package, not from staged files or generic physical directories.

Failures are recorded in `failure.json` and the ledger with a structured code. Pre-HEAD artifacts are not completion proof. Validators must reject unpublished physical revisions with `unpublished_revision:<revision_id>`.

Legacy v1 shard/revision files outside a publication package are compatibility artifacts only; they are not MT1 completion proof.

## Default State

Legacy shards use:

- `origin_kind: legacy_import`
- `operational_state: loose`
- `epistemic_state`: from source policy, usually `legacy_recorded` or `tentative`

Legacy text is not automatically confirmed.
