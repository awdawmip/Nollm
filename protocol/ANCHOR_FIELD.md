# Anchor Field

Anchor is field, not folder.

Cards do not belong to anchors.

Cards are influenced by anchor fields.

A card may be influenced by multiple anchor fields with different weights.

Anchors do not list children.

Anchors do not define a path.

Anchors are column fields crossing layers.

## Example

```yaml
anchor_fields:
  project:nollm:
    weight: 0.9
    role: primary
  protocol:core:
    weight: 0.5
    role: supporting
  decision:identity:
    weight: 0.2
    role: boundary
```

Allowed roles are `primary`, `supporting`, `adjacent`, `boundary`, `recovery`, and `warning`.

The current v0.1 `anchors: []` field remains a shorthand for anchor field presence.

## P5.4 Runtime Status

Nollm Core preserves and validates `anchor_fields` when present.

Validation checks that each field key is a non-empty string, each influence entry is a mapping, `weight` is present, weights are numeric values from 0 to 1, and roles use the allowed vocabulary.

P5.4 does not require anchor field keys to exist in the anchor registry. Anchor fields are influence metadata, not ownership tags and not folders. Core does not infer anchor fields, create anchors, or rewrite anchors automatically.

Cortex may use anchor field metadata for orientation, but Core remains deterministic and non-reasoning.
