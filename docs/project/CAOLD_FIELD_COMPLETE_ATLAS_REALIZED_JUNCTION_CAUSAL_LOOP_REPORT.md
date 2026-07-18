# CAOLD Field-Complete Atlas / Realized Junction Causal Loop Report

## Result

`CAOLD_FIELD_COMPLETE_ATLAS_CAUSAL_LOOP_IN_PROGRESS`

Input HEAD was `440b7d43ade67a2c1b8f67aa0fabf24c2b7297ef`. Rev2 closes the finite Atlas coverage and realized Junction contract gaps and validates a Provider Writer-to-field-to-Reader causal loop. The Provider-backed long-arm gate remains incomplete, so this report does not claim the task's completed status.

## Atlas And Junction

`LocalityAtlas` wire V3 carries an explicit coverage certificate. The implementation enumerates every non-empty projection at increasing aggregation orders, selects the finest complete order that fits the bounded budget, and returns explicit overflow when no supported order fits. It never samples a projection and calls it complete. The 300-Cell case reports `occupied=300`, `covered=300`, `uncovered=0`, `order=0`, and `region_count=300`; the 40-Cell, budget-8 case reports overflow with `covered=0` and `uncovered=40`.

Core exposes an active relation-group Junction only when every group is within the contact radius. Access rejects inactive, overflow, stale, unsupported, or unrealized Atlas plans before a write. One Statement remains one Atom in one Cell, and Lens text and routes remain operation-local.

## Provider Causal Gate

Ten independent scenarios used `meituan/LongCat-2.0`. In each scenario the Writer received immutable Captures and the same finite Atlas later used by the Reader path; its selected plan was applied, durable reopen was verified, and the Reader selected from the resulting field. Results were:

| Measure | Result |
|---|---:|
| Writer durable Admission | 10/10 |
| Reader reaches exact Writer statement | 10/10 |
| Multi-group Junction realized | 10/10 |
| Lens ablation changes geometry or outcome | 10/10 |
| Same-field unrelated false reach | 0/10 |
| Honest defer probes | 3/3 |

One Reader response used unsupported outer text and was recovered by one bounded schema-only correction against the unchanged final field and Recall budget. The evidence contains 27 successful Provider process attempts. Attempt elapsed time was 25.027 to 216.919 seconds, median 87.869 seconds, mean 96.376 seconds, and 2602.153 seconds total. These are validation observations, not a production latency target.

## Provider Long-Arm Attempt

The normal OpenClaw Host path durably captured four facts in one isolated workspace. Three became admitted Statements and were verified through public Access reopen. The target is at `(0,0)` and two later Tokyo facts are at `(-1,0)` and `(-2,0)`; single-entry Recall from `(-2,0)` reaches the exact target with `lateral, lateral`. Core state is 1620 bytes with SHA-256 `fd95966e8e94f57a3c8c39e6fe3b24c5546f0a9a7e4b655c1123ca4892a87b91`.

This proves one real Provider-backed Tokyo arm only. The first absolute-time fact remained retryable after two failed formation attempts with `non-deferred action requires a resolved Lens relation group`; its third attempt was processing when the bounded 660-second outer run ended. Time, weather, unrelated controls, and restart were therefore not completed. Per the one-Cell rule, no multi-cell footprint was introduced and Gate D remains `IN_PROGRESS`. The Gateway was stopped and the Live workspace was frozen.

## Evidence

| Artifact | Lines | UTF-8 bytes | SHA-256 |
|---|---:|---:|---|
| `validation/caold_field_complete_atlas_causal_loop_20260718.jsonl` | 42 | 851606 | `52771a2b5d86e46bc680663b13a8d45761d6ea715827ece0be13ec10f51fcfa1` |
| `validation/caold_field_complete_atlas_causal_loop_summary_20260718.json` | 25 | 949 | `b91a1968c20b65684f0a083a51ec9372709ab298e69128c8edc6427c7a36b037` |
| `validation/caold_field_complete_atlas_long_arm_host_20260718.jsonl` | 36 | 30370 | `db23099a1c994e1f7a5cd4d5053f33baa07295e0484fbec86926b1b7ba637348` |

The canonical evidence has 10 `causal_case`, one `causal_case_amendment`, three `defer_probe`, 27 `provider_attempt`, and one `provider_long_arm_attempt` records. Raw Host artifacts are bound by hashes in the frozen record. Evidence status is deliberately `passed=false` because the long-arm gate is not complete.

## Verification

| Suite | Result |
|---|---:|
| Core / Snapshot / Trace / Access / Lab | 218 passed, 8 warnings |
| OpenClaw Python | 49 passed |
| M0 | 45 passed |
| OpenClaw Node | 44 passed |
| OpenClaw plugin check | passed |
| Ownership manifest | 1961 tracked, 1961 rows, 0 unclassified |
| Production boundary | 0 violations, 0 cycles |

The warnings are existing `FileEvidenceStore` deprecations. `git diff --check`, bundle verification, Git object checks, and final clean-tree verification are delivery gates recorded with the bundle.

## Actual Vector And Limits

The evidence-backed planning estimate is `CORE 95 / SNAPSHOT 50 / TRACE 40 / ACCESS 96 / HISTORY 10 / AUDIT 10 / OPENCLAW 94 / LAB 90 / DISTRIBUTIONS 96`. LAB remains below the task target because Provider long arms, unrelated controls, and restart are incomplete. These values are not permanent completion claims.

Only `meituan/LongCat-2.0` on Windows was exercised. Multi-cell footprint, persistent Lens, Topic/Entity indexes, vectors, graphs, multi-entry Recall, Stitch, multi-chart growth, multi-Provider behavior, and formal release remain out of scope.
