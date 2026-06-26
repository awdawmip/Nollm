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

## MT1-R9 Trust Boundary Correction

MT1-R9 is a breaking archive/publication trust-boundary correction for the reference Python ingest path. It introduces archive manifest v3 `sources[]`, policy-derived source identity/state, SafeRoot-contained MT1 I/O, retired flat field writers, publish-journal-backed HEAD activation, repeated `_rN` recovery batches, and structured public failures. R1-R8 MT1 active artifacts require rearchive/reimport and are not a stable migration foundation.

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

## F0-01: OpenClaw Native Memory Provider Functional Alpha

A short milestone between MT1 archive ingest and later native recall runtime:

- Add @nollm/openclaw-memory as a standalone kind: \"memory\" plugin.
- Keep
ollm-memory-companion as historical/experimental companion surface.
- Implement private gent_turn_prepare recall and gent_end capture receipt.
- Use a synthetic deterministic alpha field.
- Disable legacy memory fallback.
- Validate against a fixed OpenClaw commit without model credentials.
- Document known limitations as public issue seeds.

F0 does **not**:

- complete R14 SafeRoot / capability storage;
- migrate real MEMORY.md / DREAMS.md history;
- implement finished Cortex geometry recall;
- claim production memory takeover.

The next milestone after F0 is F1 Native Ingress Alpha, which promotes capture
receipts to native shards under R14-safe storage.

## W1-01: OpenClaw Native Companion Memory MVP

A short milestone that adds explicit native remember/recall/get tools to the
existing `nollm-memory-companion` package while keeping `memory-core` active:

- Deterministic Nollm-owned store under `.nollm-memory/native-companion-v1/`.
- `nollm_memory_remember`, `nollm_memory_recall`, `nollm_memory_get` exposed as
  strict OpenClaw tool-plugin tools.
- Secret-like input guard, canonical deduplication by `(scope, kind, text)`,
  and Chinese identity/preference query aliases.
- Python sidecar commands `native-remember`, `native-recall`, `native-get`.
- Updated skill guidance for explicit user identity/preference remember/recall.
- Windows live smoke with a synthetic marker, legacy source hashes unchanged.

W1-01 does **not**:

- replace `memory-core` or claim the OpenClaw memory slot;
- write or migrate `MEMORY.md`, `DREAMS.md`, or `memory/*.md`;
- call a real LLM or use embeddings;
- automatically capture every conversation turn;
- implement R14 capability-storage hardening.
## W2-01: OpenClaw Direct Active Memory Cutover

Owner-authorized empirical trial that makes the `nollm` provider the active
OpenClaw memory-slot owner (`plugins.slots.memory = "nollm"`).

- Convert `integrations/openclaw/nollm-memory-provider/` from F0 alpha fixture
  mode to a Windows-safe native active memory provider.
- Reuse the W1 native companion store (`native-companion-v1/`).
- `agent_turn_prepare` recalls from the native store into a bounded
  `NOLLM_MEMORY_CONTEXT_V1` envelope.
- `agent_end` deterministically auto-captures explicit stable user sentences
  (remember directives, identity, preference, project/release decisions).
- No Primary-visible Nollm memory tools in active mode.
- No read/write of `MEMORY.md`, `DREAMS.md`, or `memory/*.md` by the provider.
- Local-only redacted trial metrics; tested rollback to `memory-core`.
- Record legacy `MEMORY.md` workspace bootstrap as a measured confound.

W2-01 result: `PARTIAL`. Active slot ownership, capture, and most recalls
succeeded; identity recall was confounded by legacy `MEMORY.md` bootstrap.

W2-01 does **not**:

- claim exclusive prompt memory ownership while workspace bootstrap may exist;
- clean up or tombstone `MEMORY.md`, `DREAMS.md`, or `memory/*.md`;
- wait for W1-04 generic exact-match cleanup or F0 harness closure;
- use embeddings, vector DB, SQLite recall, or external LLM calls;
- expose manual Nollm memory tools to Primary while active.
