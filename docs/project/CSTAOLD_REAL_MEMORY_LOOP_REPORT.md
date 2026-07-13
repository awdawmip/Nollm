# CSTAOLD Real Memory Loop Report

Date: 2026-07-13

## Status

`CAOLD_CROSS_SESSION_LOOP_IN_PROGRESS`.

This is a Windows/OpenClaw engineering checkpoint, not a claim of semantic
accuracy, long-term stability, release readiness, security completion, or
complete cross-session acceptance.

## Verified Facts

- Branch: `codex/cstaold-real-memory-loop`.
- Checkpoint commit: `1beb751e81a79559bd063c146e2f9337b8e1d31e`.
- Windows bridge encoding fix: `338b47c2`.
- Targeted regression after the fix: Python `32 passed`; Node `14 passed`.
- The active OpenClaw plugin is enabled, uses `dream-json-p1`, and points at
  the current worktree with `meituan/LongCat-2.0`.
- Gateway restart and health probe completed successfully after the fix.
- The initial real write sequence completed ten normal main-agent turns. Its
  event subset contains nine Formation completion records: seven successful
  and two `invalid_input` records. The failed records did not interrupt later
  main-agent turns.
- Real event records before and during this checkpoint show successful
  Placement/Core writes and Placement errors that did not stop chat delivery.
- `MemoryCursor` persisted a bounded `agent:main` GeometryAddress entry and
  retained prior session entries. No topic, entity, source, vector, graph, or
  global lookup was added.
- Two new main-agent sessions were run after the first Gateway restart. Both
  returned normally. Their complete Recall injection/natural-use proof remains
  unverified in this checkpoint.

## Bridge Root Cause And Fix

Node sends the bridge envelope as UTF-8 JSON. On this Windows host, the Python
child inherited `gbk` for stdin/stdout. A valid Chinese Formation JSON was
therefore decoded incorrectly at the Node-to-Python boundary and surfaced as
`invalid_input`, even though direct strict JSON parsing succeeded.

The bridge child now receives `PYTHONUTF8=1`. A replay using the exact logged
Chinese failure sample successfully parsed and formed two Statements after the
fix. `invalid_input` remains non-retryable; the fix does not coerce invalid
model output or broaden schema acceptance.

## Current Live Continuation

After the encoding fix and Gateway restart, ten independent normal sessions
were initiated. During the bounded observation window, five background
Formation runs started but had not produced completion records. Gateway health
remained good. This is recorded as `NOT_VERIFIED`, not as a Formation failure
or success.

## Evidence Availability

- P0/P1 historical matrix statistics are preserved from the prior checkpoint.
- P2/P3 historical direct-run prompt hashes are not recoverable:
  `prompt_sha256 = null`, `evidence_status = "not_available"`, reason:
  `historical live run did not persist prompt hash`.
- No prompt hash has been reconstructed or substituted for those attempts.
- The current report intentionally does not include full chats or hidden
  reasoning.

## Remaining Work In This Same Loop

1. Wait for or rerun a bounded post-fix live batch until completed Formation,
   Placement/Core binding, and failure-continuation counts are observable.
2. Restart Gateway, then verify one new-session related Recall, hidden
   injection, and natural main-agent use; separately verify a NONE path.
3. Record only observed results, count orphan Statements as zero only after
   directly reconciling Statement/Handle/Core state, then issue the next
   checkpoint bundle.

## Data And Plugin State

The plugin remains enabled. Existing Statement, Core, Handle, and Cursor data
were preserved and were not reset or cleared during this checkpoint.
