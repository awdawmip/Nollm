from __future__ import annotations

from copy import copy
from dataclasses import replace

import pytest

from nollm.dream_geometry.host_execution import HX1ExecutionError, HostPlanBindings, execute_host_plan
from nollm.dream_geometry.validation.cx2.types import AdmissionRequestRef, ExplicitAssembly, PromotionDecision

from test_hx1_trusted_host_bridge import _admission_binding, hx1_fixture


def test_hx1_05_missing_capture_binding_rejects_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    bindings = replace(fixture["bindings"], capture_bindings=fixture["bindings"].capture_bindings[:-1])
    _assert_zero_write(fixture["plan"], bindings, fixture["context"], tmp_path / "work")


def test_hx1_05_capture_request_id_mismatch_rejects_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    first = fixture["bindings"].capture_bindings[0]
    bad_request = replace(first.request, capture_id="cap_hx1_wrong")
    bindings = replace(fixture["bindings"], capture_bindings=(replace(first, request=bad_request),) + fixture["bindings"].capture_bindings[1:])
    _assert_zero_write(fixture["plan"], bindings, fixture["context"], tmp_path / "work")


def test_hx1_05_admission_proposal_mismatch_rejects_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    first = fixture["bindings"].admission_bindings[0]
    bindings = replace(fixture["bindings"], admission_bindings=(replace(first, proposal_ref="gp_hx1_wrong"),) + fixture["bindings"].admission_bindings[1:])
    _assert_zero_write(fixture["plan"], bindings, fixture["context"], tmp_path / "work")


def test_hx1_05_query_workset_mismatch_rejects_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    recall = replace(fixture["bindings"].recall_binding, admitted_workset_ref="workset:hx1:wrong")
    bindings = replace(fixture["bindings"], recall_binding=recall)
    _assert_zero_write(fixture["plan"], bindings, fixture["context"], tmp_path / "work")


def test_hx1_05_extra_undisclosed_binding_rejects_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    extra = fixture["bindings"].capture_bindings[0]
    bindings = replace(fixture["bindings"], capture_bindings=fixture["bindings"].capture_bindings + (replace(extra, capture_id="cap_hx1_extra"),))
    _assert_zero_write(fixture["plan"], bindings, fixture["context"], tmp_path / "work")


def test_hx1_c1_same_call_extra_admission_rejects_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    d_binding = _admission_binding("d")
    plan = replace(
        fixture["plan"],
        promotion_decisions=fixture["plan"].promotion_decisions
        + (PromotionDecision("pmd_hx1_d", "dac_hx1_d", "shard_hx1_d", "promote", ("explicit_pin", "manual_batch_selection"), "human_operator"),),
        admission_request_refs=fixture["plan"].admission_request_refs
        + (AdmissionRequestRef("admreq_hx1_d", "pmd_hx1_d", "shard_hx1_d", "gp_hx1_d", "apl_hx1_d"),),
    )
    bindings = replace(fixture["bindings"], admission_bindings=fixture["bindings"].admission_bindings + (d_binding,))
    _assert_zero_write(plan, bindings, fixture["context"], tmp_path / "work")


def test_hx1_c1_same_call_missing_and_reordered_admissions_reject_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    a_only = replace(fixture["plan"], explicit_assembly=ExplicitAssembly(("adm_hx1_a",), "host", "explicit finite host workset"))
    _assert_zero_write(a_only, fixture["bindings"], fixture["context"], tmp_path / "work")

    reordered = replace(fixture["bindings"], admission_bindings=tuple(reversed(fixture["bindings"].admission_bindings)))
    _assert_zero_write(fixture["plan"], reordered, fixture["context"], tmp_path / "work")


