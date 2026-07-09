# GRF2 Field Engine

GRF2 separates relation cost from object-object edges.

The field engine stores:

- cell identity
- profile binding
- layer coordinates
- placement occupancy
- density state

It does not store shard content, semantic edges, parent/topic relations, or
copied coverage relations inside cells. Reusable kernels are stored in
`KernelRegistry` by `(profile, direction, layer_phase, kernel_type)`.

Incremental updates operate on placement and bridge changes, invalidate bounded
regions, and rebuild relation fields from the same kernel registry.
