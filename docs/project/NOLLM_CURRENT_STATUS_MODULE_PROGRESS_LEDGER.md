# Nollm Canonical Module Progress Ledger

**Date**: 2026-07-16
**Input HEAD**: `26bd0ae68470ef8d1396014884e305cc1c3ab7ef`
**Gate 0 checkpoint**: `b16ca3bf979ca054341531b9df92388fc02b805f`
**Evidence/report checkpoint**: `71ba080bf8d2ec196ced294c1392d0f02027ac3d`
**Status**: `AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS`

This is the only active module ledger. Percentages are current planning estimates, never permanent completion claims.

| Module | Lifecycle | Current progress | Confidence | Preserved capability | Active gap | Task delta |
|---|---|---:|---|---|---|---:|
| CORE | CAPABILITY_VALIDATED | 95% | high | canonical state, bounded Coverage/Surface/Recall, atomic mutation | read existing timing/results; no algorithm changes | 0% |
| SNAPSHOT | IMPLEMENTED | 50% | medium-high | state-byte regression | versioned and incremental Snapshot | 0% |
| TRACE | IMPLEMENTED | 40% | medium | isolated public contract | long-term performance observation | 0% |
| ACCESS | IMPLEMENTED | 95% | high | Statement/Handle/Core atomic coordination, durable endpoint timing, reopen verification | broader independent durable sample | +5% delivered |
| HISTORY | PROPOSED | 10% | low | charter | paused | 0% |
| AUDIT | PROPOSED | 10% | low | charter | paused | 0% |
| OPENCLAW | IMPLEMENTED | 92% | medium-high | Formation, Placement, Recall, hidden injection, exact correlation IDs and split timing | CLI host lacks the required message_sent endpoint | +7% delivered |
| LAB | IMPLEMENTED | 95% | high | deterministic/Live runners, unified latency schema, aggregation, bottleneck report | larger cold and multi-Statement cohorts | +10% delivered |
| DISTRIBUTIONS | IMPLEMENTED | 90% | high | plugin schema and debug-only latency validation profile | host message_sent conformance | +5% delivered |

The frozen baseline has 110 records: 12 write host turns, 12 Recall host turns, 8 hidden injections, 4 NONE terminals, and 3 reopen-verified durable Placement terminals. Formal message-sent-to-durable and query-to-visible samples remain `insufficient sample` because the Windows CLI host emitted `agent_end`, not `message_sent`. Existing semantic revision and Dense Live evidence remains preserved and is not reused as latency evidence.
