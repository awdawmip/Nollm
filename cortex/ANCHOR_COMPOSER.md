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

```yaml
candidate_anchors:
  - project:nollm
  - decision:identity
  - protocol:core
```

## Rule

Compose anchors as coordinates, not as an infinite directory tree. If a needed anchor does not exist, Cortex may propose it for human or Core validation.

