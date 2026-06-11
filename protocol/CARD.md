# Card

A card is the smallest durable memory unit in Nollm Core.

## Format

Cards are Markdown files with YAML front matter.

Required fields:

- `id`: Stable card identifier.
- `title`: Short human-readable title.
- `type`: Card type from `protocol/TYPES.md`.
- `anchors`: List of anchor IDs.
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

## Body

The body should state the memory plainly. A card should be small enough to audit and large enough to preserve context.

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
