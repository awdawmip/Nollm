# Nollm

> **Not an LLM. A memory field for LLMs.**

Nollm is an evidence-first, file-first, geometry-native long-term memory system for LLM agents.

It does **not** try to replace the model. It gives the model a place to remember while it works — a persistent field where new experience can be formed, placed, revisited, revised, and connected without turning memory into a second semantic database.

A useful mental model is:

> The LLM works in the foreground; Nollm is where its memory can continue to form and, eventually, “dream” in the background.

## Why Nollm exists

Long-context systems eventually face the same pressure: keep more text in the prompt, summarize harder, or build another retrieval stack around the model.

Nollm explores a different direction:

```text
Evidence
  -> meaningful memory statements
  -> geometric placement
  -> physical locality and overlap
  -> bounded field reconstruction
  -> one-entry recall
  -> evidence fallback
```

The goal is not to find a document first and then draw geometry around it. The geometry itself is meant to carry the memory relationships.

## Core philosophy

### 1. Evidence is the fact source

Raw evidence is preserved. A remembered statement, its placement, the path used to recall it, and the model's interpretation are different things.

```text
Evidence != Interpretation
Interpretation != Placement
Placement != Fact confirmation
Recall path != Proof
```

Nollm can reorganize memory without rewriting history.

### 2. The minimum memory unit is meaningful language

Nollm does not treat a token, a fixed-size chunk, an embedding vector, or an entity node as the fundamental memory unit.

The basic semantic unit is:

> **a self-contained, meaningful statement that can be traced back to its original evidence**

### 3. Architecture is the Index

Relationships should come primarily from the memory field itself:

```text
GeometryAddress
Cell occupancy
Coverage
Lateral adjacency
bounded Bridge connections
```

Nollm deliberately avoids making these the correctness path:

```text
vector / embedding search
graph databases
Topic -> Cell routes
Entity -> Memory routes
Source -> Placement tables
persistent query -> entry caches
```

Disposable caches are allowed. A second relationship system that becomes necessary for correctness is not.

### 4. The LLM owns semantics; Core owns geometry

A real LLM decides semantic questions such as:

```text
new vs duplicate
same fact vs similar-but-different
revision vs reuse
related locality vs new locality
stitch vs defer
```

The deterministic Core does not simulate those decisions with hashes, keyword rules, pseudo-vector scores, or hand-written semantic weights.

Core is responsible for:

```text
valid addresses
physical geometry
occupancy
coverage / lateral / bridge propagation
budgets and boundaries
atomic state changes
canonical persistence
bounded recall
```

### 5. Read and write are one field operation

Nollm no longer begins by deciding “this is a read” or “this is a write”.

Both use the same **Unified Field Encounter**:

```text
stimulus
  -> Surface
  -> progressive geometric traversal
  -> one physical entry
  -> bounded Locality
  -> encounter a fact or a legal vacancy
```

The terminal state determines the effect:

```text
fact found + query            -> Recall
fact found + new proposition  -> Reuse / Revision
vacancy found + proposition   -> Placement
vacancy found + query         -> NONE
uncertain                     -> Continue / Defer
```

This keeps semantic navigation unified while preserving an atomic mutation boundary for writes.

## The physical memory field

The active geometry is a rotated, multi-scale hexagonal field.

Hard design parameters include:

```text
adjacent physical-layer rotation: 22.5 degrees
initial rotation:                  0 degrees
linear scale ratio beta:           2^(1/4)
area / density ratio:              sqrt(2)
```

A **Physical Memory Layer** is not the same thing as an **Aggregation Order**:

- physical layers are real places where memory atoms may exist;
- aggregation orders are temporary, rebuildable observation scales used to let an LLM browse a very large field within a bounded prompt budget.

Derived Surface state is disposable. Deleting it must not change memory correctness.

A recall traversal selects **one final physical entry**. Wider reach should emerge from Coverage, local adjacency, existing Bridges, and field density — not from the host selecting many independent entries and merging them afterward.

## OpenClaw: becoming the native memory system

OpenClaw is the current semantic host for Nollm.

