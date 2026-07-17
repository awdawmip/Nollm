# Nollm Architecture Amendment V3.10: Durable Capture And Async Absorption

Date: 2026-07-17

Status: active implementation amendment

## Decision

The visible conversation path ends after an immutable local Capture is durably published. Formation, semantic Placement, revision confirmation, and Admission are background absorption work and never define whether the original conversation was preserved.

```text
visible user and assistant turn
  -> OpenClaw-owned immutable Capture
  -> recoverable file spool
  -> bounded background batch Formation and Placement
  -> Access Statement, HandleBinding, and Core Atom
```

Until Admission completes, a bounded time-ordered scan of recent Capture files provides read-your-recent-writes. It uses scope, age, count, and character budgets only. It has no query, keyword, topic, source, vector, graph, or object relation index. Admission, terminal no-memory, or terminal defer removes a Capture from active Pending injection while preserving the immutable original.

## Ownership

- OpenClaw uniquely owns Capture files, state events, worker claims, retry scheduling, pending rendering, and Host correlation.
- Access owns canonical Statement validation, finite geometry entry projection, Placement validation, HandleBinding, and Admission readback.
- Core remains unchanged and owns geometry state and Recall execution.
- Lab owns fault injection, timing validation, Live evidence, and reports.
- Distributions declare configuration only.

Capture is not an Access Statement and is not a Core fact. State events never overwrite Capture bytes. Missing state events can be reconstructed from Capture files; stale processing claims are recoverable. The worker has one file lock and one process-local execution lease per spool.

## Recall

Pending Recall performs zero Provider, bridge, Surface, and Core calls. Admitted Recall projects a finite geometry-ordered physical entry view. A mechanical singleton uses zero hidden calls; otherwise one hidden semantic call selects one supplied entry or NONE. Core then recalls that single entry and the bounded Locality is injected directly into the main agent. No second Statement-selection agent runs.

## Batch Admission

Batch Formation uses one hidden call for multiple Captures. Every formed Statement carries the sorted Capture references for its bounded source batch. One frozen finite geometry view feeds one batch Placement call. Access validates every decision against that view, then applies each Statement through its existing independent atomic transaction and durable reopen check. A failed Statement is reported without rolling back or contaminating successful independent Admissions. Replay recognizes an already bound Statement before attempting another Core write. Destructive revision remains on the existing separate bounded confirmation path.

This topology satisfies the deterministic common-case call budget. Provider-backed Windows Live must still prove that the Host executes the same one-Formation and one-Placement topology before the task can be marked fully validated.

## Compatibility

Existing V1-V6 Statement, Handle, Core, and Evidence data is read without migration. Historical conversations are not backfilled into Capture. Enabling V3.10 adds only a new Capture spool. No old workspace is deleted or rewritten.
