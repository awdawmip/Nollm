# Nollm Route Book V3.7: Rotated Physical Field

Date: 2026-07-14

Status: active correction route.

## Basis

V3.7 preserves the V3.1 module boundaries, the V3.3 real-LLM semantic boundary,
and the V3.4 core-function priority. V3.6 remains a historical transitional
checkpoint: it proved cursor-free, rebuildable Surface traversal and live host
integration, but it did not prove the target physical geometry or natural
single-entry propagation.

## Physical contract

The active profile is `default_dream_v1`. It uses pointy-top, edge-to-edge
regular hexagons with `theta(0) = 0`, adjacent-layer rotation `22.5 degrees`,
and linear scale ratio `beta = 2^(1/4)`. Increasing physical layer indices are
finer; adjacent-layer cell density changes by `beta^2 = sqrt(2)`. Rotation has
an eight-layer phase cycle modulo 60 degrees while scale continues to change.

Lab owns high-precision world geometry, polygon overlap, candidate enumeration,
certification, and generated immutable templates. Core runtime loads versioned
integer artifacts and performs no polygon, trigonometric, or nondeterministic
floating-point work.

## Address domains

`GeometryAddress` identifies only a persistent physical memory cell.
`SurfaceAggregateAddress` identifies a rebuildable observation cell within an
explicit `PhysicalFieldScope`. Aggregation Order never changes physical layer
identity. A Surface includes native occupancy from every supported physical
layer in scope and reports unsupported spans explicitly.

Observation cell area grows by `sqrt(2)` per Order. Occupied Surface-cell count
is a dataset-dependent result, not a monotonic invariant. Active selection uses
only Core structure and fixed budgets and remains independent of query,
Statement, session, and previous traversal.

## Recall and placement

One OpenClaw traversal selects exactly one displayed Order-0 entry. Bounded Core
Coverage, Lateral, and Bridge propagation reconstruct locality from that entry.
Reachability of one fact from multiple independent entries is optional emergent
diagnostic evidence, never a wire contract or pass condition.

The first production placement profile writes native atoms only to physical
layer 0. Multi-layer placement, Stitch finalization, density-driven relocation,
persistent Surface caches, and large-scale performance remain future work.

## Preservation

No MemoryCursor, semantic route, relation index, graph, vector, embedding,
persistent entry hint, or Python semantic placement is permitted. OpenClaw
depends on Access public APIs; the real host LLM owns semantic decisions.
