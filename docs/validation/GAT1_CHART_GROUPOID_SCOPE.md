# GAT1 Chart Groupoid Scope

GAT1 is a pure synthetic geometry validation over the sealed GVR1 baseline:

`ffe76e4ed574209e05ef3f8e35440aa50c0cd234`

It validates finite chart-to-chart transform behavior for parameter B only, using sealed DG1 schedule, chart, hex-cell, and transform APIs.

## Fixed Window

- `CHART_LAYER_TRIPLES = ((0, 1, 2), (0, 4, 8), (1, 5, 13), (0, 8, 16))`
- `WITNESS_AXIALS = (AxialCoord(0, 0), AxialCoord(1, 0), AxialCoord(0, 1), AxialCoord(1, -1))`
- phase samples: sealed DG1 defaults
- layer phase policies: sealed DG1 defaults
- reference scale rule: source chart side length
- tolerance: sealed DG1 `DEFAULT_TOLERANCE`
- report metric rendering: diagnostics with absolute value no greater than `GAT1_REPORTING_NOISE_FLOOR = 1e-12` are displayed as `≤1.000000e-12`

This creates `32` finite synthetic cycles.

## Boundary

Same axial labels are only a reproducible coordinate-correspondence fixture. They are not overlap witnesses, physical identity claims, semantic identity claims, coverage kernels, chart records, atlas merge records, or recall traversal authorization.

The reporting noise floor is a Markdown presentation rule only. It removes platform-level float64 tail differences from derived reports; raw transform fit, validation, inverse, composition, cycle residual, and state recommendation calculations still use sealed DG1 `DEFAULT_TOLERANCE` and real finite values.

GAT1 does not modify production geometry, transform implementation, profile IDs, beta, theta, phase policy, translation policy, memory, capture, admission, assembly, recall, adapters, runtime, OpenClaw, network, database, cache, LLM, NLP, embedding, or semantic search behavior.
