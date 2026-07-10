# NOLLM GRF2R Real Scale Validation Report

## Result

GRF2R_PASS for the deterministic, in-memory real-scale fixture topology.

The benchmark did not use formula-derived scale metrics. Each generated item
created an `EvidenceShardRecord`, `SourceWindowRecord`, `EvidenceIsland`, and
`PlacementRecord`, then inserted the placement through `FieldEngine` and built
a `RelationField`. The explicit graph comparison materialized actual Python
object edges for every pair in the same generated cell.

## Gate A: Real Dataset Generation

| Dataset | Shards | Windows | Cells | Placements | Islands | Stitches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 10,000 | 10,000 | 500 | 10,000 | 10,000 | 1 |
| 100,000 | 100,000 | 100,000 | 5,000 | 100,000 | 100,000 | 1 |
| 1,000,000 | 1,000,000 | 1,000,000 | 50,000 | 1,000,000 | 1,000,000 | 1 |

## Gate B and D: Measured Field and Graph Storage

All values are bytes measured from the instantiated in-memory objects and
containers. `explicit_graph_storage_size` is a local object-object graph for
the benchmark's actual fixed-density cell topology; it is not an unexecuted
global-clique estimate.

| Dataset | Cell | Placement | Kernel | Template | Relation Field | Explicit Graph | Materialized Edges |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 1,241,024 | 4,222,634 | 39,842 | 42,444 | 5,547,164 | 6,880,984 | 95,000 |
| 100,000 | 12,335,088 | 45,826,162 | 38,642 | 42,444 | 58,243,548 | 69,248,728 | 950,000 |
| 1,000,000 | 125,643,056 | 445,027,058 | 38,642 | 42,444 | 570,752,404 | 687,195,672 | 9,500,000 |

Measured relation storage growth ratios are `58,243,548/5,547,164` and
`570,752,404/58,243,548`; both are approximately one tenfold dataset step,
not a hundredfold step. Kernel storage remained effectively constant at
39,842, 38,642, and 38,642 bytes while the actual shard count grew to one
million. Kernel reuse was respectively `10,000/38`, `100,000/38`, and
`1,000,000/38` placements per compiled kernel entry.

The final 1M run measured build latency `33,435,486,700 ns`, lookup latency
`1,461,415,600 ns`, and recall latency `919,522,600 ns`. The exact profile
continues to use integer addresses and Q16 weights; no runtime polygons or
exact-profile floats are introduced.

## Gate C: Incremental Equality

The real update path performed add, remove, move, and accepted stitch-bridge
operations. A separate full rebuild from the final placement set matched the
incremental result for selected shards, coverage paths, kernel paths, scores,
and measured storage state.

## Gate E: Failure Injection

See [NOLLM_GRF2R_FAILURE_REPORT.md](NOLLM_GRF2R_FAILURE_REPORT.md). Density
overload reached `migration_candidate` and produced a defer decision; wrong
placement performed a revision and re-placement with the two affected cells;
a false stitch was rejected, removed before field build, and therefore absent
from the rebuilt relation field.

## Baseline Comparison

The real benchmark reports lexical, fixed integer vector-like, explicit graph,
graph-plus-vector, GRF exact, stitching, multi-profile, and incremental
variants from actual allocated structures. At 1M, the measured comparison was:

| Variant | Storage (bytes) | Maintenance | Auditability |
| --- | ---: | --- | --- |
| lexical | 80,443,728 | token-set insertion | low |
| vector-like | 4,091,948 | integer fingerprint insertion | low |
| explicit graph | 687,195,672 | object-edge materialization | medium |
| graph + vector | 691,287,620 | edge plus fingerprint insertion | medium |
| GRF exact | 570,752,404 | FieldEngine insertion | high |
| GRF stitching | 570,752,404 | accepted reversible bridge | high |
| GRF multi-profile | 570,752,404 | three-profile registry | high |
| GRF incremental | 570,752,404 | local update replay | high |

## Acceptance Conditions

1. Records passed through FieldEngine and RelationField: pass.
2. Kernel storage was decoupled from shard count: pass.
3. Measured relation storage was not quadratic across the three real scale runs: pass.
4. Incremental rebuild matched a separate full rebuild: pass.
5. Every recalled placement retained its original source fallback reference: pass.
6. Density, wrong-placement, and false-stitch boundaries were executed and controlled: pass.
