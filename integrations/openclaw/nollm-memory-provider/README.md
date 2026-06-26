# @nollm/openclaw-memory

Nollm native active memory provider for OpenClaw W2-01 Direct Active Memory trial.

This package is **not** the historical `nollm-memory-companion`. The companion
remains an experimental tool surface that delegates to legacy `memory-core`.
This provider is the active memory-slot implementation selected by:

```json5
plugins.slots.memory = "nollm"
```

## Scope

- Single-user, local, Windows-native active memory trial.
- Private `agent_turn_prepare` recall from the W1 native companion store into `NOLLM_MEMORY_CONTEXT_V1`.
- Deterministic `agent_end` capture of explicit stable user sentences into the same native store.
- No Primary-visible memory tools and no Nollm geometry/navigation tools.
- No read/write of `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.

## Non-goals

- Production multi-user cutover.
- Real historical memory migration.
- R14 capability-storage hardening.
- Finished Cortex geometry recall.

See `docs/integration/openclaw/NOLLM_OPENCLAW_RUNTIME_PLUGIN_READINESS_REVIEW.md`
and the local W2-01 trial report for runtime proof, known recall boundaries, and
rollback procedure.

## W2-01 status

- Active slot `plugins.slots.memory = "nollm"` is selected by OpenClaw Gateway.
- `agent_turn_prepare` calls the native sidecar `active-prepare` and injects a
  bounded `NOLLM_MEMORY_CONTEXT_V1` envelope.
- `agent_end` calls `active-capture` with a deterministic, narrow promotion policy.
- Rollback to `memory-core` is tested and documented.
- Legacy `MEMORY.md` / `memory/*.md` / `DREAMS.md` are preserved as observed
  confounds; the provider itself does not read or write them.
