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

The completed independent 48-initial-run matrix used the same OpenClaw CLI,
Provider, model, timeout, schema, and twelve cases for every strategy:

| Strategy | Initial parses | Completed | Errors | Deterministic repairs | Mean latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| P0 `dream-v1` | 12 | 11 | 1 | 3 | 34,723 ms |
| P1 `dream-json-p1` | 12 | 12 | 0 | 0 | 33,457 ms |
| P2 `dream-json-p2` | 12 | 12 | 0 | 2 | 33,394 ms |
| P3 `dream-json-p3` | 12 | 11 | 1 | 0 | 29,461 ms |

P1 is the winner by strict initial parse success and is installed as the active
plugin prompt. The live plugin also exercised its one-call same-model format
repair and bounded P1/P2 full retry path for malformed outputs. Repairs never
changed JSON string values or added or removed fields.

One pre-guard shadow probe reached Placement in the temporary workspace. The
discovered defect was fixed before the next probe. The post-fix shadow probe
completed Formation with `statement_store_write_count=0` and emitted no new
Placement/Core event.

The active user instance then completed ten normal chats with the plugin enabled.
Fourteen P1 Formation parses were recorded during this period. Five Placement
applications succeeded and updated Core/cursors; four Placement failures were
isolated and did not block chat delivery. A successful session was reopened for
Recall: the resolver selected the exact stored statement
`dream:15c153f28a7a7d9d4e984eb06d8f522be434e25aadacd1f8353c48d5052c3b67`,
and the visible response followed the recalled Chinese/risk-first format.

## Status

`FORMATION_JSON_RESILIENCE_VALIDATED`. The required matrix, active-instance
smoke, successful StatementStore-to-Placement/Core-to-Recall path, and failure
isolation evidence are complete. This validates output resilience only; it does
not claim CSTAOLD closure, semantic accuracy, release readiness, or long-term
stability.
