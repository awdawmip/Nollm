# AGENTS.md

## Project Identity

This repository is Nollm:

> Not an LLM. A notebook for LLMs.

V2 is the only active architecture. `protocol/v2` is the only active protocol root.

V1 / MT1 / pre-V2 prototype source remains physically present as retired history; see docs/history/ for classification and migration boundaries.

## Active Layers

```text
L0 Constitution and Protocol
L1 Evidence and Identity Kernel
L2 Deterministic Domain Services
L3 Core Workflow
L4 Host Contract and Execution Bridge
L5 Host Adapter Family
L6 Terminal and Product
```

Dependencies may only point inward:

```text
L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0
```

Core does not import adapters or terminals. Adapters translate and bind host
surfaces; they do not own facts. Terminals present workflows and do not bypass
L4 Host Contract and Execution Bridge.

## Current Classification

- `reference/python/nollm/dream_geometry/` is V2 Core and domain source; do not
  add terminal, runtime, OpenClaw, network, database, cache, LLM, NLP, embedding,
  or global discovery dependencies there.
- HCG1 is an accepted L5 File Capture Adapter.
- HAG1-C1R is an accepted and unpromoted L5 File Admission Adapter candidate at
  `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`; V2L0-C1R does not merge or modify
  it.
- V2L0-C1R neither merges nor modifies HAG1-C1R.
- OpenClaw legacy is a frozen L5/L6 migration asset, not current runtime.

## Validation Guidance

Ordinary V2 repository work uses component-local pytest gates and explicitly
scoped public V2 regression gates for the affected components.

`python run_tests.py` is a legacy-inclusive repository diagnostic. It is not
the primary V2 component acceptance gate and is not evidence that V1 is active architecture.

Delivery-grade acceptance uses the TQ1 complete test matrix, parentless
evidence capsule, `verify-ref`, and a complete-history Git bundle.

## Delivery Bundle Convention

Delivery bundles must be created outside the repository:

```text
C:\Users\chaos\<bundle-name>.bundle
```

Do not place delivery bundles inside the repository or under repo/out.
