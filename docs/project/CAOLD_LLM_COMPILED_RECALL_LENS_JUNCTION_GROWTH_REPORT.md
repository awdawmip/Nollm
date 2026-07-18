# CAOLD LLM-Compiled Recall Lens / Junction Growth Report

## Result

`LLM_COMPILED_RECALL_LENS_JUNCTION_GROWTH_VALIDATED`

Input HEAD was `4f8b1c479a2634d3c1b6ae8039116154864275aa` on branch `codex/caold-llm-recall-lens-junction-growth`. The implementation closes the V3.10 Capture correctness gaps, adds finite Locality Atlas and geometry-only Junction solving, and replaces the common Formation plus Placement sequence with one Dream Sculptor operation.

## Formation Boundary

Dream Sculptor receives immutable Captures, exact reference instants, and a frozen finite Atlas. It forms complete Evidence-backed Statements, emits one to four operation-local Recall Lenses, and selects only supplied Locality candidate IDs. Access validates exact Capture spans and semantic plans. Core receives only geometry addresses and occupancy constraints, then deterministically chooses a Junction Cell. Lens text, candidate IDs, reasons, Topic/Entity labels, and query paths are not persisted.

The Prompt explicitly rejects value filtering. The 100-case deterministic cycle formed all Statements, including ten short-lived complete facts: formation and single-entry reach rates were `1.0`, value-filter and wrong-locality rates were `0.0`, average free faces were `4.55`, and duplicate/orphan counts were zero. Six additional Provider-backed Live Captures all reached verified durable Admission.

## Live Lens Evidence

The successful Host outputs were recovered with SHA-256 bindings and recorded in the JSONL evidence. Their nine validated Lenses were:

- Tokyo rain: `2026年7月17日东京的天气如何？`
- Tokyo cancellation: `东京今天因为下雨取消了哪些行程？`; `浅草相关的行程计划有哪些？` (both unresolved, while the plan still used a legal primary Junction candidate)
- Online meeting: `2026年7月17日用户参加了什么活动？`; `用户最近参加了什么线上会议？`
- Osaka rain: `2026年7月17日大阪的天气怎样？`; `2026年7月17日日本哪些地方下雨了？`
- Blue umbrella: `7月17日用户在东京站附近做了什么？`; `用户购买的雨伞有什么特征？`
- Rain stopped: `7月17日东京的天气在傍晚发生了什么变化？`; `东京的雨是何时停的？`

The selected Localities were finite Atlas IDs (`junction:*` or `locality:occupied:*`). Core converted them to Cells; the model never supplied coordinates.

## Junction Growth

T0 is one Atom and one Handle at `(0,0)`: `2026年7月17日，东京下了雨。` Later facts occupy five distinct neighboring Cells: `(-1,0)`, `(-1,1)`, `(0,-1)`, `(0,1)`, and `(1,-1)`. This leaves one free face around T0. No old Atom was copied, and reopen found six Statements, six bindings, and six Core atoms.

Three fresh natural-query Sessions used three different final entries and independently reached the same T0 Handle:

| Direction | Entry | T0 path | Hidden calls |
|---|---:|---|---:|
| Tokyo / cancelled Asakusa | `(-1,0)` | `lateral` | 1 |
| Absolute date / online meeting | `(0,1)` | `lateral` | 1 |
| Weather / Osaka rain | `(0,-1)` | `lateral` | 1 |

An unrelated cat-name query returned `NONE` with one hidden call and no fabricated memory. Each query used one final entry and one Core Recall; the three entry decisions were not merged.

## Calls And Performance

Four successful Live absorption batches produced six Statements. Three used the common one-call path. The final two-Capture batch used the permitted single strict correction, so it used two calls. Provider timeouts and malformed span output remained retryable Pending until a verified Admission; a 240-second Live timeout was needed for multi-Capture LongCat runs.

Controlled Windows measurements passed the local targets: Capture p95 `6.5379 ms` over 150 operations, Atlas p95 `37.0679 ms` over 50, and Junction p95 `15.057 ms` over 200. Live Recall operations were `18.140-25.072 s` for the three entry cases and `13.222 s` for NONE, dominated by the one hidden Provider call. The 16-sample Live Capture p95 was `1598.6344 ms` because one hot-reload/event-loop outlier occurred; this is reported separately from the controlled Capture gate.

## Failures Closed

- Unicode span instructions now expose exact role lengths and require Python character offsets.
- Generic assistant explanations are excluded unless the user supplied or adopted them.
- Worker retries bind Provider idempotency to batch plus execution attempt, while Admission request identity stays stable.
- Provider wait/session errors are retained in durable retry evidence.
- Absorption scheduling is a Host service with explicit start/stop lifecycle, preventing hot-reload worker overlap.
- Validated plans and durable outcomes are emitted to debug evidence without entering production state.

## Verification And Limits

Core/Access/Snapshot/Trace/Lab regression: `202 passed, 8 warnings`; OpenClaw Python: `48 passed`; M0 plus Coverage: `46 passed`; OpenClaw Node: `44 passed`; Sculptor Python targeted rerun: `4 passed`. Ownership was `tracked=1941 rows=1941 unclassified=0`; production boundary violations and cycles were zero.

Actual completion vector is `CORE 98 / SNAPSHOT 50 / TRACE 40 / ACCESS 98 / HISTORY 10 / AUDIT 10 / OPENCLAW 90 / LAB 97 / DISTRIBUTIONS 95`. This is a capability estimate, not a release claim.

Only `meituan/LongCat-2.0` was validated. Multi-Provider behavior, long-term statistics, multi-cell footprints, persistent semantic indexes, multi-chart growth, and formal release remain out of scope.
