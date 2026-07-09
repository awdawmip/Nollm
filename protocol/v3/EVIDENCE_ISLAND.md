# GRF Evidence Island

GRF1-B introduces dispersed evidence grouping without fact merge.

```text
EvidenceShardRef(shard_id, source_window_refs, trust_state, usage_state)
EvidenceIsland(island_id, shard_refs, source_window_refs, island_reason, state)
```

Island states:

```text
floating
patch_candidate
placed
stitch_candidate
stitched
archived
```

Island reasons:

```text
same_session_window
same_source_document
same_task_residue
manual_group
validation_fixture
```

An EvidenceIsland is not a topic folder, does not own truth, does not merge
shards, and does not create object-level semantic edges. It preserves stable
references back to original shard identifiers and source windows.

LocalPatch places an island into a GRF chart without changing its source facts:

```text
LocalPatch(
  patch_id,
  island_id,
  chart_id,
  profile_id,
  center_cell,
  occupied_cells,
  boundary_cells,
  state,
  density_pressure_q16,
  ambiguity_q16
)
```

Patch cells must share profile and chart. Q16 fields are integers in
`0..Q16_ONE`.
