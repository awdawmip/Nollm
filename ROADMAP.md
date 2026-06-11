# Roadmap

## v0.1: Protocol Scaffold

- Define Core documents for cards, anchors, ledgers, recall digests, and memory addresses.
- Define statuses and LLM-facing actions before runtime implementation.
- Freeze protocol vocabulary for statuses, types, trust, sources, actions, and validation before P1 CLI work.
- Define Cortex guidance for prompts, anchor composition, and read/write policy.
- Provide a small example notebook.
- Keep all source of truth in Markdown, YAML, and JSONL.

## v0.2: Validation And Tooling

- Add schema checks for anchors, aliases, cards, and ledger events.
- Add deterministic address validation.
- Add simple local inspection commands.
- Keep any SQLite index derived and rebuildable.

## v0.3: Recall Workflow

- Formalize recall digest generation.
- Define conflict and supersession conventions.
- Add review workflows for human audit.
- Preserve status transition history in the ledger.

## Non-Goals

- No model runtime.
- No agent orchestration.
- No vector database.
- No embedding dependency.
- No automatic ontology engine.
