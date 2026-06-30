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

DC1 does not call an LLM, parse natural language, verify world truth, place
geometry, mutate Field, run Recall, register CLI/tool surfaces, use databases,
or write Evidence/Ledger state.

Growth output is a file-first `CompiledGrowthProposal` plus a
`CompilationReceipt` under a Cortex root distinct from the Evidence root.
Query output is a `CompiledQueryProbe` returned in memory only.

Fingerprints are deterministic equivalence keys for idempotency and
recomputation. They are not signatures, authentication, anti-tamper guarantees,
or security claims.
