from __future__ import annotations

from dataclasses import replace

import pytest

from nollm.dream_geometry.host_execution import HX1ExecutionError, HostPlanBindings, execute_host_plan

from test_hx1_trusted_host_bridge import hx1_fixture


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


def _assert_zero_write(plan, bindings: HostPlanBindings, context, work_root) -> None:
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(plan, bindings, context)
    assert error.value.reason_code == "HX1_INVALID_BINDINGS"
    assert not work_root.exists() or list(work_root.iterdir()) == []
