# Nollm

Not an LLM. A notebook for LLMs.

Nollm is a structured external notebook protocol for LLMs. It gives a model a stable way to write, read, locate, and recall memory without turning the notebook into an agent, a model, a vector database, or an automatic knowledge system.

## What Nollm Is

- A card-based memory structure.
- An anchor-oriented recall system.
- A ledgered and auditable external memory.
- A protocol for memory addresses, statuses, actions, recall digests, and write discipline.

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

Core confirmations require explicit human approval in v0.1. Cortex may propose drafts, candidates, and recall digests, but it must not silently mutate Core.

## Source Of Truth

Markdown, YAML, and JSONL are the project identity. SQLite may exist later as a derived local index, but it must never become the source of truth.

Nollm v0.1 does not include embeddings, vector databases, graph providers, external LLM extraction, automatic ontology generation, or autonomous memory mutation.

## Protocol Freeze

P0.2 freezes protocol vocabulary before P1 CLI implementation: statuses, types, trust, sources, actions, addresses, and validation invariants must stay explicit and auditable.

## Reference CLI

P1 includes a minimal filesystem-first Python CLI in `reference/python`.

Run without installing:

```powershell
cd C:\Users\chaos\nollm\reference\python
python -m nollm.cli init .\demo-notebook --notebook demo
python -m nollm.cli write .\demo-notebook --type fact --title "Filesystem memory" --claim "Nollm stores memory in local files." --reason "Demo card." --anchor project:demo --source user_statement --trust unverified
python -m nollm.cli validate .\demo-notebook
python -m nollm.cli recall .\demo-notebook "filesystem memory"
```

Run tests:

```powershell
cd C:\Users\chaos\nollm\reference\python
python -m unittest discover -s tests
```

The reference CLI uses only the Python standard library and keeps Markdown, YAML, JSONL, and JSON as source-of-truth files.
