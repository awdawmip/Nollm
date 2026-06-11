# Anchor Composer

The Anchor Composer is a Cortex convention for choosing candidate anchors.

## Inputs

- Current task.
- User-stated project or domain.
- Known canonical anchors.
- Recent recall digest, if any.

## Output

A short list of candidate anchors, ordered from broad to specific.

Example:

```json
{
  "candidate_anchors": [
    {
      "anchor": "project:nollm",
      "reason": "The task concerns the Nollm project.",
      "read_depth": "shallow"
    },
    {
      "anchor": "decision:identity",
      "reason": "The task may touch project identity boundaries.",
      "read_depth": "focused"
    },
    {
      "anchor": "protocol:core",
      "reason": "The task may affect Core protocol objects.",
      "read_depth": "focused"
    }
  ],
  "new_anchor_proposals": [],
  "anti_pollution_warnings": []
}
```

## Rule

Compose anchors as coordinates, not as an infinite directory tree. If a needed anchor does not exist, Cortex may propose it for human or Core validation.
