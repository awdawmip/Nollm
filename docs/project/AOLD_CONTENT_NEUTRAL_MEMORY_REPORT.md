# AOLD Content-Neutral Memory Report

Date: 2026-07-24

```text
input HEAD: 8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea
implementation commit: 6cbaeb710cb9f0f7b3744d4971b982ab82a344f7
status: AOLD_CONTENT_NEUTRAL_MEMORY_IN_PROGRESS_AT_6cbaeb710cb9f0f7b3744d4971b982ab82a344f7
```

## Result

Offline Gates A-F pass. Gate G was not run because the repository authority for
this stage prohibits live OpenClaw, model calls, and corpus execution. The final
status therefore remains `IN_PROGRESS`; no Provider diversity or visible-answer
quality claim is made.

- Active content-eligibility classifier branches: `0`.
- Source-role blanket bans: `0`. User, assistant, tool-associated,
  model-inferred, and recalled-derived material uses Writer v4 uniformly.
- Active Writer outcomes: `plan`, `zero_new_propositions`, `retryable_defer`,
  and `incomplete_continuation` only.
- Legacy `no_memory` migrates append-only to
  `evaluated_no_new_propositions_legacy`; legacy `deferred` migrates to
  `retryable_defer_legacy`. Writer v3 terminal responses require the explicit
  offline migration parser and are rejected by the active parser.
- Zero-delta state is skipped only while Writer schema, prompt, context,
  current-memory fingerprint, and complete source coverage remain unchanged.
- A Capture larger than the normal batch receives a dedicated work item.
  UTF-8-bounded deterministic windows cover input larger than 64 KiB with fixed
  overlap and exact codepoint ranges; no category-based splitting exists.
- More than eight propositions continue across passes. The 20-proposition
  fixture completes as `8 + 8 + 4`; continuation state survives worker restart,
  preserves prior Statement IDs, and remains retryable after a pass-budget marker.
- Statement provenance v2 stores origin kinds, exact source/assistant/tool
  Evidence spans, derived Statement IDs, evaluation identity, and continuation
  pass. Legacy v1 bytes reopen byte-for-byte.
- Echo prevention relies on semantic reuse/revision/zero-delta decisions and
  exact lineage, not assistant or recalled-source exclusion. Real Provider
  behavior for reuse versus genuinely new inference remains unvalidated.
- Progressive routing uses at most two previews per region and at most 64
  codepoints per preview. The algorithm does not inspect content categories or
  redact keywords. `surface`, `open_region`, `recall`, `expand`, and `none` stay
  within one server-issued, run-scoped operation; one final entry is recalled.
- `integrations/openclaw/nollm-memory-provider` is marked
  `HISTORICAL_INVALID_FOR_CONTENT_ADMISSION` and its entry point fails closed.
  Its secret rejection, stable promotion, and weather suppression policies are
  not active dependencies.

## Evidence

`validation/aold_content_neutral_memory_20260723.jsonl`:

```text
lines: 5
bytes: 3023
sha256: c1b5146428f9c52a1cf3576768d80e8be5788a7efe200e57d346b3ad3b4d9297
```

`validation/aold_content_neutral_memory_summary_20260723.json`:

```text
bytes: 454
sha256: 2afe69ff1ce4026d2f16d17452067b45146b70fbe49b23d1e445287bdc1f4091
```

The 128/300/1000-Statement runs used real `AccessRuntime`, `CoreRuntime`,
`build_main_agent_surface`, `open_main_agent_region`, and bounded single-entry
Recall. All three runs had zero uncovered source cells, one selected entry,
root visible JSON below 4.5 KiB, and a maximum routing anchor of 64 codepoints.
Final depths were 2, 2, and 3; each Recall returned three Statements.

## Regression

```text
Core/Snapshot/Trace: 98 passed
Access: 135 passed
OpenClaw Python: 86 passed
OpenClaw Node: 61 passed
Lab: 44 passed
M0/manifest/boundary test selection: 50 passed
```

Core has no diff from the input checkpoint. The final ownership manifest and
boundary checks are delivery gates and are recorded in the delivery commit.

## Vector

```text
CORE 93% | SNAPSHOT 50% | TRACE 40% | ACCESS 90% |
HISTORY 10% | AUDIT 10% | OPENCLAW 89% |
LAB 85% | DISTRIBUTIONS 92%
```

These are planning estimates, not permanent completion claims. Remaining limits
are real Provider content-diversity behavior, assistant/tool inference quality,
visible main-agent answer quality, restart/NONE Live evidence, and live latency.
Cross-platform portability was not validated in this stage.
