# GRF1-B Validation Report

Implemented modules:

```text
reference/python/nollm/grf/evidence_island.py
reference/python/nollm/grf/local_patch.py
reference/python/nollm/grf/stitching.py
reference/python/nollm/grf/bridge_kernel.py
```

Coverage direction convention:

```text
layer_index_direction = finer_with_increasing_index
coverage_up = fine to coarse, layer_delta = -1
coverage_down = coarse to fine, layer_delta = +1
```

Residual semantics:

```text
normalization_residual_q16 = Q16 sum residual
approximation_residual_q16 = compiler/profile approximation residual
exact/aligned approximation residual = 0
dream_quasi_v1 approximation residual > 0 with boundary ambiguity
```

EvidenceIsland lifecycle:

```text
floating -> patch_candidate -> placed -> stitch_candidate -> stitched -> archived
```

StitchProposal acceptance rules:

```text
weak-only lexical_hint or llm_semantic_suggestion never accepts
manual_bridge, source_backed_ref, or reuse_observed can accept
multi-medium witnesses can accept only above threshold with low residual
rejected proposals remain serializable as anti-stitch evidence
```

BridgeKernel bounds:

```text
0 < weight_q16 <= Q16_ONE
max_steps >= 1
max_fanout >= 1
evidence_refs non-empty
no global traversal
no fact merge
```

False-friend fixture:

```text
A = Apple company released an update
B = apple fruit storage temperature
C = Apple company privacy policy
```

The A/B lexical-only proposal is rejected and retained. The A/C proposal can
accept with source-backed or manual witness support.

Non-goals:

```text
no GRF recall product
no Cognee benchmark
no OpenClaw runtime
no main promotion
```
