# M1C7 Callback Fence, Client Lease, And Token Report

## Core Lifecycle

Core has explicit `OPEN`, `CLOSING`, and `CLOSED` states guarded by a lifecycle Condition separate from the serialized state RLock. Public operation entry checks OPEN and increments the global active count before taking the state lock. Close rejects same-thread operation/callback entry, rejects while live client leases exist, atomically marks CLOSING, rejects subsequent work, waits for active operations, releases the workspace owner, then marks CLOSED.

Tracked facts include active public/transaction/consistent-read counts, per-thread activity, callback depth, Runtime generation, and live client lease identities. Exception cleanup decrements counts in `finally` and notifies close waiters.

## Core Capabilities

`CoreTransaction` is returned only by `CoreRuntime.transaction()`. It is bound to Runtime identity, generation, owner thread, active context, and a Runtime-issued token. Access uses facade operations for Core action, snapshot, and rollback. Public Core methods cannot reenter the transaction; callbacks cannot use the transaction capability; wrong-thread, foreign, and expired capabilities reject.

`CoreClientLease` is Runtime-issued and generation-bound. Access acquires one under the canonical pair lock and holds it until Access close. Core close with any live client rejects without changing OPEN. Foreign, forged, expired, and double release reject.

## Callback Fences

Trace and constructor-only Core Store hooks run under the Core callback fence. Runtime does not expose `store` or mutable `trace_sink`, and FileCoreStateStore freezes its hook when bound. Access wraps every Evidence/Binding call with both Access callback depth and either its Core client lease callback fence or active transaction callback fence. Nested Access apply/recall/saved_handle/close and direct Core reads/writes/recall/transaction/client operations reject before observing or changing intermediate state.

## Access Lifecycle And Lock Order

Access has explicit `OPEN`, `CLOSING`, and `CLOSED` under an independent lifecycle Condition. Entry increments active count before taking the canonical pair RLock. Close marks CLOSING before waiting, rejects new operations, waits active count zero, then follows pair -> Core client release -> pair release. Constructor follows provisional pair claim -> pair lock -> Core client lease -> OPEN commit, with complete pair/client cleanup on failure.

Uniform order is Access lifecycle/pair, then Core client/transaction lifecycle, then Core state lock. Core never acquires Access locks.

## Consistent Read Ownership

Each token binds Runtime identity, Runtime generation, creator thread, token identity, and active status. Wrong-thread and foreign export/end validate and reject before token, lock, or count mutation. The owner can still export, end, close, and reopen afterward. End invalidates the token before releasing its active count; repeated use rejects.

## Gate A-G Facts

- Gate A: real Core state machine, active counts, owner release linearization, and lifetime client leases.
- Gate B: Runtime/thread/generation-bound transaction facade, unified Core callback fence, private Store, frozen hook.
- Gate C: non-reentrant Access API and dual Evidence/Binding callback fence; nested writes and reads reject.
- Gate D: Access pair and Core client lease compose atomically across the complete Access lifetime.
- Gate E: owner-thread consistent-read tokens survive wrong-thread export/end attempts with zero state change.
- Gate F: Snapshot, Trace, Recall, reuse, canonical state/evidence, packages, and zero boundaries remain unchanged.
- Gate G: package tests, E2E, and adversarial matrix exercise all seven input blockers with Event timeouts and structured actual facts.

## Scope

Verified guarantees are same-process. Cross-process locking, crash recovery, distributed transactions, M2/M3, OpenClaw Live, models, corpora, PB scale, History/Audit productization, and remote GitHub work remain outside this stage.

## Final Gate Results

```text
ownership manifest = 1446 / 1446, unclassified 0
production violations = 0
production cycles = 0
nollm-core = 51 passed
nollm-snapshot = 5 passed
nollm-trace = 1 passed
nollm-access = 45 passed
M0 = 18 passed
architecture / forbidden / hygiene = 8 passed
GRF Windows regression = 112 passed
geometry parity = 9 / 9
M1-C7 E2E = passed
public API adversarial matrix = passed
compileall = passed
```

`zstandard` was available, so the complete GRF suite ran with no exclusions.
