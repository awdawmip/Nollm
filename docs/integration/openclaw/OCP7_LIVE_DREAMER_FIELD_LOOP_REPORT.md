# OCP7 Live Dreamer Field Loop Report

Status: implemented with live Dreamer blocked by missing configured agent.

## What Changed

- Dreamer input is now `nollm.dreamer_delta.v1`: semantic shards, source links, continuity, and cluster/bridge intent only.
- Core validates source snapshot hash, source SHA-256, line ranges, duplicate semantic keys, and forbidden coordinate/ranking/query fields before publishing.
- Core owns deterministic honeycomb placement and publishes immutable revisions under `fields/<field_id>/<revision_id>/`.
- `current_field.json` is only a pointer; wells bind a fixed `field_id` and `revision_id`.
- `nollm_read` requires `well_id`; surface, focus, drift, read, and trace all resolve through that well.
- Expired well cleanup removes only well records and never touches source memory files.

## Live Dreamer Attempt

An actual OpenClaw agent call was attempted through the supported CLI surface:

```text
openclaw agent --agent nollm-dreamer --message <bounded prompt> --json
```

The first attempt with bare `openclaw` was blocked by Python subprocess path resolution. The second attempt used the resolved `openclaw.cmd` and reached OpenClaw, but OpenClaw returned:

```text
Error: Unknown agent id "nollm-dreamer". Use "openclaw agents list" to see configured agents.
```

Result: `live_dreamer_blocked`. No fixture run is claimed as live dreaming. Evidence is recorded in `docs/integration/openclaw/evidence/ocp7_20260620_live_dreamer_attempt.json`.

## Operator Configuration

`build_ocp7_dreamer_agent_patch` provides a restricted `nollm-dreamer` agent fragment:

- `contextInjection: never`
- no memory search provider
- no allowed tools
- direct read/write/process/web tools denied
- prompt requires JSON-only semantic delta output

The helper does not automatically edit the user's OpenClaw config.

## Validation

- `python -m pytest reference/python/tests/test_dream_cortex_recall_spine.py -q`
- `python -m pytest reference/python/tests/test_dream_cortex_recall_spine.py reference/python/tests/test_openclaw_nollm_companion_plugin.py reference/python/tests/test_openclaw_nollm_companion_installer.py -q`
- `npm test` in `integrations/openclaw/nollm-memory-companion`
- `python reference/python/scripts/run_openclaw_nollm_memory.py ... dream-demo`

## Non-Goals Preserved

No embeddings, vector database, graph database, automatic source-memory writes, `MEMORY.md` replacement, query-conditioned Core ranking, or drift-to-trust/status mapping were added.
