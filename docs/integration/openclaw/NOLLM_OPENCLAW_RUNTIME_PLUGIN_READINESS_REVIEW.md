# Nollm OpenClaw Runtime Plugin Readiness Review

Date: 2026-06-20

This review explains how the current offline OpenClaw-Nollm memory sidecar could
later become an OpenClaw companion plugin. It is a readiness review only. It
does not implement a runtime plugin, replace OpenClaw `memory-core`, call an
LLM, or write durable OpenClaw memory files.

## Current Sidecar Commands

The experimental CLI is:

```bash
python scripts/run_openclaw_nollm_memory.py <command>
```

Current commands:

- `index`: parse OpenClaw memory files and write deterministic sidecar JSONL.
- `search`: run deterministic lexical search and attach gravity reports.
- `get`: read one candidate by `candidate_id`, `memory_id`, or `shard_id`.
- `write-candidate`: write pending review material to sidecar storage only.
- `status`: report counts, manifest details, accepted ID forms, and boundaries.

## Current Schemas

The sidecar currently writes inspectable JSON/JSONL records:

- `candidate`: source path, line range, source kind, heading path, provenance,
  text, `version_status=fixture_current`, and `trust_level=unverified_fixture`.
- `shard`: deterministic `shard_id`, candidate reference, normalized text,
  anchor vector, provenance, trust level, and version status.
- `geometry_mark`: content id, profile, chart id, layer, `q`, `r`, anchor
  vector, provenance, and `placement_status=experimental_unconfirmed`.
- `gravity_report`: `R_column_ring`, `S_scale_delta`, `A_anchor_similarity`,
  `drift_class`, projection method, and experimental status.
- `pending_write`: pending id, text, source, pending review status,
  `durable_write=false`, and `target_files_mutated=false`.

## Plugin Boundary

A future companion plugin may call the sidecar logic and expose tool-shaped
responses. It must not claim the exclusive OpenClaw memory slot yet. It must not
replace `memory-core`, auto-write `MEMORY.md`, call a real LLM, map
`drift_class` to trust/status, or hard-filter by `drift_class`.

Forbidden semantics remain explicitly false:

```json
{
  "real_openclaw_plugin": false,
  "real_llm_call": false,
  "memory_slot_replacement": false,
  "auto_memory_write": false,
  "drift_class_trust_mapping": false,
  "hard_drift_rejection": false,
  "stable_public_recall_api": false
}
```

## LLM Usage Policy

Gravity reports are instrumentation. Far drift is a warning, not rejection.
`semantic_break` is caution, not deletion. The LLM must keep `source_path` and
`line_range` visible when using sidecar results and should call `get` before
making user-facing claims from a recalled item.

## Promotion Boundary

`write-candidate` produces pending review records only. Durable writes to
OpenClaw memory files require an explicit future promotion policy and are out of
scope for this review.
