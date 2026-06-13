# Cortex Prompt

Use this prompt pattern when an LLM works with Nollm.

```text
You are using Nollm, an external notebook protocol for LLMs.

Treat Nollm Core as the source of truth. Treat your own reasoning as Cortex.

For this task:
1. Choose a memory intent.
2. Identify active anchor fields.
3. Surface current-scale cards influenced by those fields.
4. Focus on sufficient-scale cards.
5. Produce a recall digest.
6. Cite memory addresses when relying on stored memory.
7. Separate recalled facts from new inference.
8. Propose new cards only when the memory should persist.
9. Never assume embeddings, vector search, graph inference, or autonomous memory mutation.
```

This prompt guides orientation only. It does not define Core behavior.

## Memory Intent Values

- `read_none`: Do not read memory.
- `orient_only`: Identify likely anchors without reading cards.
- `recall_surface`: Surface candidate anchors or cards.
- `recall_focus`: Narrow to the most relevant memory objects.
- `write_candidate`: Propose a candidate card or status change.
- `ask_user_confirmation`: Ask before confirming or mutating Core.

## Recall Flow

Use the default read flow:

`orient -> surface -> focus -> recall_digest`

Conceptually, this is scale scan, not tree descent. Re-evaluate active anchor fields at each layer. Shift laterally if another anchor field becomes stronger. Stop when sufficient scale is reached.

Skip later steps only when the chosen memory intent does not require them.

When Core cards expose `layer`, `hex`, `anchor_fields`, or `scale_links`, treat those fields as orientation metadata. Do not assume Core has computed geometry, overlap, or automatic scale traversal.

When reading a recall digest, treat it as a reading packet, not canonical memory. Treat `active_anchor_fields` as semantic fields, not folders. Treat `scale_path` as metadata-only scale trace, not a tree path or geometry result. Do not infer semantic completeness from `sufficient_scale_reached`. Check `warnings` and `do_not_assume` before relying on recalled points.

## Anti-Pollution Rules

- Do not write inference as fact.
- Do not treat `candidate` as `confirmed`.
- Do not create new anchors for one-off topics.
- Do not create anchors automatically during `orient`.
- Do not use anchors as folders.
- Do not search a tree.
- Do not look for a leaf node.
- Do not import long raw transcripts into cards.
- Do not silently mutate Core.

## Stable Output Shapes

Memory intent:

```json
{
  "memory_intent": "recall_surface",
  "candidate_anchors": [],
  "read_depth": "surface",
  "write_intent": "none",
  "reason": "",
  "requires_core_write": false
}
```

Candidate anchors:

```json
{
  "candidate_anchors": [
    {
      "anchor": "project:nollm",
      "reason": "",
      "confidence": "low | medium | high"
    }
  ]
}
```

Read depth:

```json
{
  "read_depth": "none | orient | surface | focus | full_card",
  "max_cards": 5,
  "reason": ""
}
```

Write proposal:

```json
{
  "write_proposal": {
    "type": "decision",
    "status": "draft",
    "claim": "",
    "anchors": [],
    "source": "llm_inference",
    "trust": "llm-proposed",
    "requires_human_confirmation": true
  }
}
```

Anti-pollution warnings:

```json
{
  "anti_pollution_warnings": [
    "Do not write inference as fact."
  ]
}
```

These shapes are Cortex outputs. They are not Core truth until accepted into Core files and ledgered.
