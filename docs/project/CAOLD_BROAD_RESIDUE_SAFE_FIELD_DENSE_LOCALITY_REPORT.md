# CAOLD Broad Residue, Safe Field, And Dense Locality Report

**Date**: 2026-07-15
**Input HEAD**: `5a453847747a7f460ce37df044dec50c554b494b`
**Status**: `IN_PROGRESS`

## Gate 0: Starting Truth

The input bundle SHA-256 is `e95f13582e79d24708d14189f1f2d23e7bb80e3126c3d3f9a492f47005f8225f`. The bundle has complete history, verifies successfully, exposes the expected input branch and HEAD, and includes tag `FAST_BOUNDED_APPROXIMATE_COVERAGE_SURFACE_VALIDATED_AT_5a453847747a7f460ce37df044dec50c554b494b`. The source and candidate worktrees started clean.

The repository's V3.7 authority uses the shorter tracked filename `NOLLM_ROUTE_BOOK_V3_7_ROTATED_PHYSICAL_FIELD_20260714.md`; the two longer V3.7 paths named by the taskbook are absent from the accepted input history. No replacement authority text was invented. The tracked V3.7 physical contract, V3.9 amendment, first principles, current taskbook, and module charters govern this work.

## Independent Audit Facts To Reproduce

| Diagnostic | Observed input-audit value |
|---|---:|
| broad fixtures | 512 |
| valid / boundary unsupported | 434 / 78 |
| missed mass p99 / max | 2.1371% / 4.0140% |
| TV p99 / max | 2.8102% / 4.0140% |
| false mass max / fanout max | 0 / 7 |
| 20k valid / boundary unsupported | 17,091 / 2,909 |
| production/prototype hit mismatch | 683 |

These values are audit inputs, not substituted Full Gate results. Gate 1 must reproduce deterministic exact-Oracle statistics and separately score the production and prototype kernels.

## Gate Ledger

| Gate | State | Evidence |
|---|---|---|
| 0 authority and status | complete | active pointers and canonical ledger corrected |
| 1 broad calibration | complete | 2,048 exact fixtures and 20k diagnostics passed |
| 2 safe writable field | complete | 48 boundary sources and two-step closure passed |
| 3 occupancy semantics | pending | none |
| 4 dense field | pending | none |
| 5 dense single-entry Recall | pending | none |
| 6 OpenClaw live | pending | none |
| 7 final evidence and delivery | pending | none |

## Portability

Windows 10/11, PowerShell, Python for Windows, and Git for Windows are the primary acceptance environment. Cross-platform portability is not claimed by this task.

## Gate 1: Broad Residue Calibration

The canonical result is `validation/caold_broad_residue_coverage_calibration.json`. The runner uses fixed seeds `0x0ca01d39` and `0x0ca01d20`, 128 exact fixtures in each of the 16 phase/direction buckets, and independent Decimal polygon Oracle results. Production fixed-point and float prototype distributions are scored separately.

| Kernel / policy | missed p99 | TV p95 | false max | dominant | max fanout |
|---|---:|---:|---:|---:|---:|
| production min-hit 1 | 1.2411% | 2.0776% | 0 | 98.97% | 7 |
| production min-hit 2 | 2.5466% | 2.4613% | 0 | 98.97% | 7 |
| prototype min-hit 1 | 1.2411% | 2.0765% | 0 | 99.02% | 7 |
| prototype min-hit 2 | 2.5466% | 2.4613% | 0 | 99.02% | 7 |

The selected policy is `nollm_broad_residue_min_hit_1_v1`. It materially reduces missed mass without increasing false mass, fanout, support distance, or production cost. Production Q16 partition error was zero. Exact-Oracle mean time was 75.2142 ms per cell; production mean/p95/max were 0.4645/0.5523/2.3424 ms.

The 20,000-fixture diagnostic contained 17,036 valid expansions and 2,964 atomic boundary rejections. Production and float prototype hit counts differed in 651 valid cases (3.8213%). This is reported as fixed-point quantization evidence, not a mathematical failure; both paths were separately scored against the Oracle.

## Gate 2: Coverage-Safe Writable Field

The public contract `nollm_hex_storage_2p31_writable_2p30_depth2_v1` separates storage/transport radius `2^31-1` from active writable radius `2^30-1` and declares two `coverage_down` steps. Core preflights every Put/Move target in a batch before staging any command. Access preflights every target-bearing decision. Storage-only state still decodes and reopens, while new active writes there are rejected with structured radius and contract fields.

`validation/caold_safe_writable_field_validation.json` covers six hex boundary directions across all eight phases. It traversed 336 single-step and 816 second-step retained members. The maximum second-step radius was 1,693,666,955, leaving a storage margin of 453,816,692. All checks passed, including atomic rejection and Q40-kernel closure.

The existing live workspace `C:\Users\Administrator\.openclaw\memory\nollm-v39-bounded-approximate-v1-migrated` was inventoried read-only: 12 occupied cells, maximum radius 24, and zero storage-only cells. Its state SHA-256 remained `249DBD8ED87395EBD2BE123882106B7F4E5089AAF58A666C86E85EA7845249BD` before and after inspection.
