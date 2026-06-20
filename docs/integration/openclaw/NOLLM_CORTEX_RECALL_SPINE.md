# Nollm Cortex Recall Spine

OCP7 primary read path:

```text
field_overview -> Cortex chooses entry -> open_well -> surface -> Cortex chooses focus -> drift/read through well_id -> recall_trace
```

OpenClaw Active Memory acts as the read-side Cortex. It should use only the Nollm geometry navigation tools for the Nollm path:

- `nollm_field_overview`
- `nollm_open_well`
- `nollm_surface`
- `nollm_focus`
- `nollm_drift`
- `nollm_read`
- `nollm_recall_trace`

Rules:

- Core does not choose a semantic path from query text.
- Core does not compose prose recall digests.
- Open wells bind `field_id` and `revision_id`; surface, focus, drift, read, and trace resolve through `well_id`.
- A field refresh must not change what an existing well can read.
- Cortex chooses entry shards, focus moves, lateral drift, and final wording.
- Surface/focus/drift return true honeycomb neighborhood, coverage, Gravity Well/Mark/Report, and return-vector facts.
- Output `NONE` when the field lacks useful material.
- Do not treat `memory_search` / `memory_get` as the Nollm internal model.
- Nollm must not write `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.
