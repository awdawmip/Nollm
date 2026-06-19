# Nollm OpenClaw Memory Tool Contract

Date: 2026-06-19

These contracts describe OC0 design targets only. No OpenClaw runtime plugin is
implemented here.

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
        "projection_method": "coverage_template"
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

`nollm_memory_get` reads exact OpenClaw source text and any available Nollm
sidecar metadata.

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
