# BA1 Batch Admission Coordinator Baseline Report

- baseline_head: `1f5a66dcd639f944b1aa522a0e8ddb7a0ef3edec`
- validation_head: `40f3c91f204d15ec22a6390c186e9d337719897d`
- command: `python validation/ba1/run_ba1_batch_admission.py --output docs/validation/BA1_BATCH_ADMISSION_BASELINE_REPORT.md`
- public_objects_used: `BatchAdmissionCoordinator`, `CaptureStateStore`, `MemorySubstrateStore`, `MemoryAdmissionOrchestrator`
- formal_paths_called_by_BA1: `DA1 preflight`, `DA1 admit`

## Evidence

- ba1_01_two_deferred_candidates: `pass`
- ba1_02_canonical_order: `pass`
- ba1_03_preflight_zero_commit: `pass`
- ba1_04_retry_reopen: `pass`
- ba1_05_commit_interruption_recovery: `pass`
- ba1_06_candidate_state_isolation: `pass`
- ba1_07_dependency_boundary: `pass`
- ba1_c1_duplicate_decision_identity: `pass`
- ba1_c1_duplicate_compiled_proposal_identity: `pass`
- ba1_c1_duplicate_placement_plan_identity: `pass`
- ba1_c1_lower_preflight_normalization: `pass`

## Acceptance Matrix

- BA1-01 independent deferred admission: `pass`
- BA1-02 input order determinism: `pass`
- BA1-03 all-member preflight rejects before DA1 commit: `pass`
- BA1-04 reopen retry via DA1 idempotency: `pass`
- BA1-05 commit interruption reports completed members: `pass`
- BA1-06 no candidate mutation or evidence crossing: `pass`
- BA1-07 no direct forbidden dependencies or discovery: `pass`
- BA1-C1 duplicate promotion decision identity rejects before commit: `pass`
- BA1-C1 duplicate compiled proposal identity rejects before commit: `pass`
- BA1-C1 duplicate placement plan identity rejects before commit: `pass`
- BA1-C1 lower-layer preflight rejection normalization: `pass`

## Known Non-Goals

BA1 does not select candidates, generate PromotionDecision values, generate GrowthProposal or PlacementPlan values, mutate CI1 candidate state, persist batch state, assemble FieldSnapshots, execute recall, scan global stores, run OpenClaw/CLI/runtime, use network/database/cache, or call LLM/NLP/embedding systems.
