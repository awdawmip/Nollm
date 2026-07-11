# Core / Snapshot / Trace / Access / Lab / Distributions Baseline Truth Report

## Scope And Vector

Every Gate began and ended with:

```text
CORE +3% | SNAPSHOT +2% | TRACE 0% | ACCESS +2% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +2% | DISTRIBUTIONS +2%
```

The actual vector equals the expected vector. All deviations are zero; no
additional module was affected and no recovery cost was incurred.

## Results

- Active basis: V3.0 project book, current task, status, and ledger are reachable from `ACTIVE_PROJECT.md`; V2.2 is marked `LEGACY_REFERENCE / SUPERSEDED`; root `AGENTS.md` is generic and concise.
- Core/Lab: research Profile metadata is Lab-owned; Core exposes only `available_profile_ids()` and `runtime_profile()`; accepted registry identity remains compatible; artifact SHA-256 `21659434328e457e0d868ddc1dcbf64484739ffeb64eb61eb62197616ddf0eba` is checked at runtime; parity is 9/9.
- Snapshot: immutable `SnapshotDiff` reports equality, both digests/sizes, and finite changed top-level Core sections; non-Core bytes use the explicit `bytes` section.
- Access: `HandleBinding` requires exact canonical types; new, revision-current, revision-keep-history, forget, and reuse Store failures preserve prior Core/binding bytes; two runtimes share the trusted composition lock.
- Trace: Null/Memory/Failing/JSONL/Metrics/Composite/Inspector regressions pass; Trace remains absent from Core state and Core does not import `nollm_trace`.
- Distributions: Bare is Core-only; Minimal composes Core, Snapshot, Access, both file stores, `SnapshotService`, and `trace=None`; Debug extends Minimal with Trace and development-only Lab tools.

## Verification

```text
Core = 39 passed
Snapshot = 7 passed
Trace = 3 passed
Access = 32 passed
M0 = 24 passed
architecture / forbidden / hygiene = 8 passed
GRF = 112 passed
geometry parity = 9 / 9
Core capability validation = 25 / 25
Minimal E2E = passed
ownership manifest = 1470 / 1470; unclassified = 0
production violations = 0
production cycles = []
migration findings = 7
```

Validated code commit:
`a1c0b676c794ec7ca2bf20408cdf897bf2793c09`.

Validated code tree digest:
`c1f1fc3b9e491f96ab858eaea6ac63ccec75666e43a725f2425f61928929a041`.

```text
CAPABILITY_VALIDATED_AT_a1c0b676c794ec7ca2bf20408cdf897bf2793c09
```

The final bundle HEAD is the active baseline only after bundle replay succeeds.
This report does not claim sealing, final closure, or automatic entry to a later stage.

## Known Limitations

This task did not validate malicious Python isolation, direct file tampering,
cross-process locking, crash recovery, OpenClaw Live, real LLM placement,
memory quality, long corpora, PB scale, History/Audit products, installers, or
remote repository splitting.
