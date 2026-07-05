# AGENTS.md

## Project identity

This repository is Nollm.

Nollm means:

> Not an LLM. A notebook for LLMs.

Nollm is a structured external notebook protocol for language models.

It is designed to help LLMs write, read, locate, re-locate, audit, and recall structured memory without becoming another LLM, RAG framework, vector database, knowledge graph engine, or autonomous agent runtime.

---

## Current architecture (V1 legacy state)

Nollm uses:

* layered rotating honeycomb memory field;
* 22.5° inter-layer rotation;
* √2 density growth per layer;
* anchor column fields;
* scale scanning;
* lateral recovery;
* Core/Cortex separation;
* file-first source of truth;
* deterministic audit reporting.

V4 engineering gravity direction has been decided by the project owner and is
documented in `NOLLM_PROJECT_SPEC_V4_ENGINEERING_GRAVITY_20260616.md` and the
G0 engineering/protocol drafts under `docs/` and `protocol/`. Codex must not
reinterpret that direction, change default/secondary geometry, turn gravity
marks into reject gates, map `drift_class` to trust/status, or implement G1-G8
while applying G0 documentation.

Core principles:

```text
Not an LLM.
Architecture is the Index.
Anchor is Field, not Folder.
Recall is Scale Scan, not Tree Descent.
SQLite is Audit Projection, not Memory.
Audit is Inspection, not Recall.
Audit-check is Drift Detection, not Semantic Judgment.
Inspect is Active Inspection; Review is Compatibility.
```

---

## Non-goals

Do not turn Nollm into:

* an LLM;
* a RAG framework;
* a vector database;
* a knowledge graph engine;
* an agent runtime;
* a self-improving memory agent;
* a Cognee-like automatic memory system;
* a database-centered recall engine;
* a semantic scoring system;
* a geometry reasoning engine.

---

## Non-negotiable boundaries

Do not introduce without explicit project-owner approval:

* SQLite recall path;
* database-backed memory;
* embeddings;
* vector databases;
* graph databases;
* external LLM extraction;
* MCP server;
* automatic ontology generation;
* automatic anchor creation;
* autonomous memory rewriting;
* geometry recall;
* polygon overlap outside the D1 pure geometry kernel;
* automatic card placement;
* semantic completeness scoring;
* tree descent;
* parent/children hierarchy.
* passive human review inbox;
* mandatory human approval gate.

SQLite, if ever added, must remain:

```text
optional
rebuildable
deletable
audit-only
not part of recall
not source of truth
```

---

## Core / Cortex boundary

Nollm Core must remain:

* dumb;
* stable;
* deterministic;
* file-first;
* auditable;
* non-reasoning.

Core may:

* store cards;
* read cards;
* validate metadata;
* append ledger events when appropriate;
* build deterministic audit reports;
* compare audit snapshots;
* expose safe JSON tool actions.

Core must not:

* infer facts;
* decide semantic truth;
* create anchors automatically;
* perform semantic search;
* perform geometry recall;
* decide semantic completeness;
* rewrite memory autonomously.
* create passive human review queues;
* block LLM reads on human inspection;

Nollm is LLM-first. Human inspection is optional, active, and ledgered. Human input is an operator action, not an oracle.

Nollm Cortex may be model-side, prompt-based, adaptive, and responsible for:

* deciding when to use Nollm;
* choosing active anchor fields;
* performing scale scanning;
* deciding when sufficient scale has been reached;
* using recall/read_card outputs safely.
* composing context outside Core.

---

## Audit rules

Audit output is:

```text
derived
read-only
rebuildable
disposable
not memory
not recall
not source of truth
not a hidden index
```

Audit may summarize:

* validation state;
* card distribution;
* honeycomb metadata;
* anchor field usage;
* recall digest metadata;
* ledger distribution;
* boundary flags.

Audit must not be used as factual memory content.

Use:

```text
recall
read_card
```

for memory content.

Use:

```text
audit
audit-check
```

for inspection, governance, and drift detection.

---

## Audit-check rules

Audit-check compares current audit output against a saved audit snapshot.

Audit-check is for deterministic structural drift detection.

Audit-check is not:

* semantic correctness checking;
* memory recall;
* factual verification;
* source-of-truth comparison;
* hidden indexing.

Expected behavior:

```text
no drift  -> current structural audit output matches snapshot
drift     -> structural audit output changed
```

Audit-check must remain read-only and must not append ledger events.

---

## Active inspection rules

