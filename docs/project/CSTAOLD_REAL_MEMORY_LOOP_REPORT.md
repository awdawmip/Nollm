# CSTAOLD Real Memory Loop Report

Date: 2026-07-13

## Formation JSON Resilience

Provider/model: `meituan/LongCat-2.0` through the current OpenClaw Gateway.
No provider, credential, or direct HTTP path was added. The active user workspace
was preserved; comparative runs used `nollm-json-resilience-lab-20260713` with
`write_mode=shadow`.

The bridge accepts only BOM removal, outer whitespace, one JSON fence, one
complete object surrounded by explanatory text, and trailing commas. Every repair
records before/after SHA-256, repair types, unchanged string tokens, and no field
addition or removal. Single quotes, malformed strings, and multiple objects remain
rejected. A rejected result cannot enter Placement or Core.

The runtime attempts initial Formation, at most one same-model format repair, then
at most two full retries (`dream-json-p1`, `dream-json-p2`). Bounded raw visible
output and a hash are retained in debug evidence. Shadow mode does not run Placement.

## Current Evidence

P0 `dream-v1` produced 13 completed and 1 rejected initial parse attempts in the
independent lab. The rejected P0 response exercised same-model retry and a P2 full
retry completed. P1 started on the same twelve-case set and had both initial
successes and classified failures. The primary 48-initial-run P0/P1/P2/P3 matrix
is not complete, so no winner is selected.

One pre-guard shadow probe reached Placement in the temporary workspace. The
discovered defect was fixed before the next probe. The post-fix shadow probe
completed Formation with `statement_store_write_count=0` and emitted no new
Placement/Core event.

## Status

`IN_PROGRESS`. JSON resilience and failure isolation are implemented and tested,
but the required P2/P3 matrix, active-instance smoke, and full write/reopen/Recall
validation remain unfinished. This report does not claim CSTAOLD closure or
semantic accuracy.
