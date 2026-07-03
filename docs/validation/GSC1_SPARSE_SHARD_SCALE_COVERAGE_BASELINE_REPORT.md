# GSC1 Finite Sparse-Shard / Scale-Coverage Baseline Report

- baseline commit: `7c3ef9d3a83f87a0dccfa7e9018692be9cdc69af`
- validation kind: pure synthetic geometry validation
- runner output: this Markdown report only
- synthetic shard boundary: each source marker is a finite occupancy label for coverage diagnostics; it is not a persisted DreamShard, not memory content, not a merge key, and not recall input.

## Experiment Window

- parameter id: `B`
- layer gaps: `(1, 4, 8)`
- base layers: `(0, 8)`
- phase samples: `((0.0, 0.0), (0.5, 0.0))`
- layer phase policies: `('constant_local', 'layer_drift_control')`
- target radius: `4`
- threshold: `1.000000e-09`
- source distribution call count: `144`
- patterns: `{'singleton': (('s0', (0, 0)),), 'local_fork': (('f0', (0, 0)), ('f1', (1, 0)), ('f2', (0, 1))), 'separated_pair': (('p0', (-1, 0)), ('p1', (1, 0)))}`
- tolerance: `{'coordinate_abs_tol': '1e-12', 'coordinate_rel_tol': '1e-10', 'area_abs_tol': '1e-12', 'area_rel_tol': '1e-10'}`
- report metric rendering: values with absolute value at or below `GSC1_REPORTING_NOISE_FLOOR = 1.000000e-12` are shown as `≤1.000000e-12`; raw validation still uses sealed DG1 tolerance and real float64 values.

## Observation Summary

| pattern | source count | observations | min kernels | max kernels | max residual mass |
|---|---:|---:|---:|---:|---:|
| singleton | 1 | 24 | 1 | 4 | ≤1.000000e-12 |
| local_fork | 3 | 72 | 1 | 4 | ≤1.000000e-12 |
| separated_pair | 2 | 48 | 1 | 4 | ≤1.000000e-12 |

## Support Collision Summary

