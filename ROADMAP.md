# Nollm Roadmap

V2 is the only active architecture for Nollm. The roadmap is now organized
around V2 layers and explicit migration gates.

Allowed dependency direction:

```text
L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0
```

## Current Baseline

V2 is the only active architecture. The repository still carries retired V1,
MT1, OpenClaw, and prototype material for audit and migration reference, but
new work routes through the V2 layer constitution.

## Active Layer Targets

- L0: Constitution and protocol documents define layer authority and dependency
  direction.
- L1: Evidence and identity kernels preserve source identity and public
  projection boundaries.
- L2: Deterministic domain services provide geometry, field, compaction, and
  related pure services.
- L3: Core workflows coordinate Capture, Admission, Assembly, and Recall without
  terminal dependencies.
- L4: Host contracts and execution bridges bind trusted hosts to exact inputs,
  outcomes, receipts, and preflight checks.
- L5: Host adapters translate explicit file-first or host-first envelopes.
- L6: Terminals and products present workflows through L5/L4 only.

## Component Status

- HCG: accepted L5 File Capture Adapter.
- HAG1-C1R: accepted, unpromoted L5 File Admission Adapter candidate at
  `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`.
- HX1 and CX2: L4 host contract and bridge/conformance assets.
- OpenClaw: frozen migration asset for future L5/L6 work, not active runtime.
- V1 and MT1: retired history, not an active dependency model.
- DG5: Evidence-preserving trace compaction capability is accepted at `5e91504d0f3961be9631856a8853a58ca6bd1921`.
- DG6: Isolated snapshot compaction adapter is accepted at `47eca074045cede79d19b897ff4cae48dca23ab6`.
- DG7: Explicit reference runtime positive verification is implemented.

## Deferred Work

Future migration work may classify or adapt OpenClaw, legacy command surfaces,
and product terminals into L5/L6. That work requires explicit authorization and
must not bypass L4 contracts or make terminal state authoritative over Core
facts.

## Retired V1 Compatibility Appendix

This section preserves historical V1 route-lock and limitation language for
audit tests. It is not active architecture.

Nollm V1 Route Lock

Nollm V1 Core exposes explicit filesystem-backed objects, deterministic validation, audit projections, and tool surfaces.

Nollm V1 Core does not compose context, rank semantics, infer truth, or perform autonomous memory management.

Cortex / LLM owned context composition in retired V1 documentation.
V1 ledger/history inspection remains historical terminology.

Historical V1 limitations:

- Unicode/mojibake terminology guard remains deferred.
- No GitHub Actions yet.
- No formal CONTRIBUTING.md yet.
- No public AGENTS.example.md yet.
- Packaging remains simple.
- Generated-output recall examples are isolated and should be run against temp notebooks.
- SQLite audit projection remains future research, not V1 runtime.
- MCP remains future consideration, not V1.

Retired V1 non-goals:

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
