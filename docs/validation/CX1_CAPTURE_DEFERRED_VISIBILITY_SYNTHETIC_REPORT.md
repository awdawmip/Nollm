# CX1 Capture / Deferred / Visibility Synthetic Validation Report

- baseline_head: `3e2d96afa8ff503614907c73c3d1aac56b028bd5`
- validation_head: `3e2d96afa8ff503614907c73c3d1aac56b028bd5`
- command: `python validation/cx1/run_cx1_synthetic_validation.py --output docs/validation/CX1_CAPTURE_DEFERRED_VISIBILITY_SYNTHETIC_REPORT.md`
- public_objects_used: `CaptureIngress`, `CapturePolicy`, `CaptureVisibility`, `CaptureStateStore`, `MemorySubstrateStore`
- formal_paths_used: `none`

## Evidence

- cx1_state_matrix: `pass`
- cx1_retry_reopen: `pass`
- cx1_local_failure_closure: `pass`
- cx1_visibility_read_only: `pass`
- cx1_formal_path_isolation: `pass`

## Acceptance Matrix

- CX1-01 ephemeral zero-write/current-turn boundary: `pass`
- CX1-02 captured/deferred/persistent_explicit visibility distinction: `pass`
- CX1-03 retry and reopen deterministic replay: `pass`
- CX1-04 local failure does not publish success receipt or public candidate: `pass`
- CX1-05 visibility is explicit, physical, and read-only: `pass`
- CX1-06 formal DA1/DF1/DR1/DI1 path isolation: `pass`

## Known Non-Goals

CX1 is synthetic validation only. It does not implement or invoke LLM/NLP, GrowthProposal, PlacementPlan, DA1 admission, geometry, field, DF1 assembly, recall, global discovery, runtime, OpenClaw, CLI, network, database, cache, or real memory integration.