def test_hx1_c2_duplicate_explicit_assembly_rejects_as_plan_error(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    duplicate = replace(fixture["plan"], explicit_assembly=ExplicitAssembly(("adm_hx1_a", "adm_hx1_a"), "host", "explicit finite host workset"))
    _assert_zero_write(duplicate, fixture["bindings"], fixture["context"], tmp_path / "work", "HX1_INVALID_PLAN")


@pytest.mark.parametrize(
    "bindings",
    (
        HostPlanBindings(capture_bindings=("bad",)),  # type: ignore[arg-type]
        HostPlanBindings(admission_bindings=("bad",)),  # type: ignore[arg-type]
        HostPlanBindings(recall_binding="bad"),  # type: ignore[arg-type]
        HostPlanBindings(dg6_binding="bad"),  # type: ignore[arg-type]
    ),
)
def test_hx1_c1_malformed_binding_members_are_structured_zero_write(tmp_path, bindings) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    _assert_zero_write(fixture["plan"], bindings, fixture["context"], tmp_path / "work")


def test_hx1_c1_nested_binding_type_errors_are_structured_zero_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    bad_capture = replace(fixture["bindings"].capture_bindings[0], request="bad")
    bad_bindings = replace(fixture["bindings"], capture_bindings=(bad_capture,) + fixture["bindings"].capture_bindings[1:])
    _assert_zero_write(fixture["plan"], bad_bindings, fixture["context"], tmp_path / "work")


def test_hx1_c2_malformed_explicit_assembly_plan_rejects_before_binding_precheck(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    bad_value_plan = replace(
        fixture["plan"],
        explicit_assembly=ExplicitAssembly((["adm_hx1_a"],), "host", "explicit finite host workset"),  # type: ignore[list-item]
    )
    _assert_zero_write(bad_value_plan, fixture["bindings"], fixture["context"], tmp_path / "work", "HX1_INVALID_PLAN")

    bad_mapping_plan = {
        "plan_kind": fixture["plan"].plan_kind,
        "plan_version": fixture["plan"].plan_version,
        "plan_id": fixture["plan"].plan_id,
        "intent": fixture["plan"].intent,
        "capture_refs": fixture["plan"].capture_refs,
        "promotion_decisions": fixture["plan"].promotion_decisions,
        "admission_request_refs": fixture["plan"].admission_request_refs,
        "explicit_assembly": {"admission_ids": [["adm_hx1_a"]], "declared_by": "host", "purpose": "explicit finite host workset"},
        "recall_request": fixture["plan"].recall_request,
        "derived_views": fixture["plan"].derived_views,
        "non_inferences": fixture["plan"].non_inferences,
    }
    _assert_zero_write(bad_mapping_plan, fixture["bindings"], fixture["context"], tmp_path / "work", "HX1_INVALID_PLAN")


@pytest.mark.parametrize(
    "field,value",
    (
        ("origin", None),
        ("deferred_candidate_request", "bad"),
    ),
)
def test_hx1_c2_malformed_capture_request_nested_values_are_structured_zero_write(tmp_path, field, value) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    first = fixture["bindings"].capture_bindings[0]
    bad_request = replace(first.request, **{field: value})
    bad_bindings = replace(fixture["bindings"], capture_bindings=(replace(first, request=bad_request),) + fixture["bindings"].capture_bindings[1:])
    _assert_zero_write(fixture["plan"], bad_bindings, fixture["context"], tmp_path / "work")


@pytest.mark.parametrize("scopes", ("bad", (object(),)))
def test_hx1_c2_malformed_capture_policy_nested_values_are_structured_zero_write(tmp_path, scopes) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    first = fixture["bindings"].capture_bindings[0]
    bad_policy = replace(first.policy, allowed_visibility_scopes=scopes)
    bad_bindings = replace(fixture["bindings"], capture_bindings=(replace(first, policy=bad_policy),) + fixture["bindings"].capture_bindings[1:])
    _assert_zero_write(fixture["plan"], bad_bindings, fixture["context"], tmp_path / "work")


def test_hx1_c2_malformed_admission_and_recall_nested_values_are_structured_zero_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    first = fixture["bindings"].admission_bindings[0]
    bad_decision = _with_field(first.decision, "reasons", ("bad",))
    bad_admission = replace(fixture["bindings"], admission_bindings=(replace(first, decision=bad_decision),) + fixture["bindings"].admission_bindings[1:])
    _assert_zero_write(fixture["plan"], bad_admission, fixture["context"], tmp_path / "work")

    bad_request = _with_field(first.request, "placement_plan", "bad")
    bad_request_bindings = replace(fixture["bindings"], admission_bindings=(replace(first, request=bad_request),) + fixture["bindings"].admission_bindings[1:])
    _assert_zero_write(fixture["plan"], bad_request_bindings, fixture["context"], tmp_path / "work")

    bad_invocation = replace(fixture["bindings"].recall_binding.invocation, query_probe="bad")
    bad_recall = replace(fixture["bindings"], recall_binding=replace(fixture["bindings"].recall_binding, invocation=bad_invocation))
    _assert_zero_write(fixture["plan"], bad_recall, fixture["context"], tmp_path / "work")


def _with_field(value, field: str, replacement):
    updated = copy(value)
    object.__setattr__(updated, field, replacement)
    return updated


def _assert_zero_write(plan, bindings: HostPlanBindings, context, work_root, expected_code: str = "HX1_INVALID_BINDINGS") -> None:
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(plan, bindings, context)
    assert error.value.reason_code == expected_code
    assert type(error.value) is HX1ExecutionError
    for forbidden in ("Traceback", "AttributeError", "TypeError", "KeyError", "ValueError", "AssertionError", "nollm.dream_geometry", "\\"):
        assert forbidden not in str(error.value)
    assert not work_root.exists() or list(work_root.iterdir()) == []
