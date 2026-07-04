# Recall Digest Usage

Recall digest 和 DI1 public envelope 是从显式 admitted workset 读出的派生结果。它们可以帮助外部模型组织上下文，但不能作为新的事实源、truth proof 或隐藏索引。

Recall digest and DI1 public envelopes are derived read results. They help an external model fit explicit admitted evidence into context. They are not source memory, not proof of truth, and not a hidden index.

## Required Distinctions

面向用户回答时必须区分 confirmed、candidate、derived 和 missing_evidence，避免把未准入、未证明或仅验证视图的内容写成已确认事实。

When using a digest in a user-facing answer, separate:

- `confirmed`: backed by host-confirmed Nollm evidence for current notebook use.
- `candidate`: captured or suggested but not admitted or confirmed.
- `derived`: report, projection, digest, or validation view.
- `missing_evidence`: not found inside the current explicit admitted workset.

## Evidence Rules

- A digest must point back to DreamShard and evidence refs.
- A digest summary without evidence refs cannot be upgraded to confirmed fact.
- A missed recall means only that the explicit admitted workset did not return a hit.
- Captured-only and deferred items stay outside formal geometry recall unless the host admits them later.

## Geometry And DG6 Rules

- DG6 compacted view is verification-only.
- Geometry, cover, gravity, chart, cell, route, or trace details must not be presented as factual user conclusions.
- DG6 must not filter, rank, replace, or influence DR1/DI1 recall.

## Safe Answer Shape

```text
Confirmed from current admitted workset:
- ...

Candidate or captured-only material:
- ...

Derived validation view:
- ...

Missing evidence inside current explicit workset:
- ...
```
