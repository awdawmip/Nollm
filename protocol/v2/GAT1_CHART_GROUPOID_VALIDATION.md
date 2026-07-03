# GAT1 Chart Groupoid Validation

GAT1 validates finite synthetic coordinate transform behavior for sealed DG1 charts without creating atlas state.

## Construction Rule

For each fixed chart layer triple `(A, B, C)`, phase sample, and layer phase policy:

- build charts with `ScaleRotationSchedule(parameter_B).chart_for_layer(layer, policy.phase_for_layer(phase, layer))`;
- build four synthetic witnesses from matching axial labels with `make_hex_cell(chart, axial).center`;
- fit each pair transform from the first two witness pairs;
- validate each pair transform against all four witnesses;
- check inverse consistency, two-step composition consistency, and `cycle_residual((T_AB, T_BC, T_CA), ...)`.

## Synthetic Correspondence Boundary

Same axial label correspondence is a validation fixture only. It is not a physical overlap witness, DreamShard identity assertion, coverage kernel, ChartTransformRecord, TransformCycleCheck, atlas registry update, atlas merge, or recall path.

## Metrics

GAT1 reports finite pair residuals, cycle residuals, scale-ratio error, rotation-delta error, inverse point error, composition point error, and negative-control states. These are diagnostic values over a fixed finite test window, not production profile selectors.

## Non-Claims

GAT1 does not establish global atlas connectivity, global groupoid consistency, exact algebraic proof, semantic identity, physical identity, runtime traversal, or cross-chart recall.
