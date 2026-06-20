# OCP4 Functional Memory Loop V1 Demo Report

Run id: `ocp4_20260620_functional`

Branch: `feature/openclaw-nollm-memory`

## Runtime

- OpenClaw: `2026.6.8 (844f405)`
- Controlled agent: `ocp4-nollm-functional`
- Workspace: ignored runtime fixture under `out/nollm_runtime/openclaw_live_eval/ocp4_20260620_functional/workspace`
- `memory-core`: selected memory slot and owner
- Nollm: companion tool plugin only
- Active Memory: enabled only for `ocp4-nollm-functional`, direct chat only, transcripts persisted by OpenClaw

## Configuration

Active Memory read allowlist:

```text
memory_search
memory_get
nollm_memory_recall
nollm_memory_get
```

Write tools were excluded from Active Memory. The main controlled agent had
`nollm_memory_write_candidate` and `nollm_memory_commit_candidate` available for
explicit write-loop turns only. Generic `read`, `write`, `exec`, `process`,
`edit`, `apply_patch`, `web_search`, and `web_fetch` were denied.

## Results

| ID | Outcome | Main tool calls | Active Memory calls |
| --- | --- | --- | --- |
| F1 | Natural fact query answered from memory: Tessa Lin owns Atlas, credential TESSA-17. | `memory_search` | `nollm_memory_recall`, `memory_get` |
| F2 | Ambiguous Mira ownership query kept durable evidence primary and labelled Mira as speculative/non-owner. | `memory_search` x5 | `nollm_memory_recall`, `memory_get` x3 |
| F3 | No-memory query returned not recorded; no invented Zephyr Lantern date. | `memory_search` | `nollm_memory_recall`, `memory_search` |
| F4 | "Remember this" staged pending Nollm candidate only. | `nollm_memory_write_candidate` | `nollm_memory_recall`, `memory_get` |
| F5 | Explicit confirmation committed the staged candidate to `MEMORY.md` managed section. | `nollm_memory_commit_candidate` | `nollm_memory_recall`, `memory_get` |
| F5 verify | After successful memory-core reindex, committed item was retrievable by memory-core. | `memory_search`, `memory_get` | `memory_search`, `memory_get` |

Committed item:

```text
Atlas support rotation owner is Rowan Ives.
```

Commit result:

```text
file: MEMORY.md
line_range: 10-13
memory_core_reindex_required: true
```

After reindex, memory-core returned:

```text
Atlas support rotation owner is Rowan Ives.
Source: MEMORY.md#L10-L12
```

## Runtime Repair

The first post-commit `openclaw memory index --agent ocp4-nollm-functional --force --verbose` hit a Windows WAL lock:

```text
EBUSY: resource busy or locked, rename ... ocp4-nollm-functional.sqlite-wal ...
```

Repair used only public OpenClaw commands:

```text
openclaw gateway stop
openclaw memory index --agent ocp4-nollm-functional --force --verbose
openclaw gateway start
```

The retry succeeded and Gateway RPC came back healthy.

## Safety Checks

- `memory-core` remained the memory-slot owner.
- Nollm did not claim `kind: "memory"`.
- No direct `read` tool appeared in F1-F3 main or Active Memory tool traces.
- Nollm write candidate did not mutate durable source files.
- Durable commit required explicit confirmation and wrote only the Nollm-managed section.
- `drift_class` stayed orientation metadata; it was not mapped to trust/status or used as a hard filter.

## Known Limitations

- Active Memory persisted transcripts under OpenClaw's default plugin transcript directory rather than the requested custom transcript path.
- F2 final answer relied on durable evidence and labelled DREAMS as speculative, but did not quote the DREAMS source verbatim.
- The first memory-core reindex attempt can hit a Windows WAL lock while Gateway is active; stopping Gateway before forced reindex is the reliable local workaround.
- The semantic layout is deterministic lexical V1, not embeddings and not an ontology.
