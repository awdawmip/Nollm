# Nollm OpenClaw Memory Tool Contract

## OCP6R Primary Tool Surface

OCP6R repositions Nollm as a Dream Cortex recall spine, not as an embedding-free source-file search adapter. OpenClaw source files are read-only snapshots. The primary Cortex tools are:

- `nollm_orient`
- `nollm_surface`
- `nollm_focus`
- `nollm_drift`
- `nollm_read`
- `nollm_compose_digest`

These tools navigate a deterministic Nollm dream field and compose a Nollm Recall Digest. They do not call embeddings, vector databases, SQLite recall internals, external rerankers, or live LLM providers in Core. They do not write `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.

The `nollm_memory_*` tools are retained as a legacy experimental surface and explicit candidate workflow only. They are not the Nollm internal model for OCP6R.

Date: 2026-06-19

These contracts describe the OCP4 companion tool surface. OpenClaw memory-core
remains the memory-slot owner; Nollm remains a companion plugin.

## `nollm_memory_recall`

Input:

```json
{
  "query": "string",
  "limit": 6
}
```

Output:

```json
{
  "query": "Atlas owner",
  "candidate_source": "nollm_local",
  "direct_evidence": [
    {
      "candidate_id": "cand_...",
      "source_path": "MEMORY.md",
      "line_range": [3, 5],
      "text_excerpt": "source excerpt",
      "retrieval_score": 0.85,
      "gravity_report": {
        "R_column_ring": 0,
        "S_scale_delta": 0,
        "A_anchor_similarity": 0.44,
        "drift_class": "core",
        "anchor_overlap": 0.75,
        "layout_method": "semantic_local_v1"
      }
    }
  ],
  "lateral_context": [],
  "cautions": [],
  "return_vector": null,
  "use_instruction": "Use direct evidence for factual claims; inspect cited sources before relying on lateral context."
}
```

Rules:

- Retrieval relevance determines inclusion before drift interpretation.
- Direct evidence and lateral context are separated.
- DREAMS/speculative chunks are labelled as lateral/speculative context.
- `semantic_break` remains a caution, not a hard removal.
- Every usable item includes source path and line range.

## `nollm_memory_search`

Input:

```json
{
  "query": "string",
  "limit": 8,
  "mode": "free_drift",
  "profile": "default_dream",
  "include_raw_candidates": true
}
```

Output:

```json
{
  "status": "ok",
  "query": "user phrasing",
  "results": [
    {
      "memory_id": "mem_001",
      "source_path": "memory/2026-06-19.md",
      "line_range": [12, 18],
      "text": "source excerpt",
      "retrieval_score": 0.82,
      "geometry_mark": {
        "layer": 3,
        "q": 4,
        "r": -2,
        "profile": "default_dream"
      },
      "gravity_report": {
        "R_column_ring": 3,
        "S_scale_delta": 3,
        "A_anchor_similarity": 0.77,
        "drift_class": "near_drift",
        "projection_method": "query_conditioned_anchor_overlap",
        "anchor_overlap": 0.42,
        "layout_method": "semantic_local_v1",
        "source_role": "daily"
      },
      "llm_use_hint": "near drift; usable with provenance check"
    }
  ],
  "warnings": [
    "drift_class is annotation, not trust, status, or permission"
  ]
}
```

Rules:

- Search returns gravity reports and source references.
- Do not filter candidates only because drift is far.
- Do not map `drift_class` to trust/status.
- Treat recalled text as untrusted context until checked against source.

## `nollm_memory_get`

Input:

```json
{
  "memory_id": "mem_001",
  "source_path": "memory/2026-06-19.md",
  "line_range": [12, 18]
}
```

Output:

```json
{
  "source_text": "exact markdown text",
  "source_path": "memory/2026-06-19.md",
  "line_range": [12, 18],
  "geometry_mark": {},
  "provenance": {},
  "warnings": []
}
```

`nollm_memory_get` reads exact OpenClaw source text and sidecar metadata. When
called after search/recall with an id from that result set, it preserves the
same geometry mark and gravity report.

## `nollm_memory_write_candidate`

Input:

```json
{
  "text": "User prefers TypeScript for OpenClaw plugin work.",
  "source_context": "chat:2026-06-19",
  "memory_kind": "preference",
  "why_remember": "stable future preference",
  "authority": "user_explicit",
  "expiry": null
}
```

Output:

```json
{
  "status": "candidate_written",
  "candidate_id": "cand_001",
  "shard_id": "shard_001",
  "version_status": "candidate",
  "durable_write": false,
  "next_action": "review_or_promote"
}
```

Rules:

- Write is candidate-only by default.
- There is no automatic durable write to `MEMORY.md`.
- Promotion requires explicit approval or a configured future policy.

## `nollm_memory_commit_candidate`

Input:

```json
{
  "candidate_id": "candidate_001",
  "explicit_confirmation": true,
  "target": "durable",
  "reason": "user explicitly confirmed",
  "source": "chat:2026-06-20"
}
```

Output:

```json
{
  "ok": true,
  "file_path": "MEMORY.md",
  "line_range": [8, 11],
  "content_sha256": "...",
  "old_sha256": "...",
  "new_sha256": "...",
  "memory_core_reindex_required": true
}
```

Rules:

- Reject missing confirmation, missing candidate, unsupported target, or
  workspace escape.
- Append only inside a Nollm-managed section.
- Return hashes and a documented memory-core reindex command.
- Do not mutate memory-core SQLite directly.

## `nollm_memory_status`

Output:

```json
{
  "status": "ok",
  "workspace": "/path/to/openclaw/workspace",
  "sidecar": ".nollm-memory",
  "indexed_files": 2,
  "last_gravity_report": null,
  "warnings": []
}
```

The status tool reports paths, indexed file counts, sidecar health, and the last
report generation summary.