| pattern | gap | base layer | phase | policy | sources | incidences | unique targets | collision targets | max marker support | max residual mass |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| local_fork | 1 | 0 | (0,0) | constant_local | 3 | 9 | 6 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 1 | 0 | (0,0) | layer_drift_control | 3 | 12 | 6 | 4 | 3 | ≤1.000000e-12 |
| local_fork | 1 | 0 | (0.5,0) | constant_local | 3 | 12 | 7 | 3 | 3 | ≤1.000000e-12 |
| local_fork | 1 | 0 | (0.5,0) | layer_drift_control | 3 | 11 | 7 | 3 | 3 | ≤1.000000e-12 |
| local_fork | 1 | 8 | (0,0) | constant_local | 3 | 9 | 6 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 1 | 8 | (0,0) | layer_drift_control | 3 | 10 | 6 | 3 | 3 | ≤1.000000e-12 |
| local_fork | 1 | 8 | (0.5,0) | constant_local | 3 | 12 | 7 | 3 | 3 | ≤1.000000e-12 |
| local_fork | 1 | 8 | (0.5,0) | layer_drift_control | 3 | 10 | 6 | 3 | 3 | ≤1.000000e-12 |
| local_fork | 4 | 0 | (0,0) | constant_local | 3 | 7 | 4 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 4 | 0 | (0,0) | layer_drift_control | 3 | 7 | 4 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 4 | 0 | (0.5,0) | constant_local | 3 | 7 | 4 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 4 | 0 | (0.5,0) | layer_drift_control | 3 | 7 | 4 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 4 | 8 | (0,0) | constant_local | 3 | 7 | 4 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 4 | 8 | (0,0) | layer_drift_control | 3 | 7 | 4 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 4 | 8 | (0.5,0) | constant_local | 3 | 7 | 4 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 4 | 8 | (0.5,0) | layer_drift_control | 3 | 8 | 4 | 2 | 3 | ≤1.000000e-12 |
| local_fork | 8 | 0 | (0,0) | constant_local | 3 | 3 | 1 | 1 | 3 | ≤1.000000e-12 |
| local_fork | 8 | 0 | (0,0) | layer_drift_control | 3 | 3 | 1 | 1 | 3 | ≤1.000000e-12 |
| local_fork | 8 | 0 | (0.5,0) | constant_local | 3 | 3 | 1 | 1 | 3 | ≤1.000000e-12 |
| local_fork | 8 | 0 | (0.5,0) | layer_drift_control | 3 | 3 | 1 | 1 | 3 | ≤1.000000e-12 |
| local_fork | 8 | 8 | (0,0) | constant_local | 3 | 3 | 1 | 1 | 3 | ≤1.000000e-12 |
| local_fork | 8 | 8 | (0,0) | layer_drift_control | 3 | 4 | 2 | 1 | 3 | ≤1.000000e-12 |
| local_fork | 8 | 8 | (0.5,0) | constant_local | 3 | 3 | 1 | 1 | 3 | ≤1.000000e-12 |
| local_fork | 8 | 8 | (0.5,0) | layer_drift_control | 3 | 4 | 2 | 1 | 3 | ≤1.000000e-12 |
| separated_pair | 1 | 0 | (0,0) | constant_local | 2 | 8 | 7 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 1 | 0 | (0,0) | layer_drift_control | 2 | 8 | 7 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 1 | 0 | (0.5,0) | constant_local | 2 | 8 | 7 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 1 | 0 | (0.5,0) | layer_drift_control | 2 | 8 | 7 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 1 | 8 | (0,0) | constant_local | 2 | 8 | 7 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 1 | 8 | (0,0) | layer_drift_control | 2 | 7 | 6 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 1 | 8 | (0.5,0) | constant_local | 2 | 8 | 7 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 1 | 8 | (0.5,0) | layer_drift_control | 2 | 6 | 6 | 0 | 1 | ≤1.000000e-12 |
| separated_pair | 4 | 0 | (0,0) | constant_local | 2 | 6 | 5 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 4 | 0 | (0,0) | layer_drift_control | 2 | 6 | 5 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 4 | 0 | (0.5,0) | constant_local | 2 | 4 | 4 | 0 | 1 | ≤1.000000e-12 |
| separated_pair | 4 | 0 | (0.5,0) | layer_drift_control | 2 | 4 | 4 | 0 | 1 | ≤1.000000e-12 |
| separated_pair | 4 | 8 | (0,0) | constant_local | 2 | 6 | 5 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 4 | 8 | (0,0) | layer_drift_control | 2 | 5 | 4 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 4 | 8 | (0.5,0) | constant_local | 2 | 4 | 4 | 0 | 1 | ≤1.000000e-12 |
| separated_pair | 4 | 8 | (0.5,0) | layer_drift_control | 2 | 5 | 4 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 8 | 0 | (0,0) | constant_local | 2 | 2 | 1 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 8 | 0 | (0,0) | layer_drift_control | 2 | 2 | 1 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 8 | 0 | (0.5,0) | constant_local | 2 | 2 | 2 | 0 | 1 | ≤1.000000e-12 |
| separated_pair | 8 | 0 | (0.5,0) | layer_drift_control | 2 | 3 | 2 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 8 | 8 | (0,0) | constant_local | 2 | 2 | 1 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 8 | 8 | (0,0) | layer_drift_control | 2 | 4 | 3 | 1 | 2 | ≤1.000000e-12 |
| separated_pair | 8 | 8 | (0.5,0) | constant_local | 2 | 2 | 2 | 0 | 1 | ≤1.000000e-12 |
| separated_pair | 8 | 8 | (0.5,0) | layer_drift_control | 2 | 4 | 3 | 1 | 2 | ≤1.000000e-12 |
| singleton | 1 | 0 | (0,0) | constant_local | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 1 | 0 | (0,0) | layer_drift_control | 1 | 4 | 4 | 0 | 1 | ≤1.000000e-12 |
| singleton | 1 | 0 | (0.5,0) | constant_local | 1 | 4 | 4 | 0 | 1 | ≤1.000000e-12 |
| singleton | 1 | 0 | (0.5,0) | layer_drift_control | 1 | 4 | 4 | 0 | 1 | ≤1.000000e-12 |
| singleton | 1 | 8 | (0,0) | constant_local | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 1 | 8 | (0,0) | layer_drift_control | 1 | 3 | 3 | 0 | 1 | ≤1.000000e-12 |
| singleton | 1 | 8 | (0.5,0) | constant_local | 1 | 4 | 4 | 0 | 1 | ≤1.000000e-12 |
| singleton | 1 | 8 | (0.5,0) | layer_drift_control | 1 | 4 | 4 | 0 | 1 | ≤1.000000e-12 |
| singleton | 4 | 0 | (0,0) | constant_local | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 4 | 0 | (0,0) | layer_drift_control | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 4 | 0 | (0.5,0) | constant_local | 1 | 3 | 3 | 0 | 1 | ≤1.000000e-12 |
| singleton | 4 | 0 | (0.5,0) | layer_drift_control | 1 | 3 | 3 | 0 | 1 | ≤1.000000e-12 |
| singleton | 4 | 8 | (0,0) | constant_local | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 4 | 8 | (0,0) | layer_drift_control | 1 | 2 | 2 | 0 | 1 | ≤1.000000e-12 |
| singleton | 4 | 8 | (0.5,0) | constant_local | 1 | 3 | 3 | 0 | 1 | ≤1.000000e-12 |
| singleton | 4 | 8 | (0.5,0) | layer_drift_control | 1 | 2 | 2 | 0 | 1 | ≤1.000000e-12 |
| singleton | 8 | 0 | (0,0) | constant_local | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 8 | 0 | (0,0) | layer_drift_control | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 8 | 0 | (0.5,0) | constant_local | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 8 | 0 | (0.5,0) | layer_drift_control | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 8 | 8 | (0,0) | constant_local | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 8 | 8 | (0,0) | layer_drift_control | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 8 | 8 | (0.5,0) | constant_local | 1 | 1 | 1 | 0 | 1 | ≤1.000000e-12 |
| singleton | 8 | 8 | (0.5,0) | layer_drift_control | 1 | 2 | 2 | 0 | 1 | ≤1.000000e-12 |

