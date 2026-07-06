# TQ1 Delivery Receipt

Delivered:

- `reference/python/scripts/run_nollm_test_matrix.py` with `plan`, `run-shard`, `list-shards`, `verify`, and `cleanup`.
- Deterministic pytest collection manifest and shard assignment.
- External JSON receipts, JUnit XML, stdout/stderr tails, timeout receipts, and resume validation.
- Non-reusable receipt roots: `plan` refuses existing matrix evidence instead of overwriting it.
- Immutable execution contracts: final C7R plans bind `planned_shard_timeout_seconds=3600.0`, `retry_policy=forbidden`, `receipt_overwrite=forbidden`, and `execution_mode=single_pass`.
- Per-shard detached git worktree execution.
- Clean-source plan rejection before collection or receipt-root creation.
- Plan-owned ignored `out/nollm_runtime` snapshot manifests and fingerprints.
- Runtime fixture copy from the frozen receipt-root snapshot, not live source `out`, with copied-target fingerprint attestation before pytest starts.
- Matrix-owned worktree root markers, per-shard worktree ownership markers, and non-destructive handling of pre-existing worktrees.
- Failure-atomic cleanup: cleanup failure is recorded as a failed receipt and cannot be reported as passed.
- Structured failure receipts for worktree existence, worktree add failure, fixture copy failure, fixture target mismatch, pytest startup failure, pytest failure, malformed JUnit, timeout, and cleanup state.
- Successful receipts bind to the receipt schema, shard identity, execution contract, exact planned timeout, actual JUnit `<testcase>` proof count, raw JUnit relative path, raw JUnit SHA-256, raw JUnit size, and no-failure cleanup state, and reject malformed suite `tests` attributes.
- Verify proves that `receipts/` contains exactly the planned shard JSON files, rejects extra directories/files or missing receipts without deletion, and reports `receipt_json_count`.
- Verify proves that `junit/` contains exactly the planned shard XML files, reparses and hashes each raw JUnit file, rejects JUnit deletion/tampering/extra entries without deletion, and reports `junit_xml_count`.
- Verify treats a present `inputs/runtime_fixture_manifest.json` as frozen input evidence and rejects deletion, malformed JSON, non-regular paths, or manifest/snapshot mismatch.
- `package_nollm_tq1_delivery_evidence.py` builds and verifies the parentless TQ1-C7R Delivery Evidence Capsule ref for the single final bundle.
- Capsule `verify-ref` semantically replays the plan, root marker, receipt/JUnit inventory, runtime fixture bytes, final `--all` run log, verify log, summary, manifest, and payload inventory.
- `tools/run_nollm_test_matrix.ps1` with defaults under `C:\Users\chaos`.
- Documentation for the complete matrix gate and delivery bundle directory convention.

Not delivered:

- Nollm Core/Cortex/Geometry/Admission/Recall production behavior changes. RCH1 only changed Engineering RC release artifact verification / archive tooling.
- OpenClaw, runtime, network, LLM/NLP, embedding, cache, database, daemon, global discovery, or automatic admission integration.
- Replacement of `run_tests.py`; it remains a legacy single-process diagnostic command.
- Any tracked source byte mirroring into detached shard worktrees.
- Deletion of pre-existing or non-owned worktrees.
- A second evidence bundle, ZIP, TAR, or sidecar delivery directory. TQ1-C7R final delivery uses one complete-history Git bundle that contains both the code ref and the Delivery Evidence Capsule ref.

TQ1-C7R final delivery bundles must be written outside the repository at:

```text
C:\Users\chaos\nollm_tq1_c7r_canonical_evidence_one_hour_contract_final_closure_20260706_<short-head>.bundle
```
