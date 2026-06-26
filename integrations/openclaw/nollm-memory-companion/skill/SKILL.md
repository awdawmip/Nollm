# Nollm OpenClaw Geometry Cortex Skill

Use this skill only when the workspace has enabled the Nollm companion tools.
Nollm is a geometry-executed dream field; it is not a `MEMORY.md` search adapter and not a source-memory writer.

## Explicit native companion memory

When the user explicitly says "记住", "请记住", "remember this", or clearly
states a stable identity/preference such as "我叫…", "我偏好…":
1. Use `nollm_memory_remember`.
2. Confirm only after the tool returns `ok=true`.
3. Do not claim it was written to `MEMORY.md`.

When the user asks "我叫什么", "我偏好什么", or asks for a saved fact:
1. Use `nollm_memory_recall`.
2. Answer only from returned native memory.
3. Specific queries (for example "喜欢什么标签颜色？" or "项目何时发版？") return only the
   matching facet; broad queries (for example "我有哪些项目决定？") may return a facet
   collection. Generic tokens like `W1`, `W1-02`, pure numbers, or "代号/项目/偏好" alone
   are not relevance evidence.
4. When none is found, or when a generic test-code query has multiple candidates, say no
   uniquely relevant Nollm native memory was found.
5. Do not silently read legacy files as fallback.

The `nollm_memory_recall` tool returns an empty `results` array when no relevant native memory is found. Do not choose an unrelated returned memory and do not silently use legacy file memory as Nollm evidence. If `nollm_memory_remember` returns `memory_content_rejected` or `nollm_memory_get` returns `native_memory_not_found`, report the structured error code to the user and do not guess.

Use `nollm_memory_get` only when the user supplies a Nollm-issued `memory_id`
from a previous `nollm_memory_remember` result. Reject file paths, line locators,
and legacy source locators.

These explicit native-memory tools write only to `.nollm-memory/native-companion-v1`.
They do not replace `memory-core`, do not modify `MEMORY.md` / `DREAMS.md` /
`memory/*.md`, and do not call a real LLM.

Primary Cortex workflow:

1. Use `nollm_field_overview` to inspect the bounded field map and stale state. Use `nollm_memory_status` only for field availability/stale status. Core does not choose the semantic entry.
2. Use `nollm_open_well` after choosing an entry shard yourself, with an explicit non-negative `anchor_vector`.
3. Use `nollm_surface` around the selected center to inspect true honeycomb neighbors and cross-scale coverage.
4. Use `nollm_focus` after choosing a target yourself, for gravity and coverage facts.
5. Use `nollm_drift` only for useful lateral movement. Label lateral findings as lateral.
6. Use `nollm_read` with the current `well_id` for exact dream-shard reads.
7. Use `nollm_recall_trace` to log the explicit selected path. You, the Cortex, write the compact `NOLLM_RECALL_DIGEST` envelope or `NONE`.

In `NOLLM_RECALL_DIGEST`, put only exact shard reads under `facts`, put requested-but-unread categories under `explicit_absences`, and keep stale fields as refresh-required boundaries with no facts.

If `field_stale` is true, return `NONE` or a compact refresh-required digest. Do not present stale field contents as current knowledge.

Do not use `memory_search` / `memory_get` as the Nollm internal model.
Do not call raw file tools in the isolated Nollm Cortex path.
No tool output alone is source truth.

Gravity report = instrumentation, not permission.
Drift class = orientation, not trust.

Do not treat `drift_class` as trust, status, a ranking permission, or a hard rejection rule. Nollm must not write `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.
