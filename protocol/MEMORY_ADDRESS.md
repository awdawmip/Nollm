# Memory Address

A memory address is a deterministic reference for locating a Nollm object.

## Address Pattern

The initial pattern is:

`nollm://<notebook>/<object_type>/<id>`

## Canonical Forms

Cards:

- `nollm://<notebook>/card/<card_id>`

Anchors:

- `nollm://<notebook>/anchor/<anchor_id>`

Ledger events:

- `nollm://<notebook>/ledger/event/<event_id>`

Recall digests:

- `nollm://<notebook>/recall/<digest_id>`

Non-binding future forms:

- `nollm://layer/{layer}/hex/{q}/{r}`
- `nollm://anchor-field/{anchor_id}`

## Valid Examples

- `nollm://openclaw/card/card_0001_nollm_project_start`
- `nollm://openclaw/anchor/project:nollm`
- `nollm://openclaw/ledger/event/evt_0001`
- `nollm://openclaw/recall/sample_recall_digest`

## Invalid Examples

- `nollm://openclaw/search/nollm`: Search is not a canonical memory object.
- `nollm://openclaw/card/decisions/card_0001_nollm_project_start`: Card addresses use card IDs, not file paths.
- `nollm://openclaw/card/card_0001.md`: Card addresses omit file extensions.
- `nollm://openclaw/vector/project:nollm`: Vector addresses are outside v0.1.
- `nollm://openclaw/anchor/project/nollm`: Anchor IDs remain canonical strings, not folder paths.

## Requirements

- Addresses must be stable.
- Addresses must resolve to source-of-truth files or records.
- Addresses must not depend on generated indexes.
- Card addresses must remain stable if files are reorganized.
- Card addresses remain stable and primary in v0.1.

## Core Boundary

Core defines address syntax and resolution. Cortex uses addresses when requesting or citing memory.
