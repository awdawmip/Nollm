# CI1 Capture Ingress Baseline Report

- baseline_head: `e9437360eb93b8b80448b3671100bc5851a47ce9`
- validation_implementation_commit: `a30c657188bdea65e312d81340a7c18c4768399c`
- command: `python validation/ci1/run_ci1_baseline.py --output docs/validation/CI1_CAPTURE_INGRESS_BASELINE_REPORT.md`
- ci1_public_objects: `CaptureRequest`, `CapturePolicy`, `CaptureReceipt`, `DeferredAdmissionCandidate`, `CaptureVisibility`
- modes: `ephemeral`, `captured`, `persistent`; `none`, `minimal`, `replayable rejected`; `off`, `on_failure`, `verbose`
- default_capture_status: `captured`
- default_shard_id: `shard:ci1:641235bd11fb88d9f2dfc9a217bd7c00`
- default_write_counts: `{'ledger_events': 1, 'ci1_receipts': 0, 'ci1_candidates': 0, 'ci1_diagnostics': 0}`
- ephemeral_status: `ephemeral`
- ephemeral_tree_diff: `pass`
- ci1_1_ephemeral_scope_closure: `pass`
- ci1_1_full_receipt_idempotency: `pass`
- ci1_1_local_failure_candidate_invisibility: `pass`
- deferred_status: `deferred`
- deferred_candidate_id: `dac:d348a831351886217ba8ea0e4dbcee5c`
- session_window_ids: `('shard:ci1:641235bd11fb88d9f2dfc9a217bd7c00',)`
- source_window_ids: `('shard:ci1:042539edfda27a809369cbe43a228c99',)`
- unadmitted_isolation_import_graph: `pass`
- sealed_range_diff: `checked by delivery validation command`

## Acceptance Matrix

- C1-01 default lightweight capture: `pass`
- C1-02 ephemeral zero landing: `pass`
- C1-03 minimal deferred candidate: `pass`
- C1-04 replayable rejected: `pass`
- C1-05 diagnostics modes: `pass`
- C1-06 strict RFC3339: `pass`
- C1-07 idempotency and conflict: `pass`
- C1-08 physical visibility: `pass`
- C1-09 unadmitted isolation: `pass`
- C1-10 sealed range and hygiene: `checked by delivery validation command`
- C1-11 report regeneration: `pass`
- CI1.1-T01 ephemeral scope closure: `pass`
- CI1.1-T02 full receipt idempotency: `pass`
- CI1.1-T03 local failure candidate invisibility: `pass`

## Known Non-Goals

CI1 does not implement LLM/NLP, summaries, embeddings, semantic search, GrowthProposal, PlacementPlan, geometry, field, admission replay, DF1 assembly, recall, adapters, runtime, OpenClaw, CLI, network, database, cache, background workers, global discovery, automatic admission, or real memory integration.

CI1.1 does not claim global transaction, crash recovery, background cleanup, or DE1 rollback. It only ensures normal local CI1 commit failures do not publish a successful receipt or publicly readable deferred candidate.
