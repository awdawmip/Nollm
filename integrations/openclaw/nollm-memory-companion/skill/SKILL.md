# Nollm OpenClaw Dream Cortex Skill

Use this skill only when the workspace has enabled the Nollm companion tools.
Nollm is a dream-field recall mode; it is not a replacement memory slot and not an embedding-free `MEMORY.md` search adapter.

Primary Cortex workflow:

1. Use `nollm_orient` first for memory-relevant work. Begin from a bounded coarse surface, not aliases or raw source chunk search.
2. Use `nollm_surface` to inspect the content-bearing coarse surface before focusing.
3. Use `nollm_focus` to move to sufficient scale. Stop when the scale is enough for the task.
4. Use `nollm_drift` only when lateral context may help. Label lateral findings as lateral.
5. Use `nollm_read` to inspect a dream shard by id when a focused shard needs expansion.
6. Use `nollm_compose_digest` to return a compact Nollm Recall Digest.
7. Return to the original user task after drift. Return `NONE` when the dream field lacks useful material.

Do not use `memory_search` / `memory_get` as the Nollm internal model.

Legacy explicit write workflow:

1. Use `nollm_memory_write_candidate` only when the user asks to remember/save something. This stages only a pending candidate.
2. Use `nollm_memory_commit_candidate` only after the user explicitly confirms durable or daily commit, with `explicit_confirmation=true`.
3. Never claim that a pending candidate has been written to `MEMORY.md`.

Gravity report = instrumentation, not permission.
Drift class = orientation, not trust.

Do not treat `drift_class` as trust, status, a ranking permission, or a hard rejection rule. Nollm must not silently write `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.
