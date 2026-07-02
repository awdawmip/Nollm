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
  to the matching replayed `HexCell` from the same DF1 call.

RC1 does not reopen DG2, DF1, DR1, DI1, BA1, CI1, DA1, evidence, cortex,
geometry, field, recall policy, runtime, OpenClaw, global discovery, cache,
database, LLM/NLP, embedding, or DX2 completion.
