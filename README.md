# Nollm

Not an LLM. A notebook for LLMs.

Nollm is a structured external notebook protocol for LLMs. It gives a model a stable way to write, read, locate, and recall memory without turning the notebook into an agent, a model, a vector database, or an automatic knowledge system.

## Architecture Principles

- Not an LLM.
- Architecture is the Index.
- Anchor is Field, not Folder.
- Recall is Scale Scan, not Tree Descent.
- SQLite is Audit Projection, not Memory.

Nollm is aligned around a layered rotating honeycomb memory field. Anchors are column fields / semantic fields that cross layers. Cards are durable memory expressions at every scale. Recall scans across scale, re-evaluating active anchor fields, rather than descending a tree.

There is no absolute leaf layer. The current reference runtime remains filesystem-first and deterministic; it does not implement geometric placement yet.

P5.1 preserves and validates optional card metadata for layer, hex coordinates, anchor fields, and scale links. Core stores these fields as auditable memory metadata; Cortex may interpret them during orientation.

## What Nollm Is

- A card-based memory structure.
- An anchor-field-oriented recall system.
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

Core confirmations require explicit operator approval in v0.1. Cortex may propose drafts, candidates, and recall digests, but it must not silently mutate Core.

Nollm is LLM-first. Human inspection is optional, active, and ledgered. Human input is an operator action, not an oracle.

## Source Of Truth

Markdown, YAML, and JSONL are the project identity. SQLite, if used, is only an optional audit projection.

Nollm v0.1 does not include embeddings, vector databases, graph providers, external LLM extraction, automatic ontology generation, or autonomous memory mutation.

For canonical English/Chinese terminology and project namespace rules, see `protocol/TERMINOLOGY.md`.

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

POSIX shell:

```bash
cd reference/python
python -m nollm.cli init ./demo-notebook --notebook demo
python -m nollm.cli write ./demo-notebook \
  --type fact \
  --title "Filesystem memory" \
  --claim "Nollm stores memory in local files." \
  --reason "Demo card." \
  --anchor project:demo \
  --source user_statement \
  --trust unverified
python -m nollm.cli validate ./demo-notebook
python -m nollm.cli recall ./demo-notebook "filesystem memory"
python -m nollm.cli audit ./demo-notebook
python -m nollm.cli review ./demo-notebook
```

Cortex read flow:

```bash
python -m nollm.cli orient ./demo-notebook "why not turn Nollm into Cognee"
python -m nollm.cli surface ./demo-notebook --anchor project:demo
python -m nollm.cli focus ./demo-notebook --anchor project:demo --status candidate
python -m nollm.cli recall ./demo-notebook "why not turn Nollm into Cognee"
```

Run tests:

```powershell
cd C:\Users\chaos\nollm\reference\python
python -m pytest -q
```

The reference CLI uses only the Python standard library and keeps Markdown, YAML, JSONL, and JSON as source-of-truth files.

Audit reports are deterministic derived projections over notebook files. They are not memory, not a recall index, and not source of truth. The stable JSON contract is documented in `protocol/AUDIT_SCHEMA.md`; the OpenClaw golden snapshot lives at `examples/audit_reports/openclaw_audit.json`. Audit schema stability is for inspection and governance, not memory or recall.

Compare current audit output with a snapshot:

```bash
python -m nollm.cli audit-check ./demo-notebook --against ../../examples/audit_reports/openclaw_audit.json
```

`audit-check` is read-only and CI-friendly: exit code `0` means no drift, `1` means drift detected, and `2` means invalid input or schema error. Audit drift is structural inspection drift only; it is not semantic correctness, memory, recall, or a hidden index.

## JSON Tool Bridge

P3 adds a dependency-free JSON bridge for external LLM tool callers. It is not an MCP server and does not start a network service.

```bash
python -m nollm.cli tools
python -m nollm.cli tool ../../../examples/tool_requests/orient.json
python -m nollm.cli tool ../../../examples/tool_requests/review_openclaw.json
```

Tool requests use the `nollm.tool.v0.1` envelope and return structured `ok: true` or `ok: false` JSON responses.
Optional `request_id`, `actor`, and `actor_type` fields are echoed or ledgered where appropriate.

## Using Nollm From External LLM Tools

Recommended read flow:

```text
orient -> surface -> focus -> recall
```

For one-shot use, call `nollm.recall`. For controlled multi-step use, call `nollm.orient`, then `nollm.surface`, then `nollm.focus`.

External LLM tools should write only candidate cards unless a human explicitly approves a later status update. Nollm is not a RAG engine, autonomous memory agent, or MCP server.

## Active Inspection

Use `review` to inspect draft and candidate cards matching active metadata filters:

```bash
python -m nollm.cli review ./demo-notebook
python -m nollm.cli review ./demo-notebook --status candidate --type decision --limit 20
```

Review is a deterministic active inspection surface. It does not judge truth, approve cards, confirm memory, block reads, or replace the `status` command. `confirmed` does not mean factually true, and `human-approved` does not prove factual truth. See `protocol/REVIEW.md`.

External tools can call the same queue with `nollm.review`.
