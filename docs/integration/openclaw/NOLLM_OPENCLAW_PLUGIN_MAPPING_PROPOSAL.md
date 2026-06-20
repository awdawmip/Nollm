# Nollm OpenClaw Plugin Mapping Proposal

Date: 2026-06-20

This proposal maps the offline sidecar to the current OpenClaw companion
tool-plugin package:

```text
integrations/openclaw/nollm-memory-companion/
```

The package is a native OpenClaw tool plugin that delegates to the Python
sidecar. It is not a memory-slot implementation.

## Tool Mapping

| OpenClaw tool | Current sidecar command | Role |
| --- | --- | --- |
| `nollm_memory_search` | `search` | Return source-backed results with gravity reports. |
| `nollm_memory_get` | `get` | Resolve `candidate_id`, `memory_id`, or `shard_id` to exact text. |
| `nollm_memory_write_candidate` | `write-candidate` | Create pending review records only. |
| `nollm_memory_status` | `status` | Report sidecar health and boundaries. |

## Companion Mode First

The plugin is a companion tool provider. It may call sidecar logic, but it must
not claim the OpenClaw memory slot or replace `memory-core`.

Native package checks:

```bash
cd integrations/openclaw/nollm-memory-companion
npm run plugin:build
npm run plugin:check
npm test
```

Runtime entry configuration uses `plugins.entries.nollm-memory-companion.config`
with absolute `nollmRepoRoot` and `workspaceRoot` paths.

## Required Runtime Guardrails

A future plugin must preserve these boundaries:

- no real LLM call inside the sidecar tool path;
- no automatic durable write to `MEMORY.md`, `DREAMS.md`, or `memory/*.md`;
- no drift-to-trust or drift-to-status mapping;
- no hard rejection by `drift_class`;
- no stable public recall API claim;
- source path and line range remain visible in search and get results.

## LLM Contract

`gravity_report` is orientation data. Far drift is a warning, not rejection.
`semantic_break` is caution, not deletion. The LLM should inspect
`retrieval_score`, `R_column_ring`, `S_scale_delta`, `A_anchor_similarity`, and
provenance, then call `nollm_memory_get` before relying on a result.

## Promotion Boundary

`nollm_memory_write_candidate` maps to the sidecar pending store. Durable
OpenClaw memory promotion requires explicit future policy and review.
