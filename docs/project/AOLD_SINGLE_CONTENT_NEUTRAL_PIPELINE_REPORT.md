# AOLD Single Active Content-Neutral Pipeline Report

Date: 2026-07-26

## Result

```text
AOLD_SINGLE_CONTENT_NEUTRAL_PIPELINE_IN_PROGRESS_AT_dfddac9
```

Offline Gates A-F, H, and I pass. Gate G real Provider/OpenClaw Live was not
executed, so this report does not claim `VALIDATED`.

## Checkpoints

```text
input HEAD:          a6551feb89322826f4faa3b0c98c8b8c6152d5d4
implementation HEAD: 94caab0
classification HEAD: 1e6c67b
evidence HEAD:       dfddac9
delivery HEAD:       resolve from final bundle list-heads
```

Core has no diff from the input HEAD.

## Capability

- Active OpenClaw hooks no longer invoke Legacy Formation fallback.
- The active bridge is allowlisted; legacy actions require `legacy_bridge.py`
  with `offline_migration=true`.
- Host tool events publish immutable, scope-bound Tool Evidence with exact UTF-8,
  canonical JSON, or explicit base64 encoding.
- Access resolves exact `tool` Evidence spans without inferring tool provenance
  from action labels.
- Multi-Capture Writer output carries explicit per-Capture progress. Statement
  IDs, source coverage, continuation cursor, retry, and final zero-delta state
  remain Capture-local.
- Worker continuation has a bounded per-invocation pass budget, durable cursor,
  and bounded retry backoff.
- Diagnostics expose current retry, continuation, zero-delta, corruption, and
  explicit re-evaluation state. Active `no_memory/deferred` terminals are absent.

## Reachability

The executable Gate starts from registered hooks, `nollm_memory.execute`, and
the absorption callback, then follows TypeScript calls and the Python bridge
import graph.

```text
legacy reachable count:       0
content-category branches:    0
source-role admission gates:  0
Tool exact Evidence support:  true
production boundary issues:   0
production cycles:            0
```

`adapter.py`, `dream_adapter.py`, `sculptor.py`, `legacy_bridge.py`, and
`legacy_cartographer.py` are classified as `MIGRATION_ASSET` with
`public_api=none`.

## Evidence

```text
validation/aold_single_content_neutral_pipeline_20260724.jsonl
SHA-256: 55c2fd46e16014ec600c064cc2ed3b1fd08d2350e4865df31ca0a2134b9c803a

validation/aold_single_content_neutral_pipeline_summary_20260724.json
status: IN_PROGRESS
provider_calls: 0
gate_g_provider_validated: false
```

The synthetic pipeline gate reopened six Tool Evidence records across UTF-8,
canonical JSON, and base64. It also verified a 20-Statement retry lineage beside
a one-Statement admitted Capture without cross-contamination. The real
128/300/1000-Statement Access/Core routing runs retained zero uncovered source
cells, one selected entry, and Recall-backed output.

## Regression

```text
Core/Snapshot/Trace: 98 passed
Access:              136 passed
OpenClaw Python:     89 passed
OpenClaw Node:       64 passed
Lab:                 58 passed
M0 fixed selection:  49 passed
ownership manifest:  valid, 2092 tracked, 0 unclassified
module boundaries:   production=0, cycles=0
```

An additional non-gate probe of `test_repository_hygiene.py` retains the input
baseline disagreement: the test expects documentation of `python run_tests.py`,
while current README authority explicitly classifies that command as a historical
legacy-inclusive diagnostic. This task did not rewrite that unrelated contract.

## Remaining Gate

Gate G still requires real Provider content diversity, 20+ proposition
continuation across at least three passes, restart/timeout/format-repair evidence,
and live main-agent routing. No Live OpenClaw session, model call, or corpus run
was performed in this stage.

Cross-platform portability was not validated in this stage.
