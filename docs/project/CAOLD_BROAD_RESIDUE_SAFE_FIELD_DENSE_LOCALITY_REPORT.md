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
| 3 occupancy semantics and dense field | complete | count bands and 300-cell/1000-atom fixtures passed |
| 4 dense single-entry Recall | complete | kernel on/off, dedup, and nonblocking observation passed |
| 5 OpenClaw live | incomplete | R1/R2/R3 passed; new P1 and dense Live did not close |
| 6 final evidence and delivery | complete | full regression passed; IN_PROGRESS bundle is external delivery evidence |

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

The selected policy is `nollm_broad_residue_min_hit_1_v1`. It materially reduces missed mass without increasing false mass, fanout, support distance, or production cost. Production Q16 partition error was zero. The final replay measured exact-Oracle mean/p95 at 71.2847/74.3723 ms per cell and production mean/p95/max at 0.4230/0.4827/0.6784 ms.

The 20,000-fixture diagnostic contained 17,036 valid expansions and 2,964 atomic boundary rejections. Production and float prototype hit counts differed in 651 valid cases (3.8213%). This is reported as fixed-point quantization evidence, not a mathematical failure; both paths were separately scored against the Oracle.

## Gate 2: Coverage-Safe Writable Field

The public contract `nollm_hex_storage_2p31_writable_2p30_depth2_v1` separates storage/transport radius `2^31-1` from active writable radius `2^30-1` and declares two `coverage_down` steps. Core preflights every Put/Move target in a batch before staging any command. Access preflights every target-bearing decision. Storage-only state still decodes and reopens, while new active writes there are rejected with structured radius and contract fields.

`validation/caold_safe_writable_field_validation.json` covers six hex boundary directions across all eight phases. It traversed 336 single-step and 816 second-step retained members. The maximum second-step radius was 1,693,666,955, leaving a storage margin of 453,816,692. All checks passed, including atomic rejection and Q40-kernel closure.

The existing live workspace `C:\Users\Administrator\.openclaw\memory\nollm-v39-bounded-approximate-v1-migrated` was inventoried read-only: 12 occupied cells, maximum radius 24, and zero storage-only cells. Its state SHA-256 remained `249DBD8ED87395EBD2BE123882106B7F4E5089AAF58A666C86E85EA7845249BD` before and after inspection.

## Gate 3: Occupancy And Dense Surface

The former `density_state` API and wire field were removed. Core now exposes `occupancy_band`, whose `normal`, `dense`, and `overloaded` labels are determined only by exact atom counts. Access candidates expose `occupancy: {count, band}` and make no physical-density, importance, confidence, or semantic-crowding claim.

The first dense run exposed repeated full `bindings.json` reads for every handle. `FileHandleStore.bindings_for_handles` now performs one canonical load per bounded preview operation; Surface output is unchanged. The optimized targeted regressions passed 11/11.

The canonical evidence is `validation/caold_dense_locality_surface_validation.json`.

| Fixture | Occupied cells | Atoms | Selected order | Overflow | Cold begin | Max continuation |
|---|---:|---:|---:|---|---:|---:|
| dense cells | 300 | 300 | 8 | true | 955.91 ms | 74.32 ms |
| dense atoms | 300 | 1,000 | 8 | true | 411.54 ms | 193.47 ms |

For the 1,000-atom fixture, `N0..N8` occupied counts were `300, 248, 210, 175, 153, 138, 130, 120, 112`; every order retained aggregate mass `65,536,000`. The result exposed 31 truncated Surface cells, a one-candidate physical-entry page, exact cache-clear/reopen identity, and correct mutation invalidation. The fallback remained truthfully overflowed because Order 8 still exceeded the 48-cell active budget.

The structural fixture additionally covered six sparse cells, two 19-cell unrelated localities with no Bridge, and six boundary cells at radius `1,073,737,727`, all inside the writable field. No semantic index or persisted locality mapping was used.

## Gate 4: Dense Single-Entry Recall

`validation/caold_dense_single_entry_recall_validation.json` contains a deterministic fixture with 301 occupied physical cells and 1,000 atoms. Only 63 bounded Statements were bound for readable output; the remaining atoms are structural interference and are not semantic routes.

Entry A was submitted alone with `coverage_down` and `lateral`. Recall returned 59 unique handles within the 64-result budget, including the target at score 49,152 with canonical path `coverage_down`. The target Cell also has `coverage_down+lateral` alternatives through neighboring first-step targets, but the target appeared once. With all geometry kernels disabled, Recall returned only the direct entry and did not reach the target. `budget_exhausted=true` truthfully reports further structural interference beyond the bounded result set.

The active `default_dream_v1` Access request now rejects more than one final physical entry. The separate natural-entry observation is replayed by `run_natural_multi_entry_observation.py` and stored in `validation/caold_natural_multi_entry_observation.json`. Entry A reached the target; no independent entry B emerged. The minimum required count is zero, and the runner confirms no combined A+B request and no persisted fact-to-entry mapping. This absence is not a failure and no fact was copied to manufacture a second entry.

## Gate 5: OpenClaw Live

