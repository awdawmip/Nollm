# GCM1 Sparse-Collision / Trace-Compaction Non-Conflation Baseline Report

- baseline commit: `f850599995e75b0a5c74fa9267202958a6369bdd`
- validation kind: pure synthetic compaction validation
- runner output: this Markdown report only
- boundary: collision is shared finite DG1/GSC1 support only; it is not compaction eligibility, not evidence deletion, not DreamShard merge, and not recall authority.

## Experiment Window

- source phase: `GSC1 sealed fixture`
- parameter id: `B`
- pattern id: `local_fork`
- scenario ids: `('shared_support_distinct_shards', 'shared_support_distinct_proposals', 'shared_support_distinct_revision_proxy', 'exact_duplicate_transport_view', 'mixed_group')`

## Collision Witness

- pattern id: `local_fork`
- layer gap: `1`
- base layer: `0`
- phase: `(0,0)`
- phase policy: `constant_local`
- target ref: `('B_L0_P0_0', 0, 0)`
- supporting marker ids: `('f0', 'f1', 'f2')`
- reconstructed hex cell ref: `B_L0_P0_0:0:0`
- reconstructed chart fingerprint id: `B_L0_P0_0`

## Scenario Results

| scenario | input traces | compactions | member ids | uncompacted trace ids |
|---|---:|---:|---|---|
| shared_support_distinct_shards | 2 | 0 | () | ('a0', 'a1') |
| shared_support_distinct_proposals | 2 | 0 | () | ('b0', 'b1') |
| shared_support_distinct_revision_proxy | 2 | 0 | () | ('c0', 'c1') |
| exact_duplicate_transport_view | 2 | 1 | ('d0', 'd1') | () |
| mixed_group | 8 | 1 | ('d0', 'd1') | ('a0', 'a1', 'b0', 'b1', 'c0', 'c1') |

## Expansion Manifest Check

- compaction id: `trace_compaction:v2:25a9c2fab0649877534b477ba521dd4a`
- member trace ids: `('d0', 'd1')`
- expansion manifest: `('d0', 'd1')`
- aggregate mass: `0.5`
- expansion returns both original `GrowthTrace` values from the supplied in-memory trace index.

## Verified Facts

- The witness is selected from sealed GSC1 `build_collision_summaries()` as the canonical first `local_fork` summary with `collision_target_count > 0`.
- The target `HexCell` is reconstructed from the same GSC1 schedule, base layer, phase, phase policy, and target `CellRef`.
- Shared support cell and support key do not compact traces across distinct `origin_shard_id` values.
- Distinct proposal ids and distinct derivation proxies do not compact.
- Exact duplicate transport views compact only when every canonical evidence-bound field matches except `trace_id`.
- Compaction manifest and member ids are canonical and identical.
- `expand_compaction(...)` returns all original trace identities without deleting, replacing, or rewriting inputs.
- Reversed input order produces the same canonical compaction payload.

## Reasonable Interpretation

- DG2 trace compaction preserves evidence boundaries in this finite GSC1-supported collision witness.
- Shared geometric support is insufficient by itself to authorize trace compaction.
- Compaction is a reversible derived view over in-memory trace values, not an evidence mutation.

## Unverified Items

- Synthetic trace is not a DreamShard, AdmissionRecord, GrowthProposal, PlacementPlan, FieldSnapshot, RecallUniverse, or RecallDigest.
- The distinct revision proxy scenario is not a RevisionThread, current resolver, retired resolver, or real revision data model.
- No cover crystallization, gravity ranking, profile selection, recall traversal, runtime, OpenClaw, network, database, cache, LLM/NLP, or semantic search is exercised.

## Conclusion Limits

- GCM1 is limited to one canonical finite GSC1 `local_fork` collision witness.
- GCM1 does not modify production compaction, geometry, field, evidence, admission, assembly, recall, adapter, or runtime code.
- A support collision is not a merge signal, owner signal, parent-child signal, primary-source signal, current/retired signal, truth signal, trust signal, or compression recommendation.
