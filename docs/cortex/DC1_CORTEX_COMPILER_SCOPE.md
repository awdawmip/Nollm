# DC1 Cortex Compiler Scope

DC1 is the structured boundary between a caller/Cortex strategy and later
Geometry, Field, Recall, or Integration phases.

It compiles externally supplied drafts into finite, basis-labeled Cortex
artifacts or rejects them with stable reason codes. It does not decide truth,
does not create anchors, does not compose context, and does not place objects in
cells.

DC1.1 closes the final compiler contract details: relative-time Query exact
spans, separate Growth/Query budget schemas, `possible_conflict_refs`,
proposal/receipt semantic revalidation on reopen, and same-rule identity
consistency.

The implementation lives under `reference/python/nollm/dream_geometry/cortex/`.
It may read DE1 `DreamShard` content through the public Evidence store surface
to validate subjects and exact text-span basis references. It must not write
Evidence, Ledger, Geometry, Field, Recall, Adapter, V1, OpenClaw, runtime,
network, subprocess, SQLite, or cache state.
