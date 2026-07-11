# Nollm Architecture

M1 establishes package-level Core/Access behavior in a modular monorepo.

## Active Dependency Graph

```text
nollm-core -> Python standard library only
nollm-snapshot -> nollm-core public ports
nollm-trace -> nollm-core trace contracts
nollm-access -> nollm-core public API (+ optional snapshot API)
nollm-history -> skeleton
nollm-audit -> skeleton
```

The active production graph has zero boundary violations and zero cycles.
Distributions contain composition metadata only. Lab may import all public
modules and Legacy migration assets; production modules never import Lab.

## Core State

Core owns deterministic geometry current state. `MemoryAtom` contains only
`atom_id` and semantic-blind `payload_utf8`. `AtomHandle` contains a
`GeometryAddress` and cell-local atom ID and is the only mutation locator.

The canonical current-state JSON file is the M1 file fact source. It is not an
object relation index. Runtime occupancy rebuilds entirely from it, and Recall
correctness uses no route table. Geometry partition files are deferred until a
future scale stage.

Core Recall accepts explicit geometry entry cells only and returns Core atoms,
Handles, scores, and budget state. Source fallback and revision semantics belong
to Access. Snapshot, Trace, History, and Audit are distinct ownership domains.

## Legacy Boundary

The old mixed GRF implementation remains available for migration regression but
is absent from active distributions. OpenClaw adapters are paused migration
assets. Evidence-first V2 and older layer constitutions remain historical and
superseded rather than active architecture.
