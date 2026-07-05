# CX2 External Model Boundary

本文件定义外部 LLM、Codex 或 host-side Cortex 在 Nollm 中的可用边界。模型可以提出建议和计划，但不能把建议改写成已执行、已确认、已准入或已召回。

CX2 defines a conformance pack for external LLM, Codex, or host-side Cortex usage. It does not add a runtime surface.

## Allowed Model Behavior

An external model may:

- propose Capture candidates;
- suggest Promotion reasons from the CX2 enum;
- ask the host for missing proposal, placement, query, or finite workset refs;
- produce a CortexActionPlan for host review;
- explain a DI1 public envelope with evidence distinctions;
- report recall misses as scoped to the explicit admitted workset.

## Host-Owned Inputs

host / user / human operator 拥有所有会改变 Nollm 状态或限定正式读取范围的输入。Cortex 只能请求这些输入或解释其后果，不能替 host 生成。

The host, user, or human operator owns:

- capture content, origin, context, policy, and visibility;
- final promotion decision and selected candidate set;
- admission request IDs, proposal refs, and placement plan refs;
- explicit assembly admission IDs;
- query refs, finite admitted workset refs, and recall budgets.

`cortex_suggestion` may appear as a suggestion provenance label. It is not final promotion authority and cannot be used as the decision source for an admission request in the same plan.

## Forbidden Model Behavior

The external model must not:

- invent GrowthProposal or PlacementPlan payloads;
- create anchor, chart, cell, cover, route, or geometry choices;
- perform automatic admission or global discovery;
- call LLM APIs, embeddings, network, database, OpenClaw, runtime, cache, daemon, or session systems through CX2;
- treat DG6 as recall ranking or evidence replacement;
- treat DG7 as production runtime;
- confirm truth from a digest or validation report.

## Review Labels

Use these labels in handoff:

- `verified_fact`
- `host_input`
- `cortex_suggestion`
- `derived_view`
- `forbidden_inference`

The labels are communication aids. They are not Core status fields.
