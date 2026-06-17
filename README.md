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

There is no absolute leaf layer. The stable reference runtime remains filesystem-first and deterministic; it does not perform geometry recall or automatic card placement. D-series reference modules contain experimental Dream Geometry records and diagnostics outside the stable V1 tool surface.

P5.1 preserves and validates optional card metadata for layer, hex coordinates, anchor fields, and scale links. Core stores these fields as auditable memory metadata; Cortex may interpret them during orientation.

## V4 Engineering Gravity Decision

The decided V4 engineering direction is documented in `NOLLM_PROJECT_SPEC_V4_ENGINEERING_GRAVITY_20260616.md`.
Supporting engineering drafts live in `docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md`,
`docs/engineering/NOLLM_MINIMUM_DATA_MODEL_20260616.md`,
`docs/experiments/NOLLM_MINIMAL_ABLATION_EXPERIMENT_PLAN_20260616.md`,
`docs/geometry/NOLLM_TRUE_TILING_ENGINEERING_REQUIREMENTS_20260616.md`, and the gravity protocol stubs under `protocol/`.

These documents are decision drafts for the next experimental engineering phase.
They do not expand the stable V1 recall/tool surface, do not enable automatic card writing,
and do not map `drift_class` to trust or status.

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

## V1 Spec Freeze

Nollm V1 is scoped and frozen around explicit filesystem-backed objects, deterministic validation, audit projections, and JSON tool envelopes. Core stores, validates, reads, appends ledgered operator actions, and produces derived audit/recall outputs. Core does not compose context, rank related cards, infer truth, or run autonomous memory workflows.

## Reference CLI

V1 includes a minimal filesystem-first Python CLI in `reference/python`.

Run without installing:

```powershell
cd path\to\nollm\reference\python
python -m nollm.cli init .\demo-notebook --notebook demo
python -m nollm.cli validate .\demo-notebook
python -m nollm.cli recall .\demo-notebook "filesystem memory"
```

POSIX shell:

```bash
cd reference/python
python -m nollm.cli init ./demo-notebook --notebook demo
python -m nollm.cli validate ./demo-notebook
python -m nollm.cli recall ./demo-notebook "filesystem memory"
python -m nollm.cli audit ./demo-notebook
python -m nollm.cli inspect ./demo-notebook
python -m nollm.cli annotate ./demo-notebook card-id --note "Needs source verification."
python -m nollm.cli annotations ./demo-notebook card-id
python -m nollm.cli ledger ./demo-notebook --object-id card-id --limit 20
python -m nollm.cli history ./demo-notebook card-id
```

Cortex-side read flow:

```bash
python -m nollm.cli orient ./demo-notebook "why not turn Nollm into Cognee"
python -m nollm.cli inspect ./demo-notebook --anchor project:demo
python -m nollm.cli recall ./demo-notebook "why not turn Nollm into Cognee"
```

Run tests:

```powershell
cd path\to\nollm\reference\python
python run_tests.py
```

Use the project test command so ambient pytest plugins do not affect Nollm tests. The runner sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, runs every test file in deterministic order, and applies a hard timeout to each group.

The reference CLI uses only the Python standard library and keeps Markdown, YAML, JSONL, and JSON as source-of-truth files.

Release packaging is source-first and simple. Before packaging, review `docs/V1_RELEASE_CHECKLIST.md` and run `python3 scripts/check_package_hygiene.py ../..` from `reference/python`.

Audit reports are deterministic derived projections over notebook files. They are not memory, not a recall index, and not source of truth. The stable JSON contract is documented in `protocol/AUDIT_SCHEMA.md`; the OpenClaw golden snapshot lives at `examples/audit_reports/openclaw_audit.json`. Audit schema stability is for inspection and governance, not memory or recall.

Compare current audit output with a snapshot:

```bash
python -m nollm.cli audit-check ./demo-notebook --against ../../examples/audit_reports/openclaw_audit.json
```

`audit-check` is read-only and CI-friendly: exit code `0` means no drift, `1` means drift detected, and `2` means invalid input or schema error. Audit drift is structural inspection drift only; it is not semantic correctness, memory, recall, or a hidden index.

## JSON Tool Bridge

V1 includes a dependency-free JSON bridge for external LLM tool callers. It is not an MCP server and does not start a network service.

```bash
python -m nollm.cli tool ../../../examples/tool_requests/orient.json
python -m nollm.cli tool ../../../examples/tool_requests/inspect_openclaw.json
```

Tool requests use the `nollm.tool.v0.1` envelope and return structured `ok: true` or `ok: false` JSON responses.
Optional `request_id`, `actor`, and `actor_type` fields are echoed or ledgered where appropriate.

Top-level examples in `examples/tool_requests/*.json` are safe against committed OpenClaw. Generated-output examples, including recall examples that may write `recall_*.json` or `recall_*.md`, live under `examples/tool_requests/generated_output_examples/` and should be run against temporary notebook copies.

## Using Nollm From External LLM Tools

Recommended stable read flow:

```text
orient -> inspect/read/ledger/history as needed -> recall when a digest is useful
```

For one-shot use, call `nollm.recall`. For controlled multi-step use, call `nollm.orient`, then explicit stable reads such as `nollm.inspect`, `nollm.read_card`, `nollm.ledger`, or `nollm.history`. Cortex / the LLM composes any resulting context outside Core.

External LLM tools should write only candidate cards unless a human explicitly approves a later status update. Nollm is not a RAG engine, autonomous memory agent, or MCP server.

## Explicit Read

`read_card` reads exactly one explicit card. `read_card` is not recall. `read_card` is not context composition. `read_card` does not return neighbors. `read_card` does not rank related cards.

