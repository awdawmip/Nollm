# Nollm Protocol

The Nollm Protocol defines a notebook format for LLM memory. It is external to the model, auditable by humans, and stable enough for deterministic tooling.

Principles:

- Not an LLM.
- Architecture is the Index.
- Anchor is Field, not Folder.
- Recall is Scale Scan, not Tree Descent.
- SQLite is Audit Projection, not Memory.

For canonical English/Chinese terminology and project namespace rules, see `protocol/TERMINOLOGY.md`.

## Core Objects

- Card: A durable memory expression at a given scale.
- Anchor: A named column field / semantic field used to orient recall.
- Alias: A human or model-friendly alternate name for an anchor.
- Ledger event: An append-only JSONL record of memory changes.
- Recall digest: A temporary reading packet assembled from Core records.
- Memory address: A deterministic reference for locating a memory.

## Core Guarantees

Core stores records and validates structure. It does not infer truth, generate ontology, retrieve by embedding, or decide what matters.

## Cortex Responsibilities

Cortex decides how an LLM should orient itself against Core. It may identify active anchor fields, scan scale, read cards, produce digests, and recommend writes, but its conclusions are not Core truth until recorded as auditable Core objects.
