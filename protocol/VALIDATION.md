# Validation

Validation keeps Nollm Core deterministic before runtime implementation exists.

## Minimum Invariants

- Card statuses must be valid according to `protocol/STATUS.md`.
- Card types must be valid according to `protocol/TYPES.md`.
- Card anchors must exist in the notebook anchor set.
- Aliases must target existing anchors.
- Ledger event IDs must be unique within a notebook.
- Every card must have a creation ledger event.
- Every status change must have a ledger event.
- `confirmed` transitions require explicit operator approval in v0.1.
- Recall source addresses must resolve or be marked external.
- Derived indexes must be rebuildable from Markdown, YAML, JSON, and JSONL source files.

## Recall Digest Invariants

Recall digest JSON files must include the current recall key set:

- `query_or_task`
- `memory_intent`
- `anchors_used`
- `cards_read`
- `recalled_points`
- `warnings`
- `do_not_assume`
- `source_addresses`
- `open_questions`
- `active_anchor_fields`
- `scale_path`
- `lateral_recovery`
- `sufficient_scale_reached`

`memory_intent` must use the Cortex memory intent vocabulary. Old shortcut values such as `focus` are invalid.

Scale-scan metadata is structural metadata only. `active_anchor_fields` must be a list of strings. `scale_path` must be a list of mappings with a non-negative integer `layer`, string `card`, list-of-string `anchor_fields`, and optional string `note`. `lateral_recovery` must be a list. `sufficient_scale_reached` must be a boolean.

Validation does not infer semantic completeness, geometry correctness, or recall quality from these fields.

Validation treats `confirmed` and `human-approved` as lifecycle and provenance metadata. It does not validate factual truth, permanent correctness, or operator oracle authority.

## Audit Report Invariants

Audit reports are deterministic derived projections over existing notebook files.

An audit report may summarize validation results, cards, anchors, anchor fields, honeycomb metadata, recall digest metadata, and ledger event counts. Audit generation is read-only and must not append ledger events.

Audit output is not memory, not a recall index, and not source of truth. Deleting audit output must not change recall behavior.

P6.0 audit does not use SQLite.

## P5.4 Metadata Invariants

Honeycomb metadata remains optional for backward compatibility. When present:

- `layer` must be a non-negative integer.
- `hex` must be a mapping with integer `q` and integer `r`.
- `hex.rotation`, when present, must match `(layer * 22.5) mod 60`.
- `hex.scale`, when present, must match `2 ** (-layer / 4)`.
- Rotation or scale metadata without a valid layer is invalid.

Anchor field metadata remains optional. When present:

- `anchor_fields` must be a mapping.
- Each key must be a non-empty string.
- Each value must be a mapping.
- `weight` is required and must be between `0.0` and `1.0`.
- `role`, when present, must be `primary`, `supporting`, `adjacent`, `boundary`, `recovery`, or `warning`.
- Anchor field keys are influence labels, not ownership paths, and do not need to exist in the anchor registry in P5.4.

Scale link metadata remains optional. When present:

- `scale_links` must be a mapping.
- Allowed keys are `coarser`, `finer`, `overlaps`, and `recovery`.
- Values must be lists of non-empty strings.
- Parent, children, and leaf semantics are not canonical scale-link concepts.

P5.4 validates honeycomb metadata but does not perform automatic geometric placement.
P5.4 validates anchor field weights but does not treat anchors as folders.
P5.4 validates scale links but does not introduce parent/children or leaf semantics.

## Non-Goals

Validation must not infer ontology, generate anchors automatically, call external LLMs, build embeddings, place cards automatically, calculate polygon overlap, or mutate memory autonomously.

## MT1-R11 Active Publication Validation

Active MT1 validation uses one complete archive-bound predicate. A publication is active only when HEAD binding, manifest closure, activation binding, package semantics, archive manifest validity, contained regular paths, canonical source inventory, exact projection/link closure, full importable coverage, and source-derived shard profile all pass.

Malformed archive, source-span, ingress, ledger, or publication files must produce structured validation errors, not parser/type exceptions. MT1-R11 requires ArchiveManifest v4 `sources[]`; v2/v3 artifacts require rearchive/reimport.

R10 validates exact authoritative schemas for HEAD, receipt, revision, activation, publication manifest, source-span projection, source-span links, publish journal, handoff, state, and import request. Unknown authoritative fields deactivate the package or mark ingress untrusted. Receipt target field, revision field, activation field, manifest field, and HEAD field must all match. Batch ids are grammar-checked everywhere they appear.

Source-span inventory is full-record canonical provenance. Validation rebuilds it from verified archive blobs and compares schema, source object, original path, content hash, byte range, locator, text hash, lifecycle, disposition, reason, related shard ids, origin kind, epistemic state, and operational state. Source-span projection may alter only controlled linked lifecycle fields under exact relation closure.

Strict JSON applies to authoritative MT1 files: duplicate keys, non-finite numbers, booleans in integer fields, unknown fields, and unexpected arrays/scalars fail closed. Read/validate/report/admit APIs must not create a missing memory root. SafeStorage rejects symlink/reparse traversal and hard-linked authoritative files.
