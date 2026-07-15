# CAOLD Bounded Approximate Coverage And Lazy Surface Report

**Date**: 2026-07-15
**Status**: `VALIDATED`
**Branch**: `codex/caold-bounded-approximate-coverage-lazy-surface`

## Delivery Identity

```text
input bundle: nollm_caold_translation_normalized_coverage_physical_entry_p1_20260715_871f7820.bundle
input bundle SHA-256: a56917dfb8fd84bdef97f0407a1304a6f578fb78238dc0c7e5710e7635591596
input HEAD: 871f78203a7ef05584abf893ea0059640c7e2829
implementation HEAD before final governance/report commit: f4be146
final output HEAD: supplied by the immutable completion tag and bundle heads
final bundle SHA-256: supplied by the post-commit external delivery receipt
```

The execution pack's `SHA256SUMS.txt` verified all 11 non-self files after
mapping its Linux paths to the extracted Windows directory. Its self-entry is
incorrect: expected `7031d3...18b6`, actual
`d9e06fcd900edba31272a1e3b35263c00fbcebd8e711384053cefa6a3e1f3fae`.
This input defect did not affect the verified taskbook or overlay files.

A tracked report cannot contain the SHA-256 of a bundle that contains the
commit containing that same report. The final response is the external
delivery receipt for the immutable output HEAD, tag, bundle verification, and
bundle SHA-256.

## Scope And Progress

Expected and actual vector are identical:

```text
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +10% | DISTRIBUTIONS +5%
```

No Stitch, multi-layer semantic Placement, persistent Surface cache, PB run,
multi-Chart support, signed-64 closure, relation index, vector, graph,
embedding, Cursor, or multi-entry action was added.

## Coverage Method

The production path uses equal-area microtriangle centroids, precomputed
Q24.40 transforms, deterministic integer cube rounding, hit counts, relation
threshold pruning, and exact Q16 normalization. The selected method is K=96
(`m=4`). K=54 (`m=3`) was measured first and rejected because its p95 total
variation exceeded the 0.05 gate.

| Metric | K=54 | K=96 | Gate |
|---|---:|---:|---:|
| missed mass p99 | 0.018291 | 0.016413 | <= 0.02 |
| false mass p99 | 0 | 0 | <= 0.02 |
| total variation p95 | 0.070671 | 0.042893 | <= 0.05 |
| dominant agreement | 1.0 | 1.0 | >= 0.95 |
| max fanout | 7 | 7 | <= 8 |
| Q16 partition error | - | 0 | 0 |

The independent prototype and production implementation matched on all 96
fixtures. Production mean cell time was 0.451 ms, p95 0.745 ms, and maximum
1.554 ms. Calibration evidence:

```text
C:\Users\chaos\nollm_v39_gate1\bounded_coverage_calibration.json
SHA-256: 6647a88fe8a3ad885f9c819e82a9161d70dc9639b745c137ee8add9ef4ed9596
```

The active domain is `default_dream_v1`, `chart_id=default`, `phase=null`,
physical layers -64..64, and hex radius <= 2^31-1. Construction rejects
addresses outside this domain.

## Production Dependency Scan

The active Core/Access path has no Decimal import, dynamic polygon operation,
dynamic sin/cos, `select_entries`, or Cursor API. Scan-only matches are the
`runtime_polygon` profile capability flag (false for the active profile), a
legacy compiled-template method identifier, and a `cursor-free` docstring.
OpenClaw has zero direct `nollm_core` imports.

The historical exact polygon implementation remains available only as the
Lab/Oracle comparison path; it is not called by production Coverage or Surface.

## Lazy Surface

Surface orders are built incrementally from order 0 and stop at the first
budget-compatible order. Runtime and bounded derived LRU caches reuse canonical
prefixes; mutation/import and explicit cache clearing invalidate them.

| Fixture | Cold begin/page | Warm continuation | Selected order | Ceiling |
|---|---:|---:|---:|---:|
| 11 cells | 27.829 ms | 12.749 ms | 0 | 5000 ms |
| 217 cells | 823.615 ms | 94.673 ms | 8, overflow | 15000 ms |

The 11-cell and 217-cell targets and ceilings passed. Direct quadrature met the
budget, so no residue atlas was implemented. Benchmark evidence:

```text
C:\Users\chaos\nollm_v39_gate3\lazy_surface_benchmark.json
SHA-256: f46d6390fe7ddb9aac75fe1c285be6e48e2c8215fc004ec0ee8afbcca87a910f
```

Focused tests prove order-0 early stop, prefix continuation without rebuild,
explicit cache-clear rebuild identity, mutation invalidation, and both runtime
ceilings.

## Plugin And Data

