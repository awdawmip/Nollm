# V3.11 Starting State

Date: 2026-07-17

## Input

- Bundle: `nollm_aold_durable_capture_async_absorption_20260717_4f8b1c4.bundle`
- Bundle SHA-256: `8336569247865e25db94d50b237e58926d77f8421b9b7efcab1753b93647d521`
- Branch: `codex/aold-durable-capture-async-absorption-fast-recall`
- HEAD: `4f8b1c479a2634d3c1b6ae8039116154864275aa`
- Tag: `AOLD_DURABLE_CAPTURE_ASYNC_ABSORPTION_IN_PROGRESS_AT_4f8b1c479a2634d3c1b6ae8039116154864275aa`
- Input status: `AOLD_DURABLE_CAPTURE_ASYNC_ABSORPTION_IN_PROGRESS`
- Input bundle is complete history; starting worktree was clean.

## Baseline Verification

- Ownership manifest: 1924 tracked, 0 unclassified, valid.
- Module boundaries: 0 production violations, 0 cycles.
- Python: Core 70, Snapshot 7, Trace 3, Access 95, OpenClaw 44, M0 45, Lab 14; 278 passed.
- Node dependency install was absent in the fresh clone; `npm ci` restored the lockfile-defined toolchain with 0 vulnerabilities.
- V3.9 geometry and V3.10 deterministic Capture/Pending/worker suites pass in the baseline.

## V3.10 Checkpoint Truth

The input is a checkpoint, not completed async absorption. Known gaps are cross-scope batching, duplicate Capture for one visible turn, non-continuous drain, terminal handling of temporary model unavailability, whole-batch provenance, whole-batch partial outcomes, missing batch revision handoff, and Pending short-circuiting admitted geometry Recall.

The existing Live evidence proves fast immutable Capture, Pending across Session/restart, one recovered three-Capture batch, and one durable Admission. Provider-backed admitted Recall and the complete crash matrix remain unvalidated.

## Missing Authority Correction

The input tree contains the V3.7 route but not the architecture authority named by the active task. Gate 0 restores a concise canonical V3.7 physical-field authority and adds the V3.11 amendment. No historical Cortex product path is reactivated.
