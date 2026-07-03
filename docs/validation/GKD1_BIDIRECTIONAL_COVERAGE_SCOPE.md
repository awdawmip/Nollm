# GKD1 Bidirectional Coverage Scope

GKD1 is a pure geometry validation asset that measures existing DG1 directed coverage kernels in both directions over one finite production-B window.

## Authorized Window

- Parameter id: `B`
- Phase: `(0.0, 0.0)`
- Layer gaps: `(4, 8, 16)`
- Base layers: generated per gap as `0..16-gap`
- Phase policies: production `constant_local` and `layer_drift_control`
- Source axial stencil: `(0,0)`, `(1,0)`, `(0,1)`, `(1,-1)`, `(2,-1)`
- Target disk radius: `4`
- Target partition size: `61`
- Directions: `fine_to_coarse` and `coarse_to_fine`
- Threshold: `1e-9`
- Records: `230` per direction, `230` directional pairs

## Claims

- K_up and K_down use distinct source cells and distinct target partitions for the same tuple key.
- K_down is not derived from K_up by transposition, inverse normalization, or target reinterpretation.
- In this finite window, every pair has smaller K_up support count than K_down support count.
- In this finite window, every pair has different canonical kernel weight vectors.
- K_down has ten explicit positive residual rows in the gap-16 finite target partition.

## Non-Claims

GKD1 does not choose or recommend replacing ParameterSet B. It does not create structural containment, write permission, read authority, ranking, covers, traces, compactions, admissions, FieldSnapshots, RecallUniverse, DreamShards, runtime state, or memory objects.
