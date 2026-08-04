# V3.13 Rev1 Direct Activation Path Map

Date: 2026-08-04

This map records the renderer topology after stage commit `65353968`.
`_render_exact_statement_injection` is the single exact-text renderer. No
second renderer, activation packet, model adapter, epoch store, or activation
cache was added.

| Caller | Consumer | Provider calls | Persistence | Tests | Status |
|---|---|---:|---|---|---|
| Main-agent `nollm_field_encounter` terminal | `bridge.py` action `render_field_encounter_injection` -> current `Statement` handles -> `_render_exact_statement_injection` | 0 additional | operation-local only | `test_openclaw_field_encounter.py`, `adapter.test.mjs` | KEEP_ACTIVE |
| Background Writer Field Encounter terminal | `executeWriterEncounter` in `src/index.ts` -> same bridge action and renderer | 0 additional | operation-local; commit remains Field Encounter-owned | OpenClaw Python/Node suites | KEEP_ACTIVE |
| `agent_turn_prepare` pending fallback | `CaptureStore.renderPending`; no Statement renderer | 0 | reads pending Capture only | capture tests and live baseline | KEEP_ACTIVE |
| `agent_turn_prepare` legacy Recall branch | `build_fast_recall_prompt` / `render_recall_injection` | disabled by `legacyReaderEnabled() == false` | migration-only path | memory loop and main-agent recall tests | MIGRATION_ONLY |
| `legacy_bridge.py` | Explicit offline migration bridge | 0 | offline migration only | migration witnesses | MIGRATION_ONLY |
| `_direct_locality_injection` | Fast Recall/placement compatibility helpers; delegates to the shared renderer | caller-dependent | caller-dependent | `test_memory_loop.py` | ADAPT_TO_SHARED_RENDERER |

## Live findings

- The standard post-stage matrix completed with the real Windows OpenClaw
  Provider, but returned zero `direct_activation` responses because the
  isolated main-agent tool policy initially omitted `nollm_field_encounter`.
- After adding that tool to the isolated test profile only, the tool appeared
  in the Provider system prompt but every explicit probe returned
  `run_scope_unavailable`. The OpenClaw `before_tool_call` context did not
  supply a bindable run scope for that call. The probe is retained outside the
  repository under `D:\Nollm\artifacts\V3_13_REV1_POST\direct-probe`.
- The background Writer also remained in `processing`/`retryable_defer` and
  did not produce a durable terminal Statement from the live sample set.

These findings prevent a truthful `REMOVABLE_AFTER_LIVE` decision. This Gate
therefore performs zero deletion. No production asset is marked removable
until a real Host run reaches a terminal Field Encounter, proves current
Statement projection, and shows zero hidden duplicate renderer activity.
