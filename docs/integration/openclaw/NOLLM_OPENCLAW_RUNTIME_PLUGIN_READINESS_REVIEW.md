# Nollm OpenClaw Runtime Plugin Readiness Review

Date: 2026-06-20

This review records the current OpenClaw-Nollm companion tool plugin package
and the sidecar boundary it wraps. The package exists at:

```text
integrations/openclaw/nollm-memory-companion/
```

It is a native OpenClaw tool-plugin package that delegates to the Python
sidecar. It does not replace OpenClaw `memory-core`, claim the memory slot, call
an LLM, or write durable OpenClaw memory files.

## Current Sidecar Commands

The experimental CLI is:

```bash
python scripts/run_openclaw_nollm_memory.py <command>
```

On Windows the plugin uses a probed absolute `python.exe`; bare `python3`/`python`/`py` launchers are rejected.

Current commands:

- `index`: parse OpenClaw memory files and write deterministic sidecar JSONL.
- `search`: run deterministic lexical search and attach gravity reports.
- `get`: read one candidate by `candidate_id`, `memory_id`, or `shard_id`.
- `write-candidate`: write pending review material to sidecar storage only.
- `status`: report counts, manifest details, accepted ID forms, native companion
  memory counts, and boundaries.
- `native-remember`: write an explicit memory sentence to the Nollm-owned
  companion store (`native-companion-v1/`).
- `native-recall`: recall Nollm-owned companion memories by deterministic token
  overlap and Chinese identity/preference aliases.
- `native-get`: read one Nollm-owned companion record by Nollm-issued
  `memory_id` only.

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

## Plugin Package

The companion package exposes these tools:

- `nollm_memory_status`
- `nollm_field_overview`
- `nollm_open_well`
- `nollm_surface`
- `nollm_focus`
- `nollm_drift`
- `nollm_read`
- `nollm_recall_trace`
- `nollm_memory_remember` (W1-01 native companion memory write)
- `nollm_memory_recall` (W1-01 native companion memory recall)
- `nollm_memory_get` (W1-01 native companion memory read by id)

Build and validation commands:

```bash
cd integrations/openclaw/nollm-memory-companion
npm install
npm run plugin:build
npm run plugin:check
npm test
```

The OpenClaw CLI generator writes native metadata into
`openclaw.plugin.json`, including `configSchema`, `contracts.tools`, optional
metadata for `nollm_memory_write_candidate`, and `skills: ["skill"]`.

Configuration uses the current OpenClaw entry convention:

```json
{
  "plugins": {
    "entries": {
      "nollm-memory-companion": {
        "enabled": true,
        "config": {
          "pythonExecutable": "C:/Users/Administrator/AppData/Local/Programs/Python/Python314/python.exe",
          "pythonArgs": [],
          "nollmRepoRoot": "C:/path/to/nollm",
          "workspaceRoot": "C:/Users/Administrator/.openclaw/workspace"
        }
      }
    }
  }
}
```

Windows paths must be absolute and forward-slash normalized.

The plugin must not claim the exclusive OpenClaw memory slot. It must not
replace `memory-core`, auto-write `MEMORY.md`, call a real LLM, map
`drift_class` to trust/status, or hard-filter by `drift_class`.

Forbidden semantics remain explicitly false:

```json
{
  "memory_slot_replacement": false,
  "real_llm_call": false,
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
