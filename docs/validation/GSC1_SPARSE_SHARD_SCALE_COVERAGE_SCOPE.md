# GSC1 Sparse-Shard Scale-Coverage Scope

GSC1 is a pure synthetic validation asset for finite sparse occupancy markers over sealed DG1 coverage kernels.

## Authorized Window

- Parameter id: `B`
- Layer gaps: `(1, 4, 8)`
- Base layers: `(0, 8)`
- Phase samples: `((0.0, 0.0), (0.5, 0.0))`
- Layer phase policies: sealed DG1 defaults
- Target radius: `4`
- Threshold: `1e-9`
- Source distribution call count: `144`

## Synthetic Inputs

- `singleton`: `s0` at `AxialCoord(0, 0)`
- `local_fork`: `f0` at `AxialCoord(0, 0)`, `f1` at `AxialCoord(1, 0)`, `f2` at `AxialCoord(0, 1)`
- `separated_pair`: `p0` at `AxialCoord(-1, 0)`, `p1` at `AxialCoord(1, 0)`

These inputs are finite occupancy labels only. They are not persisted DreamShards, admissions, placements, memory records, identities, semantic objects, or recall entries.

## Validation Claims

- Every source marker is replayed through sealed DG1 `compute_distribution(...)`.
- Source geometry remains independent from occupancy grouping.
- Diagnostic support collisions preserve source marker identity.
- Canonical observations and summaries are stable under host input permutation.
- The runner writes only the requested Markdown report.

## Explicit Non-Claims

GSC1 does not create or modify production implementation, Geometry profiles, FieldSnapshots, RecallUniverse, Query, recall execution, GrowthProposal, PlacementPlan, admission state, runtime state, OpenClaw integration, CLI surface, network, database, cache, or real memory.
