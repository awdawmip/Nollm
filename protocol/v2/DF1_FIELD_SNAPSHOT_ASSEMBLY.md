# DF1 Field Snapshot Assembly

DF1 assembles only a host-supplied finite set of DA1 `AdmissionRecord` values.
It does not discover admissions, scan roots, persist snapshots, execute recall,
compile Query, call runtime surfaces, or write owner state.

Assembly order:

1. Freeze the explicit `FiniteAdmissionSet`.
2. Reject duplicate admission IDs, fingerprint conflicts, geometry profile
   mismatch, and field policy identity mismatch.
3. Replay every admission through the supplied DA1 replay validator.
4. Verify exact DE1 shard, accepted DC1 proposal receipt, PlacementPlan
   fingerprint, projection fingerprint, field profile, and verified chart link
   manifest.
5. Canonicalize replayed traces, DA1 replay covers, coverage distributions, and
   verified links.
6. Build `K_up` from the original PlacementPlan source fine cell to its supplied
   target partition, and build `K_down` from each target coarse cell back to the
   original fine source cell or supplied fine partition.
7. Reject a coverage source collision when the same `(direction, source cell)`
   has non-identical target/kernel/residual structure.
8. Reject multiple gravity chart fingerprints with
   `DF1_MULTIPLE_GRAVITY_CHARTS_UNSUPPORTED`; DF1.1 does not aggregate multiple
   gravity components.
9. Recompute internal DG2 gravity from canonical covers.
10. Return an immutable in-memory `FiniteFieldSnapshot`.

The snapshot is a derived read model. It is not a durable object, fact source,
global field, cache, database, or recall result.

DF1 policy cannot disable replay validation, verified chart-link requirements,
duplicate admission rejection, geometry profile compatibility, or field policy
identity compatibility. Such downgrades reject with
`DF1_UNSUPPORTED_POLICY_DOWNGRADE`.
