# Nollm

Nollm means:

> Not an LLM. A notebook for LLMs.

Nollm is a structured external notebook protocol for language models.
V2 is the only active architecture.

V1 / MT1 / pre-V2 prototype source remains physically present as retired history; see docs/history/ for classification and migration boundaries.

## Active Architecture

`protocol/v2` is the only active protocol root.

The active horizontal layers are:

- L0 Constitution and Protocol
- L1 Evidence and Identity Kernel
- L2 Deterministic Domain Services
- L3 Core Workflow
- L4 Host Contract and Execution Bridge
- L5 Host Adapter Family
- L6 Terminal and Product

Dependencies move inward only:

```text
L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0
```

Core does not import adapters or terminals. Adapters translate host surfaces and
do not own facts. Terminals present product workflows and do not bypass L4.

## Current Source Classification

- HCG1 is an accepted L5 File Capture Adapter.
- HAG1-C1R is an accepted and unpromoted L5 File Admission Adapter candidate at
  `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`; V2L0-C1R does not merge or modify
  it.
- V2L0-C1R neither merges nor modifies HAG1-C1R.
- OpenClaw legacy is a frozen L5/L6 migration asset, not current runtime.
- Historical V1, MT1, and pre-V2 prototype files are preserved for audit and
  migration reference only.

Local `main`, `origin/main`, and accepted component heads must be rechecked on
the delivery machine. This document does not promote remote state.

## Validation

Ordinary V2 work uses component-local pytest gates and explicitly scoped public
regression gates for the affected V2 components. Delivery-grade acceptance uses
the TQ1 matrix, parentless evidence capsule, and `verify-ref`.

`python run_tests.py` remains a legacy-inclusive repository diagnostic. It is
not the primary V2 component acceptance gate and is not evidence that V1 is active architecture. The diagnostic sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.
