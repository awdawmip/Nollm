# Roadmap

## v0.1: Protocol Scaffold

- Define Core documents for cards, anchors, ledgers, recall digests, and memory addresses.
- Define statuses and LLM-facing actions before runtime implementation.
- Freeze protocol vocabulary for statuses, types, trust, sources, actions, and validation before P1 CLI work.
- Define Cortex guidance for prompts, anchor composition, and read/write policy.
- Provide a small example notebook.
- Keep all source of truth in Markdown, YAML, and JSONL.
- Align protocol language to Anchor is Field, not Folder and Recall is Scale Scan, not Tree Descent.

## v0.2: Validation And Tooling

- Add schema checks for anchors, aliases, cards, and ledger events.
- Add deterministic address validation.
- Add simple local inspection commands.
- Keep SQLite, if used, only as an optional audit projection.

## v0.3: Recall Workflow

- Formalize recall digest generation.
- Define conflict and supersession conventions.
- Keep active inspection deterministic without introducing passive human review queues.
- Preserve status transition history in the ledger.

## Non-Goals

- No model runtime.
- No agent orchestration.
- No vector database.
- No embedding dependency.
- No automatic ontology engine.
- No geometry runtime or runtime coordinate placement yet.

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
- No polygon overlap.
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

## V1 Known Limitations

These limitations do not block V1.

- Unicode/mojibake terminology guard remains deferred.
- No GitHub Actions yet.
- No formal CONTRIBUTING.md yet.
- No public AGENTS.example.md yet.
- Packaging remains simple.
- `recall_scale_scan` example requires care because it may generate digest files.
- SQLite audit projection remains future research, not V1 runtime.
- MCP remains future consideration, not V1.
