# Nollm

Not an LLM. A notebook for LLMs.

Nollm is a structured external notebook protocol for LLMs. It gives a model a stable way to write, read, locate, and recall memory without turning the notebook into an agent, a model, a vector database, or an automatic knowledge system.

## What Nollm Is

- A card-based memory structure.
- An anchor-oriented recall system.
- A ledgered and auditable external memory.
- A protocol for memory addresses, recall digests, and write discipline.

## What Nollm Is Not

- An LLM.
- A RAG framework.
- A vector database.
- A knowledge graph engine.
- An agent runtime.
- A self-improving memory agent.
- An automatic memory system.

## Core And Cortex

Nollm Core is dumb, stable, deterministic, and auditable. It defines files, schemas, addresses, anchors, cards, ledgers, and recall digests.

Nollm Cortex is model-side and prompt-side. It helps an LLM orient itself, compose anchors, decide what to read or write, and produce recall digests from Core material.

Core stores. Cortex orients.

## Source Of Truth

Markdown, YAML, and JSONL are the project identity. SQLite may exist later as a derived local index, but it must never become the source of truth.

Nollm v0.1 does not include embeddings, vector databases, graph providers, external LLM extraction, or automatic ontology generation.

