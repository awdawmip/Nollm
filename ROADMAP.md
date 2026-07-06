# Nollm Roadmap

V2 is the only active architecture. `protocol/v2` is the only active protocol root.

V1 / MT1 / pre-V2 prototype source remains physically present as retired history; see docs/history/ for classification and migration boundaries.

## Dependency Direction

```text
L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0
```

Core does not import adapters or terminals. Adapters do not own facts.
Terminals do not bypass L4.

## Active Component Route

- L0-L3: protocol, evidence identity, deterministic domain services, and Core
  workflows.
- L4: HX1 and CX2 host contract and envelope boundary assets.
- L5: HCG1 is an accepted File Capture Adapter.
- L5: HAG1-C1R is an accepted and unpromoted File Admission Adapter candidate at
  `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`; V2L0-C1R does not merge or modify
  it.
- V2L0-C1R neither merges nor modifies HAG1-C1R.
- L5/L6 future: OpenClaw legacy is a frozen L5/L6 migration asset, not current runtime.

## Delivery Route

Delivery-grade acceptance uses explicitly scoped V2 gates, the TQ1 complete
matrix, parentless evidence capsule, `verify-ref`, and a complete-history Git
bundle. Main promotion and remote publication require separate authorization.
