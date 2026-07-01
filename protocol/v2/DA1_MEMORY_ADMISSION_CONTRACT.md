# DA1 Memory Admission Contract

DA1 owns one durable object: `AdmissionRecord`.

DA1 accepts only host-constructed structured inputs:

- `DreamShard` value object;
- raw DC1 Growth submission mapping;
- explicit `AdmissionPlacementPlan`.

DA1 performs zero-write preflight before durable writes. Preflight compiles the
Growth submission through DC1 using an overlay DE1 reader, computes DG1
`fine_to_coarse` distributions, and derives DG2 trace, residual, local cover,
and internal gravity projections in memory.

Commit order is fixed:

```text
DE1 DreamShard -> DC1 Growth Proposal + Receipt -> DA1 AdmissionRecord
```

DA1 does not persist Trace, Cover, Gravity, Field snapshots, DreamShard content
copies, raw Growth submissions, Query objects, Recall results, runtime state,
network state, database state, or cache state.

`AdmissionReceipt` is public and narrow. It exposes identifiers, counts, and
the projection fingerprint only. It must not expose cell, chart, mass, kernel,
cover id, trace id, path, or gravity potential internals.

Replay uses the `AdmissionRecord`, DE1, DC1, DG1, and DG2 public APIs to rebuild
the admission-local projection and compare the stored fingerprint and ID sets.
Mismatch rejects; DA1 never repairs or overwrites owner data during replay.
