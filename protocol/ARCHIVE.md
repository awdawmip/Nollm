# Archive Protocol

Status: MT1.

The Archive plane preserves raw legacy records before any interpretation. Archive objects are content-addressed by SHA-256 and are not active recall input.

## ArchiveManifest

`ArchiveManifest` records one snapshot:

- `schema`: `nollm.archive_manifest.v1`
- `snapshot_id`
- `created_at`
- `workspace_identity`
- `source_policy_id`
- `objects`
- `manifest_hash`

`manifest_hash` is computed from canonical JSON with `manifest_hash` set to `null`.

## ArchiveObject

Each object records:

- `archive_object_id`
- `original_relative_path`
- `content_hash`
- `byte_length`
- `line_count`
- `encoding`
- `newline_profile`
- `archived_path`

Archive bytes are copied exactly. Text decoding is only metadata.

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

The canonical archive source ref grammar is:

```text
archive://object/sha256:<64 lowercase hex digest>#B<start>-B<end>
```

`source_range_hash` is `sha256:<digest>` over the raw archived bytes selected by that exact source ref. It is distinct from a DreamShard `text_hash`.

MT1 fixture imports must reach `coverage_ratio == 1.0` with no uncovered, unsupported, or manual-review spans. That ratio means every source span is either deterministic `non_memory` or deeply validated `sharded`.

Published coverage is HEAD-only. A physical revision file, staged relation file, or failed batch projection is not active memory and cannot satisfy `require_linked` coverage unless `field/HEAD.json` points to a complete publication package for that revision.

MT1-R4 makes "complete publication package" a fail-closed admission rule. The HEAD-bound `publication-manifest.json` must be an exact inventory closure of every regular file below the publication directory, excluding the manifest itself. Unmanifested files, missing files, symlinks, absolute paths, parent-directory escapes, backslash paths, or hash mismatches make the publication inactive. Active coverage then sees no published spans.

## Canonical Inventory

R3 treats archive source spans as deterministic facts. Validation must either rebuild canonical source spans from archive object bytes or compare the persisted inventory to an immutable hash bound by the request, receipt, and publication manifest.

The canonical span fields are:

- `snapshot_id`
- `archive_object_id`
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

## Boundaries

Archive snapshot may read legacy files. Archive verify, span inventory, extraction, import, validation, and report must not read source workspace live files.

`NOLLM_MEMORY_ROOT` must be physically outside the source workspace: neither path may contain the other. Source paths are checked with `lstat` before resolution, and any source symlink is rejected.
