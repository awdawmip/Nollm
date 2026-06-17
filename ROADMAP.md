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

## V4 Engineering Gravity Decision

The next experimental engineering direction is captured in:

- `NOLLM_PROJECT_SPEC_V4_ENGINEERING_GRAVITY_20260616.md`
- `docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md`
- `docs/engineering/NOLLM_MINIMUM_DATA_MODEL_20260616.md`
- `docs/experiments/NOLLM_MINIMAL_ABLATION_EXPERIMENT_PLAN_20260616.md`
- `docs/geometry/NOLLM_TRUE_TILING_ENGINEERING_REQUIREMENTS_20260616.md`
- `protocol/GRAVITY_WELL.md`
- `protocol/GRAVITY_MARK.md`
- `protocol/DRIFT_REPORT.md`
- `protocol/RETURN_VECTOR.md`

G0 only adds these decided documents. G1-G8 remain separate implementation tasks.
The V4 drafts do not expand the stable V1 recall/tool surface and do not make
`drift_class` a trust/status mapping.

## Non-Goals

- No model runtime.
- No agent orchestration.
- No vector database.
- No embedding dependency.
- No automatic ontology engine.
- Stable V1 Core/tool surfaces do not perform geometry recall or automatic runtime placement.
- D-series reference modules may contain experimental pure geometry, placement candidate records, and deterministic diagnostics.

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
- No polygon-overlap-driven V1 recall.
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
- Generated-output recall examples are isolated and should be run against temp notebooks.
- SQLite audit projection remains future research, not V1 runtime.
- MCP remains future consideration, not V1.
