from __future__ import annotations

from dataclasses import FrozenInstanceError

from nollm.dream_geometry.validation.cx2.fixtures import valid_explicit_admission_and_recall_plan
from nollm.dream_geometry.validation.cx2.fixtures import invalid_fixtures, valid_fixtures
from nollm.dream_geometry.validation.cx2.types import (
    AdmissionRequestRef,
    CaptureRef,
    CortexActionPlan,
    DerivedViewRef,
    ExplicitAssembly,
    PromotionDecision,
    RecallRequest,
)
from nollm.dream_geometry.validation.cx2.types import CX2PlanValidationError
from nollm.dream_geometry.validation.cx2.validator import validate_cortex_action_plan


def test_cx2_valid_fixtures_produce_canonical_summaries() -> None:
    results = {name: validate_cortex_action_plan(plan) for name, plan in valid_fixtures()}

    assert results["CX2-VALID-01"].intent == "capture_only"
    assert results["CX2-VALID-01"].capture_ref_count == 1
    assert results["CX2-VALID-01"].has_recall_request is False
    assert results["CX2-VALID-02"].explicit_assembly_admission_ids == ("adm_valid_02a", "adm_valid_02b")
    assert results["CX2-VALID-02"].has_recall_request is True
    assert results["CX2-VALID-03"].promotion_decision_count == 1
    assert results["CX2-VALID-04"].derived_view_count == 1


def test_cx2_invalid_fixtures_fail_with_stable_reason_codes() -> None:
    observed: dict[str, str] = {}
    for name, plan, expected in invalid_fixtures():
        try:
            validate_cortex_action_plan(plan)
        except CX2PlanValidationError as exc:
            observed[name] = exc.reason_code
            assert exc.reason_code == expected
            assert "Traceback" not in str(exc)
            assert "\\" not in str(exc)
            assert "nollm.dream_geometry" not in str(exc)
        else:
            raise AssertionError(f"{name} unexpectedly passed")

    assert observed["CX2-INVALID-01"] == "CX2_FORBIDDEN_AUTOMATION"
    assert observed["CX2-INVALID-04"] == "CX2_INVALID_EXPLICIT_ASSEMBLY"
    assert observed["CX2-INVALID-09"] == "CX2_FORBIDDEN_DG6_INFERENCE"


def test_cx2_plan_values_are_immutable() -> None:
    _name, plan = valid_fixtures()[0]

    try:
        plan.plan_id = "cx2_mutated"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("CortexActionPlan must be immutable")


def test_cx2_mapping_input_rejects_unknown_and_forbidden_fields() -> None:
    base = {
        "plan_kind": "nollm_cortex_action_plan",
        "plan_version": "1",
        "plan_id": "cx2_mapping_unknown",
        "intent": "capture_only",
        "capture_refs": [
            {
                "capture_id": "cap_mapping",
                "shard_id": "shard_mapping",
                "persistence_state": "captured",
                "admission_state": "deferred",
                "usage_state": "tentative",
                "visibility_scope": "current_turn",
                "extra": "not allowed",
            }
        ],
        "non_inferences": [
            "no_automatic_admission",
            "no_global_discovery",
            "no_anchor_creation",
            "no_truth_confirmation",
            "no_dg6_recall_influence",
        ],
    }

    try:
        validate_cortex_action_plan(base)
    except CX2PlanValidationError as exc:
        assert exc.reason_code == "CX2_INVALID_PLAN"
    else:
        raise AssertionError("unknown field unexpectedly passed")

    forbidden = dict(base)
    forbidden.pop("capture_refs")
    forbidden["vector_query"] = "nearest"
    try:
        validate_cortex_action_plan(forbidden)
    except CX2PlanValidationError as exc:
        assert exc.reason_code == "CX2_FORBIDDEN_AUTOMATION"
    else:
        raise AssertionError("forbidden field unexpectedly passed")


def test_cx2_dataclass_input_recursively_rejects_forbidden_values() -> None:
    plan = valid_explicit_admission_and_recall_plan()
    mutated = plan.__class__(
        plan_kind=plan.plan_kind,
        plan_version=plan.plan_version,
        plan_id="cx2_dataclass_forbidden_value",
        intent=plan.intent,
        capture_refs=plan.capture_refs,
        promotion_decisions=plan.promotion_decisions,
        admission_request_refs=plan.admission_request_refs,
        explicit_assembly=plan.explicit_assembly,
        recall_request=RecallRequest("global_search", "verification", "explicit-finite-workset", 3, 1),
        derived_views=plan.derived_views,
        non_inferences=plan.non_inferences,
    )

    try:
        validate_cortex_action_plan(mutated)
    except CX2PlanValidationError as exc:
        assert exc.reason_code == "CX2_FORBIDDEN_AUTOMATION"
    else:
        raise AssertionError("dataclass forbidden value unexpectedly passed")


def test_cx2_mapping_reasons_are_normalized_to_immutable_tuple() -> None:
    mapping = {
        "plan_kind": "nollm_cortex_action_plan",
        "plan_version": "1",
        "plan_id": "cx2_mapping_reasons_tuple",
        "intent": "admission",
        "promotion_decisions": [
            {
                "decision_id": "pmd_mapping_tuple",
                "candidate_id": "dac_mapping_tuple",
                "shard_id": "shard_mapping_tuple",
                "decision": "promote",
                "reasons": ["explicit_pin"],
                "decided_by": "host_rule",
            }
        ],
        "admission_request_refs": [
            {
                "request_id": "admreq_mapping_tuple",
                "decision_id": "pmd_mapping_tuple",
                "shard_id": "shard_mapping_tuple",
                "proposal_ref": "opaque-proposal",
                "placement_plan_ref": "opaque-placement",
            }
        ],
        "non_inferences": [
            "no_automatic_admission",
            "no_global_discovery",
            "no_anchor_creation",
            "no_truth_confirmation",
            "no_dg6_recall_influence",
        ],
    }

    summary = validate_cortex_action_plan(mapping)

    assert summary.promotion_decision_count == 1


