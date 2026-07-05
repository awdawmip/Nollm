from __future__ import annotations

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


def test_hx1_c1_duplicate_explicit_assembly_rejects_as_binding_error(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    duplicate = replace(fixture["plan"], explicit_assembly=ExplicitAssembly(("adm_hx1_a", "adm_hx1_a"), "host", "explicit finite host workset"))
    _assert_zero_write(duplicate, fixture["bindings"], fixture["context"], tmp_path / "work")


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


def _assert_zero_write(plan, bindings: HostPlanBindings, context, work_root) -> None:
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(plan, bindings, context)
    assert error.value.reason_code == "HX1_INVALID_BINDINGS"
    assert type(error.value) is HX1ExecutionError
    for forbidden in ("Traceback", "AttributeError", "TypeError", "KeyError", "ValueError", "AssertionError", "nollm.dream_geometry", "\\"):
        assert forbidden not in str(error.value)
    assert not work_root.exists() or list(work_root.iterdir()) == []
