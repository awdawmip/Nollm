# Read / Write Policy

CX2 的读写策略用于防止 Cortex 把建议、解释或 digest 误写成事实。Core 保存、验证和返回公开结果；Cortex 只提出、解释和请求 host 输入。

CX2 defines how a trusted internal host or external model should talk about Nollm work without turning Cortex into a runtime.

## Responsibility Matrix

| Task | Cortex may do | Host / human must provide | Cortex must not do |
|---|---|---|---|
| Capture | Form original-text candidates and policy suggestions. | Content, origin, context refs, visibility, policy. | Auto-structure facts, global search, automatic summary, hidden persistence. |
| Promotion | Suggest enumerable reasons for review. | Final decision, selected candidates, decision provenance. | Automatic admission, "model important" as sole reason, semantic truth scoring. |
| Admission | List required materials and opaque refs. | Proposal ref, placement plan ref, shard id, admission request. | Generate geometry placement, anchors, charts, cells, or AdmissionRecord payloads. |
| Assembly | Remind host to declare a finite admitted set. | Ordered explicit admission IDs. | Discover all related admissions, use captured pool, build FieldSnapshot payloads. |
| Recall | Interpret public digest/envelope and suggest rescale questions. | Query ref, explicit admitted workset ref, budgets. | Mix captured-only material, rank with DG6, use vector search, claim global absence. |

## Read Boundary

Read results are explicit outputs from Core or validation packages. A recall digest is a context-sized derived read result, not a new fact source.

Cortex must preserve evidence refs when explaining a digest. Without DreamShard or evidence refs, a summary cannot become a confirmed fact.

## Write Boundary

Cortex 不直接写 Nollm durable state。所有写入必须通过 host 明确提交的公开路径完成。

Cortex may propose writes. It does not write durable Nollm state by itself.

A durable write must be host-owned and use the relevant public path:

- Capture through explicit CaptureRequest.
- Promotion through explicit host/human decision.
- Admission through DA1-compatible request and real host-held proposal/placement refs.
- Assembly through explicit finite admitted IDs.
- Recall through explicit query and admitted workset.

## Pollution Guards

- Do not write inference as fact.
- Do not treat `candidate`, `captured`, `deferred`, `superseded`, `rejected`, or `archived` as confirmed.
- Do not create anchors automatically.
- Do not use DG6, cover, gravity, route, chart, cell, or geometry as factual proof.
- Do not treat validator pass as execution approval.
- Do not persist CortexActionPlan as source memory.
- Do not read or write `MEMORY.md`, `DREAMS.md`, or `memory/*.md` through this pack.
