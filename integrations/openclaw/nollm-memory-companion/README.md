> **Historical / experimental companion surface**
>
> This package (`@nollm/openclaw-memory-companion`, plugin id
> `nollm-memory-companion`) is a tool plugin that exposes geometry navigation
> tools and delegates to legacy `memory-core`. It is **not** the OpenClaw active
> memory provider.
>
> The Functional Alpha active memory provider is now
> `@nollm/openclaw-memory` (plugin id `nollm`, kind `memory`). See
> `docs/integration/openclaw/F0_NOLLM_MEMORY_PROVIDER_ALPHA.md`.
# Nollm OpenClaw Memory Companion

This package is a local-development-ready OpenClaw tool plugin that wraps the
existing Nollm Python sidecar.

It is:

- a companion tool plugin for `memory-core`;
- a strict TypeScript adapter around `reference/python/scripts/run_openclaw_nollm_memory.py`;
- a source-backed search/get/status/pending-write surface with geometry and gravity instrumentation.
- a source-backed search/get/status/pending-write surface with geometry and gravity instrumentation, plus an explicit Nollm native companion-memory remember/recall/get path.

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
- A working Nollm Python sidecar. On Windows the installer must configure an absolute `python.exe` path; bare `python3`/`python`/`py` launchers are rejected.

## Configuration

### Python executable

The companion requires either:

- `pythonExecutable`: absolute path to the Python executable (recommended, required on Windows).
- `pythonCommand`: deprecated; a legacy absolute path is still accepted, but bare launchers such as `python3` are rejected on Windows.

`pythonArgs` can be used to pass discrete arguments before the sidecar script.

All Windows paths written to OpenClaw config are forward-slash normalized.

### Required paths

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

The plugin surface exposes the seven geometry navigation tools
(`nollm_field_overview`, `nollm_open_well`, `nollm_surface`, `nollm_focus`,
`nollm_drift`, `nollm_read`, `nollm_recall_trace`) and three explicit native
companion-memory tools (`nollm_memory_remember`, `nollm_memory_recall`,
`nollm_memory_get`).

### `nollm_memory_remember`

Persist an explicit user identity, preference, decision, project fact, or other
standalone memory sentence in Nollm native companion storage. It never writes
`MEMORY.md`, `DREAMS.md`, or `memory/*.md`, and it rejects secret-like input.

### `nollm_memory_recall`

Recall only Nollm native companion memories that match the user question. It
returns an empty result when no relevant native memory is found. It never falls
back to legacy files.

The relevance gate is deterministic and local: it matches by normalized
exact/substring, Latin/digit token overlap, CJK 2-gram overlap, kind-intent, and
explicit test-code markers. It does not use embeddings, vector search, or LLM
reranking.

W1-03 separates *admission* from *ranking*: `kind_intent` is no longer an
admission condition on its own. Specific queries return only records that share
a matching deterministic facet (`identity_name`, `identity_code`,
`preference_color_or_label`, `preference_response_style`, `project_release`,
`project_decision`, `generic_test_code`) or discriminative lexical evidence.
Broad queries may return a facet collection (for example "我有哪些项目决定？"),
but generic namespace tokens (`W1`, `W1-02`, pure numbers, "代号/项目/偏好")
do not alone constitute relevance. Generic test-code queries with multiple
candidates return an explicit `ambiguity` block instead of picking by timestamp.

`nollm_memory_get` distinguishes an invalid `memory_id`
(`status=invalid_input`, `code=native_memory_id_invalid`) from an unknown but
well-formed native id (`status=not_found`, `code=native_memory_not_found`).

Structured errors (for example `memory_content_rejected` for secret-like input
and `native_memory_not_found` for an unknown `memory_id`) are returned as
`ok: false` results with `{ code, message, retryable }` and are propagated by
the TypeScript bridge even when the sidecar exits with a non-zero code.

### `nollm_memory_get`

Read a single Nollm native companion memory by its Nollm-issued `memory_id`
only. File paths, line locators, and legacy source locators are rejected.

### `nollm_memory_status`

Returns field availability, current revision, stale state, source snapshot hash,
and last Dreamer status. It does not expose source text, environment variables,
filesystem listings, or secrets.

## Local Development

From this package directory:

```bash
npm install
npm run plugin:build
npm run plugin:check
npm test
```

`plugin:build` compiles TypeScript and asks the OpenClaw CLI to generate native
metadata in `openclaw.plugin.json` and `package.json`. `plugin:check` compiles,
checks generated metadata freshness, and runs OpenClaw validation.

A real OpenClaw gateway link/inspect smoke is separate:

```bash
openclaw plugins install --link .
openclaw plugins inspect nollm-memory-companion --runtime --json
```

Only treat those two commands as verified after they run in an actual OpenClaw
CLI/Gateway environment.

## Local OpenClaw Integration

From `reference/python` in the Nollm repository:

```bash
python scripts/install_openclaw_nollm_companion.py --dry-run
python scripts/install_openclaw_nollm_companion.py --apply
```

To repair an existing install on Windows:

```powershell
python scripts/install_openclaw_nollm_companion.py `
  --repair-runtime `
  --python-executable "C:/Users/Administrator/AppData/Local/Programs/Python/Python314/python.exe" `
  --workspace "C:/Users/Administrator/.openclaw/workspace" `
  --repo-root "C:/path/to/nollm"
```

The installer builds and validates this package, links it into the local
OpenClaw installation, patches only `plugins.entries.nollm-memory-companion`,
keeps source-memory write tools disabled, validates config, restarts the Gateway
unless `--no-restart` is used, and writes a machine-readable report to:

```text
<OpenClaw workspace>/.nollm-memory/integration/openclaw_integration_report.json
```

## Manual Skill Installation

The plugin manifest declares `skill` as a skill root so `skill/SKILL.md` is
discoverable when the plugin is enabled. Operators can also copy or link that
file manually into a workspace skill location. The skill is not a system prompt.

## With memory-core

Keep OpenClaw `memory-core` active as the memory owner. Configure these tools as
companion tools so the LLM can explicitly remember/recall Nollm native memories
and laterally inspect Nollm geometry/gravity instrumentation while ordinary file
memory lifecycle remains owned by `memory-core`.

The active Nollm path may use the geometry navigation tools, `nollm_memory_status`,
and the explicit native remember/recall/get tools. Legacy Python search/get/write
helpers are compatibility code only and are not registered by this plugin.

## Verification Matrix

| Check | Status in this repo |
| --- | --- |
| Package files and manifest exist | verified by Python static tests |
| Static tool names and optional write tool | verified by Python static tests |
| Non-shell bounded sidecar bridge | verified by Python static tests and package test |
| Config path and timeout constraints | verified by Python static tests and package test |
| Real OpenClaw gateway installation | skipped until an OpenClaw environment is provided |
