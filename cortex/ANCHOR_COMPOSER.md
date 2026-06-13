# Anchor Composer

The Anchor Composer is a Cortex convention for identifying active anchor fields.

## Inputs

- Current task.
- User-stated project or domain.
- Known canonical anchor fields.
- Recent recall digest, if any.

## Output

A deterministic object containing matched anchors, read depth, and warnings.

`candidate_anchors` is a compact list of anchor field IDs for downstream commands.

`matched_anchors` is the audit-rich list of match objects with `anchor`, `confidence`, `match_type`, and `reason`.

Example:

```json
{
  "input": "why not turn Nollm into Cognee",
  "candidate_anchors": [
    "anti_agentic_memory"
  ],
  "matched_anchors": [
    {
      "anchor": "anti_agentic_memory",
      "confidence": 0.9,
      "match_type": "alias",
      "reason": "Query contains an alias for the anchor."
    }
  ],
  "new_anchor_needed": false,
  "new_anchor_candidate": null,
  "read_depth": "surface",
  "write_candidate": false,
  "warnings": []
}
```

## Rule

Do not use anchors as folders. Do not search a tree. Do not look for a leaf node.

Identify active anchor fields, then perform scale scan. Re-evaluate at each layer. Shift laterally if another anchor field becomes stronger. Stop when sufficient scale is reached.

P2/P5 must not automatically create new anchors. It may only report `new_anchor_needed: true` as a suggestion.

Allowed match types:

- `id`
- `alias`
- `title`
- `neighbor`
- `keyword`
