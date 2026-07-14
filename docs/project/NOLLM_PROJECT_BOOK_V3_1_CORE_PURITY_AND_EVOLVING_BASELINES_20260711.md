# Nollm Project Book V3.1: Core Purity And Evolving Baselines

**Version:** V3.1
**Role:** Active architecture and baseline-governance authority

This book defines stable module ownership, dependency direction, public
contracts, and evidence rules. Scheduling, revisions, and temporary execution
constraints belong to the status and authorized task documents linked by the
active project basis.

## Architecture Principles

- Original Evidence remains the fact source and is kept separate from geometry.
- Files are durable facts; caches and snapshots are reconstructable derivatives.
- Geometry addresses, cell occupancy, coverage, local adjacency, and explicit
  reversible bridges provide relation and bounded recall paths.
- Semantic placement decisions are supplied explicitly by a host, model, or
  human. Deterministic runtime code validates and executes those decisions.
- Graph, vector, embedding, route-table, or external relation-index paths do not
  become correctness dependencies.

## Module Ownership

### nollm-core

Owns semantic-blind atoms, addressed handles, geometry current state, compiled
runtime kernels, bounded explicit-entry recall, atomic commands, canonical
current-state persistence, and minimal snapshot/trace ports. It owns no
Evidence policy, semantic placement, history, audit, host integration, or
dynamic compilation.

### nollm-snapshot

Owns create, restore, clone, verify, and finite structural differences over a
consistent-state public port. It does not define semantic history.

### nollm-trace

Owns optional sinks, metrics, JSONL output, composition, and inspection tools.
Observation cannot change runtime correctness or persistent state bytes.

### nollm-access

Owns original Evidence, statement and handle stores, explicit action mapping,
source fallback, entry selection, and recall formatting. Saved handles support
explicit mutation and Evidence resolution, not relation discovery.

### Optional And Host Modules

History owns semantic version policy; Audit owns external decision records;
host adapters translate external decisions through public Access contracts.
These modules do not become dependencies of the minimal runtime.

### nollm-lab

Owns research definitions, compile-time mathematics, generators, parity tools,
benchmarks, fixtures, migrations, and validation. It may consume public package
contracts and legacy baselines, but must not import private package submodules.

### nollm-distributions

Owns composition metadata only. Distributions do not implement business logic.

## Dependency Direction

```text
nollm-core          -> Python standard library
nollm-snapshot      -> public Core state port
nollm-trace         -> public Core trace contracts
nollm-access        -> public Core API; optional public Snapshot API
optional modules    -> selected public sibling APIs
host adapters       -> public Access and selected sibling APIs
nollm-lab           -> public modules and legacy validation baselines
distributions       -> composition metadata
```

Production dependencies never point into Lab or legacy implementations, and
the production graph remains acyclic.

## Public Contract Governance

- Public symbols are declared by package root allowlists and tested directly.
- Private submodules are implementation details and may evolve without Lab or
  distribution changes.
- Persistent objects reject wrong direct-constructor types and use canonical
  bytes without coercion or silent deduplication.
- Core operations require addressed handles; recall requires explicit geometry
  entries and finite budgets.
- Generated runtime artifacts are digest-checked and reproduced by Lab without
  runtime compilation.

## Evolving Baseline Governance

- Capability evidence binds a concrete code revision and stable code-tree digest.
- A later documentation-only revision may declare an active baseline only when
  it leaves the validated code tree unchanged and all read-only checks pass.
- The active project basis is the single machine-readable navigation source for
  the project book, status, ledger, authorized task, and latest report.
- Superseded books, tasks, and reports remain historical references and cannot
  override active governance.
- The active V3.6 route may add rebuildable semantic-blind Surface projections
  and bounded Access navigation while preserving these ownership and dependency
  rules.
- Completion estimates use five-percent increments or explicit ranges and do
  not imply permanence or authorization for later work.
- Each new capability or route requires a separately authorized task and fresh
  evidence; no baseline automatically starts another stage.
