# Card

A card is a durable memory expression at a given scale.

Every layer is made of cards. A card is never only content and never only index.

## Format

Cards are Markdown files with YAML front matter.

Required fields:

- `id`: Stable card identifier.
- `title`: Short human-readable title.
- `type`: Card type from `protocol/TYPES.md`.
- `anchors`: v0.1 shorthand list for anchor field presence.
- `created`: ISO 8601 date or timestamp.
- `status`: Current lifecycle state from `protocol/STATUS.md`.
- `claim`: The main durable statement.
- `reason`: Why the card exists.
- `source`: Source kind from `protocol/SOURCE.md`.
- `trust`: Trust value from `protocol/TRUST.md`.

Recommended fields:

- `evidence_refs`: Addresses or citations supporting the claim.
- `implications`: Consequences for future recall or work.
- `do_not_infer`: Statements Cortex must not infer from this card.
- `supersedes`: Card IDs replaced by this card.
- `related`: Nearby card IDs.
- `ledger_event`: Event ID that created or last changed the card.
- `layer`: Integer scale layer.
- `hex`: Honeycomb placement metadata.
- `anchor_fields`: Weighted anchor field influence.
- `scale_links`: Links to coarser, finer, overlapping, or recovery cards.

P5.4 optional metadata shape:

```yaml
layer: 0
hex:
  q: 0
  r: 0
  rotation: 0
  scale: 1
anchor_fields:
  architecture_is_index:
    weight: 0.9
    role: primary
scale_links:
  coarser: []
  finer: []
  overlaps: []
  recovery: []
```

These fields are optional for compatibility with older cards. When present, the P5.4 reference runtime stores, reads, and validates them as memory metadata.

P5.4 validates honeycomb metadata but does not perform automatic geometric placement. It validates anchor field weights but does not treat anchors as folders. It validates scale links but does not introduce parent, children, or leaf semantics.

Core does not compute hex placement, polygon overlap, or scale traversal. Cortex may interpret this metadata during orientation.

## Body

The body should state the memory plainly at its scale. A card should be small enough to audit and large enough to preserve context.

Markdown body remains human-readable, but front matter and structured sections should be LLM-friendly. A reader should be able to extract the claim, evidence, limits, and status without guessing.

## Structured Sections

Cards may mirror front matter in short sections:

- `Claim`
- `Reason`
- `Evidence`
- `Implications`
- `Do Not Infer`

These sections do not replace front matter. They make the card easier for humans and Cortex to audit together.

## Core Boundary

Core stores the card. Cortex may decide when a card is useful, whether it should be recalled, or whether a new card should be proposed.
