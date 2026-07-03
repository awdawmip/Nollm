# GCM1 Sparse-Collision Trace-Compaction Scope

GCM1 is a pure synthetic validation asset for DG2 trace compaction behavior over one finite collision witness selected from sealed GSC1.

## Authorized Witness

- Source fixture: sealed GSC1 `build_collision_summaries()`
- Pattern: `local_fork`
- Selection: canonical first summary with `collision_target_count > 0`
- Support cell: canonical first colliding target `CellRef` in that summary
- HexCell: reconstructed from the same GSC1 parameter, base layer, phase, phase policy, and target axial coordinate

## Validated Scenarios

- `shared_support_distinct_shards`
- `shared_support_distinct_proposals`
- `shared_support_distinct_revision_proxy`
- `exact_duplicate_transport_view`
- `mixed_group`

## Claims

- Shared target support does not compact traces across origin shard boundaries.
- Proposal and derivation proxy differences prevent compaction.
- Exact duplicate transport views compact losslessly and expand through the public DG2 compaction API.
- Mixed input compacts only the exact duplicate group.
- Reordered input produces the same canonical compaction payload.

## Non-Claims

GCM1 does not create DreamShard, AdmissionRecord, GrowthProposal, PlacementPlan, FieldSnapshot, RecallUniverse, RecallDigest, RevisionThread, current/retired decision, cover crystallization, gravity rank, runtime state, OpenClaw integration, CLI surface, database, cache, network, LLM/NLP, embedding, semantic search, or production compaction API changes.
