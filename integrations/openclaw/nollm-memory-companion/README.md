# Nollm OpenClaw Memory Companion

This package is a local-development-ready OpenClaw tool plugin that wraps the
existing Nollm Python sidecar.

It is:

- a companion tool plugin for `memory-core`;
- a strict TypeScript adapter around `reference/python/scripts/run_openclaw_nollm_memory.py`;
- a source-backed search/get/status/pending-write surface with geometry and gravity instrumentation.

It is not:

- an OpenClaw active memory slot;
- a replacement for `memory-core`;
- a real LLM caller;
- a durable writer for `MEMORY.md`, `DREAMS.md`, or `memory/*.md`;
- a vector DB, graph DB, MCP server, daemon, or stable public recall API.

## Prerequisites

- Node >= 22.
- TypeScript ESM.
- OpenClaw >= 2026.5.17 with the tool-plugin SDK available.
- A working Nollm Python sidecar.
- Python command available as `python3` or configured explicitly.

## Configuration

Required paths must be absolute:

- `nollmRepoRoot`: absolute path to the Nollm repository.
- `workspaceRoot`: absolute path to the OpenClaw workspace.

Optional paths are also absolute when provided:

- `sidecarScript`: defaults to `<nollmRepoRoot>/reference/python/scripts/run_openclaw_nollm_memory.py` and must resolve under `nollmRepoRoot`.
- `sidecarOutDir`: defaults to `<workspaceRoot>/.nollm-memory` and must resolve under `workspaceRoot`.

Runtime bounds:

- `commandTimeoutMs`: default `15000`, allowed `1000..60000`.
- `maxSearchResults`: default `5`, allowed `1..20`.

No secrets are accepted or needed.

## Tools

### `nollm_memory_search`

Searches the Nollm sidecar and returns candidate relevance plus source,
provenance, geometry, gravity, drift, and LLM-use hints. `drift_class` is
preserved as orientation only and never converted into trust, status, ranking
permission, or a hard rejection rule.

### `nollm_memory_get`

Gets exact source-backed content by accepted `candidate_id`, `memory_id`, or
`shard_id`. Use this before making factual user-facing claims from recalled
memory.

### `nollm_memory_write_candidate`

Creates a pending-review record only. It does not write durable OpenClaw memory.

Example output shape:

```json
{
  "ok": true,
  "pending_review": true,
  "durable_write": false,
  "target_files_mutated": false
}
```

### `nollm_memory_status`

Returns sidecar counts, source roles, accepted ID forms, and forbidden-semantics
flags. It does not expose environment variables, filesystem listings, or
secrets.

## Local Development

From this package directory:

```bash
npm install
npm run plugin:build
npm test
npm run plugin:validate
```

`plugin:validate` performs package-local static checks. A real OpenClaw gateway
load test is separate:

```bash
openclaw plugins install --link .
openclaw plugins list
```

Only treat the gateway load as verified after it runs in an actual OpenClaw
environment.

## Manual Skill Installation

Copy or link `skill/SKILL.md` into the target OpenClaw workspace skill location
according to that workspace's normal procedure. The skill is not auto-installed
and is not a system prompt.

## With memory-core

Keep OpenClaw `memory-core` active as the memory owner. Configure these tools as
companion tools so the LLM can laterally inspect Nollm geometry/gravity
instrumentation while ordinary file memory lifecycle remains owned by
`memory-core`.

An optional Active Memory experiment can combine `memory_search`, `memory_get`,
`nollm_memory_search`, and `nollm_memory_get` only after explicit operator
opt-in. Nollm gravity reports annotate drift and do not replace source
verification.

## Verification Matrix

| Check | Status in this repo |
| --- | --- |
| Package files and manifest exist | verified by Python static tests |
| Static tool names and optional write tool | verified by Python static tests |
| Non-shell bounded sidecar bridge | verified by Python static tests and package test |
| Config path and timeout constraints | verified by Python static tests and package test |
| Real OpenClaw gateway installation | skipped until an OpenClaw environment is provided |

