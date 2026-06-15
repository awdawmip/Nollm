# D1 Pure Geometry Kernel

D1 is Nollm's pure deterministic geometry layer for Dream Geometry. It computes
hex coordinates, layer transforms, cell polygons, polygon overlaps, coverage
weights, bounded local charts, and similarity transforms.

## Scope

- Axial and cube hex coordinates.
- Pointy-top axial-to-world and world-to-axial transforms.
- Runtime layer parameters: `beta`, `theta_deg`, `s0`, `origin`,
  `translation`, `finer_down`, and `rotation_mod_deg`.
- Convex polygon intersection for regular hex cells.
- Many-to-many coverage weights from polygon overlap area.
- Finite `LocalChart` projection from one layer disk to another layer.
- `SimilarityTransform` primitives for later chart gluing work.

## Non-Scope

D1 is not recall. D1 is not placement. D1 does not choose semantic placement,
update cards, run recall, expand audit or history, assign memories to geometry,
query vector stores, query graph stores, or provide MCP behavior.

## Coordinate Convention

D1 uses axial `(q, r)` coordinates with cube coordinates `(x, y, z)` where
`x + y + z == 0`. Cube directions are the standard six axial-neighbor
directions.

## Layer Transform Convention

The layout is pointy-top:

```text
x = s * sqrt(3) * (q + r/2)
y = s * 3/2 * r
world = origin + translation + R(rotation) * local
```

By default, layer increases downward toward finer scale:

```text
side_length(layer) = s0 * beta ** (-layer)
rotation(layer) = (layer * theta_deg) mod 60 degrees
```

## Coverage

Coverage is deterministic geometric overlap:

```text
I(H_a, H_b) = Area(H_a intersection H_b)
```

The kernel returns `weight_source`, `weight_target`, and `jaccard`. It does not
normalize coverage by default and it does not create parent-child ownership
relations. Nearest-center rounding is used only to generate candidate target
cells before polygon overlap is computed.

## LocalChart

`LocalChart` is a bounded local geometry helper. It projects a finite disk of
seed-layer cells into another layer. It is not a global atlas and it does not
decide chart acceptance or conflict resolution.

## SimilarityTransform

`SimilarityTransform` represents `z -> a z + b`, where
`a = scale * exp(i * rotation)`. D1 exposes apply, inverse, compose, and
two-point construction as primitive support for later D2 gluing work, not as a
gluing policy.

## Tests

Run the Python test suite from `reference/python`:

```bash
python3 run_tests.py
```
