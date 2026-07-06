# Nollm V2 Layer Constitution

V2 is the only active architecture for Nollm. This constitution defines the
horizontal dependency layers from Core to Terminal and binds source
classification for future work.

## Layer Definitions

### L0 Constitution and Protocol

L0 owns normative vocabulary, layer rules, compatibility policy, and protocol
contracts. L0 is documentation and contract authority. It does not import or
depend on implementation source.

### L1 Evidence and Identity Kernel

L1 owns evidence identity, content identity, projection fingerprint contracts,
and identity distinction rules. It preserves real evidence identity separately
from host request IDs, terminal message IDs, and public projection references.

### L2 Deterministic Domain Services

L2 owns deterministic domain services such as geometry, field, evidence
preserving compaction, and finite verification kernels. L2 services may use L1
identity contracts and L0 protocol terms only.

### L3 Core Workflow

L3 owns Core workflows for Capture, Admission, Assembly, and Recall. L3
coordinates explicit objects and deterministic services but does not know host
adapters, terminals, sessions, runtime products, OpenClaw, network services, or
databases.

### L4 Host Contract and Execution Bridge

L4 owns trusted host contracts, exact input binding, execution bridge receipts,
preflight validation, reopen fingerprints, public envelope boundaries, and
integration shells. L4 binds hosts to Core workflows without making host state a
Core fact.

HX1 and CX2 are L4 assets. DC1 is a deterministic Cortex compiler component;
external Cortex policy is model-side policy outside Core and is not renamed into
DC1.

### L5 Host Adapter Family

L5 owns host-specific adapters that translate explicit host inputs into L4
contracts. HCG1 is an accepted L5 File Capture Adapter.
HAG1-C1R is an accepted but unpromoted L5 File Admission Adapter. HAG1-C1R remains a candidate at
`0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`.

Adapters do not own evidence facts, placement facts, admission facts, field
facts, or recall facts.

### L6 Terminal and Product

L6 owns terminal surfaces, product UX, terminal message identity, operator
presentation, and product-specific workflows. L6 must enter Core through L5/L4.
Terminal code must not bypass Host Contract and Execution Bridge.

## Dependency Direction

The only allowed dependency direction is inward:

```text
L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0
```

Forbidden inward dependencies include:

- L0 importing implementation source;
- L1 importing workflow, adapter, terminal, runtime, or product code;
- L2 importing Core workflow, adapter, terminal, runtime, or product code;
- L3 importing L4, L5, L6, OpenClaw, CLI runtime, database, network, cache, LLM,
  NLP, embedding, semantic search, or global discovery code;
- L4 making terminal identity authoritative over Core facts;
- L5 rewriting evidence identity or owning Core facts;
- L6 calling Core implementation directly while bypassing L4.

## Business Paths Are Vertical

Capture, Admission, and Assembly are business paths, not layers.

```text
Capture:
  explicit content -> Capture workflow -> DreamShard / CaptureReceipt

Admission:
  explicit candidate + decision + growth + placement -> AdmissionRecord

Assembly / Recall:
  verified AdmissionRecord inputs -> finite assembly -> recall contract
```

Each path may cross several layers while preserving layer authority.

## Object Authority

- Core facts are owned by L0-L3 contracts and deterministic workflows.
- Adapters translate host input and bind it to L4 contracts.
- Terminals present product interactions and own terminal-facing messages only.

No adapter or terminal may promote host convenience fields into Core fact
authority.

## Identity Distinctions

V2 keeps these identities separate:

- real evidence identity: byte or object identity of source evidence;
- host request ID: explicit host-provided request identity;
- terminal message ID: product or terminal message identity;
- CX2 projection reference: public envelope projection reference.

These identifiers may be related by receipts, but none is a substitute for
another.

## Versioning and Compatibility

V2 protocol documents are the active compatibility surface. Historical V1, MT1,
and pre-V2 prototype material may remain in the repository as retired history.
Physical presence is not active API status.

OpenClaw legacy is a frozen L5/L6 migration asset for future adapter or terminal
work. It is not an active Core dependency or current runtime path.
