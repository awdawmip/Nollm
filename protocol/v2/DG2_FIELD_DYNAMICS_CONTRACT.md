# DG2 Field Dynamics Contract

DG2 Field Dynamics consumes sealed DG1 geometry outputs and protocol enums only.
It does not read Evidence, interpret text, call runtime, or expose gravity as an
external query surface.

## Trace

Trace propagation accepts a parent `GrowthTrace` and a DG1 `K_up`
`CoverageDistribution`. For every parent trace:

```text
sum(derived_trace.mass) + residual.mass == parent.mass
```

within DG1 float tolerance. Residual reasons remain explicit.

## Cover

Coarse Cover aggregation is local to one `(chart_geometry_fingerprint,
cell_ref)` pair. Stable eligibility is evaluated by a versioned `CoverPolicy`
and requires independent support, axis diversity, no provisional mass, bounded
genericity / ambiguity / conflict, and sufficient stability.

## Gravity

Gravity Snapshot is internal Field state computed from stable or crystallized
covers. It is not an anchor, query parameter, index, memory selector, or fact
truth score.

## Compaction

Trace compaction is a reversible view. It may group only fully compatible
traces and must expand back to the original member trace IDs.
