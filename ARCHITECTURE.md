# Nollm Architecture

V2 is the only active architecture for Nollm. Older V1, MT1, and pre-V2
prototype material is retained only as retired history, audit evidence, and
migration input.

## Layer Constitution

The active dependency model is Core to Terminal by layers:

```text
L0 Constitution and Protocol
L1 Evidence and Identity Kernel
L2 Deterministic Domain Services
L3 Core Workflow
L4 Host Contract and Execution Bridge
L5 Host Adapter Family
L6 Terminal and Product
```

Allowed dependency direction:

```text
L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0
```

No inward layer may import an outward layer. In particular:

- Core facts are established by L0-L3 contracts and domain services.
- L4 binds trusted hosts to exact contracts and execution receipts.
- L5 adapters translate explicit host files, requests, or envelopes.
- L6 terminals present product workflows and own terminal message identity.

Core does not know OpenClaw, command-line products, UI terminals, sessions, or
host-specific adapters.

## Business Path View

The business paths are vertical flows across the layers:

- Capture: explicit content to bounded capture state and receipt.
- Admission: explicit candidate to accepted admission record.
- Assembly: verified admission records to finite field snapshot and recall
  universe contracts.

The paths are not layers. A Capture implementation can include L1 facts, L3
workflow, L4 host binding, and L5 adapter code without collapsing those
responsibilities into one namespace.

## Identity Boundaries

V2 keeps these identifiers distinct:

- real evidence identity: byte-level or object-level identity of source evidence;
- host request ID: identity assigned by the trusted host or adapter envelope;
- terminal message ID: identity assigned by a product or terminal surface;
- CX2 projection reference: public envelope projection identity, not Core fact
  ownership.

Adapters may translate these identifiers into structured envelopes. They must
not rewrite evidence identity or make terminal identity authoritative over Core
facts.

## Current Accepted Source

The local main baseline for V2L0 is
`8bb324a3a5de46bebb6eadd217820627a971e2a0`. Main and remote state are
machine-local facts and must be rechecked before any delivery.

HCG is an accepted L5 File Capture Adapter. HAG1-C1R is accepted but unpromoted
at `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`; V2L0 does not merge it. HX1 and
CX2 remain L4 host contract and external cortex conformance assets. DC1 is the
deterministic Cortex compiler component; it is not the external model-side
Cortex policy.

## Legacy Boundary

Historical V1, MT1, OpenClaw, and pre-V2 prototype files may remain physically
present. They are not active architecture, active API, active runtime, or an
implicit dependency source for V2 Core work.
OpenClaw is a frozen migration asset for future L5/L6 work.

## Retired V1 Compatibility Appendix

This section preserves historical V1 route-lock language for audit tests. It is
not active architecture.

Nollm V1 Route Lock

Nollm V1 Core exposes explicit filesystem-backed objects, deterministic validation, audit projections, and tool surfaces.

Nollm V1 Core does not compose context, rank semantics, infer truth, or perform autonomous memory management.

Cortex / LLM owned context composition in retired V1 documentation.
V1 ledger/history inspection remains historical terminology.

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
