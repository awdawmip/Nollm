# @nollm/openclaw-memory

Nollm native active memory provider for OpenClaw Functional Alpha.

This package is **not** the historical `nollm-memory-companion`. The companion
remains an experimental tool surface that delegates to legacy `memory-core`.
This provider is the active memory-slot implementation selected by:

```json5
plugins.slots.memory = "nollm"
```

## Scope

- Single-user, local, synthetic-fixture Functional Alpha.
- Private `agent_turn_prepare` recall into `NOLLM_MEMORY_CONTEXT_V1`.
- `agent_end` capture receipts under `nollmDataRoot` only.
- No Primary-visible memory tools and no Nollm geometry/navigation tools.
- No read/write of `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.

## Non-goals

- Production multi-user cutover.
- Real historical memory migration.
- R14 capability-storage hardening.
- Finished Cortex geometry recall.

See `docs/integration/openclaw/F0_NOLLM_MEMORY_PROVIDER_ALPHA.md` for the
full contract, known issues, and integration instructions.
