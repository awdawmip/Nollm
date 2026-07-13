# CSTAOLD Real Memory Loop Report

Date: 2026-07-13

## Status

`CAOLD_CROSS_SESSION_LOOP_COMPLETED` for the bounded Windows/OpenClaw
checkpoint defined by the current Rev.1 task. This is not a claim of semantic
accuracy, long-term stability, release readiness, security completion, or
cross-provider portability.

## Verified Facts

- Branch: `codex/cstaold-real-memory-loop`.
- Historical checkpoint commit: `1beb751e81a79559bd063c146e2f9337b8e1d31e`.
- Windows bridge encoding fix: `338b47c2`.
- Targeted regression: Python `32 passed`; Node `14 passed`.
- The active OpenClaw plugin is enabled, uses `dream-json-p1`, and points at
  this worktree with `meituan/LongCat-2.0`.
- Gateway health probes passed before and after the continuation restart.
- A serial real main-agent write session completed after restart. Its bounded
  Formation sequence produced Statement
  `dream:0113e3ea0b48355f0f683e30508354ce2a48e3324caadb46c93d400b7cc1304a`;
  Placement applied it with `core_write_count=1`, created its Handle binding,
  and persisted the bounded session and `agent:main` GeometryAddress cursor.
- Gateway was restarted after that write. A distinct related main-agent
  session entered Recall through the agent cursor. The exact Recall request
  selected the Statement above, returned hidden context with
  `visible_message_count=0`, and the visible main-agent response used the
  requested Chinese, risks-before-progress structure without mentioning
  Nollm.
- A second distinct session asked an unrelated France-capital question. It
  returned only the direct answer and no Recall injection was observed. The
  subsequent Formation result was `defer` with zero Statement writes.
- Continuation reconciliation found both Statements formed in this serial
  continuation to have a canonical Handle binding and a matching Core atom.
  The unrelated turn formed none. Therefore
  `orphan_statement_count=0` for this continuation.

## Bridge And Failure Boundary

Node sends UTF-8 bridge envelopes. On this Windows host, the Python child had
inherited `gbk` for stdin/stdout, causing valid Chinese Formation JSON to be
misclassified at the Node-to-Python boundary. The bridge child now receives
`PYTHONUTF8=1`.

The serial write's first two model outputs still produced recorded engineering
input errors before the final bounded Formation result succeeded. The main
agent remained available throughout. This report records that observed retry
sequence; it does not reinterpret those errors as semantic results or claim a
quality rate from one continuation.

## Evidence Limits

- The installed hook traces successful Recall injection, but its `none`
  branch is intentionally silent. The unrelated-session result is therefore
  recorded as observed `no-injection`, which is sufficient for the task's
  `NONE or no injection` requirement; it is not represented as a separately
  traced raw Recall-agent `NONE` response.
- P2/P3 historical direct-run prompt hashes are not recoverable:
  `prompt_sha256 = null`, `evidence_status = "not_available"`, reason:
  `historical live run did not persist prompt hash`.
- No prompt hash has been reconstructed or substituted for those attempts.
- The report intentionally excludes full chats and hidden reasoning. The
  related-session output demonstrates formatting preference use only; it is
  not evidence that any additional project facts in that output are accurate.

## Data And Plugin State

The plugin remains enabled. Existing Statement, Core, Handle, and Cursor data
were preserved and were not reset or cleared. No source/topic/entity route,
vector, graph, global lookup, or Python semantic placement was added.
