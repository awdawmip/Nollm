# GCM1 Sparse-Collision Trace-Compaction Validation Protocol

GCM1 validates the non-conflation boundary between GSC1 support collisions and DG2 trace compaction.

## Inputs

The protocol reads one finite collision witness from the sealed GSC1 fixture. It does not scan for new patterns, expand the GSC1 window, or construct proxy cells.

The fixture constructs in-memory DG2 `GrowthTrace` values using the reconstructed witness `HexCell`. These traces are synthetic transport views only. They are not DreamShards, admissions, revision records, covers, field snapshots, recall universes, or runtime state.

## Operation

For each scenario:

1. Build explicit `GrowthTrace` inputs.
2. Call DG2 `compact_traces(...)`.
3. For the exact duplicate scenario, call DG2 `expand_compaction(...)` with an in-memory trace index.
4. Compare canonical compaction payloads for normal and reversed input order.
5. Confirm that non-duplicate traces remain outside compaction member manifests.

## Boundary

Support collision is not compaction eligibility. Compaction is a reversible derived view and does not delete or replace evidence. The distinct revision proxy scenario checks a trace-derivation boundary only; it is not a `RevisionThread` or current/retired resolver.
