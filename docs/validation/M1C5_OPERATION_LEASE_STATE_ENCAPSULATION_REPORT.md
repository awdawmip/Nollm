# M1C5 Operation Lease, State Encapsulation, and Canonical Recall Report

## Input

Input HEAD `2142eba63c0e65c5fce0a097affdf3733a2a81ed`; bundle SHA-256 `cbce4fb42bd3118deb1083d814d6265f9156a73e38c5987fb746ffe66a1eb9b2`; branch `codex/m1c4-single-owner-kernel-public-contract-final-closure`; clean worktree. External Linux audit: 109 passed, 1 skipped; exactly two zstandard-dependent historical tests unavailable.

## Lifecycle State Machines

Core is OPEN until close acquires the same RLock used by mutation, Recall, state reads, restore, Snapshot and transaction leases. Close waits for another thread's active operation, rejects an active same-thread consistent-read token, enters CLOSED, then releases the workspace owner. CLOSED rejects public reads and writes. A Core transaction lease holds the Core lock across Access snapshot, Core action, Binding action and both rollback attempts.

Access operations acquire the canonical pair RLock before checking OPEN and retain it through capture/apply/recall/saved_handle. Close acquires that same lock before releasing its pair lease. Multiple identical pairs share one lock; a different Access root cannot bind until the last active lease closes. Access construction rejects a closed Core.

## Gate Results

- Gate A: blocked mutation prevents close/owner release; consistent-read same-thread mutation rejects; Recall and transaction lease serialize direct mutation.
- Gate B: failed Access transaction cannot erase a direct Core success; close cannot release a pair during an active operation.
- Gate C: Store write requires Runtime capability; validator cannot be publicly rebound; live CellStore is not exposed; occupied_cells works and rejects CLOSED.
- Gate D: Recall cells/handles/kernels are exact, sorted and unique; unknown kernels reject; mapping performs no silent dedupe. Compiler flags are exact canonical strings and dream_quasi residual is exactly Q16_ONE/16.
- Gate E: reentrant Trace mutation rejects while outer result remains stable; Snapshot bytes equal disk/runtime bytes after close/reopen.
- Gate F: deterministic E2E and public API adversarial matrix emit structured facts from actual operations.

## Concurrency Sequences

Deterministic Event-based tests block Core file replacement or Binding replacement. Close and direct mutation remain blocked behind the owning lease. Only after the old operation commits or rolls back can close release or a new operation proceed. Therefore no successful operation is later removed by an older rollback or owner.

## Validation Scope

Final Windows commands record package counts, M0/architecture/GRF regressions, 9/9 full geometry parity, manifest, boundary, E2E, adversarial matrix, compileall, diff and clean status. Guarantees are same-process only. Cross-process locking, process-crash recovery, databases, distributed transactions, PB scale, OpenClaw Live, model calls, corpora, and History/Audit products are explicitly out of scope.

```text
manifest = 1434 / 1434
nollm-core = 39 passed
nollm-snapshot = 5 passed
nollm-trace = 1 passed
nollm-access = 35 passed
M0 = 18 passed
architecture / forbidden / hygiene = 8 passed
GRF Windows regression = 112 passed
full geometry parity = 9 / 9 passed
production violations = 0
production cycles = 0
M1-C5 E2E = passed
public API adversarial matrix = passed
```

## M2 Gate

M1 public contracts are suitable as an M2 prerequisite only after the complete Final Gate and bundle verification recorded by this delivery. This report does not start M2 or claim placement quality.
