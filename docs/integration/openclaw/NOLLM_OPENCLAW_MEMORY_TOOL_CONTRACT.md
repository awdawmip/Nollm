# Nollm OpenClaw Tool Contract

Status: OCP6S.

Nollm is a geometry-executed dream-field companion. It does not own OpenClaw's memory slot and does not write `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.

## Primary Geometry Tools

### `nollm_field_overview`

Input: optional `field_id`, optional `limit`.

Output: bounded coarse field map, chart id, geometry profile, scale availability, and cell descriptors. It has no query score and does not choose a semantic entry.

### `nollm_open_well`

Input:

```json
{
  "entry_shard_id": "surface_openclaw_nollm",
  "entry_task": "current user task",
  "anchor_vector": {"openclaw": 1.0, "nollm": 1.0}
}
```

Output: an ephemeral Gravity Well derived from the Cortex-selected entry shard and Cortex-proposed non-negative anchor vector. Core does not extract anchors from query text.

### `nollm_surface`

Input: `well_id`, `center_shard_id`, `radius`, optional `target_scale`.

Output: true same-layer honeycomb neighbors and cross-scale coverage candidates. Relationship methods include `same_layer_neighbor` and `coverage_template`.

### `nollm_focus`

Input: `well_id`, explicit `target_shard_id`, optional `target_scale`.

Output: exact target shard, coverage facts when crossing scale, and a Gravity Report. Core does not choose the target.

### `nollm_drift`

Input: `well_id`, explicit `current_shard_id`, optional explicit `chosen_shard_id`, optional `radius`.

Output: actual neighboring cells and/or selected drift target with `R_column_ring`, `S_scale_delta`, `A_anchor_similarity`, `drift_class`, `projection_method`, and return vector. Drift is orientation only.

### `nollm_read`

Input: explicit `shard_id`.

Output: exact dream shard, source trace, and Gravity Mark. It is not raw Markdown chunk retrieval.

### `nollm_recall_trace`

Input: `well_id` and a Cortex-selected shard path.

Output: deterministic trace and drift facts for logging. It returns no prose digest; the Cortex writes the Recall Digest or `NONE`.

## Legacy Inspection Tools

`nollm_memory_recall`, `nollm_memory_search`, `nollm_memory_get`, and `nollm_memory_status` are retained as legacy experimental inspection surfaces. They are not the OCP6S internal model.

Source-memory write tools are not exposed by the OpenClaw plugin. Compatibility Python functions fail closed with `source_memory_write_disabled`.
