# D2 Local Chart and Gluing Proposal Skeleton

D2 builds on D1 geometry primitives without turning them into recall,
placement, or a global atlas. This document defines the minimal records needed
to discuss local chart gluing later.

## Scope

- Describe local chart identity.
- Describe finite chart seeds and radii.
- Describe candidate overlap between bounded charts.
- Describe a gluing proposal record.
- Use D1 `SimilarityTransform` as a candidate transform primitive.
- Record residual or error fields for later review.

## Non-Scope

- No global atlas.
- No graph of charts.
- No automatic placement.
- No recall ranking.
- No card writing.
- No semantic scoring.
- No accept/reject policy.

## Local Chart Identity

A local chart identity is a stable label for a bounded geometry view:

```text
chart_id
seed_hex
source_radius
layer_ids
parameter_signature
```

`seed_hex` is a D1 `HexAddress`. `source_radius` is finite. `layer_ids` names
the bounded layers used by the chart. `parameter_signature` records the D1
layer parameters used to compute geometry.

## Candidate Chart Overlap

Candidate overlap is derived from D1 many-to-many coverage rows. It is not
ownership and it does not assign one cell to another.

```text
source_chart_id
target_chart_id
overlap_rows
coverage_denominator
coverage_sum
```

Nearest-center behavior remains D1 candidate generation only. Polygon overlap
determines the actual coverage rows.

## Gluing Proposal Record

A gluing proposal is a proposal, not a decision:

```text
proposal_id
source_chart_id
target_chart_id
similarity_candidate
residual
evidence_rows
status
```

`similarity_candidate` is a D1 `SimilarityTransform`. `residual` is a numeric
error field. `evidence_rows` may reference bounded overlap evidence. `status`
is descriptive only until a later D2 policy defines acceptance.

## Deferred Policy

Later work may define acceptance thresholds, conflict handling, and atlas
construction. This skeleton does not implement those policies.
