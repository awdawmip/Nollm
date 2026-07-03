# GKC1 Directional Kernel Composition Scope

GKC1 is a pure geometry validation asset that measures finite two-step compositions of existing DG1 directed coverage kernels.

## Authorized Window

- Parameter id: `B`
- Base layer: `0`
- Phase: `(0.0, 0.0)`
- Layer gaps: `(4, 8, 16)`
- Phase policies: production `constant_local` and `layer_drift_control`
- Source axial stencil: `(0,0)`, `(1,0)`, `(0,1)`, `(1,-1)`, `(2,-1)`
- Target disk radius: `4`
- Directions: `fine_coarse_fine` and `coarse_fine_coarse`
- Threshold: `1e-9`
- Settings: `30`
- Composition observations: `60`

## Claims

- Both two-step directions are built from real production single-leg DG1 coverage distributions.
- Composed weights are first-leg weight multiplied by second-leg weight and summed by return target ref.
- Composition residual is first-leg residual plus first-leg-weighted second-leg residual.
- Every observation returns to the source chart but not to an identity distribution on the source cell.
- Gap-16 residual remains visible in both two-step directions.

## Non-Claims

GKC1 does not choose or recommend replacing ParameterSet B. It does not create production composition APIs, structural containment, write permission, read authority, ranking, covers, traces, compactions, admissions, FieldSnapshots, RecallUniverse, DreamShards, runtime state, or memory objects.
