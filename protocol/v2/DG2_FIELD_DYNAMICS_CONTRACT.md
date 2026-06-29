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
Every positive DG1 kernel mass is explicitly materialized as a derived trace
unless it is explicitly accounted as residual. Field must not hide sub-tolerance
positive mass in `accounting_error`; that value is only floating summation error.

## Cover

Coarse Cover aggregation is local to one `(chart_geometry_fingerprint,
cell_ref)` pair. Stable eligibility is evaluated by a versioned `CoverPolicy`
and requires independent support, axis diversity, no provisional mass, bounded
genericity / ambiguity / conflict, and sufficient stability.
The provisional, multi-support, and multi-axis floors are structural and cannot
be relaxed by policy. `build_local_covers` accepts trace identity sets, not
multisets; duplicate `trace_id` input is rejected. `CoarseCover` records
`policy_id`, `policy_version`, and cover identity includes the complete policy
semantic payload.

## Gravity

Gravity Snapshot is internal Field state computed from stable or crystallized
covers. It is not an anchor, query parameter, index, memory selector, or fact
truth score.
Snapshot input is a cover identity set; duplicate `cover_id` input is rejected.

## Compaction

Trace compaction is a reversible view. It may group only fully compatible
traces and must expand back to the original member trace IDs.
Compaction accepts trace identity sets, rejects duplicate `trace_id`, and
expansion rejects duplicate or missing manifest IDs.
