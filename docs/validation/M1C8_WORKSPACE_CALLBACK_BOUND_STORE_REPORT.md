# M1C8 Workspace Callback And Bound Store Report

## Ownership And Coordination

The canonical Access/Core pair coordinator owns pair identity, a shared transaction RLock, pair refcount, per-thread callback depth/kind, compatible HandleStore configuration, bound Store identities, and one live writer capability. Same-pair AccessRuntime instances share this coordinator. Evidence has a separate workspace lock for capture-only file persistence.

Access callback order is pair callback fence, Core client/transaction callback fence, callback invocation, then exact reverse cleanup in `finally`. Public Access entry first checks the pair fence and Core client-operation guard before lifecycle state or active count changes. Cross-instance capture, apply, recall, saved_handle, close, and constructor attacks therefore reject while the target remains unchanged; rejected close remains `OPEN`.

Core client callbacks now run the same lifecycle-reentry check as Trace, Store, transaction, and consistent-read callbacks before lease validation or active-count increment. Same-lease recursion, different-lease recursion, and transaction-callback-to-client-callback all reject, return no hidden success, and leave callback/activity counts at zero.

## Bound Store Capability

`FileHandleStore` read operations remain public. `put`, `revise_current`, `remove_handle`, and `import_state` require the exact active pair-owned writer capability. Missing, foreign, forged, and expired identities reject. Access rollback uses the same capability. The last pair client unbinds all compatible Store objects and expires the capability.

HandleStore canonical workspace/path and constructor hook are immutable after binding. Same-pair Store objects require identical canonical path and immutable hook configuration. Runtime binding freezes fault injection; tests and Lab use constructor-time armed hooks.

`FileCoreStateStore` captures private workspace/path at construction. Core captures canonical `state_path` once, validates an injected Store workspace, claims ownership using that path, and freezes Store hook/validator/callback-runner/owner capability at bind. Retained Store and Trace redirect attempts reject; redirected files are not created and canonical disk, Runtime, and Snapshot bytes agree.

## Runtime Configuration

Access stores Core, EvidenceStore, HandleStore, canonical Access root, and canonical Core state path in private fields with read-only properties. Reassignment attempts reject and later apply still targets the original Core. Default EvidenceStore workspace/root and HandleStore workspace/path are also read-only.

Lock order remains Access lifecycle check, canonical pair transaction lock, Core client/transaction lifecycle, then Core state lock. Core paths never acquire Access locks. Callback checks happen before state transitions or Store access.

## Gate A-G

- Gate A: pair-scoped callback fence covers two independent AccessRuntime instances and constructor entry; normal and exceptional cleanup passed.
- Gate B: recursive same/different Core client callbacks and transaction-to-client callback reject with zero success/count leakage; cross-Access close stays OPEN.
- Gate C: all HandleStore mutations require the live pair capability; direct, foreign, forged, expired, callback, and import bypasses reject with unchanged bytes.
- Gate D: Access dependencies and canonical identities are read-only; retained Store and Trace rebinding/configuration attacks do not redirect future work.
- Gate E: Core Store workspace/path and Runtime state path are stable; retained/Trace/Store callback redirection rejects and no alternate file is created.
- Gate F: Core, Snapshot, Trace, Access, M0, architecture, GRF, canonical Recall, nine-template parity, and zero-boundary regressions are rerun in the final gate.
- Gate G: minimal E2E and the bounded adversarial matrix emit facts from actual attacks, including callback cleanup, disk/Runtime/Snapshot equality, 9/9 templates, and zero cycles.

## Verification Status

Verified facts are the behaviors asserted by package tests, E2E, adversarial matrix, ownership scanner, and final regression commands. The design assumes callbacks execute in-process and Python object identity remains the capability boundary. Cross-process locking, crash recovery, third-party callback sandboxing, distributed transactions, M2/M3, OpenClaw Live, model/corpus execution, PB scale, database, graph/vector/embedding, and remote GitHub work were not validated and remain out of scope.

## Final Gate Results

```text
ownership manifest = 1453 / 1453, unclassified 0
production violations = 0
production cycles = 0
nollm-core = 56 passed
nollm-snapshot = 5 passed
nollm-trace = 1 passed
nollm-access = 51 passed
M0 = 18 passed
architecture / forbidden / hygiene = 8 passed
GRF Windows regression = 112 passed
geometry parity = 9 / 9
M1-C8 minimal E2E = passed
public API adversarial matrix = passed
compileall = passed
```

`zstandard` was available, so the complete GRF suite ran with no exclusions. Bundle identity is reported after the immutable final commit is created.
