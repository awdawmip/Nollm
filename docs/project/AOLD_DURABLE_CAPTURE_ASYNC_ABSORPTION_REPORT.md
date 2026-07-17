# AOLD Durable Capture And Async Absorption Report

Date: 2026-07-17

Input: `ca50a97e0b9ea6a6358ff37ececbb5cfb4eaaa61`

Status: `AOLD_DURABLE_CAPTURE_ASYNC_ABSORPTION_IN_PROGRESS`

## Result

OpenClaw now owns an immutable local Capture spool and append-only absorption state. The visible turn publishes exact user/assistant UTF-8 content before returning; Formation, Placement, and Admission run later. Pending read-your-recent-writes is a bounded chronological read with no query index and no Provider call. Admitted Recall has a deterministic singleton path and an at-most-one-call finite geometry-entry path.

The task remains `IN_PROGRESS`. Provider-backed Windows Live proved Capture, cross-session/restart Pending, recovered multi-Capture batch Formation/Placement, independent Admission, and durable reopen. It did not complete the prescribed 10-turn Capture run, the admitted Recall warm/cold/dense/NONE matrix, or all four crash injection points. The final standalone admitted Recall probe deferred because OpenClaw did not expose request-scoped subagent methods to that command context. Deterministic Recall tests are not used as a substitute for that missing Live proof.

## Capture

- Provider-backed Live: 4 immutable Captures; publish p50 `15.3742 ms`, p95/max `17.7320 ms`.
- Deterministic run: p50 `3.9248 ms`, p95 `4.6359 ms`, max `10.2706 ms`.
- Dedicated 150-turn performance run: p50 `4.2236 ms`, p95 `8.0814 ms`, max `32.8942 ms`.
- Foreground topology: `0 Provider / 0 bridge / 0 Core` calls.
- Duplicate hook replay preserves one immutable Capture identity. Missing sidecar state reconstructs from the Capture file; state transitions never rewrite Capture bytes.
- Capture files remained present through controlled Gateway stops and restarts. The old V6 workspace was not modified during Live.

The measured interval is Capture publication inside the post-visible delivery hook. It is the closest available host timestamp to visible reply completion; no stronger UI-render timestamp claim is made.

## Pending Read-Your-Writes

- One not-yet-admitted fact was available in a new Session and again in another new Session after Gateway restart.
- Live local preparation was `3.436 ms` then `5.271 ms`; p95/max `5.271 ms`.
- Additional Provider calls: `0`.
- Admission moved all three batch Captures to terminal `admitted`; diagnostic pending count is `0`, so raw Pending injection exits after handoff.
- Selection is scope, age, count, and character bounded only. There is no query matching, topic/source index, graph, vector, embedding, or semantic cache.

## Absorption

- One recovered Provider-backed batch admitted 3 Captures as 1 Statement.
- Common batch calls: Formation `1`, Placement `1`; Provider durations were `27.089 s` and `20.026 s`.
- The first claim was intentionally interrupted. Restart recovered the same batch identity at attempt 2 and reached terminal Admission without duplicate binding.
- First Capture to Admission was about `652.0 s`, including intentional worker disablement, backlog wait, timeout, and restart. The recovered processing interval was about `61.1 s`; this run does not establish a general latency percentile.
- Current spool state: 3 admitted, 1 terminal deferred from the early missing-model-metadata probe, 0 pending/processing, 0 orphan Capture.
- Durable reopen verifies the admitted Statement through the Access-owned Statement, HandleBinding, and Core consistency boundary. Matching bindings: 1; duplicate Admission count: 0.

## Admitted Recall

- Deterministic contract: singleton `0` hidden calls; multi-entry relevant/NONE `1` hidden call; selected entry then direct bounded Locality injection with no second Statement selector.
- Provider-backed standalone probe: not validated. It emitted a request-scoped subagent-runtime defer before injection. Therefore Live hidden-call latency, query-to-injection, query-to-visible, warm/cold, dense, NONE, and multi-fact results remain open.
- No fallback to multi-entry or legacy query selection was added.

## Recovery And Data

- Immutable Capture and append-only state events survive Gateway restart. A stale processing claim is recovered without changing batch identity; retries cannot absorb newly arrived Captures into the replayed batch.
- Admission applies Statements independently; one local failure does not roll back unrelated successful Statements.
- Old workspace: `nollm-aold-memory-latency-v1`, preserved with tree SHA-256 `95d5045978c744adac1c82a3a864b1c66b84bb3861da4acf2d632fd4e7028f1b` and latest file timestamp before the Live window.
- New workspace: `nollm-aold-durable-capture-async-absorption-v1`. Capture originals remain in its OpenClaw-owned spool after terminal Admission/defer.
- Gateway is stopped and the Live workspace is frozen. Diagnostic state: plugin `0.13.0` loaded, worker configured but not alive, task state `Ready`, pending `0`, admitted `3`, deferred `1`.

## Verification

- Fixed Python suites: Core 70, Snapshot 7, Trace 3, Access 95, OpenClaw Python 44, M0 45, Lab 14: `278 passed`.
- Node: `38 passed`; TypeScript build and `plugin:check` passed.
- Ownership: `1917/1917` tracked files classified; manifest valid; production violations `0`; production cycles `0`.
- Frozen deterministic Evidence: 4 lines, 899 bytes, SHA-256 `4a2ae8091344e4e9629124df00520882c203d3272767809ec5b07151852ac2be`.
- Frozen Live Evidence: 24 lines, 9195 bytes, SHA-256 `ade8e2d881c1359bd43d339e70f70963e5a83266652dc91d4d5b3a3935ef2b1e`.
- Deterministic summary: 1 line, 600 bytes, SHA-256 `fc6be51bd51985b483b5309fc54705808fca3445068d2322aff6f891ce35276b`.
- Live summary: 1 line, 3314 bytes, SHA-256 `ced7533bca6cc7ba9602b98bafede75da33796be91dfdcd13dd068856032c85b`.

## Scope And Progress

Actual task delta by owned production surface: Core/Snapshot/Trace `0`; Access `+2%` (batch composition and public durable reopen verification); OpenClaw `+12%` against its expanded Capture/worker/Pending/Recall scope; Distributions `+3%`; Lab adds deterministic and Live evidence tooling. Planning estimates remain Core 95%, Snapshot 50%, Trace 40%, Access 97%, OpenClaw 82%, Lab 95%, and Distributions 93%.

No external queue/database, graph/vector/embedding, topic/source/query index, persistent Surface cache, or legacy multi-entry Recall path was added. The original repository/workspace remains separate and untouched. Delivery uses the report commit's HEAD, an `IN_PROGRESS_AT_<HEAD>` tag, a clean tree, and one complete-history Git bundle.
