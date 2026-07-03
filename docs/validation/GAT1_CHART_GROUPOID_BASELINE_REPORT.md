# GAT1 Finite Chart-Atlas Transition / Groupoid Baseline Report

- baseline commit: `ffe76e4ed574209e05ef3f8e35440aa50c0cd234`
- validation kind: pure synthetic geometry validation
- runner output: this Markdown report only
- synthetic correspondence boundary: same axial label is a coordinate-test fixture, not an overlap witness, not chart merge evidence, and not recall traversal authorization.

## Experiment Window

- parameter id: `B`
- layer range: `0..16`
- chart layer triples: `((0, 1, 2), (0, 4, 8), (1, 5, 13), (0, 8, 16))`
- witness axial labels: `((0, 0), (1, 0), (0, 1), (1, -1))`
- phase samples: `((0.0, 0.0), (0.5, 0.0), (0.3333333333333333, 0.3333333333333333), (0.2, 0.4))`
- layer phase policies: `('constant_local', 'layer_drift_control')`
- cycle count: `32`
- reference scale rule: `source chart side_length`
- tolerance: `{'coordinate_abs_tol': '1e-12', 'coordinate_rel_tol': '1e-10', 'area_abs_tol': '1e-12', 'area_rel_tol': '1e-10'}`
- report metric rendering: values with absolute value at or below `GAT1_REPORTING_NOISE_FLOOR = 1.000000e-12` are shown as `≤1.000000e-12`; raw validation still uses sealed DG1 tolerance and real float64 values.

## Pair And Cycle Summary

| triple | phase | policy | cycle state | witness geometry | cycle max residual | cycle rms residual | linear identity error | translation identity error | max pair residual | max scale error | max rotation error |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| (0, 1, 2) | (0,0) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 1, 2) | (0,0) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 1, 2) | (0.5,0) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 1, 2) | (0.5,0) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 1, 2) | (0.333333,0.333333) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 1, 2) | (0.333333,0.333333) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 1, 2) | (0.2,0.4) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 1, 2) | (0.2,0.4) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 4, 8) | (0,0) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 4, 8) | (0,0) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 4, 8) | (0.5,0) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 4, 8) | (0.5,0) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 4, 8) | (0.333333,0.333333) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 4, 8) | (0.333333,0.333333) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 4, 8) | (0.2,0.4) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 4, 8) | (0.2,0.4) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (1, 5, 13) | (0,0) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (1, 5, 13) | (0,0) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (1, 5, 13) | (0.5,0) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (1, 5, 13) | (0.5,0) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (1, 5, 13) | (0.333333,0.333333) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (1, 5, 13) | (0.333333,0.333333) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (1, 5, 13) | (0.2,0.4) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (1, 5, 13) | (0.2,0.4) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 8, 16) | (0,0) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 8, 16) | (0,0) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 8, 16) | (0.5,0) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 8, 16) | (0.5,0) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 8, 16) | (0.333333,0.333333) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 8, 16) | (0.333333,0.333333) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 8, 16) | (0.2,0.4) | constant_local | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |
| (0, 8, 16) | (0.2,0.4) | layer_drift_control | verified | nondegenerate | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 | ≤1.000000e-12 |

## Aggregate Bounds

- cycles checked: `32`
- directed pair validations checked: `96`
- max pair residual: `≤1.000000e-12`
- max cycle residual: `≤1.000000e-12`
- max scale-ratio error: `≤1.000000e-12`
- max rotation-delta error: `≤1.000000e-12`

## Negative Controls

- shifted target witness validation state: `rejected`
- duplicate witness validation state: `requires_review`
- tampered cycle residual state: `rejected`
- orientation reversing validation state: `rejected`

## Verified Facts

- Parameter B is the only sampled parameter.
- All charts are constructed from sealed DG1 `ScaleRotationSchedule.chart_for_layer(...)` with sealed default phase samples and layer phase policies.
- Each synthetic pair uses four fixed same-label axial witnesses; fit uses the first two witness pairs and validation uses all four.
- All 32 finite cycles are computed from real pair fits, inverse checks, pair composition checks, and DG1 `cycle_residual(...)`.
- Scale ratio and rotation delta consistency are finite checks against the source and target chart geometry.
- Report metric rendering uses a fixed presentation noise floor only for Markdown text; it is not an acceptance threshold.
- Negative controls do not verify.

## Reasonable Interpretation

- Under finite synthetic coordinate correspondence, DG1 transform primitives agree with the sealed schedule chart geometry.
- The result is useful as a precursor signal for future real overlap-witness atlas work.
- The result is not itself atlas evidence and does not authorize runtime traversal.

## Unverified Items

- No real overlap witness is created or verified.
- No ChartTransformRecord, TransformCycleCheck, Atlas registry, global chart connectivity, atlas merge, or cross-chart recall is created.
- No DreamShard physical or semantic identity is inferred.
- No exact algebraic proof is established; results use DG1 float64 tolerance.

## Conclusion Limits

- Layer window is limited to `0..16`.
- Chart triples are fixed to the four listed triples.
- Correspondence stencil is fixed to four axial labels and remains synthetic.
- Same axial label does not prove the same physical location or semantic object.
- GAT1 does not change profile, beta, theta, phase policy, translation policy, memory, admission, assembly, recall, adapter, or runtime behavior.
