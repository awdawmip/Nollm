# D2 Local Chart and Gluing Proposal Records

D2 builds on D1 geometry primitives without turning them into recall,
placement, or a global atlas. The current implementation is a minimal immutable
record layer in `nollm.chart_gluing`.

## Scope

- Record local chart identity.
- Record finite chart seeds and radii.
- Summarize bounded overlap from D1 `Coverage` rows.
- Record gluing proposals.
- Store a D1 `SimilarityTransform` as a candidate transform primitive.
- Record residual or error fields for later review.

## Non-Scope

- No global atlas.
- No graph of charts.
- No automatic placement.
- No recall ranking.
- No card writing.
- No semantic scoring.
- No accept/reject policy.
- No parent-child ownership.

## Local Chart Identity

A local chart identity is a stable label for a bounded geometry view:

```text
chart_id
seed_hex
source_radius
layer_ids
parameter_signature
```

`LocalChartSpec` stores these values. `seed_hex` is a D1 `HexAddress`.
`source_radius` is finite. `layer_ids` names the bounded layers used by the
chart. `parameter_signature` records the D1 layer parameters used to compute
geometry.

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

`summarize_chart_overlap` computes a deterministic `coverage_sum` from bounded
D1 coverage rows using a selected denominator: `source`, `target`, or `union`.

## Gluing Proposal Record

A gluing proposal is not an accepted gluing decision:

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
defaults to `candidate` and remains descriptive until a later D2 policy defines
acceptance.

## Deferred Policy

Later work may define acceptance thresholds, conflict handling, and atlas
construction. This skeleton does not implement those policies.
