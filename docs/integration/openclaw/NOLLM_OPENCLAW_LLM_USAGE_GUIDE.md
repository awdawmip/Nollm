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

## Native Companion Memory (W1-01)

In addition to the geometry Cortex path, the companion plugin now exposes
three explicit native-memory tools:

- `nollm_memory_remember`: use when the user explicitly says "记住",
  "请记住", "remember this", or states a stable identity/preference
  (e.g., "我叫…", "我偏好…"). The tool returns `ok=true` and a Nollm-issued
  `memory_id`. Confirm only after the tool succeeds; do not claim the write
  went to `MEMORY.md`.
- `nollm_memory_recall`: use when the user asks "我叫什么", "我偏好什么",
  or asks for a previously requested remembered fact. Answer only from the
  returned native memory; when none is found, say no Nollm native memory was
  found. Do not silently read legacy files as fallback.
- `nollm_memory_get`: use only when the user supplies a Nollm-issued
  `memory_id` from a previous `nollm_memory_remember` result. Reject file
  paths, line locators, and legacy source locators.

These tools write only to `.nollm-memory/native-companion-v1/`. They do not
replace `memory-core`, do not modify legacy source memory files, and do not
call a real LLM.

## Legacy Tools


`nollm_memory_recall`, `nollm_memory_search`, and `nollm_memory_get` are not part of the OCP10 Active Memory surface. They are not the Nollm internal model.

`nollm_memory_write_candidate` and `nollm_memory_commit_candidate` are not exposed by the plugin. Python compatibility functions fail closed with `source_memory_write_disabled`.

## W2-01 Direct Active Memory Usage

Status: owner-authorized empirical active-memory trial.

The `nollm` provider owns `plugins.slots.memory`. There are no Primary-visible
Nollm memory tools in active mode. Recall and capture run automatically through
OpenClaw hooks:

- `agent_turn_prepare` injects a bounded `NOLLM_MEMORY_CONTEXT_V1` envelope.
- `agent_end` auto-captures only explicit stable user sentences.

Capture is deterministic and narrow: explicit remember directives, identity
statements, preference statements, and project/release decisions. It does not
capture assistant messages, tool outputs, questions, or secrets.

Legacy `MEMORY.md`, `DREAMS.md`, and `memory/*.md` are preserved and may still
be bootstrap-injected by the host; W2 measures this as a confound and does not
claim exclusive prompt memory ownership.

Trial metrics are local-only and redacted; no raw transcripts or secrets are
stored in Git. Rollback to `memory-core` was tested and succeeded.
