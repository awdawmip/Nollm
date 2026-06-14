# Nollm V1 Release Notes Draft

Nollm V1 is a structured external notebook protocol for LLMs.

Slogan: Not an LLM. A notebook for LLMs.

## What V1 Is

- A file-first notebook protocol using Markdown, YAML, JSON, and JSONL.
- A card-based memory structure with explicit anchors and addresses.
- A deterministic Core for validation, explicit reads, audit projections, recall digests, ledger/history inspection, and JSON tool envelopes.
- A Cortex-facing protocol that lets an LLM decide what to read, how to compose context, and what writes to propose outside Core.

## What V1 Is Not

- Not an LLM.
- Not a RAG framework.
- Not a vector database.
- Not a knowledge graph engine.
- Not an agent runtime.
- Not an automatic memory system.
- Not an MCP server.

## Core / Cortex Boundary

Core stores and exposes explicit filesystem-backed objects. It does not infer truth, rank semantics, compose context, approve memory automatically, or manage memory autonomously.

Cortex / the LLM orients, chooses what to read next, composes context outside Core, interprets recall, proposes writes, and resolves ambiguity.

## Stable CLI Surface

Stable V1 CLI commands:

```text
validate
orient
recall
read
inspect
review
annotate
annotations
ledger
history
audit
audit-check
tool
```

Internal or experimental helpers such as `init`, `tools`, `surface`, `focus`, `write`, and `status` remain outside the stable external V1 surface.

## Stable Tool Surface

Stable V1 tool actions:

```text
nollm.validate
nollm.orient
nollm.recall
nollm.read_card
nollm.inspect
nollm.review
nollm.annotate
nollm.annotations
nollm.ledger
nollm.history
nollm.audit
```

Existing internal or experimental actions such as `nollm.surface`, `nollm.focus`, `nollm.write_card`, and `nollm.update_status` are not part of the stable external V1 surface.

## Example Notebook

The OpenClaw notebook under `examples/openclaw/` is the V1 fixture notebook. It validates, has a stable audit snapshot, and includes committed sample recall digest fixtures.

Safe top-level tool requests under `examples/tool_requests/*.json` can run against committed OpenClaw. Generated-output recall examples are isolated under `examples/tool_requests/generated_output_examples/` and should run against temporary notebook copies.

## Audit And Audit-Check

`audit` produces deterministic derived inspection reports. Audit output is not memory, not recall, not source of truth, and not a hidden index.

`audit-check` compares audit output against a saved snapshot for structural drift. Drift is not semantic correctness or factual truth.

## Known Limitations

See `docs/V1_KNOWN_LIMITATIONS.md`.
