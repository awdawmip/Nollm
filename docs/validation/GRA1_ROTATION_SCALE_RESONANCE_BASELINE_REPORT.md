# GRA1 Rotation-Scale Resonance / Phase-Drift Separation Baseline Report

- baseline commit: `2ce5c13f48c2478010acb73c4a612678e7830b10`
- validation kind: pure synthetic geometry validation
- runner output: this Markdown report only
- boundary: scale/rotation commensurability is not exact center-sublattice alignment, not cover authority, not parent/child structure, not compression permission, and not recall authority.

## Experiment Window

- parameter id: `B`
- beta: `1.189207115`
- delta theta degrees: `22.5`
- max layer: `16`
- layer gaps: `(1, 2, 4, 8, 16)`
- base layer counts: `{1: 16, 2: 15, 4: 13, 8: 9, 16: 1}`
- phase samples: `((0.0, 0.0), (0.5, 0.0), (0.3333333333333333, 0.3333333333333333), (0.2, 0.4))`
- phase policies: `('constant_local', 'layer_drift_control')`
- axial center stencil: `((0, 0), (1, 0), (0, 1), (1, -1), (2, -1))`
- observation count: `432`
- tolerances: `{'angle_degrees': '1e-12', 'scale': '1e-12', 'lattice': '1e-12'}`

## Recurrence Candidates

| gap | side ratio | rotation mod hex degrees | nearest integer scale | scale integer error |
|---:|---:|---:|---:|---:|
| 1 | 1.189207115 | 22.5 | 1 | 0.189207115003 |
| 2 | 1.41421356237 | 15 | 1 | 0.414213562373 |
| 4 | 2 | 30 | 2 | 4.4408920985e-16 |
| 8 | 4 | 0 | 4 | 8.881784197e-16 |
| 16 | 16 | 0 | 16 | 7.1054273576e-15 |

## Observation Counts

- total observations: `432`
- exact center-sublattice: `21`
- commensurate phase-separated: `59`
- noncommensurate: `352`

## Classification Summary

| gap | phase policy | classification | count |
|---:|---|---|---:|
| 1 | constant_local | noncommensurate | 64 |
| 1 | layer_drift_control | noncommensurate | 64 |
| 2 | constant_local | noncommensurate | 60 |
| 2 | layer_drift_control | noncommensurate | 60 |
| 4 | constant_local | noncommensurate | 52 |
| 4 | layer_drift_control | noncommensurate | 52 |
| 8 | constant_local | commensurate_phase_separated | 18 |
| 8 | constant_local | exact_center_sublattice | 18 |
| 8 | layer_drift_control | commensurate_phase_separated | 36 |
| 16 | constant_local | commensurate_phase_separated | 1 |
| 16 | constant_local | exact_center_sublattice | 3 |
| 16 | layer_drift_control | commensurate_phase_separated | 4 |

## Constant-Local Findings

| gap | phase | count | classifications | max center residual |
|---:|---|---:|---|---:|
| 8 | (0,0) | 9 | ('exact_center_sublattice',) | 5.3290705182e-15 |
| 16 | (0,0) | 1 | ('exact_center_sublattice',) | 1.24344978758e-14 |

## Layer-Drift Findings

| gap | phase | count | classifications | max center residual | relative phase samples |
|---:|---|---:|---|---:|---|
| 8 | (0,0) | 9 | ('commensurate_phase_separated',) | 0.486486486486 | (('0.783784', '0.609756'), ('0.648649', '0.365854'), ('0.513514', '0.121951')) |
| 16 | (0,0) | 1 | ('commensurate_phase_separated',) | 0.432432432432 | (('0.567568', '0.219512'),) |

## Verified Facts

- Parameter B is the only sampled parameter and is read from production `PARAMETER_MATRIX`.
- Each gap samples every legal base layer in the finite `0..16` layer window.
- All four production default phase samples and both production layer phase policies are included.
- All 432 observations use production `ScaleRotationSchedule.chart_for_layer(...)`, `axial_to_world(...)`, `world_to_fractional_axial(...)`, `normalized_phase(...)`, and `relative_phase(...)`.
- Gap 8 and gap 16 are the only sampled integer-scale, hex-orientation commensurate gaps under the fixed tolerances.
- Candidate recurrence classifications across gap 8 and 16: `{'exact_center_sublattice': 21, 'commensurate_phase_separated': 59, 'noncommensurate': 0}`.
- Each observation stores five center-map rows and can be reclassified from recorded numeric fields.

## Reasonable Interpretation

- Gap 8 and gap 16 expose finite scale/rotation recurrence candidates for engineering baseline B.
- Exact center-sublattice alignment, when present, is a finite chart-center mapping result.
- Phase drift can separate commensurate scale/rotation from exact center-grid alignment in the sampled stencil.

## Unverified Items

- No polygon overlap, coverage kernel, trace, cover, gravity, compaction, admission, field snapshot, recall universe, or recall digest is computed.
- Commensurate phase-separated is not a proof of global non-overlap or full-plane anti-resonance.
- Exact center-sublattice alignment is not semantic hierarchy, memory hierarchy, parent/child relation, cover eligibility, compression permission, admission permission, or recall permission.

## Conclusion Limits

- GRA1 does not choose, replace, deprecate, or modify ParameterSet B.
- GRA1 does not recommend a production profile replacement.
- The result is limited to the finite layers, gaps, phases, policies, and five-point center stencil listed above.
- GRA1 changes no production geometry, field, evidence, admission, assembly, recall, adapter, runtime, CLI, network, database, cache, LLM/NLP, embedding, semantic search, or OpenClaw behavior.
