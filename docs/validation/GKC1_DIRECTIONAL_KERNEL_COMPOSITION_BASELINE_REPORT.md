# GKC1 Directional Kernel Composition / Non-Identity Baseline Report

- baseline commit: `f2629ba08aeec0a7179e640536a35dd720ab28a1`
- validation kind: pure synthetic geometry validation
- runner output: this Markdown report only
- boundary: two-step directed geometry composition is measured over finite partitions and creates no production composition API, write permission, read authority, ranking, or profile selection.

## Experiment Window

- parameter id: `B`
- beta: `1.189207115`
- delta theta degrees: `22.5`
- base layer: `0`
- phase: `(0.0, 0.0)`
- phase policies: `('constant_local', 'layer_drift_control')`
- layer gaps: `(4, 8, 16)`
- source axial stencil: `((0, 0), (1, 0), (0, 1), (1, -1), (2, -1))`
- target disk radius: `4`
- target partition size: `61`
- coverage threshold: `1e-09`
- setting count: `30`
- composition observation count: `60`
- tolerances: `{'mass': '1e-12', 'coverage_area_abs': '1e-12'}`
- report metric rendering: values with absolute value at or below `GKC1_REPORTING_NOISE_FLOOR = 1.000000e-12` are shown as `<=1.000000e-12`; raw validation still uses real float64 values.

## Single-Leg Construction

- Every first leg and every second leg is computed with production `compute_distribution(...)`.
- Every source, intermediate, and return target cell is built with production `make_hex_cell(...)`.
- Every finite target disk is centered with production `nearest_axial(...)` from the true source cell center.

## Composition Construction

- `fine_coarse_fine` multiplies retained fine-to-coarse weights by independently computed coarse-to-fine weights.
- `coarse_fine_coarse` multiplies retained coarse-to-fine weights by independently computed fine-to-coarse weights.
- Composition residual is first-leg residual plus first-leg-weighted second-leg residual.
- Composed weights are not normalized a second time.

## Fine->Coarse->Fine Summary

| gap | policy | count | support min | support max | self min | self max | positive residual | residual min | residual max |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | constant_local | 5 | 7 | 18 | 9.375000e-02 | 2.500000e-01 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 4 | layer_drift_control | 5 | 9 | 22 | 9.061227e-02 | 2.500000e-01 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 8 | constant_local | 5 | 19 | 19 | 6.250000e-02 | 6.250000e-02 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 8 | layer_drift_control | 5 | 25 | 46 | 3.284542e-02 | 6.250000e-02 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 16 | constant_local | 5 | 61 | 61 | 3.906250e-03 | 3.906250e-03 | 5 | 7.617187e-01 | 7.617187e-01 |
| 16 | layer_drift_control | 5 | 61 | 61 | 3.906250e-03 | 3.906250e-03 | 5 | 7.617187e-01 | 7.617187e-01 |

## Coarse->Fine->Coarse Summary

| gap | policy | count | support min | support max | self min | self max | positive residual | residual min | residual max |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | constant_local | 5 | 7 | 7 | 6.250000e-01 | 7.355204e-01 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 4 | layer_drift_control | 5 | 7 | 7 | 6.877899e-01 | 7.562589e-01 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 8 | constant_local | 5 | 7 | 7 | 9.062500e-01 | 9.062500e-01 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 8 | layer_drift_control | 5 | 7 | 7 | 8.531075e-01 | 8.531075e-01 | 0 | <=1.000000e-12 | <=1.000000e-12 |
| 16 | constant_local | 5 | 1 | 1 | 2.382813e-01 | 2.382813e-01 | 5 | 7.617187e-01 | 7.617187e-01 |
| 16 | layer_drift_control | 5 | 1 | 1 | 2.382812e-01 | 2.382813e-01 | 5 | 7.617187e-01 | 7.617188e-01 |

## Mass and Residual Ledger

- positive residual by direction and gap: `{('coarse_fine_coarse', 16): 10, ('fine_coarse_fine', 16): 10}`
- observations with positive first-leg residual: `10`
- observations with positive weighted second-leg residual: `10`
- Gap-16 residual is finite radius-4 partition mass and is retained in the ledger.

## Non-Identity Summary

- observation count: `60`
- observations with source chart equal to return chart: `60`
- observations with intermediate chart different from source chart: `60`
- observations with self return mass below one: `60`
- observations with positive identity distance: `60`

## Central Regression Anchors

| composition direction | gap | self return mass |
|---|---:|---:|
| coarse_fine_coarse | 4 | 6.250000e-01 |
| coarse_fine_coarse | 8 | 9.062500e-01 |
| coarse_fine_coarse | 16 | 2.382813e-01 |
| fine_coarse_fine | 4 | 2.500000e-01 |
| fine_coarse_fine | 8 | 6.250000e-02 |
| fine_coarse_fine | 16 | 3.906250e-03 |

## Verified Facts

- Parameter B is the only sampled parameter and is read from production `PARAMETER_MATRIX`.
- All 60 observations are formed from real production single-leg distributions.
- Every observation preserves `composed_kernel_mass + composition_residual_mass = composition_total_mass` in production tolerance.
- Every observation returns to the source chart and remains non-identity at source-cell level.
- Gap-16 residual remains visible in both composition directions.

## Reasonable Interpretation

- Returning to the source chart is not the same as returning all mass to the source cell.
- Higher self-return mass is a finite geometry diagnostic, not a permission or ranking rule.
- The two-step relation is a finite composed distribution, not a production transport mechanism.

## Unverified Items

- No all-plane statement, parameter replacement recommendation, structural containment claim, write condition, read authority, ranking rule, or factual ordering is established.
- No Field, Evidence, Admission, Assembly, Recall, runtime, adapter, database, network, LLM/NLP, embedding, semantic search, or OpenClaw path is exercised.
- No cover, trace, compaction, FieldSnapshot, RecallUniverse, DreamShard, InterpretationRecord, RevisionThread, LedgerEvent, or CaptureReceipt is created.

## Conclusion Limits

- GKC1 is limited to base layer `0`, phase `(0.0, 0.0)`, gaps `(4, 8, 16)`, both layer phase policies, five source axial points, target disk radius `4`, and the two existing DG1 coverage directions.
- Non-identity observations do not create structural containment, compression permission, admission permission, or recall authority.
- Residual mass is finite partition boundary mass, not an error or semantic failure.
- GKC1 does not select, modify, replace, deprecate, or recommend replacing ParameterSet B.
- GKC1 changes no production geometry, field, evidence, admission, assembly, recall, adapter, runtime, CLI, network, database, LLM/NLP, embedding, semantic search, or OpenClaw behavior.