The OpenClaw plugin is version `0.11.0`. Its schema now declares coverage Policy `nollm_broad_residue_min_hit_1_v1`, writable-field contract `nollm_hex_storage_2p31_writable_2p30_depth2_v1`, storage radius `2^31-1`, active writable radius `2^30-1`, two coverage-down steps, and the existing bounded single-entry Surface wire. The plugin remains enabled and is linked from this worktree. Gateway restart exceeded the calling CLI's 120-second wait, but an independent probe confirmed the replacement process was healthy, write-capable, and loaded version 0.11.0.

The old V3.9 workspace was copied non-destructively to `C:\Users\Administrator\.openclaw\memory\nollm-caold-broad-residue-safe-field-dense-locality-v1`. The source remains 32 files with inventory SHA-256 `8bf328849cda023a2a9ac7ce79b0f91083827d82032aa13d24d1391b4e85f964`. After live attempts, the copy contains 37 files, 34 Statement files, and 12 occupied physical cells. The old evidence file remains unchanged at SHA-256 `613c99d916889c9cccdfaee0b88b13daef2d9210a4458991745e0d41610a2b97`. The pre-change OpenClaw config backup has SHA-256 `54a10e9cebe691e27070a2e57255db1d1d54cddbefd222cae5911e5f153c4d16`.

| Gate | Actual result |
|---|---|
| R1 Alpha | passed; entry `(layer=0,q=-1,r=1)`, four Alpha Statements, hidden injection, correct visible answer |
| R2 Office | passed; entry `(layer=0,q=7,r=0)`, only Office/cafe Statements, correct visible answer |
| R3 NONE | passed; `completed_none`, no entry or injection, visible answer Jupiter |
| new P1 | incomplete; Formation emitted `dream:b93c2e...5745`, but Placement rejected root `return_to_parent` with `invalid_surface_traversal`; zero writes |
| P1 retry | incomplete; main provider timed out after 302 seconds before a successful delivered response; no Formation/write |
| restart Recall | failed; the Surface model selected unrelated Alpha entry `(16,0)` instead of the persisted BX-3917 entry, and the visible answer denied the code |
| dense coral Live | incomplete; outer 364-second call ended without a delivered response, Formation, or coral Statement |

R2 measured `surface_build_ms=427`, `surface_order_count=1`, `surface_projection_count=11`, `surface_page_count=2`, `physical_entry_resolution_ms=0`, `recall_core_ms=112`, `recall_agent_ms=100574`, and `total_operation_ms=103592`. R3 measured 375/1/11/2/0/0/29163/30184 for the same fields. The failed P1 Placement measured `surface_build_ms=356` and `placement_subagent_ms=81611`; no Core write occurred. Provider/model time is therefore separated from sub-second Surface and Core time.

The external live evidence is frozen at `C:\Users\chaos\nollm_caold_broad_residue_safe_field_dense_live_20260715.jsonl`: 115 canonical JSON lines, SHA-256 `7b7cee3ba5a383a510dceac714f01684fe33b547219dbb733fdd22a46bd6ee5f`. Failed attempts were retained. Because P1 and dense Live did not pass, this delivery remains `IN_PROGRESS` and must not receive the completion tag.

## Gate 6: Regression And Delivery

Expected progress was `C +5 | S 0 | T 0 | A +5 | H 0 | U 0 | O +5 | L +10 | D +5`. Actual progress was `C +5 | S 0 | T 0 | A +5 | H 0 | U 0 | O +2 | L +5 | D +5`. OpenClaw remained below target because new P1 and dense Live did not close; Lab reached 95% rather than exceeding that stated target. No module deviated by more than five percentage points, and no Stitch, multi-layer Placement, persistent Surface cache, semantic index, or new cross-module dependency was introduced.

| Module | Actual progress | State |
|---|---:|---|
| Core | 95% | broad Policy, safe writable field, occupancy bands validated |
| Snapshot | 50% | unchanged; regression passed |
| Trace | 40% | unchanged; regression passed |
| Access | 95% | dense finite preview and single-entry Recall validated |
| History | 10% | unchanged |
| Audit | 10% | unchanged |
| OpenClaw | 92% | plugin 0.11 and R1/R2/R3 validated; P1/dense Live open |
| Lab | 95% | broad, safe-field, dense Surface, and Recall runners passed |
| Distributions | 85% | contracts and plugin schema updated; formal release remains |

Final regression results were: Core 68 passed; Snapshot 7; Trace 3; Access 84 with 8 existing deprecation warnings; OpenClaw Python 37; M0 45; governance 8; OpenClaw Node 19; and `plugin:check` passed. All five CAOLD runners passed. The ownership manifest matches all 1,853 Git-tracked files with zero unclassified paths. Production boundary violations and cycles are zero. Machine scans found zero direct OpenClaw `nollm_core` imports, production Decimal/polygon calls, `select_entries`, `Cursor`, Topic/Source/Entity-to-Cell routes, active `<FINAL_DELIVERY_HEAD>` placeholders, or active `保持封板` text. `git diff --check` is required again after the delivery commit.

The legal delivery tag has form `CAOLD_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_IN_PROGRESS_AT_<HEAD>`. No completion tag is authorized. The final complete-history bundle filename, verified heads, and SHA-256 are external delivery evidence because embedding the bundle hash inside the bundled report would be self-referential.
