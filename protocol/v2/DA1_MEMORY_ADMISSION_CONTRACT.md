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

DA1.1 replay closure rules:

- Cross-chart placement records store only a minimal canonical link manifest:
  source chart geometry fingerprint, target chart geometry fingerprint,
  `direction: source_to_target`, and `verified: true`.
- Same-chart placement records must keep `verified_chart_link` as `null`.
- Replay reconstructs a DG2 `VerifiedChartLink` from that manifest and rejects
  missing, reversed, unverified, or fingerprint-mismatched links.
- Non-empty admission stores must not open through a public path unless replay
  validation is supplied and executed.
- `placement_plan_fingerprint` must equal the canonical fingerprint of
  `placement_plan_payload` on every on-disk read.
- `recorded_at` is `null` or an RFC3339 timestamp with timezone; DA1 never
  fills it from the system clock.
- Every axis placement must materialize at least one positive DG1 K_up kernel.
  Full-residual zero-kernel partitions reject before any durable write.

DA1.1R timestamp profile:

```text
null
YYYY-MM-DDTHH:MM:SS[.fraction](Z|+HH:MM|-HH:MM)
```

The date must be extended form, the separator must be uppercase `T`, seconds
are required, fractional seconds require at least one digit after `.`, and the
offset must be `Z` or coloned `+HH:MM` / `-HH:MM` with `HH` in `00..23` and
`MM` in `00..59`. DA1 rejects space-separated ISO text, basic ISO date/time
text, uncoloned offsets, out-of-range offsets, naive timestamps, relative time,
locale text, and any value rejected by Python calendar parsing. Accepted text
is preserved exactly.