Inspect is the preferred deterministic active inspection surface over metadata filters.

Inspect is not:

* passive human review;
* an approval queue;
* a read gate;
* memory recall;
* semantic scoring;
* truth assessment;
* priority assignment by Nollm.

`review_reason` is metadata-derived only.

`review` remains a compatibility command; its semantics are active inspection.

`confirmed` means currently accepted as stable within the notebook. It does not mean factually true, permanently correct, or human oracle truth.

`human-approved` means an operator accepted the record for current notebook use. It is provenance metadata, not proof of factual truth, and it does not outrank source evidence, ledger consistency, or later corrections.

---

## Annotation rules

Annotations are operator notes.

Annotations are ledgered.

Annotations do not modify card content.

Annotations do not change status.

Annotations do not change trust.

Annotations do not prove truth.

Annotations do not approve memory.

Annotations do not block LLM usage.

Annotations are not passive human review.

Annotations are active operator actions.

Do not use annotations as recall input by default, source evidence, semantic scoring, or approval.

Audit may count annotations.

Inspect/review may show `annotation_count`.

Annotation text is not recall content.

Annotation text does not change status or trust.

Annotation text does not prove truth.

Annotation counts are not semantic risk scores.

`annotation_count` means there are operator notes, not that a card is more or less reliable.

---

## Ledger and history rules

Ledger is an audit trail, not memory recall.

History is object-level ledger inspection.

Ledger/history do not prove truth.

Ledger/history do not approve memory.

Ledger/history do not change status or trust.

Ledger/history are read-only unless an explicit write action such as annotate/status is used.

Annotation text may appear in history because history is explicit audit inspection, but annotation text is still not recall content.

---

## Explicit read and context boundary

`read_card` reads exactly one explicit card.

`read_card` is not recall.

`read_card` is not context composition.

`read_card` does not return neighbors.

`read_card` does not rank related cards.

Core does not assemble deterministic context.

Context composition belongs to Cortex / LLM using explicit calls.

If an LLM needs context, it should make explicit read/inspect/history/ledger/recall calls and compose outside Core.

Surface relation:

* `read` / `read_card` = explicit object read;
* `inspect` / `review` = active metadata surface;
* `history` = object-level ledger trail;
* `ledger` = ledger query;
* `annotations` = annotation listing;
* `recall` = scale-scan digest;
* context composition = Cortex-side, not Core.

Do not add `nollm.context`, neighbor summaries, shared-anchor card bundles, related-card ranking, semantic matches, or automatic context composition to Core.

---

## Example and test hygiene

Top-level tool request examples must remain runnable:

```text
examples/tool_requests/*.json
```

Non-runnable placeholders must live under:

```text
examples/tool_requests/templates/
```

Expected-failure examples, if added, must live under:

```text
examples/tool_requests/error_cases/
```

Mutating tool examples used in tests must run against temporary notebook copies or must clean generated files reliably.

Tests must not leave generated artifacts in:

```text
examples/openclaw/recalls/
```

Only committed sample recall files should remain there:

```text
sample_recall_digest.json
sample_recall_digest.md
```

Generated files matching the following must not be committed unless intentionally promoted to fixtures:

```text
recall_*.json
recall_*.md
```

---

## Required validation commands

Before reporting completion of a Codex task, run from:

```bash
cd reference/python
```

Required commands:

```bash
python3 run_tests.py
python3 -m nollm.cli validate ../../examples/openclaw
python3 -m nollm.cli audit ../../examples/openclaw
```

Use `python3 run_tests.py` as a legacy single-process diagnostic command so ambient pytest plugins do not affect Nollm tests. The runner sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and delegates to pytest in one process.

For delivery-grade complete-suite verification after TQ1, use the bounded complete test matrix instead of treating single-process `run_tests.py` as the only full-suite proof. The matrix receipts and worktrees must be outside the repository under:

```text
C:\Users\chaos\nollm_test_runs\<git-commit>\
C:\Users\chaos\nollm_test_worktrees\<git-commit>\
```

When relevant to the phase, also run:

```bash
python3 -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/orient.json
python3 -m nollm.cli tool ../../examples/tool_requests/recall_scale_scan.json
```

For audit drift phases, also run:

```bash
python3 -m nollm.cli audit-check ../../examples/openclaw --against ../../examples/audit_reports/openclaw_audit.json
```

---

## Development style

Prefer small, reviewable changes.

Every change should preserve:

