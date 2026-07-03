# GKD1 Bidirectional Coverage Validation Protocol

GKD1 compares existing DG1 `fine_to_coarse` and `coarse_to_fine` coverage distributions without turning either direction into an inverse of the other.

## Inputs

The protocol uses production ParameterSet B, production chart schedules, production hex-grid helpers, production `make_hex_cell(...)`, production `compute_distribution(...)`, and production `distribution_metrics(...)`.

## Operation

For each fixed gap, legal base layer, phase policy, and source axial:

1. Build coarse and fine charts from production `ScaleRotationSchedule`.
2. For K_up, build the fine source cell, center a coarse radius-4 target disk from the true source center, and compute `CoverageDirection.fine_to_coarse`.
3. For K_down, build the coarse source cell, center a fine radius-4 target disk from the true source center, and compute `CoverageDirection.coarse_to_fine`.
4. Record source and target chart identity, source and target side lengths, target partition size, support count, effective support count, maximum mass, kernel mass, residual mass, total mass, residual reasons, canonical target refs, and descending kernel weights.
5. Pair same tuple-key K_up and K_down records only by opaque observation keys and compare support count relation plus exact kernel weight vector equality.

## Boundary

K_up and K_down remain separate directed geometry kernels. Different support counts, different kernel vectors, and finite residual mass do not imply structural containment, write permission, read authority, ranking, memory identity, profile selection, or all-plane behavior.
