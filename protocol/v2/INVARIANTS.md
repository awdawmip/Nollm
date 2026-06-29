# V2 Invariants

- I-V2-001: Original Evidence must not be replaced or silently overwritten by Cover, Trace, or Gravity.
- I-V2-002: Cortex may propose semantics but must not confirm facts, place cells, or mutate Field directly.
- I-V2-003: Geometry must not depend on natural language, LLMs, OpenClaw, runtime, or legacy recall.
- I-V2-004: Coverage must use directed `K↑ / K↓` (`K_up` / `K_down`), not undirected parent-child edges.
- I-V2-005: Gravity is Field/Core internal and must not be an external query parameter or named index.
- I-V2-006: Query Probe is temporary by default and must not be silently persisted as Evidence.
- I-V2-007: Unverified Chart Transform must not support atlas merge or recall identity inference.
- I-V2-008: Validation must not enter production paths or write production state.
- I-V2-009: Adapter must not define, recompute, or bypass Geometry / Field rules.
- I-V2-010: V1 legacy and V2 are import-isolated during DG0.
- I-V2-011: Field propagates only through supplied, DG1-confirmed directed coverage distributions; it must not create nearest-center parent links.
- I-V2-012: Every propagation conserves parent trace mass after explicit residual accounting.
  - DG2.1 clarification: `accounting_error` is only floating summation error; it is not a sink for unclassified positive kernel mass.
- I-V2-013: Every derived Trace and Cover preserves origin shard, proposal, basis, support, and geometry provenance.
  - DG2.1 clarification: Trace and Cover source identities are set-like; duplicate identity cannot be counted twice.
- I-V2-014: `provisional_llm_generalization` cannot become accepted, stable, or crystallized by Field alone.
  - DG2.1 clarification: provisional mass blocks stability regardless of `CoverPolicy`.
- I-V2-015: Field cannot write, replace, or delete Evidence, Card, Ledger, or original Trace inputs.
- I-V2-016: Stable Cover requires explicit multi-support and anti-black-hole eligibility under a versioned policy.
  - DG2.1 clarification: multi-support and multi-axis floors are structural and cannot be relaxed by policy.
- I-V2-017: Gravity Snapshot is internal Field state; it cannot be accepted as an external anchor, index, or query parameter.
- I-V2-018: Trace compaction is lossless and reversible; it cannot merge across origin, basis, axis, state, geometry, residual, or support boundaries.
  - DG2.1 clarification: compaction is a set-level view and must reject duplicate or missing expansion manifest identities.

Pure geometry acceptance comes before semantics and runtime.
