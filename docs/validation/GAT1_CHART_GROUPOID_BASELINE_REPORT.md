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

## Pair And Cycle Summary

| triple | phase | policy | cycle state | witness geometry | cycle max residual | cycle rms residual | linear identity error | translation identity error | max pair residual | max scale error | max rotation error |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| (0, 1, 2) | (0,0) | constant_local | verified | nondegenerate | 2.482534e-16 | 2.077037e-16 | 1.110223e-16 | 0.000000e+00 | 4.577567e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 1, 2) | (0,0) | layer_drift_control | verified | nondegenerate | 2.482534e-16 | 2.077037e-16 | 1.110223e-16 | 0.000000e+00 | 4.475452e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 1, 2) | (0.5,0) | constant_local | verified | nondegenerate | 1.332661e-16 | 6.916933e-17 | 5.551115e-17 | 5.169937e-17 | 4.965068e-16 | 1.110223e-16 | 0.000000e+00 |
| (0, 1, 2) | (0.5,0) | layer_drift_control | verified | nondegenerate | 4.440892e-16 | 2.387666e-16 | 1.110223e-16 | 2.387625e-16 | 4.965068e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 1, 2) | (0.333333,0.333333) | constant_local | verified | nondegenerate | 1.110223e-16 | 7.850462e-17 | 5.551115e-17 | 1.177569e-16 | 4.965068e-16 | 1.110223e-16 | 0.000000e+00 |
| (0, 1, 2) | (0.333333,0.333333) | layer_drift_control | verified | nondegenerate | 1.665335e-16 | 1.177569e-16 | 5.551115e-17 | 8.777084e-17 | 4.965068e-16 | 1.110223e-16 | 0.000000e+00 |
| (0, 1, 2) | (0.2,0.4) | constant_local | verified | nondegenerate | 2.482534e-16 | 1.468687e-16 | 5.551115e-17 | 1.415262e-16 | 6.280370e-16 | 1.110223e-16 | 0.000000e+00 |
| (0, 1, 2) | (0.2,0.4) | layer_drift_control | verified | nondegenerate | 2.482534e-16 | 1.841097e-16 | 5.551115e-17 | 1.755417e-16 | 9.930137e-16 | 1.110223e-16 | 0.000000e+00 |
| (0, 4, 8) | (0,0) | constant_local | verified | nondegenerate | 2.482534e-16 | 2.077037e-16 | 1.110223e-16 | 0.000000e+00 | 2.220446e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 4, 8) | (0,0) | layer_drift_control | verified | nondegenerate | 2.482534e-16 | 2.077037e-16 | 1.110223e-16 | 0.000000e+00 | 4.440892e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 4, 8) | (0.5,0) | constant_local | verified | nondegenerate | 1.110223e-16 | 5.551115e-17 | 0.000000e+00 | 1.110223e-16 | 4.440892e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 4, 8) | (0.5,0) | layer_drift_control | verified | nondegenerate | 1.110223e-16 | 5.551115e-17 | 0.000000e+00 | 1.110223e-16 | 6.661338e-16 | 8.881784e-16 | 0.000000e+00 |
| (0, 4, 8) | (0.333333,0.333333) | constant_local | verified | nondegenerate | 2.220446e-16 | 1.301852e-16 | 0.000000e+00 | 1.110223e-16 | 4.965068e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 4, 8) | (0.333333,0.333333) | layer_drift_control | verified | nondegenerate | 2.775558e-16 | 2.513374e-16 | 0.000000e+00 | 2.220446e-16 | 7.021667e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 4, 8) | (0.2,0.4) | constant_local | verified | nondegenerate | 1.570092e-16 | 1.110223e-16 | 0.000000e+00 | 1.570092e-16 | 4.577567e-16 | 4.440892e-16 | 0.000000e+00 |
| (0, 4, 8) | (0.2,0.4) | layer_drift_control | verified | nondegenerate | 1.110223e-16 | 5.551115e-17 | 0.000000e+00 | 1.110223e-16 | 4.965068e-16 | 4.440892e-16 | 0.000000e+00 |
| (1, 5, 13) | (0,0) | constant_local | verified | nondegenerate | 3.140185e-16 | 2.305551e-16 | 2.220446e-16 | 0.000000e+00 | 2.220446e-16 | 1.110223e-16 | 0.000000e+00 |
| (1, 5, 13) | (0,0) | layer_drift_control | verified | nondegenerate | 2.371437e-16 | 1.804446e-16 | 5.233642e-17 | 2.640570e-16 | 2.288783e-16 | 0.000000e+00 | 0.000000e+00 |
| (1, 5, 13) | (0.5,0) | constant_local | verified | nondegenerate | 4.965068e-16 | 3.597534e-16 | 2.220446e-16 | 2.721838e-16 | 4.002966e-16 | 5.551115e-17 | 0.000000e+00 |
| (1, 5, 13) | (0.5,0) | layer_drift_control | verified | nondegenerate | 1.241267e-16 | 1.000742e-16 | 5.233642e-17 | 1.320285e-16 | 8.881784e-16 | 1.776357e-15 | 0.000000e+00 |
| (1, 5, 13) | (0.333333,0.333333) | constant_local | verified | nondegenerate | 5.721958e-16 | 4.319984e-16 | 2.281291e-16 | 2.952247e-16 | 3.140185e-16 | 1.110223e-16 | 0.000000e+00 |
| (1, 5, 13) | (0.333333,0.333333) | layer_drift_control | verified | nondegenerate | 6.479604e-16 | 4.302114e-16 | 2.220446e-16 | 5.281140e-16 | 7.108896e-16 | 1.776357e-15 | 0.000000e+00 |
| (1, 5, 13) | (0.2,0.4) | constant_local | verified | nondegenerate | 2.220446e-16 | 1.249001e-16 | 5.233642e-17 | 1.476124e-16 | 2.860979e-16 | 1.110223e-16 | 0.000000e+00 |
| (1, 5, 13) | (0.2,0.4) | layer_drift_control | verified | nondegenerate | 2.220446e-16 | 1.309228e-16 | 5.233642e-17 | 6.601426e-17 | 4.577567e-16 | 1.110223e-16 | 0.000000e+00 |
| (0, 8, 16) | (0,0) | constant_local | verified | nondegenerate | 0.000000e+00 | 0.000000e+00 | 0.000000e+00 | 0.000000e+00 | 2.220446e-16 | 1.776357e-15 | 0.000000e+00 |
| (0, 8, 16) | (0,0) | layer_drift_control | verified | nondegenerate | 2.482534e-16 | 2.077037e-16 | 1.110223e-16 | 0.000000e+00 | 4.965068e-16 | 1.776357e-15 | 0.000000e+00 |
| (0, 8, 16) | (0.5,0) | constant_local | verified | nondegenerate | 1.110223e-16 | 5.551115e-17 | 4.930381e-32 | 1.110223e-16 | 3.140185e-16 | 1.776357e-15 | 0.000000e+00 |
| (0, 8, 16) | (0.5,0) | layer_drift_control | verified | nondegenerate | 4.440892e-16 | 4.440892e-16 | 0.000000e+00 | 4.440892e-16 | 7.021667e-16 | 1.776357e-15 | 0.000000e+00 |
| (0, 8, 16) | (0.333333,0.333333) | constant_local | verified | nondegenerate | 2.220446e-16 | 1.922963e-16 | 2.220446e-16 | 4.475452e-16 | 7.021667e-16 | 5.329071e-15 | 0.000000e+00 |
| (0, 8, 16) | (0.333333,0.333333) | layer_drift_control | verified | nondegenerate | 4.440892e-16 | 4.440892e-16 | 0.000000e+00 | 4.440892e-16 | 3.140185e-16 | 1.776357e-15 | 0.000000e+00 |
| (0, 8, 16) | (0.2,0.4) | constant_local | verified | nondegenerate | 1.110223e-16 | 5.551115e-17 | 0.000000e+00 | 1.110223e-16 | 2.482534e-16 | 1.776357e-15 | 0.000000e+00 |
| (0, 8, 16) | (0.2,0.4) | layer_drift_control | verified | nondegenerate | 4.965068e-16 | 3.090730e-16 | 2.220446e-16 | 2.220446e-16 | 4.965068e-16 | 5.329071e-15 | 0.000000e+00 |

## Aggregate Bounds

- cycles checked: `32`
- directed pair validations checked: `96`
- max pair residual: `9.930137e-16`
- max cycle residual: `6.479604e-16`
- max scale-ratio error: `5.329071e-15`
- max rotation-delta error: `0.000000e+00`

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
