# DG1 Geometry Conventions

Status: DG1 pure geometry convention. This file defines the coordinate and numeric rules for the V2 geometry kernel only. It does not authorize Field, Cortex, Recall, Adapter, CLI, OpenClaw, or runtime integration.

## Axial, Cube, And World Coordinates

DG1 uses axial coordinates `(q, r)` and cube coordinates `(x, y, z) = (q, -q-r, r)`.

DG1 fixes the cube-compatible pointy axial basis for `(q, r)`, equivalent to `q - r omega^2` for `omega = -1/2 + sqrt(3)i/2`. In this reference lattice adjacent centers are one unit apart. A regular hexagon with side length `s` has adjacent center spacing `sqrt(3) * s`, so world coordinates use:

```text
Phi_chart(q, r) = translation + sqrt(3) * side_length * R_theta(q + r(1/2 + sqrt(3)i/2))
```

DG1 must not treat the Eisenstein unit as the hex side length.

## Hex Orientation

DG1 fixes one polygon convention:

```text
axial coordinate: (q, r)
cube coordinate: (x, y, z) = (q, -q-r, r)
world center lattice: Phi_chart(q, r)
polygon vertex orientation: theta + pi/6 + k*pi/3, k = 0..5
vertices are emitted counter-clockwise
adjacent center directions are theta + n*pi/3
```

The area of one regular hex cell is:

```text
3 * sqrt(3) * side_length^2 / 2
```

Same-layer neighboring hexes share only a boundary edge and have zero positive intersection area under DG1 tolerance.

## Local Charts

`LocalChart` has an explicit `chart_id`, `layer_index`, `side_length`, `rotation_radians`, `translation`, and immutable phase metadata. Translation is a first-class chart parameter. No global origin is required by the kernel.

Layer index is an experiment/report coordinate only. It is not a parent-child relation and does not authorize recall or placement.

## Phase

`normalized_phase(chart)` maps translation back through inverse rotation and inverse `sqrt(3) * side_length` scaling into fractional axial coordinates, then returns `(q mod 1, r mod 1)`. It is a single-chart local diagnostic.

`relative_phase(source_chart, target_chart)` reports `phase(source <- target)` by mapping the target chart origin, or an explicit world reference point, into the source chart fractional axial basis and reducing it mod 1. DG1 baseline recurrence scans compute `phase(layer0 <- layer)` over target layers derived from `base_layer + gap`; they do not compare repeated copies of one local phase input.

`phase_distance` is a torus distance over `[0, 1)^2`.

Phase is a numeric anti-resonance diagnostic. It is not a query entry, anchor, or semantic coordinate. Rotation recurrence, relative phase recurrence, and coverage recurrence are separate finite-window diagnostics.

## Numeric Mode

DG1 uses standard Python `float` arithmetic and reports it as:

```text
numeric_mode: float64_tolerance
coordinate abs_tol: 1e-12
coordinate rel_tol: 1e-10
area abs_tol: 1e-12
area rel_tol: 1e-10
```

Floating-point results are approximate. DG1 does not claim exact algebraic-number computation for `2^(1/4)`, `phi`, `sqrt(3)`, or `22.5 degrees`.

## Coverage Discipline

`K_up` and `K_down` are directed kernels. Candidate filtering may use circumcircle checks, but confirmed coverage must use convex polygon intersection area.

A distribution may claim mass conservation only against one finite, non-overlapping target partition. Incomplete partitions and threshold truncation must produce residual mass. Overlapping target cells must be rejected before aggregation.

Target cells in one partition must share the same immutable chart geometry fingerprint: chart id, layer index, side length, normalized rotation, translation, and phase metadata items. Matching `chart_id` alone is not sufficient.

DG1 does not implement cross-chart multi-hypothesis aggregation.

## Transform Witness Discipline

Verified transforms must be finite, non-zero-scale, orientation-preserving similarities. A verified recommendation requires residuals within tolerance and at least three distinct source and target witnesses containing a non-collinear triple. Degenerate, duplicate, or collinear witness sets remain `requires_review` or `rejected`.

Cycle residual verification checks both witness residuals and the composed transform itself: `|a - 1|` and `|b| / reference_scale` must be within tolerance, and the witness set must be nondegenerate. A single fixed point of a non-identity transform cannot verify a cycle.
