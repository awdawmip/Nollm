# Nollm V2 Module Boundaries DG0

Status: DG0 boundary scaffold. This document defines the parallel Dream Geometry V2 module map. It does not integrate V2 with V1 runtime, OpenClaw, memory providers, CLI commands, or real memory.

## Module Map

The V2 namespace is `nollm.dream_geometry`. It is parallel to existing V1 and D-series modules.

| Module | Allowed responsibility | Forbidden responsibility |
| --- | --- | --- |
| `protocol` | Stable object names, states, ownership, dependency rules, invariants. | Computing geometry, reading cards, writing memory, natural language understanding, runtime calls. |
| `evidence` | Dream Shard, source, trust, state, time, revision, ledger persistence protocol. | Entity classification, coverage, gravity, recall ranking. |
| `geometry` | Chart, hex, transform, overlap, `K_up` / `K_down`, cycle residual, anti-resonance metrics. | Natural language, OpenClaw, fact truth, real memory writes. |
| `field` | Growth Trace, Coarse Cover, internal gravity, compression, merge, split. | Growth Proposal generation, external gravity exposure, Evidence replacement. |
| `cortex` | Candidate Growth Proposal and Query Probe compilation. | Fact confirmation, direct placement, direct Field mutation, final recall. |
| `recall` | Probe propagation, evidence fallback, state/time/revision filtering, Recall Digest. | LLM calls, Evidence writes, direct OpenClaw reads. |
| `adapters` | Thin CLI, JSON, OpenClaw, and receipt adaptation after core validation exists. | Defining math, bypassing ledger, recomputing geometry internals, runtime reverse dependency. |
| `validation` | Read-only fixtures, property tests, metrics, reports. | Production recall path, production state mutation. |

## Dependency DAG

```text
protocol
  -> evidence
  -> geometry
  -> cortex

evidence + geometry
  -> field

protocol + evidence + geometry + field + cortex
  -> recall

protocol + evidence + cortex + recall
  -> adapters

validation
  -> may read protocol, evidence, geometry, field, cortex, recall, adapters
```

Production modules must not import `validation`. V1 and OpenClaw runtime modules must not import `nollm.dream_geometry` during DG0. V2 must not import V1 runtime, OpenClaw, sidecar, native memory, subprocess runners, or legacy recall.

## Allowed Data Flow

```text
Dream Shard
  -> Cortex candidate Growth Proposal
  -> Core geometry validation in a Local Chart
  -> directed coverage kernels
  -> Field Trace / Cover / internal gravity
  -> Query Probe through the same geometry
  -> Recall Digest with exact Evidence fallback
  -> thin Adapter exposure
```

Evidence, Trace, and Cover are distinct objects. Evidence remains durable and auditable. Trace and Cover cannot replace raw evidence. Gravity is internal to Field/Core and is not an external selector.

## V1 Legacy And V2 Parallel Boundary

Existing V1 modules remain in place and keep their current behavior. DG0 does not move, delete, rename, or rewrite `reference/python/nollm/*.py` modules. Existing anchor-oriented fields are V1 legacy or migration-only material. They are not V2 external recall selectors.

V2 is not production recall. V2 is not OpenClaw runtime. V2 is not a memory provider. V2 is a boundary and protocol scaffold for later deterministic geometry work.

## Future Task Order

1. DG0: Module boundaries and constitution.
2. DG1: Pure Geometry Kernel and coverage-kernel validation.
3. DG2: Field Dynamics with traces, covers, and internal gravity.
4. DG3: Cortex compiler contracts and fixed fixtures.
5. DG4: Pure geometry Query Probe and Recall Resolver.
6. DG5: Compression, revision, anti-resonance, and scale experiments.
7. DG6: Isolated adapter integration.
8. DG7: Runtime positive verification after DG0-DG6 acceptance.

## Open Owner Decisions

- Exact DG1 geometry kernel parameter defaults remain unapproved until independent anti-resonance validation exists.
- The future migration shape for legacy anchor fields remains history/diagnostic only until a reviewed adapter task defines trace conversion.
- No runtime integration gate is open until DG0-DG6 have independent acceptance evidence.
