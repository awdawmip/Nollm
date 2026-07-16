# AOLD Real Memory Latency Timing Glossary

Date: 2026-07-16

Status: `AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS`

This glossary freezes the timing meanings used by the real layer-0 memory-loop baseline. It defines measurement semantics only; it does not authorize architecture changes or optimization.

## Clock Domains

- `epoch_ms`: wall-clock timestamp used only to correlate hooks and processes on the same Windows host.
- `monotonic_ns`: process-local high-resolution timestamp used to derive durations. Node uses `process.hrtime.bigint()` or `performance.now()`; Python uses `perf_counter_ns()`.
- Monotonic values from different processes are never subtracted.
- File modification time and JSONL line order are not event clocks.

## Write Timeline

- `T0_TURN_VISIBLE`: epoch timestamp when the Formation-triggering `message_sent` hook is observed. It is not user-message receipt or main-agent start.
- `background_queue_wait_ms`: process-local duration from hook observation to Formation background work start.
- `formation_prompt_build_us`: local time spent building the Formation prompt.
- `formation_provider_total_ms`: total Provider wait for Formation calls, including declared repair/retry calls.
- `formation_local_total_ms`: local Formation prompt and parse work; Provider wait is excluded.
- `turn_to_formation_complete_ms`: elapsed time from `T0_TURN_VISIBLE` to parsed terminal Formation output.
- `formation_ms`: deprecated compatibility field. Its historical meaning is cumulative elapsed time and it is excluded from formal statistics.
- `statement_start_offset_ms`: offset from `T0_TURN_VISIBLE` to one Statement entering Placement.
- `statement_to_durable_ms`: process-local duration from that Statement entering Placement to its durable commit endpoint.
- `turn_to_statement_durable_ms`: elapsed epoch-correlated time from `T0_TURN_VISIBLE` to that Statement's durable commit endpoint.
- `turn_to_first_durable_ms`: time from `T0_TURN_VISIBLE` to the first accepted current memory's durable commit.
- `turn_to_all_durable_ms`: time from `T0_TURN_VISIBLE` until all accepted Statements from the turn reach durable commit.
- `turn_to_terminal_no_memory_ms`: time from `T0_TURN_VISIBLE` to a no-memory terminal result such as defer or zero Statements.

## Durable Memory

- `T_DURABLE_COMMIT`: the Statement file, current HandleBinding, and Core MemoryAtom have been written atomically; the Handle resolves to the same readable Atom; immediate readback passes; and the result is not defer, NONE, pending, or provisional revision.
- `T_DURABLE_REOPEN_VERIFIED`: a scheduled close/reopen verification confirms that the same canonical Statement, current HandleBinding, and Core Atom remain readable.
- Formation output, a Placement decision, or a provisional revision is not durable memory.
- A partial Statement, Binding, or Core write is a failure, never a durable sample.

## Recall Timeline

- `Q0_QUERY_PREPARE`: epoch timestamp when the correlated `agent_turn_prepare` hook is observed.
- `Q_INJECTION_READY`: Surface traversal, physical entry resolution, Core Recall, Recall-Agent selection, and hidden injection rendering are complete and the payload is ready to return to the main agent.
- `query_to_injection_ready_ms`: process-local duration from `Q0_QUERY_PREPARE` to `Q_INJECTION_READY`.
- `query_to_recall_terminal_ms`: process-local duration from `Q0_QUERY_PREPARE` to a NONE or failed terminal decision.
- `Q_VISIBLE_ANSWER`: epoch timestamp when `message_sent` is observed for the same session and main-agent run.
- `query_to_visible_answer_ms`: epoch-correlated duration from `Q0_QUERY_PREPARE` to `Q_VISIBLE_ANSWER`.
- `injection_ready_to_visible_answer_ms`: epoch-correlated duration from `Q_INJECTION_READY` to `Q_VISIBLE_ANSWER`.
- Injection readiness is not a visible answer. Missing or mismatched run correlation is recorded as `visible_answer_correlation_unavailable`, never inferred.

## Correlation

- `turn_correlation_id`: SHA-256 of session key, run ID, and visible assistant-message hash.
- Formation records bind `formation_request_id`, `formation_run_id`, `turn_correlation_id`, material ID, and Statement IDs.
- Placement records bind `placement_request_id`, turn ID, Statement ID/index/count, selected entry, action, and outcome.
- Recall records bind `recall_request_id`, hashed session key, main run ID, query hash, entry cell, selected Statement IDs, injection hash, and visible-answer hash.
- Correlation identifiers are debug-validation evidence only. They do not create a persistent semantic route or query/session index.

## Reporting Rules

- Provider, local, Surface, Core, persistence, confirmation, and main-agent time are reported separately.
- Warm, cold, dense hidden-preview, NONE, multi-Statement, reuse, revision, defer, and failure samples are separate cohorts.
- Missing cohorts are reported as `insufficient sample`; no values are estimated.
- One Provider/workstation baseline is not a permanent SLA or architecture invariant.
