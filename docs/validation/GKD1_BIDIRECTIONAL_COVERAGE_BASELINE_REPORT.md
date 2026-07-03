# GKD1 Bidirectional Coverage-Kernel / Directional Non-Inversion Baseline Report

- baseline commit: `39b673fbba829f1c3285e9496b5af9c9890bf0af`
- validation kind: pure synthetic geometry validation
- runner output: this Markdown report only
- boundary: K_up and K_down are measured as separate directed geometry kernels; their differences do not grant structural containment, write permission, read authority, ranking, or profile selection.

## Experiment Window

- parameter id: `B`
- beta: `1.189207115`
- delta theta degrees: `22.5`
- max layer: `16`
- phase: `(0.0, 0.0)`
- phase policies: `('constant_local', 'layer_drift_control')`
- layer gaps: `(4, 8, 16)`
- base layer counts: `{4: 13, 8: 9, 16: 1}`
- source axial stencil: `((0, 0), (1, 0), (0, 1), (1, -1), (2, -1))`
- target disk radius: `4`
- target partition size: `61`
- coverage threshold: `1e-09`
- records per direction: `230`
- directional pairs: `230`
- tolerances: `{'mass': '1e-12', 'coverage_area_abs': '1e-12'}`
- report metric rendering: values with absolute value at or below `GKD1_REPORTING_NOISE_FLOOR = 1.000000e-12` are shown as `<=1.000000e-12`; raw validation still uses real float64 values.

## Directional Construction

- K_up uses a fine source cell, a coarse target disk, and `CoverageDirection.fine_to_coarse`.
- K_down uses a coarse source cell, a fine target disk, and `CoverageDirection.coarse_to_fine`.
- The two directions use distinct source cells and distinct target partitions for the same tuple key.
- K_down is not computed from K_up weights, target refs, or a matrix inverse.

## K_up Summary

| gap | policy | count | support min | support max | positive residual | residual min | residual max |
|---:|---|---:|---:|---:|---:|---:|---:|
| 4 | constant_local | 65 | 1 | 3 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 4 | layer_drift_control | 65 | 1 | 3 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 8 | constant_local | 45 | 1 | 1 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 8 | layer_drift_control | 45 | 1 | 3 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 16 | constant_local | 5 | 1 | 1 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 16 | layer_drift_control | 5 | 1 | 1 | 0 | <=1.000000e-12 | <=1.000000e-12 |

## K_down Summary

| gap | policy | count | support min | support max | positive residual | residual min | residual max |
|---:|---|---:|---:|---:|---:|---:|---:|
| 4 | constant_local | 65 | 7 | 10 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 4 | layer_drift_control | 65 | 7 | 12 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 8 | constant_local | 45 | 19 | 19 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 8 | layer_drift_control | 45 | 25 | 25 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 16 | constant_local | 5 | 61 | 61 | 5 | 7.617187e-01 | 7.617187e-01 |
| 16 | layer_drift_control | 5 | 61 | 61 | 5 | 7.617187e-01 | 7.617188e-01 |

## Directional Pair Comparison

- pair count: `230`
- K_up support less than K_down support: `230`
- equal support count: `0`
- K_up support greater than K_down support: `0`
- exact kernel weight vector matches: `0`
- kernel weight vector differs: `230`

## Residual Boundary Summary

- K_up zero residual records: `230`
- K_up positive residual records: `0`
- K_down zero residual records: `220`
- K_down positive residual records: `10`
- K_down positive residual gap counts: `{16: 10}`
- K_down positive residual policy counts: `{'constant_local': 5, 'layer_drift_control': 5}`
- K_down positive residual source axials: `((0, 0), (0, 1), (1, -1), (1, 0), (2, -1))`
- K_down positive residual values: `('0.76171875',)`
- The K_down residual result is constrained by target disk radius `4`; it is finite-window boundary mass.

## Verified Facts

- Parameter B is the only sampled parameter and is read from production `PARAMETER_MATRIX`.
- Every source hex and target partition cell is built with production `make_hex_cell(...)`.
- Every target disk is centered with production `nearest_axial(...)` from the true source cell world center.
- Every coverage row is computed with production `compute_distribution(...)` and `distribution_metrics(...)`.
- Every record preserves `kernel_mass + coverage_residual_mass = total_mass` in production tolerance.
- The fixed window yields 230 K_up rows, 230 K_down rows, and 230 pair rows.
- All pair rows have smaller K_up support count than K_down support count.
- All pair rows have different canonical kernel weight vectors.
- K_down positive residual rows are retained as explicit finite target-partition boundary observations.

## Reasonable Interpretation

- K_up and K_down are different directed geometry kernels because their source area normalization and target partitions differ.
- The observed K_down residual means the supplied radius-4 fine partition is finite; it is not silently full-plane coverage.
- The fixed-window support relation is a reproducible diagnostic, not a quality ranking.

## Unverified Items

- No all-plane statement, parameter replacement recommendation, structural containment claim, write condition, read authority, ranking rule, or factual ordering is established.
- No Field, Evidence, Admission, Assembly, Recall, runtime, adapter, database, network, LLM/NLP, embedding, semantic search, or OpenClaw path is exercised.
- No cover, trace, compaction, FieldSnapshot, RecallUniverse, DreamShard, InterpretationRecord, RevisionThread, LedgerEvent, or CaptureReceipt is created.

## Conclusion Limits

- GKD1 is limited to phase `(0.0, 0.0)`, gaps `(4, 8, 16)`, both layer phase policies, five source axial points, target disk radius `4`, and the two existing DG1 coverage directions.
- Directional support differences are not structural containment evidence.
- K_down residual is not an error or semantic failure.
- GKD1 does not select, modify, replace, deprecate, or recommend replacing ParameterSet B.
- GKD1 changes no production geometry, field, evidence, admission, assembly, recall, adapter, runtime, CLI, network, database, LLM/NLP, embedding, semantic search, or OpenClaw behavior.
