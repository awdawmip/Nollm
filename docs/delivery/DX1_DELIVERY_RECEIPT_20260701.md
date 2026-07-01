# DX1 Delivery Receipt - Synthetic Memory Cycle Validation

Date: 2026-07-01

Branch: `feature/dx1-end-to-end-synthetic-memory-cycle-validation`

Base sealed commit: `76a4d1ba8b97043ea2c673ca64ab6f816be18a12`

## Scope

DX1 validates one synthetic end-to-end memory cycle across sealed public module
APIs:

- DE1 synthetic Evidence store writes and public reads;
- DC1 Growth Proposal and Query Probe compilation;
- DG1 directed coverage distributions;
- DG2 trace propagation, local covers, and gravity snapshot calculation;
- DR1 finite RecallUniverse validation and recall resolution;
- DI1 public IntegrationShell recall envelope.

## Boundary

DX1 is validation-only. It does not modify sealed production Geometry, Field,
Evidence, Cortex, Recall, or Adapter implementation modules.

DX1 does not add NLP, embeddings, semantic search, anchor retrieval, LLM calls,
OpenClaw, runtime, CLI, network, database, cache, session, real memory, or
global window admission.

DX1 does not expose Gravity, score, mass, chart, cell, cover, trace, kernel,
route, path, filesystem, store root, or private provenance internals in the
public DI1 envelope.

## Validation Artifacts

- `reference/python/nollm/dream_geometry/validation/dx1_synthetic_cycle_fixture.py`
- `reference/python/nollm/dream_geometry/validation/dx1_synthetic_cycle_report.py`
- `reference/python/tests/test_dx1_synthetic_memory_cycle.py`
- `reference/python/tests/test_dx1_synthetic_memory_cycle_boundaries.py`
- `reference/python/tests/test_dx1_synthetic_memory_cycle_determinism.py`
- `protocol/v2/DX1_SYNTHETIC_MEMORY_CYCLE_CONTRACT.md`
- `docs/validation/DX1_SYNTHETIC_MEMORY_CYCLE_BASELINE_REPORT.md`

## Scenario Coverage

- S01: complete synthetic cycle resolves exactly one primary target.
- S02: missing relative-time runtime resolution defers without evidence.
- S03: exact mismatch does not recall the target.
- S04: retired usage state is context-only.
- S05: public envelope hides internal geometry and private provenance.
- S06: same input rerun is deterministic and persists no recall output.
- S07: input permutation leaves the public mapping unchanged.

## Verification

The final command transcript and bundle verification are recorded in the Codex
turn that produced this receipt.

DX1 stops here. No DX1.x work is opened by this receipt.
