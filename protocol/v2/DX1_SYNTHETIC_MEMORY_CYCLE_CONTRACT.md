# DX1 Synthetic Memory Cycle Contract

DX1 defines an end-to-end synthetic validation cycle over sealed V2 modules.
It is a validation artifact only.

DX1 may construct synthetic DE1 Evidence, compile synthetic DC1 Growth
Proposals and Query Probes, execute DG1/DG2 geometry and field primitives,
supply a finite DR1 RecallUniverse, and call DI1 to materialize the public
recall envelope.

DX1 must not add production behavior to Geometry, Field, Evidence, Cortex,
Recall, or Adapters.

## Required Chain

DX1 validation must use real public APIs:

- DE1 public store write/read APIs for synthetic DreamShard, Interpretation,
  Revision, and UsageState records;
- DC1 public compiler APIs for Growth Proposal and Query Probe objects;
- DG1 public local chart and directed coverage APIs;
- DG2 public trace propagation, local cover, and gravity snapshot APIs;
- DR1 public universe validation and recall resolver APIs;
- DI1 public IntegrationShell call surface.

The validation cycle must not construct sealed output objects to bypass the
module that owns them.

## Synthetic-Only Boundary

All DX1 memory material is synthetic and temporary. DX1 must not read, scan,
import, or mutate real memory, OpenClaw state, runtime state, sessions, caches,
databases, network resources, or global windows.

DX1 must not introduce NLP, embeddings, semantic search, anchor retrieval, LLM
calls, automatic universe construction, automatic context composition, or
runtime adapters.

## Public Output Boundary

DX1 validates that DI1 exposes only the Public Recall Envelope. Public output
must not expose Gravity, score, mass, chart, cell, cover, trace, kernel, route,
path, filesystem, store root, or private provenance internals.

DreamShard content selected by sealed DR1 may remain verbatim. Interpretation
and Revision records remain contextual and do not replace primary evidence.

## Required Scenarios

DX1 baseline validation covers:

- S01: complete synthetic memory cycle resolves exactly one primary target;
- S02: missing runtime relative-time resolution defers without evidence;
- S03: exact mismatch does not recall the target;
- S04: retired usage state is context-only, not active primary evidence;
- S05: public envelope hides internal geometry and private provenance;
- S06: same input rerun is deterministic and does not persist recall output;
- S07: input permutation does not change the public recall mapping.

## Validation Witness Closure

DX1 validation witness must compare sealed implementation paths across the
sealed baseline-to-current commit range, not only the local working tree.

S07 input-order validation must permute inputs before owner APIs compute their
derived artifacts, including coverage candidate target order and contextual
record tuple order. Reversing only already-computed output lists is not a
complete witness.

## Non-Goals

DX1 is not a runtime, CLI, OpenClaw adapter, memory provider, database, cache,
network service, benchmark harness, or production integration layer. It does
not open DX1.x work after the synthetic cycle is accepted.
