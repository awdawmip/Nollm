# Nollm OpenClaw LLM Usage Guide

Status: OCP10.

Nollm is not an embedding-free `MEMORY.md` search adapter. Treat OpenClaw `MEMORY.md`, `DREAMS.md`, and `memory/*.md` as read-only source snapshots.

Primary Cortex path:

```text
nollm_field_overview
-> field_stale check; return NONE/refresh-required when stale
-> Cortex chooses entry shard
-> nollm_open_well, yielding a well_id bound to one field revision
-> nollm_surface
-> Cortex chooses focus
-> nollm_focus
-> optional nollm_drift
-> nollm_read with well_id
-> nollm_recall_trace
-> Cortex writes NOLLM_RECALL_DIGEST or NONE
```

Core only executes geometry and returns deterministic facts: true honeycomb neighborhoods, cross-scale coverage, Gravity Well/Mark/Report data, drift class, and return vectors. Core does not rank by query text and does not compose prose recall digests.

## Windows Runtime Note

On Windows, `nollm_memory_status` and all companion tools require an absolute, probed `pythonExecutable` in `plugins.entries.nollm-memory-companion.config`. Bare `python3`/`python`/`py` launchers are rejected with a structured configuration error. The companion remains a tool-only companion; `memory-core` stays the active memory owner.

## Cortex Rules

- Inspect `nollm_field_overview` first.
- Use `nollm_memory_status` only for field availability/stale status; it is not recall.
- If `field_stale` is true, return `NONE` or a compact refresh-required digest instead of presenting stale facts as current.
- Choose the entry shard yourself.
- Call `nollm_open_well` with an explicit non-negative `anchor_vector`.
- Use `nollm_surface` before focusing.
- Choose focus and drift targets yourself.
- Use `nollm_read` with the current `well_id` for exact dream-shard reads.
- Use `nollm_recall_trace` only as structural logging.
- Write the compact `NOLLM_RECALL_DIGEST` envelope yourself, or return `NONE`.
- Put read facts under `facts` and requested-but-unread categories under `explicit_absences`.
- Treat `explicit_absences` as response boundaries for the primary.

No tool output alone is source truth. Drift labels are orientation only; never map them to trust, status, permission, or rejection.

## OCP10 Grounding Status

The structured digest contract is implemented. Live OpenClaw primary grounding remains not reliable because Active Memory inherits the target agent tool policy: hiding Nollm tools from the primary also prevents the Active Memory sub-agent from using them.

## Legacy Tools

`nollm_memory_recall`, `nollm_memory_search`, and `nollm_memory_get` are not part of the OCP10 Active Memory surface. They are not the Nollm internal model.

`nollm_memory_write_candidate` and `nollm_memory_commit_candidate` are not exposed by the plugin. Python compatibility functions fail closed with `source_memory_write_disabled`.
