# DG2 Field Dynamics Conventions

DG2 Field code treats all text-like values as opaque caller-provided labels.
`axis`, `support_key`, `basis_refs`, `shard_id`, and `proposal_id` are compared
for equality and provenance only; Field does not parse their semantics.

## Trace Propagation

Write-side propagation accepts only DG1 `fine_to_coarse` coverage
distributions. For each parent trace:

```text
derived_mass + residual_mass = parent_mass
```

within DG1 float tolerance. Residual reasons remain explicit.

Cross-chart propagation requires a caller-supplied verified chart link whose
source and target fingerprints exactly match the source and target cells.

## Cover

Cover aggregation is local to one `(chart_geometry_fingerprint, cell_ref)`.
Stable eligibility is policy-versioned and requires mass, independent support,
axis diversity, no provisional mass, bounded genericity / ambiguity / conflict,
and sufficient stability.

## Gravity

Gravity is an internal Field snapshot. It is computed only from stable or
crystallized covers and records support and penalty terms separately. It is not
an external anchor, index, query parameter, recall selector, or truth score.

## Compaction

Trace compaction is a reversible view. It groups only fully compatible traces
and expands back to original member trace IDs. It does not delete or mutate
member traces.
