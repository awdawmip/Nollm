"""Synthetic CX2 conformance fixtures."""

from __future__ import annotations

from dataclasses import replace

from .types import (
    AdmissionRequestRef,
    CaptureRef,
    CortexActionPlan,
    DerivedViewRef,
    ExplicitAssembly,
    PromotionDecision,
    RecallRequest,
)
from .validator import REQUIRED_NON_INFERENCES


def valid_capture_only_plan() -> CortexActionPlan:
    return CortexActionPlan(
        plan_kind="nollm_cortex_action_plan",
        plan_version="1",
        plan_id="cx2_valid_capture_only",
        intent="capture_only",
        capture_refs=(
            CaptureRef(
                capture_id="cap_valid_01",
                shard_id="shard_valid_01",
                persistence_state="captured",
                admission_state="deferred",
                usage_state="tentative",
                visibility_scope="current_turn",
            ),
        ),
        non_inferences=REQUIRED_NON_INFERENCES,
    )


def valid_explicit_admission_and_recall_plan() -> CortexActionPlan:
    return CortexActionPlan(
        plan_kind="nollm_cortex_action_plan",
        plan_version="1",
        plan_id="cx2_valid_explicit_admission_recall",
        intent="mixed_explicit",
        capture_refs=(
            CaptureRef("cap_valid_02a", "shard_valid_02a", "captured", "candidate", "active", "source_window"),
            CaptureRef("cap_valid_02b", "shard_valid_02b", "captured", "candidate", "active", "source_window"),
        ),
        promotion_decisions=(
            PromotionDecision(
                "pmd_valid_02a",
                "dac_valid_02a",
                "shard_valid_02a",
                "promote",
                ("explicit_pin", "source_backed_fact"),
                "host_rule",
            ),
            PromotionDecision(
                "pmd_valid_02b",
                "dac_valid_02b",
                "shard_valid_02b",
                "promote",
                ("task_dependency", "manual_batch_selection"),
                "human_operator",
            ),
        ),
        admission_request_refs=(
            AdmissionRequestRef("admreq_valid_02a", "pmd_valid_02a", "shard_valid_02a", "opaque-host-proposal-a", "opaque-host-placement-a"),
            AdmissionRequestRef("admreq_valid_02b", "pmd_valid_02b", "shard_valid_02b", "opaque-host-proposal-b", "opaque-host-placement-b"),
        ),
        explicit_assembly=ExplicitAssembly(("adm_valid_02a", "adm_valid_02b"), "host", "explicit finite DG7-style admitted workset"),
        recall_request=RecallRequest("opaque-host-query-02", "verification", "explicit-finite-admitted-workset-02", 4, 3),
        non_inferences=REQUIRED_NON_INFERENCES,
    )


def valid_do_not_admit_with_source_window_plan() -> CortexActionPlan:
    return CortexActionPlan(
        plan_kind="nollm_cortex_action_plan",
        plan_version="1",
        plan_id="cx2_valid_do_not_admit",
        intent="capture_only",
        capture_refs=(
            CaptureRef("cap_valid_03", "shard_valid_03", "persistent", "do_not_admit", "retired", "source_window"),
        ),
        promotion_decisions=(
            PromotionDecision("pmd_valid_03", "dac_valid_03", "shard_valid_03", "do_not_admit", ("revision_event",), "user"),
        ),
        non_inferences=REQUIRED_NON_INFERENCES,
    )


def valid_dg6_view_only_plan() -> CortexActionPlan:
    return replace(
        valid_explicit_admission_and_recall_plan(),
        plan_id="cx2_valid_dg6_view_only",
        derived_views=(DerivedViewRef("dg6_compacted_view", "opaque-dg6-projection-ref", "verification_only"),),
    )


def dg7_correspondence_fixture() -> dict[str, object]:
    return {
        "fixture_id": "CX2-DG7-CORRESPONDENCE-01",
        "statement": (
            "DG7 A/B/C/D is an accepted finite positive chain instance for boundary language only; "
            "CX2 does not run DG7 as an external model runtime."
        ),
        "assembled_admission_ids": ("adm_dg7_a", "adm_dg7_b"),
        "captured_only_admission_ids": ("adm_dg7_c",),
        "admitted_unassembled_ids": ("adm_dg7_d",),
    }


