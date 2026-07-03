# RC1 DF1 to DR1 RecallUniverse Scope

RC1 is a controlled production contract repair for the DF1 assembly boundary.

It only closes the public handoff:

```text
DA1 AdmissionRecord
-> DF1 assemble_field_snapshot(...)
-> RecallUniverse
-> DR1 resolve_recall(...)
```

The repair keeps two derived views separate:

- `FiniteFieldSnapshot.coarse_covers`: DG2 local cover view. `support_cell`
  remains `CellRef`.
- `RecallUniverse.covers`: DR1 executable cover view. `support_cell` is bound
  to replayed `HexCell` values from the same DF1 call only when every declared
  `support_trace_id` is present and every support trace cell matches the cover's
  `CellRef` and `chart_fingerprint`.

RC1-C1 closes the support-trace binding rule: a matching subset of support
traces is not sufficient. Missing one support trace or finding one mismatched
support trace must fail closed before returning a `RecallUniverse`.

RC1 does not reopen DG2, DF1, DR1, DI1, BA1, CI1, DA1, evidence, cortex,
geometry, field, recall policy, runtime, OpenClaw, global discovery, cache,
database, LLM/NLP, embedding, or DX2 completion.
