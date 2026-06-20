# Nollm OpenClaw LLM Usage Guide

Status: OCP6S.

Nollm is not an embedding-free `MEMORY.md` search adapter. Treat OpenClaw `MEMORY.md`, `DREAMS.md`, and `memory/*.md` as read-only source snapshots.

Primary Cortex path:

```text
nollm_field_overview
-> Cortex chooses entry shard
-> nollm_open_well
-> nollm_surface
-> Cortex chooses focus
-> nollm_focus
-> optional nollm_drift
-> nollm_read
-> nollm_recall_trace
-> Cortex writes Recall Digest or NONE
```

Core only executes geometry and returns deterministic facts: true honeycomb neighborhoods, cross-scale coverage, Gravity Well/Mark/Report data, drift class, and return vectors. Core does not rank by query text and does not compose prose recall digests.

## Cortex Rules

- Inspect `nollm_field_overview` first.
- Choose the entry shard yourself.
- Call `nollm_open_well` with an explicit non-negative `anchor_vector`.
- Use `nollm_surface` before focusing.
- Choose focus and drift targets yourself.
- Use `nollm_read` for exact dream-shard reads.
- Use `nollm_recall_trace` only as structural logging.
- Write the compact Recall Digest yourself, or return `NONE`.

No tool output alone is source truth. Drift labels are orientation only; never map them to trust, status, permission, or rejection.

## Legacy Tools

`nollm_memory_recall`, `nollm_memory_search`, `nollm_memory_get`, and `nollm_memory_status` remain legacy experimental inspection tools. They are not the Nollm internal model for OCP6S.

`nollm_memory_write_candidate` and `nollm_memory_commit_candidate` are not exposed by the plugin. Python compatibility functions fail closed with `source_memory_write_disabled`.
