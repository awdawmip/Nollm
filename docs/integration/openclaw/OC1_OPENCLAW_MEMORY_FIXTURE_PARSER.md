# OC1 OpenClaw Memory Fixture Parser

Date: 2026-06-20

OC1 adds an offline deterministic parser for the OpenClaw memory fixture. It is
the bridge from OpenClaw file-first memory to later Nollm sidecar indexing.

## Scope

The parser reads:

- `MEMORY.md` as durable memory;
- `memory/YYYY-MM-DD.md` as daily memory;
- optional `DREAMS.md` as dreams material if present.

It emits auditable memory candidates with POSIX source paths, 1-based inclusive
line ranges, source hashes, chunk hashes, heading paths, and stable
`memory_id` values.

## Command

```bash
cd reference/python
python scripts/parse_openclaw_memory_fixture.py \
  --workspace ../../examples/openclaw_memory_fixture \
  --output ../../out/nollm_runtime/openclaw_memory_fixture_index.json
```

The output is a runtime report under `out/nollm_runtime/`.

## Non-Goals

OC1 does not search yet. It does not enrich chunks with geometry marks or
gravity reports yet. It does not create `.nollm-memory/`, write durable memory,
call an LLM, implement an OpenClaw plugin, replace the memory slot, create
anchors, or map `drift_class` to trust/status/permission.
