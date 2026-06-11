# Nollm Cortex

Nollm Cortex is the model-side orientation layer for Nollm. It is not the source of truth.

## Responsibilities

- Interpret the current task.
- Select likely anchors.
- Request cards and ledger context from Core.
- Compose recall digests.
- Propose writes when durable memory is warranted.

## Limits

Cortex must not silently mutate Core. It must preserve source addresses and distinguish recalled memory from inference.

## Core Relationship

Core is deterministic storage and audit. Cortex is adaptive orientation. The boundary is the main safety feature of Nollm.

