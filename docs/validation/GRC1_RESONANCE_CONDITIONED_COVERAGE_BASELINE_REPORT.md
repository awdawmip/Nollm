# GRC1 Resonance-Conditioned Coverage / Non-Hierarchy Baseline Report

- baseline commit: `1c9b1f0498051cd62b66cfad2fa05a6071778ab3`
- validation kind: pure synthetic geometry validation
- runner output: this Markdown report only
- boundary: scale/rotation commensurability, exact center alignment, singleton coverage, and multi-support coverage are diagnostic axes only; none is hierarchy, compression permission, admission permission, or recall authority.

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
- coverage direction: `fine_to_coarse`
- coverage threshold: `1e-09`
- observation count: `230`
- tolerances: `{'angle_degrees': '1e-12', 'scale': '1e-12', 'lattice': '1e-12', 'coverage_area_abs': '1e-12'}`
- report metric rendering: values with absolute value at or below `GRC1_REPORTING_NOISE_FLOOR = 1.000000e-12` are shown as `≤1.000000e-12`; raw validation still uses real float64 values.

## Alignment Classification Summary

| gap | policy | alignment class | count |
|---:|---|---|---:|
| 4 | constant_local | noncommensurate | 65 |
| 4 | layer_drift_control | noncommensurate | 65 |
| 8 | constant_local | exact_center_sublattice | 45 |
| 8 | layer_drift_control | commensurate_phase_separated | 45 |
| 16 | constant_local | exact_center_sublattice | 5 |
| 16 | layer_drift_control | commensurate_phase_separated | 5 |

## Coverage Summary

| gap | policy | coverage class | count |
|---:|---|---|---:|
| 4 | constant_local | multisupport | 39 |
| 4 | constant_local | singleton | 26 |
| 4 | layer_drift_control | multisupport | 57 |
| 4 | layer_drift_control | singleton | 8 |
| 8 | constant_local | singleton | 45 |
| 8 | layer_drift_control | multisupport | 23 |
| 8 | layer_drift_control | singleton | 22 |
| 16 | constant_local | singleton | 5 |
| 16 | layer_drift_control | singleton | 5 |

## Exact-Center Conditional Coverage

- exact-center observations: `50`
- exact-center singleton observations: `50`
- exact-center max coverage mass range: `1.000000e+00` .. `1.000000e+00`
- exact-center residual mass range: `≤1.000000e-12` .. `≤1.000000e-12`

## Phase-Separated Conditional Coverage

- gap 8 layer-drift singleton observations: `22`
- gap 8 layer-drift multi-support observations: `23`
- gap 16 layer-drift singleton observations: `5`
- gap 16 layer-drift multi-support observations: `0`

## Noncommensurate Control

- gap 4 observations: `130`
- gap 4 alignment classes: `('noncommensurate',)`
- gap 4 singleton observations: `34`
- gap 4 multi-support observations: `96`

## Conditional Matrix

| alignment class | coverage class | count |
|---|---|---:|
| commensurate_phase_separated | multisupport | 23 |
| commensurate_phase_separated | singleton | 27 |
| exact_center_sublattice | singleton | 50 |
| noncommensurate | multisupport | 96 |
| noncommensurate | singleton | 34 |

## Verified Facts

- Parameter B is the only sampled parameter and is read from production `PARAMETER_MATRIX`.
- Every source hex and target partition cell is built with production `make_hex_cell(...)`.
- Every target disk is centered with production `nearest_axial(...)` from the true source cell world center.
- Every coverage row is computed with production `compute_distribution(...)` and `distribution_metrics(...)`.
- All 230 observations retain alignment diagnostics and coverage diagnostics as separate fields.
- Exact-center rows are singleton coverage rows in this finite window.
- Phase-separated rows include both singleton and multi-support outcomes in this finite window.

## Reasonable Interpretation

- In the fixed GRC1 window, exact center alignment and singleton coverage coincide for the sampled rows.
- Center-map non-exactness is not equivalent to multi-support coverage.
- Noncommensurate gap 4 acts only as a finite coverage control, not as a profile decision.

## Unverified Items

- No all-plane statement, profile replacement recommendation, semantic hierarchy, memory hierarchy, compression permission, admission condition, or recall authority is established.
- No Field, Evidence, Admission, Assembly, Recall, runtime, adapter, cache, database, network, LLM/NLP, embedding, semantic search, or OpenClaw path is exercised.
- No cover, trace, compaction, FieldSnapshot, RecallUniverse, DreamShard, InterpretationRecord, RevisionThread, LedgerEvent, or CaptureReceipt is created.

## Conclusion Limits

- GRC1 is limited to phase `(0.0, 0.0)`, gaps `(4, 8, 16)`, both layer phase policies, five source axial points, target disk radius `4`, and fine-to-coarse direction.
- Exact center plus singleton coverage is not hierarchy evidence.
- Phase-separated singleton coverage is not contradiction or proof of global non-overlap.
- GRC1 does not select, modify, replace, deprecate, or recommend replacing ParameterSet B.
- GRC1 changes no production geometry, field, evidence, admission, assembly, recall, adapter, runtime, CLI, network, database, cache, LLM/NLP, embedding, semantic search, or OpenClaw behavior.
