# NOLLM GRF2 Field Engine Architecture

GRF2 moves relation maintenance from object-object edges to cell-field,
kernel, and template assets.

Core assets:

- `CellRegistry`: cell identity, profile binding, layer, occupancy, density.
- `PlacementIndex`: placement identity to cell lookup, neighbor lookup, move/remove.
- `KernelRegistry`: reusable kernels keyed by profile, direction, phase, type.
- `IncrementalFieldBuilder`: local invalidation and deterministic rebuild.

Cells never own evidence content or semantic edges. Evidence fallback remains
through placement source refs.
