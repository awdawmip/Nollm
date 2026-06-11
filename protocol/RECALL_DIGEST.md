# Recall Digest

A recall digest is a temporary reading packet assembled from Nollm Core records.

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
  "open_questions": []
}
```

`memory_intent` should use the values defined in `cortex/CORTEX_PROMPT.md`.

## Status

A recall digest is not canonical memory by itself. If it contains new durable knowledge, Cortex should propose a card and Core should ledger it.