def test_cx2_c1_01_mapping_shape_failures_are_structured() -> None:
    base = _valid_capture_only_mapping()
    cases = (
        ("capture_refs", None, "CX2_INVALID_PLAN"),
        ("promotion_decisions", None, "CX2_INVALID_PROMOTION"),
        ("admission_request_refs", None, "CX2_INVALID_ADMISSION_REQUEST"),
        ("derived_views", None, "CX2_INVALID_PLAN"),
        ("non_inferences", None, "CX2_INVALID_PLAN"),
        ("capture_refs", "bad", "CX2_INVALID_PLAN"),
        ("promotion_decisions", {"bad": True}, "CX2_INVALID_PROMOTION"),
    )

    for field, value, reason in cases:
        payload = dict(base)
        payload[field] = value
        _assert_structured_error(payload, reason)

    promotion_bad = _valid_admission_mapping()
    promotion_bad["promotion_decisions"][0]["reasons"] = None
    _assert_structured_error(promotion_bad, "CX2_INVALID_PROMOTION")

    assembly_bad = _valid_recall_mapping()
    assembly_bad["explicit_assembly"]["admission_ids"] = None
    _assert_structured_error(assembly_bad, "CX2_INVALID_EXPLICIT_ASSEMBLY")


def test_cx2_c1_02_direct_dataclass_nested_shape_failures_are_structured() -> None:
    plan = valid_explicit_admission_and_recall_plan()
    cases = (
        ("capture_refs", ("bad",), "CX2_INVALID_PLAN"),
        ("promotion_decisions", ("bad",), "CX2_INVALID_PROMOTION"),
        ("admission_request_refs", ("bad",), "CX2_INVALID_ADMISSION_REQUEST"),
        ("explicit_assembly", "bad", "CX2_INVALID_EXPLICIT_ASSEMBLY"),
        ("recall_request", "bad", "CX2_INVALID_RECALL_REQUEST"),
        ("derived_views", ("bad",), "CX2_INVALID_PLAN"),
    )

    for field, value, reason in cases:
        _assert_structured_error(CortexActionPlan(**{**_plan_dict(plan), field: value}), reason)


def _assert_structured_error(plan, reason_code: str) -> None:
    try:
        validate_cortex_action_plan(plan)
    except CX2PlanValidationError as exc:
        assert type(exc) is CX2PlanValidationError
        assert exc.reason_code == reason_code
        rendered = str(exc)
        for forbidden in ("Traceback", "TypeError", "AttributeError", "KeyError", "ValueError", "\\", "nollm.dream_geometry"):
            assert forbidden not in rendered
    else:
        raise AssertionError(f"plan unexpectedly passed; expected {reason_code}")


def _valid_capture_only_mapping() -> dict:
    return {
        "plan_kind": "nollm_cortex_action_plan",
        "plan_version": "1",
        "plan_id": "cx2_valid_capture_mapping",
        "intent": "capture_only",
        "capture_refs": [
            {
                "capture_id": "cap_shape",
                "shard_id": "shard_shape",
                "persistence_state": "captured",
                "admission_state": "deferred",
                "usage_state": "tentative",
                "visibility_scope": "current_turn",
            }
        ],
        "non_inferences": [
            "no_automatic_admission",
            "no_global_discovery",
            "no_anchor_creation",
            "no_truth_confirmation",
            "no_dg6_recall_influence",
        ],
    }


def _valid_admission_mapping() -> dict:
    payload = _valid_capture_only_mapping()
    payload.update(
        {
            "plan_id": "cx2_valid_admission_mapping",
            "intent": "admission",
            "capture_refs": [],
            "promotion_decisions": [
                {
                    "decision_id": "pmd_shape",
                    "candidate_id": "dac_shape",
                    "shard_id": "shard_shape",
                    "decision": "promote",
                    "reasons": ["explicit_pin"],
                    "decided_by": "host_rule",
                }
            ],
            "admission_request_refs": [
                {
                    "request_id": "admreq_shape",
                    "decision_id": "pmd_shape",
                    "shard_id": "shard_shape",
                    "proposal_ref": "opaque-proposal",
                    "placement_plan_ref": "opaque-placement",
                }
            ],
        }
    )
    return payload


def _valid_recall_mapping() -> dict:
    payload = _valid_capture_only_mapping()
    payload.update(
        {
            "plan_id": "cx2_valid_recall_mapping",
            "intent": "recall",
            "capture_refs": [],
            "explicit_assembly": {
                "admission_ids": ["adm_shape"],
                "declared_by": "host",
                "purpose": "explicit finite host workset",
            },
            "recall_request": {
                "query_ref": "opaque-query",
                "memory_intent": "verification",
                "admitted_workset_ref": "explicit-finite-workset",
                "max_cards": 1,
                "max_layers": 1,
            },
        }
    )
    return payload


def _plan_dict(plan):
    return {
        "plan_kind": plan.plan_kind,
        "plan_version": plan.plan_version,
        "plan_id": plan.plan_id,
        "intent": plan.intent,
        "capture_refs": plan.capture_refs,
        "promotion_decisions": plan.promotion_decisions,
        "admission_request_refs": plan.admission_request_refs,
        "explicit_assembly": plan.explicit_assembly,
        "recall_request": plan.recall_request,
        "derived_views": plan.derived_views,
        "non_inferences": plan.non_inferences,
    }
