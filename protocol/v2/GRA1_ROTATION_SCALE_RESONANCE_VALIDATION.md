# GRA1 Rotation-Scale Resonance Validation Protocol

GRA1 measures finite rotation-scale recurrence and phase-drift separation with production DG1 chart schedules.

## Inputs

The protocol uses only production `ScaleRotationSchedule`, `LayerPhasePolicy`, `chart_for_layer(...)`, `axial_to_world(...)`, `world_to_fractional_axial(...)`, `normalized_phase(...)`, and `relative_phase(...)`.

It does not handwrite `LocalChart` values, similarity transforms, coverage kernels, atlas state, field state, memory state, runtime state, or profile replacement logic.

## Operation

For every fixed gap, legal base layer, default phase sample, and layer phase policy:

1. Build the coarse and fine charts from production ParameterSet B.
2. Measure side-length ratio and rotation delta modulo hex orientation symmetry.
3. Map five coarse chart centers through production world coordinates into fine fractional axial coordinates.
4. Record nearest integer fine axial coordinates and maximum center-map residual.
5. Classify the row as `exact_center_sublattice`, `commensurate_phase_separated`, or `noncommensurate` using the fixed tolerances.

## Boundary

Scale/rotation commensurability is not exact center-sublattice alignment. Exact center-sublattice alignment is not parent/child structure, cover eligibility, memory hierarchy, compression permission, admission permission, or recall permission.
