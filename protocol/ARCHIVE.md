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

Every non-empty byte range must have one disposition:

- `sharded`
- `non_memory`
- `manual_review`
- `unsupported`

MT1 fixture imports must reach `coverage_ratio == 1.0` with no uncovered, unsupported, or manual-review spans.

## Boundaries

Archive snapshot may read legacy files. Archive verify, span inventory, extraction, import, validation, and report must not read source workspace live files.
