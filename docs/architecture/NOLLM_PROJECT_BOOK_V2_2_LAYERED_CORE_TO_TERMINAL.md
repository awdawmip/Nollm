# LEGACY_REFERENCE / SUPERSEDED

This historical V2.2 project book is superseded by the [active modular project book](../project/NOLLM_PROJECT_BOOK_V3_0_MODULAR_GEOMETRY_INFRASTRUCTURE_M1_20260711.md).

# Nollm Project Book V2.2: Layered Core to Terminal

V2.2 separates business paths from dependency layers.

## Horizontal Layers

```text
L0 Constitution and Protocol
L1 Evidence and Identity Kernel
L2 Deterministic Domain Services
L3 Core Workflow
L4 Host Contract and Execution Bridge
L5 Host Adapter Family
L6 Terminal and Product
```

Dependency direction is inward only:

```text
L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0
```

## Vertical Business Paths

Capture, Admission, and Assembly are vertical paths that use the layers without
owning them.

- Capture starts from explicit content and produces bounded capture objects.
- Admission starts from explicit candidate and decision inputs and produces
  admission records.
- Assembly starts from verified admissions and produces finite assembly and
  recall contract objects.

## Authority Model

Core owns facts. Adapters translate. Terminals present.

Host convenience fields, terminal message IDs, and public projection references
can be receipt evidence, but they are not substitutes for real evidence
identity or Core object authority.

## Source Reclassification

The repository root must guide future contributors to V2. Legacy source remains
for audit and migration, not as active architecture. OpenClaw remains a frozen
migration asset until a later L5/L6 task explicitly activates adaptation.
