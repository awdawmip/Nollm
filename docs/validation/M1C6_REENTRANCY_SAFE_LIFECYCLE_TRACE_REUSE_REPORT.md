# M1C6 Reentrancy-Safe Lifecycle, Trace Isolation, and Reuse Report

## State Machines

Core is `OPEN` while its workspace owner is claimed. Every public operation enters the Runtime RLock and increments a thread-local operation depth. A transaction lease is an operation with the same lifecycle accounting. Cross-thread close waits for the lock; same-thread close observes nonzero operation/Trace depth and raises without changing state or releasing the owner. Successful close transitions directly to `CLOSED` while holding the lock. Exception cleanup decrements depth in `finally` blocks.

Access is `OPEN` while its canonical `(Access root, Core state path)` pair lease is held. Public capture/apply/recall/saved_handle operations increment thread-local Access operation depth under the pair RLock. Same-thread close during an operation or Binding callback raises; cross-thread close waits. Construction acquires a provisional pair first, then a Core transaction lease and validates OPEN. Failure releases the provisional pair before propagating.

## Lock Order And Linearization

The uniform Access lock order is Access pair coordinator, then Core transaction/lifecycle lease. There is no Access path that first holds a Core lease and then acquires a pair. Core-only operations acquire only the Core lock.

Reuse linearizes at the Binding file replacement while the Core transaction lease is still held. Handle validation and Binding commit are in one Core lease, so direct remove cannot interleave between them. A later remove may invalidate a previously committed binding, but a Handle already absent before commit cannot be successfully bound.

## Trace Isolation

All Core events use `CoreRuntime._emit_trace`. It increments Trace callback depth around failure-isolated sink delivery. Any callback attempt to enter Core mutation, Recall, Snapshot lifecycle, restore, transaction lease, or close rejects. The workspace owner remains claimed, so a callback cannot open a replacement Runtime. Null, failing, and reentrant sinks preserve the outer result and canonical state bytes.

## Gate Results

- Gate A: explicit Core operation/transaction depth; same-thread close rejected; cross-thread close waits; owner survives until operation exit.
- Gate B: batch, Recall, Snapshot freeze/release, operation events, and rollback events use the guarded Runtime emitter; Trace is observation-only.
- Gate C: Access operation depth and atomic constructor close the check/acquire race; provisional pair cleanup is tested.
- Gate D: reuse holds the Core lease through Binding commit; Binding callback cannot close or cross-root rebind; rollback cannot delete a returned write from another owner.
- Gate E: canonical Recall, Store capability, Cell encapsulation, Snapshot bytes, nine kernels, compiler metadata, Evidence, and package boundaries remain intact.
- Gate F: deterministic package tests, E2E, and the public adversarial matrix emit actual lifecycle, reentry, pair, rollback, and reuse facts with bounded Event timeouts.

## Verification Classification

Verified facts are the command results and structured E2E/matrix facts in this report. The same-process RLock/thread-local model is an intentional stage constraint. No claim is made for cross-process locking or process-crash recovery. No unresolved M1-C6 correctness item remains after the Final Gate. M2, OpenClaw Live, model calls, corpora, PB scale, databases, History/Audit productization, and remote GitHub work were not started.

## Final Gate Results

```text
ownership manifest = 1440 / 1440, unclassified 0
production violations = 0
production cycles = 0
nollm-core = 44 passed
nollm-snapshot = 5 passed
nollm-trace = 1 passed
nollm-access = 39 passed
M0 = 18 passed
architecture / forbidden / hygiene = 8 passed
GRF Windows regression = 112 passed
geometry parity = 9 / 9
M1-C6 E2E = passed
public API adversarial matrix = passed
compileall = passed
```

`zstandard` was available, so the complete GRF suite ran with no exclusions. Bundle identity is recorded in the final delivery after commit.
