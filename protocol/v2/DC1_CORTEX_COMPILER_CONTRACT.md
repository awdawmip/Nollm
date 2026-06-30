# DC1 Cortex Compiler Contract

DC1 defines `nollm.dream_geometry.cortex` as a deterministic compiler for
externally supplied structured drafts.

It accepts only:

- structured Growth Proposal submissions for a DE1 `DreamShard`;
- structured Query Probe submissions for an ephemeral query.

It rejects missing fields, unknown fields, invalid IDs, invalid enum values,
legacy anchor/tree inputs, unresolved basis references, invalid text spans,
relative-time Growth axes, persistent Query attempts, and query memory-basis
attempts with stable `DC1_*` reason codes.

Growth budget is `max_axes`, `max_total_steps`, and `max_ray_steps`, capped at
`8/48/16`. Query budget is `max_axes`, `max_charts`, `max_layers`, and
`max_cells_per_layer`, capped at `8/64/64/256`. Query budget values are finite
future-DR1 limits only; DC1 does not choose charts, layers, cells, or recall
paths.

`relative_time` is forbidden in Growth. A Query containing `relative_time` must
set `requires_runtime_resolution=true` and include at least one exact
`explicit_in_query` text span for the relative expression. DC1 preserves the
text and optional `reference_instant`; it never computes a resolved absolute
time.

Growth submissions include `possible_conflict_refs`, a list of explicit DE1
DreamShard or InterpretationRecord IDs. DC1 validates existence and
deduplication only. These refs are not basis, not truth claims, and not conflict
adjudication.

Within one proposal, the same `rule_id` must always carry the same
`(rule_version, rule_label, source_ref)` identity.

DC1 does not call an LLM, parse natural language, verify world truth, place
geometry, mutate Field, run Recall, register CLI/tool surfaces, use databases,
or write Evidence/Ledger state.

Growth output is a file-first `CompiledGrowthProposal` plus a
`CompilationReceipt` under a Cortex root distinct from the Evidence root.
Query output is a `CompiledQueryProbe` returned in memory only.

On reopen, the Cortex store validates the persisted proposal with the same
compiled-growth semantic contract and re-normalizes each accepted receipt
`input_snapshot` to verify submitted fingerprint, normalized proposal, and
normalized fingerprint consistency.

Pre-DC1.1 artifacts that omit `possible_conflict_refs` in both proposal and
receipt snapshot may reopen only as `legacy_dc1_read_only`. This path preserves
raw fingerprints and files, uses an in-memory validation view with empty
conflict refs, keeps legacy rule-label variance as historical read-only state,
and does not relax current `compile_growth()` submissions.

Fingerprints are deterministic equivalence keys for idempotency and
recomputation. They are not signatures, authentication, anti-tamper guarantees,
or security claims.
