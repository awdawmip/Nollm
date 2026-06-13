# Audit Schema

The audit schema is the stable JSON contract for derived notebook inspection.

It is for inspection and governance. It is not a memory schema, not a recall digest schema, and not source memory. Recall must not read audit snapshots.

Audit reports are rebuildable from notebook source files. The current reference implementation must keep every boundary flag false.

## Required Top-Level Sections

- `validation`
- `notebook`
- `cards`
- `honeycomb`
- `anchor_fields`
- `recall_digests`
- `ledger`
- `boundaries`

## `validation`

- `pass`: boolean
- `issue_count`: integer
- `issues`: list

## `notebook`

- `name`: string
- `path`: string
- `cards`: integer
- `anchors`: integer
- `ledger_events`: integer
- `recall_digests`: integer

## `cards`

- `by_status`: object
- `by_type`: object
- `by_trust`: object
- `by_source`: object
- `by_layer`: object

## `honeycomb`

- `cards_with_layer`: integer
- `cards_with_hex`: integer
- `cards_with_anchor_fields`: integer
- `cards_with_scale_links`: integer
- `invalid_honeycomb_metadata_count`: integer

## `anchor_fields`

- `anchor_count`: integer
- `anchor_ids`: list
- `card_anchor_usage_counts`: object
- `anchor_field_usage_counts`: object

## `recall_digests`

- `recall_digest_count`: integer
- `memory_intent_counts`: object
- `digests_with_active_anchor_fields`: integer
- `digests_with_scale_path`: integer
- `digests_with_lateral_recovery`: integer
- `digests_with_sufficient_scale_reached`: integer

## `ledger`

- `ledger_event_count`: integer
- `ops_count`: object
- `actor_type_count`: object
- `status_transition_count`: integer
- `missing_referenced_object_count`: integer

## `boundaries`

- `uses_sqlite`: boolean
- `uses_embeddings`: boolean
- `uses_vector_db`: boolean
- `uses_graph_db`: boolean
- `uses_external_llm`: boolean
- `performs_geometry_recall`: boolean
- `performs_polygon_overlap`: boolean
- `performs_automatic_placement`: boolean
- `performs_semantic_completeness_scoring`: boolean

All boundary flags must be `false` for the current reference implementation.

## Golden Snapshot

`examples/audit_reports/openclaw_audit.json` is a deterministic OpenClaw audit snapshot.

`examples/audit_reports/*.json` files are examples and regression fixtures. They are not notebook source memory and must not be read by recall.

## Drift Comparison

Audit snapshots may be compared with current audit output using:

```bash
python3 -m nollm.cli audit-check <notebook_path> --against <snapshot.json>
```

Drift comparison validates both reports against this schema, removes environment-dependent fields, and compares the remaining structure deterministically.

Ignored fields:

- `notebook.path`

The result is a JSON object with:

- `ok`: boolean
- `matches`: boolean
- `drift_count`: integer
- `drifts`: list
- `ignored_fields`: list

Audit drift is a structural regression signal. It is not semantic scoring, not recall, not memory, and not a hidden index.
