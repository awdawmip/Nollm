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
All positive DG1 kernel mass is materialized as derived trace mass unless it is
explicitly residualized. DG2 does not use geometry coordinate tolerance to hide
small positive trace mass.

Cross-chart propagation requires a caller-supplied verified chart link whose
source and target fingerprints exactly match the source and target cells.

## Cover

Cover aggregation is local to one `(chart_geometry_fingerprint, cell_ref)`.
Stable eligibility is policy-versioned and requires mass, independent support,
axis diversity, no provisional mass, bounded genericity / ambiguity / conflict,
and sufficient stability.
The provisional, two-support, and two-axis floors are structural hard rules and
cannot be relaxed by `CoverPolicy`. Cover inputs are trace identity sets; a
duplicate `trace_id` is rejected instead of deduplicated or counted twice.
`CoarseCover` keeps `policy_id` and `policy_version`, and cover identity includes
the full policy semantic payload.
`CoarseCover` also keeps `policy_fingerprint`, a deterministic ID over the full
policy semantic payload. Evaluators reject policy ID, version, or fingerprint
mismatch. Stable and crystallized cover values must satisfy the structural
floors directly, and crystallization rechecks those floors before the final
state transition.

## Gravity

Gravity is an internal Field snapshot. It is computed only from stable or
crystallized covers and records support and penalty terms separately. It is not
an external anchor, index, query parameter, recall selector, or truth score.
Gravity snapshot inputs are cover identity sets; duplicate `cover_id` is
rejected.

## Compaction

Trace compaction is a reversible view. It groups only fully compatible traces
and expands back to original member trace IDs. It does not delete or mutate
member traces.
Compaction rejects duplicate trace identities before grouping, and expansion
rejects duplicate or missing manifest IDs.
`member_trace_ids` and `expansion_manifest` are the same non-empty canonical
tuple. Expansion validates that relation before returning traces, so a forged
manifest cannot silently drop a member.
