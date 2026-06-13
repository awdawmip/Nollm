# Recall Digest

A recall digest is a temporary reading packet assembled from Nollm Core records after a scale scan.

## Purpose

Recall digests help an LLM enter a task with relevant memory while keeping source records traceable.

## Markdown Form

A Markdown digest must include:

- `query_or_task`
- `memory_intent`
- `anchors_used`
- `cards_read`
- `recalled_points`
- `warnings`
- `do_not_assume`
- `source_addresses`
- `open_questions`
- `active_anchor_fields`
- `scale_path`
- `lateral_recovery`
- `sufficient_scale_reached`

## JSON Form

A JSON digest uses the same required keys:

```json
{
  "query_or_task": "",
  "memory_intent": "orient_only",
  "anchors_used": [],
  "cards_read": [],
  "recalled_points": [],
  "warnings": [],
  "do_not_assume": [],
  "source_addresses": [],
  "open_questions": [],
  "active_anchor_fields": [],
  "scale_path": [],
  "lateral_recovery": [],
  "sufficient_scale_reached": false
}
```

`memory_intent` should use the values defined in `cortex/CORTEX_PROMPT.md`.

## Scale-Scan Metadata

Current generated JSON digests include:

```json
{
  "active_anchor_fields": [],
  "scale_path": [],
  "lateral_recovery": [],
  "sufficient_scale_reached": true
}
```

`active_anchor_fields` is the sorted set of anchor field keys found on selected cards.

`scale_path` is a deterministic metadata list built from selected cards that already contain `layer`. It is not a tree path. It is metadata-only in the reference runtime.

`lateral_recovery` is emitted as a list. The reference runtime does not simulate recovery.

`sufficient_scale_reached` is `true` when the deterministic recall selected at least one card. It does not claim completeness.

Core does not perform geometry-based recall.

Markdown digests render the standard key set plus scale-scan metadata.

External LLMs must treat recall digests as reading packets, not canonical memory. `active_anchor_fields` are active semantic fields, not ownership folders. `scale_path` is not a tree path and must not be used to infer geometric overlap. `sufficient_scale_reached` means only that the deterministic policy selected at least one usable card set; it does not prove semantic completeness. Always inspect `warnings` and `do_not_assume` before relying on recalled points.

## Status

A recall digest is not canonical memory by itself. If it contains new durable knowledge, Cortex should propose a card and Core should ledger it.
