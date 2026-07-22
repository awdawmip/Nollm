# AOLD Routing-Only Real Main-Agent Live Report

Date: 2026-07-22

Status: `AOLD_ROUTING_ONLY_REAL_MAIN_AGENT_LIVE_IN_PROGRESS_AT_fe90e89d6c935baa913813c4a9911d90a53b596a`

Input HEAD: `53182a40d7fb443a81d90cf560dc905d96a2e208`

Implementation/evidence checkpoint: `fe90e89d6c935baa913813c4a9911d90a53b596a`

Delivery identity: `AOLD_ROUTING_ONLY_REAL_MAIN_AGENT_LIVE_IN_PROGRESS_DELIVERY_20260722`

## Capture And Echo Control

Every visible user/assistant turn remains an immutable Raw Capture, including
turns that use Recall. Recall no longer suppresses the turn. An append-only,
reopenable directive records role-level source eligibility and memory-tool use.
User-originated text stays source eligible in mixed turns. Recalled assistant
text is context-only and cannot become a new proposition source. Missing or late
directives default safely to context-only assistant handling.

## Routing-Only Surface

The preselection Surface exposes opaque operation-local region/entry aliases,
bounded routing anchors, occupancy, child availability, and routing counts. It
does not expose complete Statement bodies, private Core/Atlas fingerprints, or
policy state. Full Statement text is returned only after selecting one entry by
Recall or by same-entry expansion.

The 80-Statement offline field produced 27 visible regions and 80 routing cards.
Visible routing JSON was 7,784 UTF-8 bytes with 1,053 routing text characters.
Exact complete-Statement leakage and target content leakage were both zero.
Surface-only output is not accepted as answer or semantic product evidence.

## Scope And Profile

The supported deployment is explicitly single-scope. `active-memory`
installation requires a Capture scope, and the tool binds only when the actual
Host-derived scope exactly matches it. Mismatched scopes fail closed for tool
binding while their visible turns remain Captured. Diagnose reports scope,
scope mode, directive grace period, profile, workspace, and routing budgets.

The install script and manifest were validated offline. No live installation,
Gateway restart, Provider/model call, or real Host tool run was authorized.

## Evidence

The deterministic fixture contains 80 Statements across eight Localities and 47
targets declared before Recall: 40 default, five expansion, and two restart.

| Measure | Result | Evidence class |
| --- | ---: | --- |
| declared target reach | `1.0` | deterministic conformance |
| expanded target reach | `1.0` | deterministic conformance |
| restart target reach | `1.0` | deterministic conformance |
| maximum unrelated leakage | `0` | returned-ID computation |
| complete Statement leakage | `0` | visible Surface bytes |
| routing cards | `80` | deterministic conformance |
| routing text characters | `1053` | deterministic conformance |
| visible JSON UTF-8 bytes | `7784` | deterministic conformance |
| default p95 result count | `4` | deterministic conformance |
| default p95 characters | `224` | deterministic conformance |
| bounded function p95 | `697.2 ms` | Python function timing only |
| Provider-backed Statements | `0` | not executed |
| semantic NONE | unavailable | not executed |
| query-to-visible latency | unavailable | not executed |

No natural-chat, mixed-turn visible-answer, Provider latency, retry, or live
restart result is claimed. Status therefore remains `IN_PROGRESS`.

## Evidence Identity

| File | Git blob | Lines | Bytes | SHA-256 of Git blob bytes |
| --- | --- | ---: | ---: | --- |
| `validation/aold_routing_only_real_main_agent_live_20260722.jsonl` | `d359b4a42e7b01117179797db257e8ff5cd11a84` | 51 | 136746 | `54a8caf35eeb48e329c5953d38691d40643d50c39516aadc5329bb65b0a6e9d6` |
| `validation/aold_routing_only_real_main_agent_live_summary_20260722.json` | `a2f38287bb2f2a3a7ebd35a606fcf9b45d7f5f03` | 1 | 1237 | `d16b78e06274f991fe7bc8088e300cd6c05a1dcdca81b2156083ec4102f11a55` |

## Verification

- OpenClaw Node/build/plugin check: `56 passed`; plugin import passed.
- Core/Snapshot/Trace/Access/OpenClaw Python: `301 passed, 8 warnings` in 91.08 seconds.
- Routing evidence tests: `2 passed` in 31.12 seconds; standalone verifier passed.
- Full Lab: `44 passed` in 94.03 seconds.
- M0 governance matrix: `45 passed` in 28.15 seconds.
- Ownership manifest: 2,068 tracked files, 2,068 rows, zero unclassified.
- Module boundaries: zero production violations and zero production cycles; seven inherited migration diagnostics.
- JSON manifests and PowerShell scripts parsed successfully; `git diff --check` passed.
- Core tree remains `83bb1fb4d28a0ee2a2a3f3f3efc85f1b4ba7c0c7`.

The eight warnings are inherited Access deprecation warnings. Bundle and
clean-clone identities are recorded after the delivery commit because a commit
cannot contain its own object identity.

## Actual Vector

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +8% | DISTRIBUTIONS +3%
```

## Completion Boundary

Offline contracts, tests, and deterministic evidence are closed. Real Provider
Writer chats, real main-agent Host invocation, semantic NONE, mixed-turn visible
answers, live latency, and live installation remain unexecuted. This delivery
does not claim semantic product acceptance and does not modify Core.
