# GKC1 Directional Kernel Composition Validation Protocol

GKC1 compares finite two-step compositions of existing DG1 coverage kernels without adding production composition, inverse, transport, or atlas APIs.

## Inputs

The protocol uses production ParameterSet B, production chart schedules, production hex-grid helpers, production `make_hex_cell(...)`, production `compute_distribution(...)`, and the existing DG1 coverage directions.

## Operation

For each fixed gap, phase policy, and source axial at base layer `0`:

1. Build coarse and fine charts from production `ScaleRotationSchedule`.
2. For `fine_coarse_fine`, compute a fine-to-coarse first leg from the fine source cell, then compute a coarse-to-fine second leg for each retained coarse target cell.
3. For `coarse_fine_coarse`, compute a coarse-to-fine first leg from the coarse source cell, then compute a fine-to-coarse second leg for each retained fine target cell.
4. Sum composed target weights as `first_weight * second_weight`.
5. Propagate residual as first-leg residual plus first-leg-weighted second-leg residual.
6. Record source, intermediate, and return chart ids, support counts, mass ledger fields, return target refs, return weights, self-return mass, nonself-return mass, and identity-distance diagnostic.

## Boundary

Returning to the source chart remains separate from returning all mass to the source cell. The finite non-identity result does not imply structural containment, write permission, read authority, ranking, memory identity, profile selection, or all-plane behavior.