* human auditability;
* LLM readability;
* deterministic outputs;
* stable status semantics;
* clear Core/Cortex boundary;
* file-first source of truth;
* read-only audit behavior;
* generated artifact hygiene.

When adding tests that call subprocesses, always use explicit timeouts.

When adding examples, keep path semantics clear and runnable from the documented working directory.

---

## GitHub hygiene

This file is intended as local agent guidance unless the project owner explicitly decides to publish it.

Before uploading to GitHub, exclude local/private/dev artifacts such as:

```text
AGENTS.md
settings.json
.venv/
__pycache__/
*.pyc
.pytest_cache/
build/
dist/
*.egg-info/
coverage outputs
local generated recall_*.json/md
local generated audit outputs
temporary zip packages
```

Public repository guidance should live in:

```text
README.md
CONTRIBUTING.md
docs/
protocol/
```

not in local-only agent instruction files.

## Delivery bundle convention

For Nollm delivery bundles on the project owner's Windows workspace, create the final complete-history `.bundle` outside the repository at:

```text
C:\Users\chaos\<bundle-name>.bundle
```

Do not place delivery bundles inside the repository or under repo/out.

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

V1 CLI commands:

- `validate`
- `orient`
- `recall`
- `read`
- `inspect`
- `review`
- `annotate`
- `annotations`
- `ledger`
- `history`
- `audit`
- `audit-check`
- `tool`

Stable V1 tool actions:

- `nollm.validate`
- `nollm.orient`
- `nollm.recall`
- `nollm.read_card`
- `nollm.inspect`
- `nollm.review`
- `nollm.annotate`
- `nollm.annotations`
- `nollm.ledger`
- `nollm.history`
- `nollm.audit`

Internal or experimental CLI helpers that remain available but are not the V1 external surface: `init`, `tools`, `surface`, `focus`, `write`, and `status`.

Internal or experimental tool actions that remain available but are not the V1 external surface: `nollm.surface`, `nollm.focus`, `nollm.write_card`, `nollm.update_status`, and `nollm.read_card` legacy `card_id_or_address` input compatibility. They must preserve the same Core boundaries and must not introduce new V1 concepts.

Compatibility labels:

- `review` remains compatibility naming for active inspection.
- `inspect` is preferred.
- `read_card` is explicit single-card read.
- context composition is not a Core action.

## V1 Explicit Non-Goals

- No SQLite runtime.
- No database-backed recall.
- No embedding/vector search.
- No graph database.
- No MCP server.
- No external LLM calls.
- No geometry recall.
- No polygon overlap outside the D1 pure geometry kernel.
- No automatic card placement.
- No automatic anchor creation.
- No automatic status approval.
- No autonomous memory rewriting.
- No semantic completeness scoring.
- No truth scoring.
- No passive human review inbox.
- No mandatory human approval gate.
- No tree descent.
- No parent/children hierarchy.
- No automatic context composition.
- No deterministic context bundle.
- No neighbor/related-card ranking.

Pure polygon overlap is permitted only inside the D1 geometry kernel as a
deterministic geometric primitive. It must not be used as geometry recall,
automatic card placement, automatic anchor creation, semantic scoring, or
parent/children ownership.

## Dream Geometry V2 Route Lock - Owner Authorized 2026-06-29

The V2 amendment in `docs/architecture/NOLLM_GEOMETRY_ARCHITECTURE_AMENDMENT_V2_ATLAS_COVERAGE_KERNELS_20260629.md` is the owner-authorized target route for Dream Geometry V2 where it conflicts with older V4, V1, or Anchor-oriented descriptions about local charts, external Anchor entry, directed coverage kernels, Query Probe entry, and gravity visibility.

This route lock applies only to new V2 paths. V1 and W-series runtime behavior remain frozen legacy paths unless a later task explicitly authorizes migration or adapter work.

DG0 is limited to:

- V2 module boundaries;
- protocol constitution;
- parallel no-runtime Python package scaffolding;
- executable dependency firewall tests.

DG0 does not authorize geometry recall, automatic placement, OpenClaw integration, plugin work, sidecar work, true memory writes, agent trials, rollback work, or runtime changes.

V2 uses a local cellular atlas, directed `K↑ / K↓` (`K_up` / `K_down`) coverage kernels, Query Probe entry, exact Evidence fallback, and internal Field/Core gravity. Gravity is not an external anchor, query parameter, named index, or adapter-visible selector.

Future Geometry Kernel work must be implemented and independently verified before any runtime, CLI, JSON tool, OpenClaw, or adapter task may depend on it.
