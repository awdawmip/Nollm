# Card

A card is the smallest durable memory unit in Nollm Core.

## Format

Cards are Markdown files with YAML front matter.

Required fields:

- `id`: Stable card identifier.
- `type`: Card type, such as `decision`, `fact`, `note`, or `question`.
- `anchors`: List of anchor IDs.
- `created`: ISO 8601 date or timestamp.
- `status`: Current lifecycle state.

Recommended fields:

- `supersedes`: Card IDs replaced by this card.
- `related`: Nearby card IDs.
- `ledger_event`: Event ID that created or last changed the card.

## Body

The body should state the memory plainly. A card should be small enough to audit and large enough to preserve context.

## Core Boundary

Core stores the card. Cortex may decide when a card is useful, whether it should be recalled, or whether a new card should be proposed.

