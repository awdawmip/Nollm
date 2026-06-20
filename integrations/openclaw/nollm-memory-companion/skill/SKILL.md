# Nollm OpenClaw Geometry Cortex Skill

Use this skill only when the workspace has enabled the Nollm companion tools.
Nollm is a geometry-executed dream field; it is not a `MEMORY.md` search adapter and not a source-memory writer.

Primary Cortex workflow:

1. Use `nollm_field_overview` to inspect the bounded field map and stale state. Use `nollm_memory_status` only for field availability/stale status. Core does not choose the semantic entry.
2. Use `nollm_open_well` after choosing an entry shard yourself, with an explicit non-negative `anchor_vector`.
3. Use `nollm_surface` around the selected center to inspect true honeycomb neighbors and cross-scale coverage.
4. Use `nollm_focus` after choosing a target yourself, for gravity and coverage facts.
5. Use `nollm_drift` only for useful lateral movement. Label lateral findings as lateral.
6. Use `nollm_read` with the current `well_id` for exact dream-shard reads.
7. Use `nollm_recall_trace` to log the explicit selected path. You, the Cortex, write the compact Recall Digest or `NONE`.

If `field_stale` is true, return `NONE` or a compact refresh-required digest. Do not present stale field contents as current knowledge.

Do not use `memory_search` / `memory_get` as the Nollm internal model.
Do not call raw file tools in the isolated Nollm Cortex path.
No tool output alone is source truth.

Gravity report = instrumentation, not permission.
Drift class = orientation, not trust.

Do not treat `drift_class` as trust, status, a ranking permission, or a hard rejection rule. Nollm must not write `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.
