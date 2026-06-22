# Archive Protocol

Status: MT1.

The Archive plane preserves raw legacy records before any interpretation. Archive objects are content-addressed by SHA-256 and are not active recall input.

## ArchiveManifest

`ArchiveManifest` records one snapshot:

- `schema`: `nollm.archive_manifest.v4`
- `snapshot_id`
- `created_at`
- `workspace_identity`
- `workspace_identity_scheme`
- `source_policy_id`
- `sources`
- `snapshot_seed_hash`
- `manifest_hash`
- `archive_manifest_hash`

`manifest_hash` is computed from canonical JSON with `manifest_hash` and `archive_manifest_hash` set to `null`.

## Archive Source

Each canonical source entry records:

- `source_object_id`
- `original_relative_path`
- `content_hash`
- `byte_length`
- `line_count`
- `encoding`
- `newline_profile`
- `archived_path`
- `origin_kind`
- `epistemic_state`
- `operational_state`

Archive bytes are copied exactly. Text decoding and source state are derived from the fixed source policy, not trusted from mutable manifest text.

## SourceSpan

Coverage uses byte ranges: `[start_byte, end_byte_exclusive)`. Line ranges are display aids only.

Every byte range has a lifecycle:

- `inventoried`: byte range was sealed from an ArchiveObject.
- `classified`: deterministic non-memory or import-candidate classification was assigned.
- `linked`: at least one committed DreamShard relation exists.
- `validated`: deep provenance checks have passed against a published field revision.

Every byte range must have one disposition:

- `sharded`
- `non_memory`
- `manual_review`
- `unsupported`

`sharded` is a completed fact, not an import intent. A span is `sharded` only when `related_shard_ids` is non-empty and every linked shard maps exactly back to that span by archive digest, byte range, text hash, and `continuity_refs`.

`non_memory.reason` is controlled. MT1-R1 defines:

- `structural_heading`
- `blank`

The legacy R1 archive source ref grammar was:

```text
archive://object/sha256:<64 lowercase hex digest>#B<start>-B<end>
```

MT1-R9 replaces that legacy grammar with:

```text
archive://snapshot/<snapshot_id>/source/<source_object_id>/blob/sha256:<digest>#B<start>-B<end>
```

`source_range_hash` is `sha256:<digest>` over the raw archived bytes selected by that exact source ref. It is distinct from a DreamShard `text_hash`.

MT1 fixture imports must reach `coverage_ratio == 1.0` with no uncovered, unsupported, or manual-review spans. That ratio means every source span is either deterministic `non_memory` or deeply validated `sharded`.

Published coverage is HEAD-only. A physical revision file, staged relation file, or failed batch projection is not active memory and cannot satisfy `require_linked` coverage unless `field/HEAD.json` points to a complete publication package for that revision.

MT1-R4 makes "complete publication package" a fail-closed admission rule. The HEAD-bound `publication-manifest.json` must be an exact inventory closure of every regular file below the publication directory, excluding the manifest itself. Unmanifested files, missing files, symlinks, absolute paths, parent-directory escapes, backslash paths, or hash mismatches make the publication inactive. Active coverage then sees no published spans.

MT1-R5 extends fail-closed admission to the active trust root. `field/`, `field/HEAD.json`, `field/publications/`, the selected publication directory, and its manifest must be contained beneath the memory root and must not be symlinks. `HEAD.field_id`, `HEAD.field_revision_id`, and `HEAD.publication_manifest_hash` must bind exactly to the publication manifest and revision. Malformed active JSON or JSONL artifacts produce structured validation errors rather than raw parser exceptions.

## Canonical Inventory

R3 treats archive source spans as deterministic facts. Validation must either rebuild canonical source spans from archive object bytes or compare the persisted inventory to an immutable hash bound by the request, receipt, and publication manifest.

The canonical span fields are:

- `snapshot_id`
- `source_object_id`
- `original_relative_path`
- `span_id`
- `start_byte`
- `end_byte_exclusive`
- `text_hash`
- initial `disposition`
- initial `reason`

Published projections are constrained transforms of this canonical inventory:

- canonical `non_memory(blank | structural_heading)` must remain unchanged.
- canonical `classified_pending` may only become `sharded` with exact links and published shards.
- canonical `classified_pending` must not become `non_memory`.
- no projection may change byte ranges, object ids, paths, span ids, or raw text hashes.

Active shard reads are revision-limited. Readers may only enumerate `revision.json.shard_ids`; they must not glob every shard file in the package. Every listed shard must have a matching `shards/<shard_id>.json` payload, and every shard payload in the package must be listed by the revision.

Source-span links are exact publication relations. Every active shard source ref must have exactly one matching link, and every published link must point back to a canonical importable span, the active shard roster, and the projected `sharded` relation. Extra, duplicate, orphan, non-memory, or unprojected links are invalid.

