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

## Protocol Index

- `ACTIONS`: Allowed protocol actions and their Core/Cortex boundaries.
- `ANCHOR`: Anchor fields used for orientation; not folders, trees, or embeddings.
- `ANCHOR_FIELD`: Weighted anchor-field metadata stored on cards.
- `AUDIT`: Deterministic derived inspection reports.
- `AUDIT_SCHEMA`: Stable JSON contract for audit projections.
- `CARD`: Markdown memory card structure and front matter.
- `HONEYCOMB_FIELD`: Optional layered honeycomb metadata; not runtime geometry.
- `JSON_ENVELOPE`: Dependency-free JSON request/response envelope.
- `LEDGER`: Append-only JSONL audit trail.
- `MEMORY_ADDRESS`: Deterministic references for locating memory objects.
- `RECALL_DIGEST`: Reading packet produced from Core records.
- `REVIEW`: Active inspection semantics; review is compatibility naming.
- `ANNOTATION`: Ledgered operator notes that do not mutate card content.
- `HISTORY`: Object-level ledger inspection.
- `READ`: Explicit single-card read boundary.
- `SCALE_SCAN`: Scale-scan recall vocabulary; not tree descent.
- `SOURCE`: Source labels for card provenance.
- `STATUS`: Card lifecycle states.
- `TERMINOLOGY`: Canonical naming and bilingual terminology guard.
- `TOOL_SURFACE`: Stable V1 and internal/experimental tool actions.
- `TRUST`: Trust/provenance labels; not factual truth scoring.
- `TYPES`: Card type vocabulary.
- `VALIDATION`: Deterministic structural validation rules.

## V1 Route Lock

Nollm V1 Core exposes explicit filesystem-backed objects, deterministic validation, audit projections, and tool surfaces. Core does not compose context, rank semantics, infer truth, perform automatic approval, or run autonomous memory management.

Cortex / the LLM composes context, decides what to read next, interprets recall, proposes writes, and resolves ambiguity outside Core.
