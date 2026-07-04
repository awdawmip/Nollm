# CX2 JSON Bridge Examples

以下 JSON 是声明性 plan / tool envelope 示例，只用于 host review 或 validator conformance。它们不是自动运行请求，也不代表 Core 已经执行。

These examples are declaration-only plan or tool-envelope examples. They are not automatic runtime calls.

## Capture-Only Plan

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

## Explicit Admission And Recall Plan

```json
{
  "plan_kind": "nollm_cortex_action_plan",
  "plan_version": "1",
  "plan_id": "cx2_example_mixed",
  "intent": "mixed_explicit",
  "promotion_decisions": [
    {
      "decision_id": "pmd_example_a",
      "candidate_id": "dac_example_a",
      "shard_id": "shard_example_a",
      "decision": "promote",
      "reasons": ["explicit_pin", "source_backed_fact"],
      "decided_by": "host_rule"
    }
  ],
  "admission_request_refs": [
    {
      "request_id": "admreq_example_a",
      "decision_id": "pmd_example_a",
      "shard_id": "shard_example_a",
      "proposal_ref": "opaque-host-proposal-a",
      "placement_plan_ref": "opaque-host-placement-a"
    }
  ],
  "explicit_assembly": {
    "admission_ids": ["adm_example_a"],
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

## Structured Rejection Envelope

```json
{
  "ok": false,
  "kind": "nollm_cx2_cortex_action_plan_error",
  "reason_code": "CX2_INVALID_EXPLICIT_ASSEMBLY",
  "message": "explicit assembly admission ids must be non-empty, unique strings"
}
```
