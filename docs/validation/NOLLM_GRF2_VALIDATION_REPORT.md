# NOLLM GRF2 Validation Report

## Gate A

GATE_A_PASS

- CellRegistry exists.
- PlacementIndex exists.
- Density pressure is deterministic.
- Evidence identity, placement identity, and cell identity are separate.
- No object semantic edge is stored in cells.

## Gate B

GATE_B_PASS

- Kernel storage is independent from shard count.
- Multiple profiles coexist: eisenstein_exact_v1, dream_quasi_v1, aligned_baseline_v1.
- Template reload is deterministic by stable registry digest.
- Exact runtime float count = 0.

## Gate C

GATE_C_PASS

- Incremental rebuild is deterministic.
- Unaffected region remains unchanged.
- Stitch update is represented as local impact.
- Replay equality is achieved for placement field reconstruction.

## Gate D

GATE_D_PASS

- Large synthetic validation covers 10000, 100000, and 1000000 evidence items.
- Uniform, hotspot, and island scenarios are reported.
- relation_storage_size remains below explicit_graph_storage_size in every scenario.
- runtime_polygon_count = 0.
- runtime_float_count_exact_profile = 0.
- average_kernel_fanout <= 7.
- source fallback is preserved.

## Gate E

GATE_E_PASS

- Density overload boundary reports split/defer/migration.
- Wrong placement boundary reports revision/re-placement/local impact scope.
- False stitch boundary reports reject/rollback/bridge decay.
- Profile conflict boundary compares eisenstein_exact, dream_quasi, and aligned profiles.

## Baseline Comparison

Reported baselines:

- B0 lexical
- B1 vector-like
- B2 explicit graph
- B3 graph+vector
- N0 GRF exact
- N1 GRF stitching
- N2 GRF multi-profile
- N3 GRF incremental

GRF2 answer:

The prototype relation cost is represented by `cell_count + placement_count + kernel_size`;
explicit graph cost is represented by object-object pair storage. In the 1,000,000
synthetic item report, GRF relation storage remains below explicit graph storage
and kernel storage is reused independently of shard count.
