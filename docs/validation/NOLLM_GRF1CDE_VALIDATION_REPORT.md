# GRF1-CDE Validation Report

## Gate C

```text
GATE_C_PASSED
- LocalPatch center containment enforced;
- StitchRecord / BridgeKernel patch alignment enforced;
- candidate_transform schema tightened;
- PlacementRecord has source_fallback_refs;
- GeometryMark declares not_fact_confirmation;
- MinimalAdmissionRecord does not copy coverage edge list;
- No placement object contains semantic_edge / parent / truth_score.
```

## Gate D

```text
GATE_D_PASSED
- RelationField runtime uses coverage template lookup;
- exact profile runtime has float operation count = 0;
- polygon/shapely/sin/cos runtime count = 0;
- top-B pruning deterministic;
- bridge propagation bounded;
- every RecallDigest selected shard has source_fallback_ref;
- CoverageReport contains path and drift info;
- no global semantic search or embedding path exists.
```

## Gate E

```text
GATE_E_PASSED
- Synthetic mini validation datasets created;
- Cognee-style local baseline reported, not actual Cognee run;
- false-stitch decoys include Apple company / apple fruit / Apple privacy;
- polygon_runtime_call_count = 0;
- runtime_float_operation_count = 0 for eisenstein_exact_v1;
- average_kernel_fanout = 3/1 <= configured bound;
- false_stitch_rate is reported;
- relation_storage_size is fixture-linear, not O(N^2).
```

Mini validation metrics:

```text
dataset_items = 9
B0_lexical: recall_correctness=7/7, source_faithfulness=7/13, false_stitch_rate=2/13, missed_stitch_rate=0/7, relation_storage_size=13
B1_vector_like_hashed_bow: recall_correctness=5/7, source_faithfulness=5/5, false_stitch_rate=0/5, missed_stitch_rate=2/7, relation_storage_size=5
B2_explicit_graph: recall_correctness=7/7, source_faithfulness=7/7, false_stitch_rate=0/7, missed_stitch_rate=0/7, relation_storage_size=7
N0_evidence_only: recall_correctness=0/7, source_faithfulness=0/1, false_stitch_rate=0/1, missed_stitch_rate=7/7, relation_storage_size=0
N1_geometry_mark_only: recall_correctness=2/7, source_faithfulness=2/2, false_stitch_rate=0/2, missed_stitch_rate=5/7, relation_storage_size=2
N2_grf_coverage_propagation: recall_correctness=4/7, source_faithfulness=4/4, false_stitch_rate=0/4, missed_stitch_rate=3/7, relation_storage_size=4
N3_grf_plus_stitching: recall_correctness=7/7, source_faithfulness=7/7, false_stitch_rate=0/7, missed_stitch_rate=0/7, relation_storage_size=7
N4_grf_coverage_report_visible: recall_correctness=7/7, source_faithfulness=7/7, false_stitch_rate=0/7, missed_stitch_rate=0/7, relation_storage_size=7
context_token_cost_estimate = 49
```

Failure / limitation cases:

```text
1. B0 lexical baseline recalls all expected pairs but also hits Apple company / apple fruit false friends.
2. B1 vector-like token overlap misses two expected stitch pairs.
3. N0 evidence-only misses all stitch relations because it has no relation field.
4. N1 geometry mark only misses five expected stitch relations.
5. Fixtures are synthetic and small; runtime is in-memory and non-production.
```

Next recommended task:

```text
GRF1-F: persistence / file-first storage / replayable GRF objects.
```
