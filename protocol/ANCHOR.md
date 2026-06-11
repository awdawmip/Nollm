# Anchor

An anchor is a coordinate for recall. It is not a category, folder, taxonomy, ontology node, infinite directory, or semantic embedding.

## Purpose

Anchors help Cortex and humans locate memory by stable orientation points.

Examples:

- `project:nollm`
- `decision:identity`
- `protocol:core`

## Anchor Rules

- Anchors should be stable.
- Anchors should be specific enough to locate memory.
- Anchors should not become unbounded taxonomies.
- Anchors may have aliases, but the canonical anchor remains the coordinate.

## Creation Criteria

Create an anchor only when it is likely to orient repeated recall. Do not create anchors for one-off topics, transient phrasing, or every noun in a conversation.

An anchor should have:

- A clear canonical ID.
- A concise definition.
- A known scope.
- At least one expected card or recall use.
- No better existing anchor.

## Limits

Recommended v0.1 limits:

- `max_aliases`: 8
- `max_neighbors`: 12
- `max_definition_chars`: 280
- `max_active_cards`: 50

If an anchor exceeds these limits, Cortex should propose splitting, narrowing, or archiving nearby material. Core should not auto-generate a new hierarchy.

## Temporary Anchors

Temporary anchors must include an expiration date or event. After expiration, they should be removed, archived, or promoted through explicit review.

## Core Boundary

Core records anchor definitions. Cortex composes and selects anchors during recall.
