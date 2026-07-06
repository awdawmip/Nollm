# Nollm

Nollm means:

> Not an LLM. A notebook for LLMs.

Nollm is a structured external notebook protocol for language models. The
active project architecture is V2. V1, MT1, and pre-V2 prototypes remain in the
repository only as retired history and migration reference material.

## Active Architecture

V2 is the only active architecture for repository navigation, implementation
planning, and acceptance routing.

The horizontal dependency layers are:

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
do not own Core facts. Terminals present product interactions and must not
bypass the L4 Host Contract and Execution Bridge.

## Business Paths

Capture, Admission, and Assembly are vertical business paths. They are not
replacement names for the horizontal layers.

- Capture accepts explicit content from a host and produces bounded capture
  state such as DreamShard and CaptureReceipt.
- Admission accepts explicit candidates, decisions, growth, and placement to
  produce AdmissionRecord.
- Assembly and Recall consume verified admissions through explicit finite
  assembly and recall contracts.

## Source Classification

- `protocol/v2/` is the normative V2 constitution and boundary namespace.
- `reference/python/nollm/dream_geometry/` contains accepted V2 Core work and
  sealed implementations that must not depend on terminal or adapter code.
- HCG is an accepted L5 File Capture Adapter.
- HAG1-C1R is an accepted but unpromoted L5 File Admission Adapter candidate at
  `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`; V2L0 does not merge or modify it.
- OpenClaw is a frozen migration asset for possible future L5/L6 adapter and
  terminal work. It is not the current Nollm runtime path.
- Historical V1, MT1, and pre-V2 prototype files are preserved for audit and
  migration reference. Their physical presence is not an active API.

Local `main`, `origin/main`, and accepted component heads must be rechecked on
the machine performing a delivery. This document does not promote remote state.

## Validation

The legacy single-process diagnostic remains documented for repository hygiene:

```powershell
cd reference/python
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python run_tests.py
```

Equivalent environment marker: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

Delivery-grade matrix evidence after TQ1 is produced outside the repository
under `C:\Users\chaos\nollm_test_runs\...` and sealed into a delivery bundle.

## Retired V1 Compatibility Appendix

This appendix preserves historical V1 route-lock language for tests and audit
navigation. It does not make V1 active.

Nollm V1 Route Lock

Nollm V1 Core exposes explicit filesystem-backed objects, deterministic validation, audit projections, and tool surfaces.

Nollm V1 Core does not compose context, rank semantics, infer truth, or perform autonomous memory management.

Cortex / LLM owned context composition in the retired V1 framing. V1 ledger/history inspection remains historical terminology.

Stable historical V1 tool actions:

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

Internal or experimental historical actions:

- `nollm.surface` is internal or experimental.
- `nollm.focus` is internal or experimental.
- `nollm.write_card` is internal or experimental.
- `nollm.update_status` is internal or experimental.
