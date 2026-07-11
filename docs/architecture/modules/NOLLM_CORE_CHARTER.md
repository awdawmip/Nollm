# Nollm Core Charter

Purpose: deterministic geometry current-state operations, bounded geometry-entry recall, atomic writes, and Snapshot/Observability ports.

- Persistent state: cells, occupancy, geometry addresses, bridge/stitch runtime, current atom handles.
- Temporary state: bounded frontier, transaction staging, partition calculations.
- Public API: put/remove/replace/batch, bounded recall, consistent-read/export/import ports, `TraceSink.emit`.
- Forbidden API: source, host, user, session, LLM, prompt, semantic placement, history, audit, trace storage.
- Dependencies: Python/standard math and its own public contracts only; no Nollm product module.
- Failure: Core failures affect correctness; optional port consumers must not.
- Distributions: all variants.
- Future repository: `nollm-core`.
- Current sources: pure files in `reference/python/nollm/grf`; mixed files remain `SPLIT` candidates for M1.
