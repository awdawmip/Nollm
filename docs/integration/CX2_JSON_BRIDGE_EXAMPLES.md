# CX2 JSON Bridge Examples

以下 JSON 是声明性 plan / tool envelope 示例，只用于 host review 或 validator conformance。它们不是自动运行请求，也不代表 Core 已经执行。

These examples are declaration-only plan or tool-envelope examples. They are not automatic runtime calls.

## Capture-Only Plan

<!-- cx2-plan:start capture_only -->
```json
{
  "plan_kind": "nollm_cortex_action_plan",
  "plan_version": "1",
  "plan_id": "cx2_example_capture",
  "intent": "capture_only",
  "capture_refs": [
    {
      "capture_id": "cap_example_01",
      "shard_id": "shard_example_01",
      "persistence_state": "captured",
      "admission_state": "deferred",
      "usage_state": "tentative",
      "visibility_scope": "current_turn"
    }
  ],
  "non_inferences": [
    "no_automatic_admission",
    "no_global_discovery",
    "no_anchor_creation",
    "no_truth_confirmation",
    "no_dg6_recall_influence"
  ]
}
```
<!-- cx2-plan:end -->

## Explicit Admission And Recall Plan

<!-- cx2-plan:start mixed_explicit -->
```json
{
  "plan_kind": "nollm_cortex_action_plan",
  "plan_version": "1",
  "plan_id": "cx2_example_mixed",
  "intent": "mixed_explicit",
  "capture_refs": [
    {
      "capture_id": "cap_example_a",
      "shard_id": "shard_example_a",
      "persistence_state": "captured",
      "admission_state": "candidate",
      "usage_state": "active",
      "visibility_scope": "source_window"
    },
    {
      "capture_id": "cap_example_b",
      "shard_id": "shard_example_b",
      "persistence_state": "captured",
      "admission_state": "candidate",
      "usage_state": "active",
      "visibility_scope": "source_window"
    }
  ],
  "promotion_decisions": [
    {
      "decision_id": "pmd_example_a",
      "candidate_id": "dac_example_a",
      "shard_id": "shard_example_a",
      "decision": "promote",
      "reasons": ["explicit_pin", "source_backed_fact"],
      "decided_by": "host_rule"
    },
    {
      "decision_id": "pmd_example_b",
      "candidate_id": "dac_example_b",
      "shard_id": "shard_example_b",
      "decision": "promote",
      "reasons": ["task_dependency", "manual_batch_selection"],
      "decided_by": "human_operator"
    }
  ],
  "admission_request_refs": [
    {
      "request_id": "admreq_example_a",
      "decision_id": "pmd_example_a",
      "shard_id": "shard_example_a",
      "proposal_ref": "opaque-host-proposal-a",
      "placement_plan_ref": "opaque-host-placement-a"
    },
    {
      "request_id": "admreq_example_b",
      "decision_id": "pmd_example_b",
      "shard_id": "shard_example_b",
      "proposal_ref": "opaque-host-proposal-b",
      "placement_plan_ref": "opaque-host-placement-b"
    }
  ],
  "explicit_assembly": {
    "admission_ids": ["adm_example_a", "adm_example_b"],
    "declared_by": "host",
    "purpose": "explicit finite host workset"
  },
  "recall_request": {
    "query_ref": "opaque-host-query",
    "memory_intent": "verification",
    "admitted_workset_ref": "explicit-finite-admitted-workset",
    "max_cards": 4,
    "max_layers": 3
  },
  "non_inferences": [
    "no_automatic_admission",
    "no_global_discovery",
    "no_anchor_creation",
    "no_truth_confirmation",
    "no_dg6_recall_influence"
  ]
}
```
<!-- cx2-plan:end -->

## Structured Success Envelope

This is only a validator summary. It is not a Core execution result, AdmissionRecord, FieldSnapshot, RecallUniverse, ledger event, or recall response.

```json
{
  "ok": true,
  "kind": "nollm_cx2_cortex_action_plan_summary",
  "result": {
    "plan_id": "cx2_example_mixed",
    "intent": "mixed_explicit",
    "capture_ref_count": 2,
    "promotion_decision_count": 2,
    "admission_request_count": 2,
    "explicit_assembly_admission_ids": ["adm_example_a", "adm_example_b"],
    "has_recall_request": true,
    "derived_view_count": 0
  }
}
```

## Structured Rejection Envelope

This is only a validator rejection. It is not a runtime response and does not execute or roll back Core state.

```json
{
  "ok": false,
  "kind": "nollm_cx2_cortex_action_plan_error",
  "reason_code": "CX2_INVALID_EXPLICIT_ASSEMBLY",
  "message": "explicit assembly admission ids must be non-empty, unique strings"
}
```