OpenClaw `2026.6.11`, Node `24.17.0`, and inherited
`meituan/LongCat-2.0` were used. The loaded plugin is version `0.10.0` from
this worktree and declares the V3.9 geometry, coordinate, residual, and Surface
Wire contracts.

The accepted V3.8 workspace could not be opened under the V3.9 registry. It
was preserved and migrated non-destructively to:

```text
C:\Users\Administrator\.openclaw\memory\nollm-v39-bounded-approximate-v1-migrated
mapping: physical addresses unchanged; geometry registry v5 -> v6
cells=12 atoms=14 bindings=14 statement_files=26 bridges=0
Statement tree SHA-256 before/after: 584daeb012e4185c83eed5e640ef4f4539ef89f93572cf08e0d392edd8ff4c4f
HandleBinding SHA-256 before/after: d0c3477bfd5d80f0db410445ddbf20960e601872f7aac1b9427d39dd2c3b476b
migration receipt SHA-256: 9c3860686d7715a44f3c4230990e3bda9192a54f4d1a96839e89c3644ffddb5b
```

The source workspace remains unchanged. The migration tool accepts only the
exact V3.8 registry identity, writes through a temporary directory, reopens
with current public Core/Access APIs, verifies canonical bytes, and atomically
publishes a new target.

## Real Memory Loop

The first R1 attempt is truthfully retained as
`recall_surface_terminal/invalid_input`; it exposed the V3.8 registry mismatch
and injected no memory. After non-destructive migration:

| Gate | Result |
|---|---|
| R1 Alpha | initial Order 0; entry `layer=0,q=-1,r=1`; four current Alpha statements; hidden injection; correct answer |
| R2 Office | initial Order 0; different entry `layer=0,q=7,r=0`; visitor/cafe statements; no Alpha in answer |
| R3 NONE | initial Order 0; `completed_none`; no entry or injection; main agent answered Jupiter |
| P1 | formed `dream:91b6c8...280dc`; one explicit physical entry; `revision_current`; `core_write_count=1` |
| Restart Recall | replacement Gateway healthy; new session selected only P1 statement; answer `BX-3917` |

P1 timing:

```text
formation_ms=43156
statement_persist_ms=2
surface_build_ms=2775
surface_order_count=1
surface_projection_count=11
surface_page_count=2
placement_prompt_build_ms=809
placement_subagent_ms=127153
physical_entry_resolution_ms=400
decision_validation_ms=14
placement_apply_ms=12
handle_bind_ms=1
total_operation_ms=133767
timeout_stage=null
```

The live 11-cell Surface build met the 5-second hard ceiling, though not the
1-second target due to process/open overhead. Geometry is no longer a
multi-minute stage and is significantly below model latency.

The 76-line external live evidence is frozen at:

```text
C:\Users\chaos\nollm_v39_openclaw_live_20260715.jsonl
SHA-256: 613c99d916889c9cccdfaee0b88b13daef2d9210a4458991745e0d41610a2b97
```

It retains failed attempts, successful R1/R2/R3/P1, hidden-injection counts,
one unrelated background Placement failure, and all terminal subagent events;
no evidence was overwritten.

## Regression And Governance

| Gate | Result |
|---|---:|
| Core | 62 passed |
| Snapshot | 7 passed |
| Trace | 3 passed |
| Access | 82 passed, 8 deprecation warnings |
| OpenClaw Python | 37 passed |
| M0 governance | 45 passed |
| OpenClaw Node | 19 passed |
| OpenClaw plugin check | passed |
| migration + memory-loop focus | 11 passed |
| ownership manifest | tracked 1835, rows 1835, unclassified 0 |
| module boundaries | production 0, cycles 0, migration findings 7 |
| `git diff --check` | passed |

The candidate worktree uses explicit package-minimal `PYTHONPATH` values. A
system editable `nollm_reference` points at another checkout; the M0 gate put
this candidate's `reference/python` first and passed all 45 tests without
modifying the global installation.

## Known Limitations

```text
The active coordinate domain is bounded to 2^31-1 hex radius.
Only default chart, null phase, and layer-0 semantic Placement are active.
K=96 is calibrated on the bounded 96-fixture matrix, not all-plane exact support.
217-cell overflow remains truthful at Order 8 within the hard runtime ceiling.
The live 11-cell build passed the ceiling but missed the 1-second target.
Provider/model latency remains tens to hundreds of seconds.
Gateway restart CLI timed out while the scheduled service restarted successfully.
OpenClaw reports pre-existing shared SQLite/config-health migration warnings.
Cross-platform portability was not validated in this Windows-first stage.
```

V3.9 closes only bounded approximate Coverage, lazy Surface, and the retained
single-entry R1/R2/R3/P1 loop. Follow-on capability requires a new taskbook.
