# AGENTS.md

## Project identity

This repository is Nollm.

Nollm means:

> Not an LLM. A notebook for LLMs.

Nollm is a structured external notebook protocol for language models.

## Non-goals

Do not turn Nollm into:

- an LLM
- a RAG framework
- a vector database
- a knowledge graph engine
- an agent runtime
- a self-improving memory agent
- a Cognee-like automatic memory system

## Architecture principles

- Nollm Core must be dumb, stable, deterministic, and auditable.
- Nollm Cortex may be model-side, prompt-based, and adaptive.
- Architecture is the index.
- Anchors are coordinates, not infinite directories.
- Cards are the primary memory unit.
- Ledger events are append-only.
- Recall output must be small, structured, and suitable for LLM context.
- Markdown/YAML/JSONL are the source of truth.
- SQLite, if used, is only a derived index.

## v0.1 restrictions

Do not introduce:

- embeddings
- vector databases
- graph databases
- external LLM extraction
- automatic ontology generation
- autonomous memory rewriting
- production dependencies without explicit approval

## Development style

Prefer small, reviewable changes.

Every change should preserve:

- human auditability
- LLM readability
- stable status semantics
- clear Core/Cortex boundary