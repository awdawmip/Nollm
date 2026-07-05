# TQ1 Delivery Receipt

Delivered:

- `reference/python/scripts/run_nollm_test_matrix.py` with `plan`, `run-shard`, `list-shards`, `verify`, and `cleanup`.
- Deterministic pytest collection manifest and shard assignment.
- External JSON receipts, JUnit XML, stdout/stderr tails, timeout receipts, and resume validation.
- Per-shard detached git worktree execution.
- Clean-source plan rejection before collection or receipt-root creation.
- Plan-owned ignored `out/nollm_runtime` snapshot manifests and fingerprints.
- Runtime fixture copy from the frozen receipt-root snapshot, not live source `out`.
- Matrix-owned worktree root markers and non-destructive handling of pre-existing worktrees.
- Structured failure receipts for worktree existence, worktree add failure, pytest failure, timeout, and cleanup state.
- `tools/run_nollm_test_matrix.ps1` with defaults under `C:\Users\chaos`.
- Documentation for the complete matrix gate and delivery bundle directory convention.

Not delivered:

- Production Nollm module changes.
- OpenClaw, runtime, network, LLM/NLP, embedding, cache, database, daemon, global discovery, or automatic admission integration.
- Replacement of `run_tests.py`; it remains a legacy single-process diagnostic command.
- Any tracked source byte mirroring into detached shard worktrees.
- Deletion of pre-existing or non-owned worktrees.

Future Nollm delivery bundles must be written outside the repository at:

```text
C:\Users\chaos\<bundle-name>.bundle
```