def valid_fixtures() -> tuple[tuple[str, CortexActionPlan], ...]:
    return (
        ("CX2-VALID-01", valid_capture_only_plan()),
        ("CX2-VALID-02", valid_explicit_admission_and_recall_plan()),
        ("CX2-VALID-03", valid_do_not_admit_with_source_window_plan()),
        ("CX2-VALID-04", valid_dg6_view_only_plan()),
    )


def invalid_fixtures() -> tuple[tuple[str, object, str], ...]:
    valid = valid_explicit_admission_and_recall_plan()
    return (
        (
            "CX2-INVALID-01",
            {
                "plan_kind": "nollm_cortex_action_plan",
                "plan_version": "1",
                "plan_id": "cx2_invalid_auto_admit",
                "intent": "admission",
                "auto_admit": True,
                "promotion_decisions": [
                    {
                        "decision_id": "pmd_invalid_01",
                        "candidate_id": "dac_invalid_01",
                        "shard_id": "shard_invalid_01",
                        "decision": "promote",
                        "reasons": ["model_important"],
                        "decided_by": "cortex_suggestion",
                    }
                ],
                "non_inferences": list(REQUIRED_NON_INFERENCES),
            },
            "CX2_FORBIDDEN_AUTOMATION",
        ),
        (
            "CX2-INVALID-02",
            replace(valid, plan_id="cx2_invalid_missing_reason", promotion_decisions=(PromotionDecision("pmd_invalid_02", "dac_invalid_02", "shard_invalid_02", "promote", (), "host_rule"),)),
            "CX2_INVALID_PROMOTION",
        ),
        (
            "CX2-INVALID-03",
            replace(
                valid,
                plan_id="cx2_invalid_defer_admission",
                promotion_decisions=(PromotionDecision("pmd_invalid_03", "dac_invalid_03", "shard_invalid_03", "defer", ("session_closure",), "host_rule"),),
                admission_request_refs=(AdmissionRequestRef("admreq_invalid_03", "pmd_invalid_03", "shard_invalid_03", "opaque-proposal", "opaque-placement"),),
            ),
            "CX2_INVALID_ADMISSION_REQUEST",
        ),
        (
            "CX2-INVALID-04",
            replace(valid, plan_id="cx2_invalid_duplicate_assembly", explicit_assembly=ExplicitAssembly(("adm_dup", "adm_dup"), "host", "explicit finite set")),
            "CX2_INVALID_EXPLICIT_ASSEMBLY",
        ),
        (
            "CX2-INVALID-05",
            replace(valid, plan_id="cx2_invalid_recall_no_workset", recall_request=RecallRequest("opaque-query", "verification", "", 3, 1)),
            "CX2_INVALID_RECALL_REQUEST",
        ),
        (
            "CX2-INVALID-06",
            replace(valid, plan_id="cx2_invalid_global_vector", recall_request=RecallRequest("opaque-query", "verification", "global_discovery", 3, 1)),
            "CX2_FORBIDDEN_AUTOMATION",
        ),
        (
            "CX2-INVALID-07",
            {"plan_kind": "nollm_cortex_action_plan", "plan_version": "1", "plan_id": "cx2_invalid_auto_anchor", "intent": "capture_only", "auto_anchor": True},
            "CX2_FORBIDDEN_AUTOMATION",
        ),
        (
            "CX2-INVALID-08",
            {"plan_kind": "nollm_cortex_action_plan", "plan_version": "1", "plan_id": "cx2_invalid_truth_score", "intent": "capture_only", "truth_score": 0.98},
            "CX2_FORBIDDEN_AUTOMATION",
        ),
        (
            "CX2-INVALID-09",
            replace(valid_dg6_view_only_plan(), plan_id="cx2_invalid_dg6_rank", derived_views=(DerivedViewRef("dg6_compacted_view", "opaque-dg6", "recall_rank"),)),
            "CX2_FORBIDDEN_DG6_INFERENCE",
        ),
        (
            "CX2-INVALID-10",
            {"plan_kind": "nollm_cortex_action_plan", "plan_version": "1", "plan_id": "cx2_invalid_payload", "intent": "capture_only", "field_snapshot_payload": {}},
            "CX2_INVALID_PLAN",
        ),
    )


def all_fixtures() -> tuple[tuple[str, object], ...]:
    return tuple((name, plan) for name, plan in valid_fixtures()) + tuple((name, plan) for name, plan, _code in invalid_fixtures())


__all__ = [
    "all_fixtures",
    "dg7_correspondence_fixture",
    "invalid_fixtures",
    "valid_fixtures",
]