## Aggregate Bounds

- observations checked: `144`
- summaries checked: `72`
- max residual mass: `≤1.000000e-12`
- max marker support per target: `3`
- total diagnostic collision targets: `65`

## Verified Facts

- Parameter B is the only sampled parameter.
- The fixed window is limited to layer gaps `(1, 4, 8)`, base layers `(0, 8)`, phases `(0.0, 0.0)` and `(0.5, 0.0)`, and sealed DG1 layer phase policies.
- All 144 source distributions are computed through sealed DG1 `compute_distribution(...)` over finite target disks.
- Source geometry is independent from occupancy grouping: identical source axial labels produce identical per-source kernels across singleton and local-fork patterns.
- Support collision summaries preserve marker identity as diagnostic incidence sets and do not collapse sources.
- Reordered host-supplied marker input produces the same canonical observations and summaries.
- Report metric rendering uses a fixed presentation noise floor only for Markdown text; it is not an acceptance threshold.

## Reasonable Interpretation

- Finite sparse occupancy can be replayed through DG1 scale coverage without creating a global field or runtime state.
- Diagnostic collision targets identify shared finite target support, not shard equivalence.
- The result is useful as a precursor validation for future sparse scale-coverage analysis.

## Unverified Items

- No real DreamShard is created, stored, reopened, or admitted.
- No GrowthProposal, PlacementPlan, Geometry profile selection, FieldSnapshot, RecallUniverse, Query, or recall execution is created.
- No parent, child, ownership, primary-source, semantic, or identity relationship is inferred from shared target support.
- No exact algebraic proof is established; results use DG1 float64 tolerance.

## Conclusion Limits

- GSC1 is a pure validation asset and changes no production implementation.
- Target windows are finite disks with radius `4`; no global admission discovery or global scale field is scanned.
- Synthetic source markers are finite occupancy labels only, not persisted shards or memory records.
- GSC1 does not authorize runtime, OpenClaw, CLI, network, database, cache, Field, Recall, or adapter behavior.
