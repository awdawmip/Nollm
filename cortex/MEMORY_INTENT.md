# Memory Intent

Memory intent is a Cortex-side planning shape. It tells an LLM how much Nollm memory to read before acting.

It is not Core truth and must not mutate Core.

## Shape

```json
{
  "memory_intent": "read_none | orient_only | recall_surface | recall_focus | write_candidate | ask_user_confirmation",
  "candidate_anchors": [],
  "read_depth": "none | orient | surface | focus | full_card",
  "write_intent": "none | candidate | needs_confirmation",
  "reason": "short explanation"
}
```

## Values

- `read_none`: Do not consult memory.
- `orient_only`: Identify likely anchors without reading cards.
- `recall_surface`: Read sparse anchor surfaces.
- `recall_focus`: Read focused card front matter and claims.
- `write_candidate`: Propose a candidate write.
- `ask_user_confirmation`: Ask before a Core mutation or confirmation.

P2 uses deterministic filesystem matching only. It does not call an LLM, create embeddings, or create anchors automatically.

## Anchor Lists

`candidate_anchors` is a compact list of anchor IDs for downstream commands.

`matched_anchors` is the audit-rich list of match objects with `anchor`, `confidence`, `match_type`, and `reason`.
