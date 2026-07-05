# CX2 CortexActionPlan v1

CX2 的 `CortexActionPlan` 是给可信内部 host、Codex 或外部模型使用的声明性计划对象。它用于提交前审查，不执行 Core 行为，不写 durable state，也不代表任何事实已经被采纳。

`CortexActionPlan` is a machine-readable, declaration-only plan for trusted internal hosts and external models. It is reviewable before any Core action. It is not executable and does not write durable state.

## Object Nature

`CortexActionPlan` is:

- host or external-model suggestion for one finite workflow;
- a way to keep Capture, Promotion, Admission, Assembly, and Recall distinct;
- a conformance object for validation-only tests;
- immutable in the Python validation package.

It is not:

- DreamShard;
- DeferredAdmissionCandidate;
- GrowthProposal;
- PlacementPlan;
- AdmissionRecord;
- FieldSnapshot;
- RecallUniverse;
- recall result;
- ledger event;
- runtime command.

## Minimal Shape

```yaml
plan_kind: nollm_cortex_action_plan
plan_version: "1"
plan_id: cx2_...
intent: capture_only | admission | recall | mixed_explicit
capture_refs: []
promotion_decisions: []
admission_request_refs: []
explicit_assembly:
  admission_ids: [adm_...]
  declared_by: host | user | human_operator
  purpose: explicit finite text
recall_request:
  query_ref: opaque-host-reference
  memory_intent: recall_focus | orientation | verification
  admitted_workset_ref: explicit finite host reference
  max_cards: positive integer
  max_layers: positive integer
non_inferences:
  - no_automatic_admission
  - no_global_discovery
  - no_anchor_creation
  - no_truth_confirmation
  - no_dg6_recall_influence
```

Opaque references are host-held pointers. They are not global query keys.

## Required Semantics

- Capture、Admission、Usage、Visibility 四类状态必须分开表达，不能互相代替。
- Promotion 只能给出可枚举原因和来源；`cortex_suggestion` 只是建议来源，不是 host 确认。
- 被 admission request 引用的 promote decision 必须来自 `host_rule`、`user` 或 `human_operator`；`cortex_suggestion` 不能直接绑定 admission request。
- Assembly 的 admission IDs 必须由 host/user/human operator 明确给出，不能由 Cortex 自动发现。
- Recall 必须绑定显式 admitted workset；未命中只表示当前 workset 内未命中。
- DG6 只能作为 view-only 验证语境；DG7 只能作为显式有限链 correspondence witness。

- Capture persistence state, admission state, usage state, and visibility scope are separate.
- Promotion has enumerable reasons and provenance.
- Admission requests may reference only promote decisions.
- Explicit assembly admission IDs are non-empty, ordered, unique, and host/user/human declared.
- Recall always references an explicit admitted workset.
- DG6 may appear only as view-only verification context.
- The plan must list forbidden non-inferences.

## Rejected Fields

The CX2 validator rejects forbidden automation and payload fields such as:

```text
semantic_embedding
vector_query
similarity_threshold
global_search
auto_anchor
auto_axis
auto_chart
auto_cell
auto_cover
auto_parent
truth_score
importance_score
auto_admit
runtime_command
network_endpoint
cache_key
database_query
field_snapshot_payload
admission_record_payload
recall_result_payload
```

## Non-Equivalence Rules

```text
CortexActionPlan(decision=promote) != DA1 admission completed
explicit_assembly.admission_ids != DF1 snapshot built
recall_request != DR1 / DI1 result
cortex_suggestion != human or host confirmation
validator pass != execution approval
```