The V3.14 direction is to stop running Nollm beside OpenClaw's memory system and instead occupy OpenClaw's official exclusive memory slot:

```text
plugins.slots.memory
        -> nollm-memory
        -> memory_search / memory_get
        -> Nollm Unified Field Encounter
```

The repository now contains the native `@nollm/openclaw-memory` package checkpoint with:

- `kind: memory` ownership;
- standard `memory_search` / `memory_get` tool contracts;
- OpenClaw tool-factory `agentId` / `sessionKey` scope;
- a progressive single-entry Field Encounter transport;
- Memory Capability registration;
- ClawHub-oriented package metadata.

The older custom `nollm_field_encounter` route is historical migration input, not the long-term integration model.

### One-command install target

The release target is:

```bash
openclaw plugins install clawhub:@nollm/openclaw-memory
```

A real one-command release must not require a Nollm Git checkout, a manually configured Python path, or hand-created workspaces. Platform runtime packaging, clean install/update/uninstall tests, Windows live validation, and ClawHub security/release gates remain release-validation work; the repository should not claim public one-click availability until those gates are actually closed.

## Repository architecture

### `nollm-core`

Semantic-blind physical memory state:

```text
MemoryAtom / AtomHandle
GeometryAddress
Cell occupancy
Coverage / Lateral / Bridge runtime
atomic mutation
canonical state
bounded recall
```

### `nollm-access`

The semantic/evidence boundary around Core:

```text
Evidence
MemoryStatement
Handle binding
Field Encounter orchestration
LLM/Human decisions
current-statement projection
Evidence-backed recall formatting
```

### `nollm-snapshot`

Snapshot creation, restore, clone, verify, and state comparison over Core's canonical state interface.

### `nollm-trace`

Optional trace sinks, metrics, inspectors, and observational tooling. Trace is not memory truth.

### OpenClaw integration

Hosts the real LLM workflow, background formation, native memory-slot tools, hidden recall injection, and failure-open behavior.

### Lab

Owns physical-math validation, Coverage compilation, experiments, fault injection, scale studies, and historical baselines. Production packages must not depend on Lab.

## What Nollm is not

Nollm is not intended to become:

- a vector database with a hexagonal visualization;
- a knowledge graph with geometry added afterward;
- GraphRAG wrapped in another retrieval layer;
- a global Topic/Entity routing table;
- a Python rules engine pretending to make semantic decisions;
- a security/audit platform inside the geometry Core.

Traditional retrieval systems remain useful baselines. They are not the intended correctness path of Nollm.

## Current status

The main branch now carries the V3.14 native-memory-slot development baseline together with the earlier validated Core, Access, Snapshot, Trace, and Unified Field Encounter work.

The implementation should be read as a **capability baseline**, not as a sealed architecture or a claim that general memory quality has been solved.

In particular:

- the geometry and module boundaries remain evolvable;
- the native OpenClaw memory-slot package is on the main development line;
- public ClawHub one-command release still requires its platform/runtime and release-validation gates;
- History and Audit remain non-core and paused;
- legacy GRF code is compatibility / research material, not the active runtime design.

The canonical project pointer is [`docs/project/ACTIVE_PROJECT.md`](docs/project/ACTIVE_PROJECT.md). Historical documents are evidence of how the architecture evolved, not instructions to restore superseded designs.

## Validation

Typical package and governance checks:

```powershell
python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests
python -m pytest -q integrations/openclaw/formation-loop/tests
python -m pytest -q reference/python/tests/m0
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_active_tree_assets.py
```

Native memory-slot package checks live under:

```text
integrations/openclaw/nollm-memory-provider
```

## Design rule of thumb

Before adding a new subsystem, ask:

```text
Does it preserve original evidence?
Does the relationship come from geometry or from another index?
Would deleting this cache change correctness?
Is the LLM still making the semantic decision?
Is Core still deterministic and semantic-blind?
Can the same result be achieved with fewer components?
```

If the answer moves Nollm toward a second semantic database, the design should be reconsidered.

## License

MIT.
