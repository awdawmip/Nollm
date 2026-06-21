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
  activation.json
  publication-manifest.json
```

`field/HEAD.json` is the only active visibility pointer and must be written last. Active readers, dedupe, coverage, provenance, and reports read from the HEAD publication package, not from staged files or generic physical directories.

R3 replaces `artifact-hashes.json` with a HEAD-bound publication manifest:

```text
field/publications/<field_revision_id>/publication-manifest.json
```

The manifest records:

- `schema`
- `field_revision_id`
- `field_id`
- `batch_id`
- `snapshot_id`
- `artifact_hashes` for `revision.json`, `receipt.json`, `source-span-links.jsonl`, `source-span-projection.jsonl`, and every `shards/<id>.json`.

`field/HEAD.json` includes:

```text
field_id
field_revision_id
publication_manifest_hash
activation_hash
```

Validation first checks the HEAD manifest hash and activation hash, then every payload artifact hash, then semantic consistency.

MT1-R4 treats the manifest as an exact closure, not a partial hash list. The set of manifest artifact paths must exactly equal the publication payload files, excluding `publication-manifest.json`. Symlinks, path escapes, absolute paths, backslash paths, extra files, missing files, and mismatched hashes make the publication inactive. Revision and receipt metadata must agree with the package: shard counts must match their lists, created shards must be in the revision, and every active shard file must match a `revision.json.shard_ids` entry.

Staged validation is a separate entrypoint. It validates `field/.staging/<batch_id>/publication/` with the same canonical inventory, source ref, text binding, relation, projection, and manifest rules, but without requiring HEAD.

Failures are recorded in `failure.json` and the ledger with a structured code. Pre-HEAD artifacts are not completion proof. Validators must reject unpublished physical revisions with `unpublished_revision:<revision_id>`.

Legacy v1 shard/revision files outside a publication package are compatibility artifacts only; they are not MT1 completion proof.

After atomic HEAD replace succeeds, the publication is truth. Later ledger or journal write failure must not return import failure; it returns published success with `reconciliation_pending`. Reconcile may repair the audit journal to match the verified HEAD package.

The post-HEAD handoff records the candidate revision, candidate manifest hash, prior HEAD, batch id, and publish start time before HEAD is replaced. If a finalization error happens after HEAD and the package is still verified, the batch remains `publishing` and the result is `published: true` with `reconciliation_pending: true`. If package verification fails after HEAD or during reconcile, the batch is quarantined and HEAD is restored to the prior verified value or removed when no prior HEAD existed.

Reconcile is a validator, not a pointer check. It must verify HEAD manifest binding, exact publication closure, revision-limited shard semantics, source-span projection, archive provenance, and coverage before it records `committed`.

MT1-R5 makes finalization durable before terminal state. After HEAD activation, commit or reconcile must verify the active package, write or verify the migration report, write or verify exactly one finalization ledger event, and write `committed` last. If report, ledger, or final state persistence fails first, the batch remains `publishing` and the caller receives `published: true` with `reconciliation_pending: true`. Reconcile is idempotent and repairs missing finalization artifacts before it can mark the batch committed.

The single-snapshot publication schema is non-destructive. If a verified active field already exists, importing a different `snapshot_id` into the same target field is rejected with `cross_snapshot_replacement_not_supported`; targeting a different field under the single `field/HEAD.json` root is rejected with `single_head_field_switch_not_supported`. A future multi-snapshot composition protocol must be explicit before active memory can be replaced or merged across snapshots.

MT1-R6 makes retry behavior state-driven. A `commit` request for a `publishing` batch must delegate to reconciliation only; it must not restage, copy a new publication, replace HEAD, create a second revision, or mark the batch failed merely because the retry was made. A `committed` duplicate request is successful only after the committed receipt, HEAD package, provenance, and finalization ledger are still trusted.

If `field/HEAD.json` exists but the active publication cannot be admitted or deep-validated, all new plan, commit, duplicate, and replacement writes are blocked with `active_field_integrity_unresolved` until an explicit repair or quarantine workflow establishes the field outcome. A corrupt active field is not equivalent to an absent field.

Malformed ingress state, request, receipt, or handoff records fail closed with structured errors. When a `publishing` batch has a trusted handoff, recovery may restore the recorded prior HEAD and quarantine the batch; if the handoff itself is untrusted, callers receive a recovery-required result and no replacement publication may be activated.

Failed and quarantined batches are terminal. Recovery creates a replacement batch with `recovery_of` unless the original batch is in `publishing` and HEAD already points to a valid package, in which case reconcile commits the journal without reimporting.

MT1-R7 separates active publication truth from ingress workflow state. A field becomes active only when `field/HEAD.json` points at a publication package whose `activation.json` is included in the manifest closure and binds the field, revision, batch, snapshot, source policy, receipt hash, revision hash, source-span link hash, source-span projection hash, and the `nollm.legacy_import_shard_profile.v1` profile. `HEAD.json` is written last and is the only active pointer.

Ingress state, import receipts, migration reports, handoffs, and ledger entries are audit/recovery material. They may be required to finalize a batch journal, but they do not authorize active admission, rollback, or replacement. A forged or inconsistent handoff returns structured recovery-required errors and must not redirect HEAD or finalize a batch. The ingress receipt must be canonical-equal to the package receipt for a legacy import validation to succeed.

The R7 legacy-import shard profile is immutable for every shard related to a source span in an MT1 publication. Validation enforces `origin_kind: legacy_import`, `operational_state: loose`, `epistemic_state: legacy_recorded`, exact source refs, exact continuity refs, canonical raw/text hashes, current normalization, recomputed idempotence key and shard id, archive-ingest seed geometry intent, empty anchor weights, and the listed schema fields regardless of the shard's mutable `origin_kind` value. Unknown shard fields are rejected except `created_at`, which is informational and must be a valid UTC timestamp.

## Default State

Legacy shards use:

- `origin_kind: legacy_import`
- `operational_state: loose`
- `epistemic_state`: `legacy_recorded` for MT1 active publication profile

Legacy text is not automatically confirmed.
