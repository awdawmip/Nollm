# GRC1 Resonance-Conditioned Coverage Scope

GRC1 is a pure geometry validation asset that measures DG1 fine-to-coarse coverage under finite resonance-conditioned chart observations.

## Authorized Window

- Parameter id: `B`
- Phase: `(0.0, 0.0)`
- Layer gaps: `(4, 8, 16)`
- Base layers: generated per gap as `0..16-gap`
- Phase policies: production `constant_local` and `layer_drift_control`
- Source axial stencil: `(0,0)`, `(1,0)`, `(0,1)`, `(1,-1)`, `(2,-1)`
- Target disk radius: `4`
- Direction: `fine_to_coarse`
- Threshold: `1e-9`
- Observation count: `230`

## Claims

- Alignment class and coverage metrics are computed independently with production DG1 APIs.
- Exact-center rows are singleton coverage rows in this finite window.
- Phase-separated rows include both singleton and multi-support outcomes in this finite window.
- Center-map non-exactness is not equivalent to multi-support coverage.

## Non-Claims

GRC1 does not choose or recommend replacing ParameterSet B. It does not create hierarchy, covers, traces, compactions, admissions, FieldSnapshots, RecallUniverse, DreamShards, runtime state, compression permission, admission permission, or recall authority.
