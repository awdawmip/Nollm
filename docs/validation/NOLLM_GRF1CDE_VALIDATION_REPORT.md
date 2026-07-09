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

Pending implementation.
