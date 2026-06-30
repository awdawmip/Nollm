# V2 Module Dependency Rules

The only allowed production dependency direction uses this convention:

```text
A -> B means module A is allowed to import module B in Python source.
```

Allowed edges:

```text
evidence -> protocol
geometry -> protocol
cortex -> protocol, evidence
field -> protocol, evidence, geometry
recall -> protocol, evidence, geometry, field, cortex
adapters -> protocol, evidence, cortex, recall
validation -> protocol, evidence, geometry, field, cortex, recall, adapters
```

Protocol is the foundation/service layer, so production modules import protocol contracts. The arrows above are import edges, not visual foundation arrows.

Forbidden edges include:

- `geometry -> cortex`
- `geometry -> recall`
- `geometry -> adapters`
- `geometry -> OpenClaw`
- `field -> adapters`
- `field -> OpenClaw`
- `evidence -> geometry`
- `cortex -> field`
- `adapters -> geometry internals`
- V1/OpenClaw runtime -> V2 during DG0
- V2 -> V1 runtime/OpenClaw during DG0

The executable source of truth for these rules is `nollm.dream_geometry.protocol.dependency_rules`.

DG2 active implementation subset:

```text
field -> protocol, geometry
validation/dg2 -> protocol, geometry, field
```

Field may carry opaque evidence reference strings supplied by callers, but DG2
Field code must not import the evidence implementation, read Evidence, write
Evidence, or depend on adapters, OpenClaw, runtime, V1 modules, or validation.

DE1 active implementation subset:

```text
evidence -> protocol
validation/de1 -> protocol, evidence
```

Evidence may use Python standard-library file and JSON helpers for its
file-first store. Evidence must not import geometry, field, cortex, recall,
adapters, V1 modules, OpenClaw, runtime, databases, or vector search.

DC1 active implementation subset:

```text
cortex -> protocol, evidence
validation/dc1 -> protocol, evidence, cortex
```

Cortex may use the DE1 public read surface to resolve DreamShard subjects and
exact text-span support. Cortex must not write Evidence, Ledger, Geometry,
Field, Recall, Adapter, V1, OpenClaw, runtime, database, network, or subprocess
state.
