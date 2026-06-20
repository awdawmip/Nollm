# OCP3b Strict Live E2E Evaluation Report

Status: complete for the controlled local run.

Run id: `ocp3b_20260620_141159`

Evidence package: `docs/integration/openclaw/evidence/ocp3b_20260620_141159/`

## Conclusions

- Integration: `supported`
- Safety for the tested path: `supported`
- Value hypothesis: `inconclusive`

The run proves that OpenClaw can load `memory-core` as the memory-slot owner and load Nollm as a companion tool plugin, and that controlled live agent turns can call both tool families without direct file-read contamination or workspace context injection.

The run does not prove the value hypothesis. Explicit Nollm use added provenance and geometry/drift visibility, but it did not improve factual answer correctness over the valid memory-core baseline. Autonomous Nollm adoption was not observed when Nollm tools were available but unnamed.

## Runtime Facts

- OpenClaw: `OpenClaw 2026.6.8 (844f405)`
- Node: `v24.17.0`
- Python: `Python 3.14.6`
- Model route: `kimi/kimi-for-coding`
- `memory-core`: loaded, selected memory slot, tools `memory_search` and `memory_get`
- `nollm-memory-companion`: loaded companion tool plugin, not selected as memory slot

## Controls

- Isolated controlled corpus under ignored runtime output.
- Fresh session key for each scored turn.
- Per-agent `contextInjection: never`.
- `bootstrapMaxChars: 1` and `bootstrapTotalMaxChars: 1`.
- Direct file and process tools denied for scored agents, including `read`, `exec`, `process`, `edit`, and `write`.
- Baseline allowed only `memory_search` and `memory_get`.
- Nollm condition allowed memory-core tools plus Nollm companion tools.
- Write safety used a copied workspace and enabled `nollm_memory_write_candidate` only for that copied workspace.

## Repairs

Two local runtime repairs were required:

1. The baseline isolated agents used `memorySearch.provider: "none"` and `fallback: "none"` so the controlled run used OpenClaw memory-core FTS behavior without unavailable external embedding dependencies.
2. Nollm companion initially failed with `spawn EINVAL` because the local Python command resolved to a command shim. Re-running the installer pinned the plugin config to the Python 3.14 executable and restored successful Nollm tool calls.

Both failures are preserved in ignored raw runtime evidence and summarized in the committed evidence package.

## Results

- Baseline tasks B1-B4 passed with memory-core tool traces.
- Nollm tasks N1-N5 passed with memory-core retrieval first and Nollm enrichment where required.
- N6 autonomous adoption: `not_observed`.
- N7 write safety: pending-only sidecar write; durable source hashes unchanged.
- Direct-read contamination count: `0`.
- Context-injection contamination count: `0`.
- Durable source mutation result: `unchanged`.

## Limitations

- Single local OpenClaw installation, model route, and controlled corpus.
- The run measures tool validity and safety, not broad product value.
- Nollm drift labels remain navigation/provenance instrumentation only and are not mapped to trust, status, authorization, or hard filtering.
