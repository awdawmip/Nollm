# GRC1 Resonance-Conditioned Coverage Validation Protocol

GRC1 compares finite center-alignment diagnostics with production DG1 coverage distributions without merging the two concepts.

## Inputs

The protocol uses production ParameterSet B, production chart schedules, production hex-grid helpers, production `make_hex_cell(...)`, production `compute_distribution(...)`, and production `distribution_metrics(...)`.

## Operation

For each fixed gap, legal base layer, phase policy, and source axial:

1. Build coarse and fine charts from production `ScaleRotationSchedule`.
2. Compute the GRA1-equivalent coarse-center to fine-coordinate residual for the source axial.
3. Classify the alignment using fixed tolerances.
4. Build the fine source `HexCell`.
5. Locate the coarse target disk with production `nearest_axial(...)` from the true source cell center.
6. Compute the fine-to-coarse distribution over the finite target disk.
7. Record support count, effective support count, maximum mass, residual mass, target refs, and weights.

## Boundary

Scale/rotation recurrence, exact center alignment, singleton coverage, and multi-support coverage remain separate diagnostics. None implies parent/child hierarchy, cover eligibility, compression permission, admission permission, recall authority, or memory identity.
