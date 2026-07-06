# Nollm Architecture

V2 is the only active architecture. `protocol/v2` is the only active protocol root.

V1 / MT1 / pre-V2 prototype source remains physically present as retired history; see docs/history/ for classification and migration boundaries.

## Layer Constitution

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

Core does not import adapters or terminals. Core facts are owned by L0-L3
contracts and deterministic workflows. Adapters translate explicit host inputs
and do not own facts. Terminals present product workflows and do not bypass L4.

## Business Paths

Capture, Admission, and Assembly are vertical business paths. They are not
replacement names for the horizontal layers.

## Identity Boundaries

V2 keeps real evidence identity, host request ID, terminal message ID, and CX2
projection reference distinct.

## Current Component Classification

- HCG1 is an accepted L5 File Capture Adapter.
- HAG1-C1R is an accepted and unpromoted L5 File Admission Adapter candidate at
  `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`; V2L0-C1R does not merge or modify
  it.
- V2L0-C1R neither merges nor modifies HAG1-C1R.
- HX1 and CX2 are L4 host contract and public envelope assets.
- DC1 is a deterministic Cortex compiler component; external Cortex policy is
  model-side policy outside Core.
- OpenClaw legacy is a frozen L5/L6 migration asset, not current runtime.
