# Nollm Cortex

Nollm Cortex is the model-side orientation layer for Nollm. It is not the source of truth.

## Responsibilities

- Interpret the current task.
- Identify active anchor fields.
- Request cards and ledger context from Core.
- Compose recall digests.
- Propose writes when durable memory is warranted.
- Perform scale scan: re-evaluate at each layer, shift laterally if another anchor field becomes stronger, and stop when sufficient scale is reached.

## Limits

Cortex must not silently mutate Core. It must preserve source addresses and distinguish recalled memory from inference. It must not use anchors as folders, search a tree, or look for a leaf node.

## Core Relationship

Core is deterministic storage and audit. Cortex is adaptive orientation. The boundary is the main safety feature of Nollm.
