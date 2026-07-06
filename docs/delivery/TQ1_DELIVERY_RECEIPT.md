# TQ1 Delivery Receipt

Delivered:

- `reference/python/scripts/run_nollm_test_matrix.py` with `plan`, `run-shard`, `list-shards`, `verify`, and `cleanup`.
- Deterministic pytest collection manifest and shard assignment.
- External JSON receipts, JUnit XML, stdout/stderr tails, timeout receipts, and resume validation.
- Non-reusable receipt roots: `plan` refuses existing matrix evidence instead of overwriting it.
- Per-shard detached git worktree execution.
- Clean-source plan rejection before collection or receipt-root creation.
- Plan-owned ignored `out/nollm_runtime` snapshot manifests and fingerprints.
- Runtime fixture copy from the frozen receipt-root snapshot, not live source `out`, with copied-target fingerprint attestation before pytest starts.
- Matrix-owned worktree root markers, per-shard worktree ownership markers, and non-destructive handling of pre-existing worktrees.
- Failure-atomic cleanup: cleanup failure is recorded as a failed receipt and cannot be reported as passed.
- Structured failure receipts for worktree existence, worktree add failure, fixture copy failure, fixture target mismatch, pytest startup failure, pytest failure, malformed JUnit, timeout, and cleanup state.
- Successful receipts bind to the actual JUnit `<testcase>` proof count and reject malformed suite `tests` attributes.
- `tools/run_nollm_test_matrix.ps1` with defaults under `C:\Users\chaos`.
- Documentation for the complete matrix gate and delivery bundle directory convention.

Not delivered:

- Nollm Core/Cortex/Geometry/Admission/Recall production behavior changes. RCH1 only changed Engineering RC release artifact verification / archive tooling.
- OpenClaw, runtime, network, LLM/NLP, embedding, cache, database, daemon, global discovery, or automatic admission integration.
- Replacement of `run_tests.py`; it remains a legacy single-process diagnostic command.
- Any tracked source byte mirroring into detached shard worktrees.
- Deletion of pre-existing or non-owned worktrees.
- Git-bundled matrix receipts; final matrix evidence remains external under `C:\Users\chaos\nollm_test_runs`.

Future Nollm delivery bundles must be written outside the repository at:

```text
C:\Users\chaos\<bundle-name>.bundle
```
