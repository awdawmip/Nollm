# Memory Address

A memory address is a deterministic coordinate for locating a Nollm object.

## Address Pattern

The initial pattern is:

`nollm://<notebook>/<object_type>/<path_or_id>`

Examples:

- `nollm://lobster/card/decisions/card_0001_nollm_project_start`
- `nollm://lobster/anchor/project:nollm`
- `nollm://lobster/ledger/event/evt_0001`

## Requirements

- Addresses must be stable.
- Addresses must resolve to source-of-truth files or records.
- Addresses must not depend on generated indexes.

## Core Boundary

Core defines address syntax and resolution. Cortex uses addresses when requesting or citing memory.

