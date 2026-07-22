# AOLD Main-Agent Provider Live Selectivity Report

Date: 2026-07-22

Status: `AOLD_MAIN_AGENT_PROVIDER_LIVE_IN_PROGRESS_AT_9cc0f005cce15e022884ce4a0fb930b17668fe08`

Input HEAD: `ec83e0cb22299f2d62d0d6e021911595f8c783a9`

## Delivery

| Commit | Purpose |
| --- | --- |
| `438469dc1127491c053bb9d3f5a060ff5e409c95` | Correct the Rev5 live and evidence baseline. |
| `793a01f5d8e657ad61fc2c38922667df468d6a06` | Scope native memory operations to one trusted main-agent run. |
| `9cc0f005cce15e022884ce4a0fb930b17668fe08` | Bind profiles and declared-target Recall evidence. |

The Core tree remains `83bb1fb4d28a0ee2a2a3f3f3efc85f1b4ba7c0c7`, unchanged from the input.

## Writer Live

Real Provider Writer execution was not performed under the active execution
constraint. Live chats, created Statements, first-attempt/retry rate, durable
reopen, and live provenance counts are therefore all `0` or `not measured`.
No semantic product evidence is claimed.

## Main-Agent Tool

The Host issues the operation identity and binds it to trusted `toolCallId`,
session, run, configured scope, workspace, timestamps, Core fingerprint,
Atlas/page fingerprints, complete ProgressiveAtlasPolicy, selected region and
entry, and expansion state. Cross-run, cross-session, expired, mismatched
region, mismatched Policy, and stale-reopen use is rejected.

Operations have a five-minute configurable TTL and a bounded capacity. They are
removed on NONE, fatal failure, successful expanded completion, session end,
gateway stop, and service stop. A bridge process/JSON failure during expansion
preserves the operation for one truthful retry.

Successful Recall is recorded at exact run scope. Capture of the recalled answer
is suppressed only in that same run; a later run in the same session remains
eligible. Pending Surface state alone does not suppress Capture. The hidden
Reader remains disabled and the deterministic harness made zero hidden child
calls. Real main-agent Provider tool calls were not executed.

## Recall Evidence

The offline conformance corpus contains 80 Statements across eight Localities
and 47 targets declared before Recall: 40 default, five expansion, and two
restart cases.

| Measure | Result | Evidence class |
| --- | ---: | --- |
| declared target reach | `1.0` | deterministic conformance |
| expanded target reach | `1.0` | deterministic conformance |
| restart target reach | `1.0` | deterministic conformance |
| maximum forbidden-ID leakage | `0` | computed from returned IDs |
| default p95 result count | `4` | deterministic conformance |
| default p95 characters | `224` | deterministic conformance |
| bounded locality function p95 | `581.4 ms` | Python function timing only |
| semantic NONE | unavailable (`0` executed) | not product evidence |
| query to visible answer | unavailable | Provider/Host not executed |

The evidence does not relabel function timing as end-to-end tool latency and
does not infer NONE or visible-answer quality without a real main-agent run.

## Profiles

`shadow-observation` and `active-memory` are explicit distribution profiles.
`active-memory` selects `statement-store`, requires a Statement workspace, and
binds the memory workspace to it by default. Diagnostic output includes profile,
write mode, workspaces, operation TTL, region bound, Provider/model, and active
Evidence. No live installation or Provider call was made.

## Evidence Identity

| File | Git blob | Lines | Bytes | SHA-256 of Git blob bytes |
| --- | --- | ---: | ---: | --- |
| `validation/aold_main_agent_provider_live_selectivity_20260722.jsonl` | `7d49eab9e720aedc73afd5a9a4660ee8108a7e7d` | 51 | 139578 | `49c722f4c903da73aa87b7c94a5f216b2001606f101f1c41f8553c746ef1821d` |
| `validation/aold_main_agent_provider_live_selectivity_summary_20260722.json` | `092a002c8e72117d0be769790dc1172373f28db2` | 1 | 1023 | `3a7b958b02740c44dcdf3ae28e757ed6e02c846a523f271a0b0785fdeae62353` |

## Verification

- Core/Snapshot/Trace/Access/OpenClaw Python: `300 passed, 8 warnings`.
- Lab: `43 passed`.
- M0 matrix: `45 passed`.
- OpenClaw Node: `55 passed`.
- Ownership manifest: 2062 tracked files, 2062 rows, zero unclassified.
- Production boundary violations: zero; cycles: zero; migration diagnostics: seven.

The Node dependency audit reports 11 inherited advisories (one low, seven
moderate, two high, one critical); dependency upgrades are outside this task.

## Actual Vector

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +10% | DISTRIBUTIONS +5%
```

## Completion

Status remains `IN_PROGRESS`. Offline operation scoping, Capture suppression,
Policy reopen, profile truth, declared-target metrics, leakage calculation,
restart validation, evidence verification, and regressions are closed. Real
Provider Writer chats, real main-agent tool invocation, semantic NONE,
query-to-visible timing, and visible-answer quality remain unexecuted and are
not claimed.