Core does not assemble deterministic context. Context composition belongs to Cortex / LLM using explicit calls. If an LLM needs context, it should make explicit read/inspect/history/ledger/recall calls and compose outside Core.

Surface relation:

- `read` / `read_card` = explicit object read
- `inspect` / `review` = active metadata surface
- `history` = object-level ledger trail
- `ledger` = ledger query
- `annotations` = annotation listing
- `recall` = scale-scan digest
- context composition = Cortex-side, not Core

## Active Inspection

Use `inspect` to inspect draft and candidate cards matching active metadata filters:

```bash
python -m nollm.cli inspect ./demo-notebook
python -m nollm.cli inspect ./demo-notebook --status candidate --type decision --limit 20
```

Inspect is a deterministic active inspection surface. It does not judge truth, approve cards, confirm memory, block reads, or replace the `status` command. `confirmed` does not mean factually true, and `human-approved` does not prove factual truth. See `protocol/REVIEW.md`.

External tools should call the same surface with `nollm.inspect`.

`review` remains a compatibility command; its semantics are active inspection.

## Operator Annotations

Use `annotate` to append operator notes to the ledger for an existing card:

```bash
python -m nollm.cli annotate ./demo-notebook card-id --note "Needs source verification." --annotation-type source_request
python -m nollm.cli annotations ./demo-notebook card-id --limit 20
```

Annotations are operator notes. Annotations are ledgered. Annotations do not modify card content, change status, change trust, prove truth, approve memory, block LLM usage, or create passive human review. Annotations are active operator actions, not recall inputs.

Audit may count annotations. Inspect/review may show `annotation_count`. Annotation text is not recall content. Annotation text does not change status or trust. Annotation text does not prove truth. Annotation counts are not semantic risk scores. annotation_count means there are operator notes, not that a card is more or less reliable.

External tools can call `nollm.annotate` and `nollm.annotations`. Mutating annotation examples live under `examples/tool_requests/templates/` so committed OpenClaw examples remain stable.

## Ledger And History

Use `ledger` to query compact ledger events and `history` to inspect the ledger trail for one card:

```bash
python -m nollm.cli ledger ./demo-notebook --object-id card-id --limit 20
python -m nollm.cli history ./demo-notebook card-id
```

Ledger is an audit trail, not memory recall. History is object-level ledger inspection. Ledger/history do not prove truth, approve memory, change status, change trust, or perform semantic scoring. Ledger/history are read-only unless an explicit write action such as annotate/status is used.

Annotation text may appear in history because history is explicit audit inspection, but annotation text is still not recall content.

## Nollm V1 Route Lock

Nollm V1 Core exposes explicit filesystem-backed objects, deterministic validation, audit projections, and tool surfaces.

Nollm V1 Core does not compose context, rank semantics, infer truth, or perform autonomous memory management.

Core:

- explicit object read/write surfaces
- validation
- deterministic audit/audit-check
- scale-scan recall digest
- active inspection metadata
- annotation ledger
- ledger/history inspection
- tool bridge

Cortex / LLM:

- context composition
- deciding what to read next
- interpreting recall
- deciding how to use annotations/history
- proposing writes
- resolving ambiguity

## V1 Allowed Surface

| CLI command | Tool action | Read/write | Writes ledger? | Mutates card files? | Returns body/text? | V1 status | Notes / boundaries |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `validate` | `nollm.validate` | read | no | no | no | stable | Deterministic structural validation only. |
| `orient` | `nollm.orient` | read | no | no | no | stable | Anchor-field orientation; not context composition. |
| `recall` | `nollm.recall` | derived write | no | no | yes | stable | May write recall digest files; not canonical memory or semantic completeness. |
| `read` | `nollm.read_card` | read | no | no | yes | stable | Explicit single-card read; no neighbors or ranking. |
| `inspect` | `nollm.inspect` | read | no | no | no | stable | Active metadata inspection; not truth or approval. |
| `review` | `nollm.review` | read | no | no | no | stable | Compatibility name for active inspection. |
| `annotate` | `nollm.annotate` | write | yes | no | no | stable | Appends operator notes; does not approve or change trust/status. |
| `annotations` | `nollm.annotations` | read | no | no | yes | stable | Lists annotation ledger events. |
| `ledger` | `nollm.ledger` | read | no | no | yes | stable | Audit trail query; not recall or truth. |
| `history` | `nollm.history` | read | no | no | yes | stable | Object-level ledger inspection. |
| `audit` | `nollm.audit` | read | no | no | no | stable | Derived inspection projection; not memory. |
| `audit-check` | none | read | no | no | no | stable | Compares audit snapshots; structural drift only. |
| `tool` | envelope runner | read/write by action | by action | by action | by action | stable | Executes JSON envelope actions. |
| `surface` | `nollm.surface` | read | no | no | no | internal/experimental | Existing orientation helper; not stable V1 external surface. |
| `focus` | `nollm.focus` | read | no | no | no | internal/experimental | Existing orientation helper; not stable V1 external surface. |
| `write` | `nollm.write_card` | write | yes | yes | yes | internal/experimental | Candidate/draft writing helper; no direct confirmed writes. |
| `status` | `nollm.update_status` | write | yes | yes | no | internal/experimental | Operator transition helper; must preserve confirmation boundaries. |
| `tools` | none | read | no | no | no | internal/experimental | Local manifest inspection helper, not a protocol action. |
| `init` | none | write | no | yes | no | internal/experimental | Local notebook bootstrap helper, not a memory protocol action. |

Compatibility labels:

- `review` remains compatibility naming for active inspection.
- `inspect` is preferred.
- `read_card` is explicit single-card read.
- context composition is not a Core action.