For MT1 `legacy_import` shards, identity is derived from the archive source range. Validation recomputes normalized text, `source_range_hash`, `text_hash`, `idempotence_key`, `shard_id`, and exact `continuity_refs` from the canonical source ref plus source policy. Any mismatch makes the active field untrusted and prevents dedupe or replacement writes.

## Boundaries

Archive snapshot may read legacy files. Archive verify, span inventory, extraction, import, validation, and report must not read source workspace live files.

`NOLLM_MEMORY_ROOT` must be physically outside the source workspace: neither path may contain the other. Source paths are checked with `lstat` before resolution, and any source symlink is rejected.

MT1-R11 distinguishes opening an existing memory root from initializing one. Read, validate, inspect, admit, and report operations must not create a missing memory root. Archive creation validates the source/workspace boundary before creating storage directories.

## MT1-R9 Archive v3

R9 makes source identity and source state policy-derived. Blob identity is the SHA-256 content hash and may be shared by byte-identical files. Source-entry identity is a snapshot-local record and remains distinct for different original paths even when bytes are equal.

`ArchiveManifest` v3 uses `schema: nollm.archive_manifest.v3`, a self-bound `archive_manifest_hash`, and exactly one canonical `sources[]` list. Independent `objects`, `source_entries`, and `archive_object_id` aliases are invalid.

Verification derives and compares:

- `source_policy_id: openclaw_legacy_v1`
- allowed original relative path
- source states from policy (`DREAMS.md` is `tentative`; `MEMORY.md` and `memory/**/*.md` are `legacy_recorded`)
- `source_object_id` from snapshot id, policy id, path, and content hash
- canonical `archived_path`
- blob hash, byte length, encoding, newline profile, and line count

Canonical source refs bind snapshot, source entry, blob hash, and byte range:

```text
archive://snapshot/<snapshot_id>/source/<source_object_id>/blob/sha256:<digest>#B<start>-B<end>
```

Manifest files, blob files, source-span inventories, and every traversed ancestor must stay under `memory_root` and must not be symlinks. Snapshot ids and artifact ids are grammar-checked before path construction.

An archive-only snapshot with no importable spans is successful archive evidence, but it does not create an active field revision and does not block the later first substantive import. R1-R8 archive/source-ref artifacts are not active-compatible after R9 and require rearchive/reimport with `legacy_mt1_archive_v2_requires_rearchive`.

## MT1-R10 Archive Trust Boundary

A self-hash is not a signature. MT1-R10 treats self-hashes as corruption checks only; trust-bearing source identity is rederived from source policy and archived bytes. Unknown ArchiveManifest top-level fields and unknown source-entry fields are invalid. In R10, `created_at` and `workspace_identity` were display/audit metadata; MT1-R11 supersedes that model by binding opaque workspace identity into ArchiveManifest v4 snapshot identity.

Archive source order is canonical by `original_relative_path`. Snapshot reports distinguish `source_count` from `unique_blob_count`, because byte-identical source paths may share one blob.

Canonical source span construction must start from a verified archive view and contained blob reads. It must not construct a filesystem path from mutable manifest text without validating the digest grammar and SafeRoot containment.

## MT1-R11 Archive v4 And SafeStorage

ArchiveManifest v3 is no longer active-compatible and returns `legacy_mt1_archive_v3_requires_rearchive`. New snapshots use `schema: nollm.archive_manifest.v4`.

The snapshot seed includes:

- archive schema
- source policy id
- opaque `workspace_identity`
- `workspace_identity_scheme`
- ordered `(original_relative_path, content_hash)` entries

The default workspace identity is a SHA-256 digest of the canonical absolute workspace root. The raw absolute path is not written into the manifest. `source_object_id` is derived from snapshot id, policy id, workspace identity scheme, workspace identity, original path, and content hash.

If a manifest path for the computed `snapshot_id` already exists:

- byte-identical canonical manifest bytes are reused without rewriting;
- any canonical byte mismatch fails with `snapshot_id_collision`;
- existing blobs are verified read-only and are never repaired in place.

SafeStorage is the archive write boundary. It rejects symlink/reparse paths, rejects hard-linked authoritative files when read or verified, writes blobs and manifests through temporary files in the same controlled directory, and publishes manifests last. Boolean JSON values are not accepted as integers, duplicate JSON keys and non-finite numbers fail closed, and unknown authoritative fields remain invalid.

Source-span inventory is treated as deterministic derived provenance. Active validation rebuilds canonical spans from verified archive blobs and compares the full record, including `schema`, `locator`, `lifecycle`, `reason`, `related_shard_ids`, source states, byte ranges, and hashes.
