# Nollm OpenClaw Memory Adapter Design

Date: 2026-06-19

OC0 is a design-only integration step. It does not implement an OpenClaw
runtime plugin, call an LLM, replace OpenClaw memory, or write durable memory.
OC1 begins the offline path by parsing the fixture into auditable candidates;
it still does not search, enrich with gravity reports, or write durable memory.
The target sidecar prototype extends that path with deterministic sidecar
JSONL/JSON files, lexical search, gravity reports, and pending writes while
remaining offline and experimental.

## Position

OpenClaw remains the memory file and candidate retrieval source. Its user-facing
memory model is file-first:

- `MEMORY.md`: compact durable memory.
- `memory/YYYY-MM-DD.md`: daily working notes and observations.
- `DREAMS.md`: optional review surface for dreaming summaries.
- `memory_search`: retrieves candidate chunks.
- `memory_get`: reads exact source text.

Nollm is the topology and gravity instrumentation layer. It receives candidate
memory chunks, attaches geometry marks and gravity reports, and returns
auditable context for the model to interpret.

In short: OpenClaw remains the memory file / candidate retrieval source. Nollm
is the topology + gravity instrumentation layer. The first target is companion
tool mode, not immediate memory-slot replacement. Replacement mode is later and
must not be implemented in OC0.

## Mapping

The planned adapter maps OpenClaw material as follows:

```text
OpenClaw memory chunk
  -> DreamShard candidate
  -> GeometryMark
  -> GravityReport
  -> LLM use / caution / return decision
```

`drift_class` is an annotation in the gravity report. It is not permission,
trust, status, or an automatic reject gate.

## Modes

Mode A is companion tool mode. Nollm-specific tools sit beside OpenClaw memory
and do not claim the memory slot. This is the first target.

Mode B is later memory-slot replacement mode. It may expose compatibility
aliases after Mode A is proven, but it is not implemented in OC0.

## Sidecar Layout

Nollm metadata stays beside OpenClaw memory files:

```text
.nollm-memory/
  shards.jsonl
  geometry_marks.jsonl
  gravity_reports/
    <query_run_id>.json
  ledger.jsonl
```

OpenClaw files stay intact. Nollm sidecar records are candidate metadata,
geometry, reports, and audit entries.

## Non-Goals

OC0 does not:

- implement a real OpenClaw runtime plugin;
- call a real LLM;
- replace the OpenClaw memory slot;
- write to `MEMORY.md` automatically;
- map `drift_class` to trust or status;
- introduce vector DB, graph DB, embedding, or OpenClaw core changes;
- claim that Nollm proves long-term memory.
