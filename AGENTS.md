# AGENTS.md

## Project Identity

This repository is Nollm:

> Not an LLM. A notebook for LLMs.

Nollm is a structured external notebook protocol for language models.

## Active Architecture

V2 is the only active architecture for new work. V1, MT1, and pre-V2 prototype
content is retired history unless a task explicitly authorizes migration work.

The active layers are:

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
surfaces; they do not own facts. Terminals present workflows; they do not bypass
L4 Host Contract and Execution Bridge.

## Current Classification

- `protocol/v2/` is the normative V2 protocol namespace.
- `reference/python/nollm/dream_geometry/` is V2 Core and domain source; do not
  add terminal, runtime, OpenClaw, network, database, cache, LLM, NLP, embedding,
  or global discovery dependencies there.
- HCG is an accepted L5 File Capture Adapter.
- HAG1-C1R is accepted but unpromoted at
  `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`; do not merge or modify it unless
  a later task explicitly authorizes that.
- OpenClaw is a frozen migration asset for possible future L5/L6 work, not the
  current Nollm runtime.

## Required Validation Commands

Before reporting completion of ordinary repository tasks, run from
`reference/python` when applicable:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python run_tests.py
python -m nollm.cli validate ../../examples/openclaw
python -m nollm.cli audit ../../examples/openclaw
```

For delivery-grade complete-suite verification after TQ1, use the bounded
complete test matrix outside the repository under:

```text
C:\Users\chaos\nollm_test_runs\<git-commit>\<matrix-id>\
C:\Users\chaos\nollm_test_worktrees\<git-commit>\<matrix-id>\
```

Delivery bundles must be complete-history bundles outside the repository, for
example under `C:\Users\chaos\`.

Delivery bundle convention:

```text
C:\Users\chaos\<bundle-name>.bundle
```

## Development Rules

Preserve deterministic outputs, file-first evidence, exact identity boundaries,
and the V2 layer dependency direction. Do not add LLM calls, embeddings, vector
databases, graph databases, SQLite-backed recall, network services, runtime
activation, OpenClaw integration, or terminal bypasses unless a task explicitly
authorizes that scope.

Pure polygon overlap is permitted only inside the D1 geometry kernel.

Dream Geometry V2 Route Lock remains the historical name for the owner-approved
V2 geometry direction; V2L0 now classifies it under the active layer
constitution.

The V2 amendment is active under V2L0. The historical phrase "parallel, not yet integrated" is retained only as retired wording.

Pure polygon overlap is not geometry recall and is not automatic card placement.

Do not place delivery bundles inside the repository or under repo/out.
