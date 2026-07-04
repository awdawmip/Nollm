from __future__ import annotations

from dataclasses import FrozenInstanceError

from nollm.dream_geometry.validation.cx2.fixtures import valid_explicit_admission_and_recall_plan
from nollm.dream_geometry.validation.cx2.fixtures import invalid_fixtures, valid_fixtures
from nollm.dream_geometry.validation.cx2.types import RecallRequest
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
