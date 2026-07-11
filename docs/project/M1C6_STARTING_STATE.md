# M1C6 Starting State

## Input

- Bundle: `nollm_m1c5_operation_lease_state_encapsulation_canonical_recall_20260711_664c6c0a.bundle`
- SHA-256: `692ac7247fccb6a8ec4fa9d6b8189d66d1fc5e927ee36fa475b99c665b3db86c`
- Branch: `codex/m1c5-operation-lease-state-encapsulation-canonical-recall`
- HEAD: `664c6c0af1780cf14544a7d364302635623fec74`
- Input worktree: clean
- Clone: `git clone --branch codex/m1c5-operation-lease-state-encapsulation-canonical-recall <bundle> C:\Users\chaos\nollm_m1c6_work`
- Work branch: `codex/m1c6-reentrancy-safe-lifecycle-trace-isolation-reuse-consistency`

`Get-FileHash -Algorithm SHA256`, `git bundle verify`, and `git bundle list-heads` matched the values above. The bundle records complete history. `git fsck --no-reflogs --connectivity-only` exited 0; it listed only dangling delivery commits contained in the complete bundle.

## Accepted Input Gates

M1-C5 recorded Manifest 1434/1434, production violations 0, production cycles 0, Core 39, Snapshot 5, Trace 1, Access 35, M0 18, architecture/forbidden/hygiene 8, GRF Windows 112, geometry parity 9/9, E2E pass, and adversarial matrix pass. The input `M1C5_STARTING_STATE.md` was only three physical lines (`git show ... | Measure-Object -Line`), confirming the evidence-detail blocker. `zstandard_available=True` in this Windows environment.

## External Reproduction Against Input HEAD

The new M1-C6 tests were executed against the unmodified input package paths using explicit `PYTHONPATH=C:\Users\chaos\nollm\packages\...`.

```powershell
python -m pytest -q packages/nollm-core/tests/test_m1c6_reentrant_lifecycle.py
python -m pytest -q packages/nollm-access/tests/test_m1c6_reuse_and_lifecycle.py
```

Actual Core result: `4 failed in 0.38s`.

1. `core.recall.begin`: Trace `put(trace-added)` succeeded and the same Recall returned it.
2. `core.snapshot.release`: Trace mutation succeeded; sink rejection was false.
3. `core.batch.begin`: Trace `close()` succeeded; the old runtime became closed while the outer put continued.
4. `transaction_lease`: same-thread `close()` did not raise, so the owner could be replaced before lease exit.

Actual Access result: `3 failed in 0.34s`.

1. Binding callback `access.close()` did not raise; the old pair could be released from inside `_atomic()`.
2. During reuse, direct `core.remove()` completed while Binding commit was blocked (`removed.wait(0.1) == True`).
3. Constructor blocked after the old `is_open` check, Core closed, and construction still returned an AccessRuntime (`outcomes` was non-empty).

The Binding callback reproduction also attempted a different Access root after closing the old runtime, demonstrating the cross-root rollback path described by the taskbook. The test's injected failure then exercised rollback. These are same-process deterministic Event-based reproductions; no model, network, OpenClaw, corpus, database, or external relation index was used.

## Environment

Windows + PowerShell + Python for Windows + Git for Windows. Guarantees under test are same-process. Cross-process locks, crash recovery, M2/M3, live models, PB scale, and remote GitHub operations are outside M1-C6.
