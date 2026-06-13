# Anchor

Anchor is Field, not Folder.

An anchor is a cross-layer semantic field, not a folder, category, parent node, tree node, ontology node, index entry, infinite directory, or semantic embedding.

Cards do not belong to anchors. Cards are influenced by anchor fields.

## Purpose

Anchors help Cortex and humans orient memory by stable column fields / semantic fields.

Examples:

- `project:nollm`
- `decision:identity`
- `protocol:core`

## Anchor Rules

- Anchor fields should be stable.
- Anchor fields should be specific enough to orient memory.
- Anchors should not become unbounded taxonomies.
- Anchors may have aliases, but the canonical anchor remains the field identity.
- Anchors do not list children.
- Anchors do not define a path.

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

## Card Influence

Current v0.1 cards may use:

```yaml
anchors:
  - project:nollm
```

This is a shorthand for anchor field presence, not ownership.

Future cards may use:

```yaml
anchor_fields:
  project:nollm:
    weight: 0.9
    role: primary
  protocol:core:
    weight: 0.4
    role: supporting
```

Allowed roles:

- `primary`
- `supporting`
- `adjacent`
- `boundary`
- `recovery`

## Core Boundary

Core records anchor field definitions. Cortex identifies active anchor fields during recall.
