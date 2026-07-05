from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from nollm.dream_geometry.host_execution import HX1ExecutionError, execute_host_plan, receipt_to_mapping
from nollm.dream_geometry.validation.cx2.types import DerivedViewRef

from test_hx1_trusted_host_bridge import hx1_fixture


def test_hx1_07_same_plan_same_root_reopens_identical_receipt(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    first = receipt_to_mapping(execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"]))
    before_tree = _tree_manifest(tmp_path / "work")
    second = receipt_to_mapping(execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"]))
    after_tree = _tree_manifest(tmp_path / "work")

    assert second == first
    assert second["output_fingerprint"] == first["output_fingerprint"]
    assert second["execution_input_fingerprint"] == first["execution_input_fingerprint"]
    assert after_tree == before_tree


def test_hx1_c1_same_plan_id_changed_query_ref_reopen_mismatch(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    before_tree = _tree_manifest(tmp_path / "work")
    plan = replace(fixture["plan"], recall_request=replace(fixture["plan"].recall_request, query_ref="query:hx1:changed"))
    bindings = replace(fixture["bindings"], recall_binding=replace(fixture["bindings"].recall_binding, query_ref="query:hx1:changed"))
    _assert_reopen_mismatch(plan, bindings, fixture["context"], tmp_path / "work", before_tree)


def test_hx1_c1_same_plan_id_changed_growth_submission_reopen_mismatch(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    before_tree = _tree_manifest(tmp_path / "work")
    first = fixture["bindings"].admission_bindings[0]
    changed_submission = {**first.request.growth_submission, "do_not_infer": ["hx1 changed valid preimage"]}
    changed_request = replace(first.request, growth_submission=changed_submission)
    bindings = replace(fixture["bindings"], admission_bindings=(replace(first, request=changed_request),) + fixture["bindings"].admission_bindings[1:])
    _assert_reopen_mismatch(fixture["plan"], bindings, fixture["context"], tmp_path / "work", before_tree)


def test_hx1_c1_same_plan_id_changed_capture_policy_reopen_mismatch(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    before_tree = _tree_manifest(tmp_path / "work")
    first = fixture["bindings"].capture_bindings[0]
    bindings = replace(fixture["bindings"], capture_bindings=(replace(first, policy=replace(first.policy, policy_id="cp_hx1_changed")),) + fixture["bindings"].capture_bindings[1:])
    _assert_reopen_mismatch(fixture["plan"], bindings, fixture["context"], tmp_path / "work", before_tree)


def test_hx1_c1_same_plan_id_changed_context_reopen_mismatch(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    before_tree = _tree_manifest(tmp_path / "work")
    context = replace(fixture["context"], batch_policy_id="policy:hx1:changed")
    _assert_reopen_mismatch(fixture["plan"], fixture["bindings"], context, tmp_path / "work", before_tree)


def test_hx1_c1_same_plan_id_changed_finite_set_reopen_mismatch(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    before_tree = _tree_manifest(tmp_path / "work")
    context = replace(fixture["context"], finite_set_id="hx1_changed_finite_set")
    _assert_reopen_mismatch(fixture["plan"], fixture["bindings"], context, tmp_path / "work", before_tree)


def test_hx1_c1_same_plan_id_changed_dg6_view_reopen_mismatch(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    before_tree = _tree_manifest(tmp_path / "work")
    plan = replace(fixture["plan"], derived_views=(DerivedViewRef("dg6_compacted_view", "view:hx1:changed", "verification_only"),))
    bindings = replace(fixture["bindings"], dg6_binding=replace(fixture["bindings"].dg6_binding, view_ref="view:hx1:changed"))
    _assert_reopen_mismatch(plan, bindings, fixture["context"], tmp_path / "work", before_tree)


def _assert_reopen_mismatch(plan, bindings, context, work_root, before_tree) -> None:
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(plan, bindings, context)
    assert error.value.reason_code == "HX1_REOPEN_MISMATCH"
    assert _tree_manifest(work_root) == before_tree
    for forbidden in ("Traceback", "AttributeError", "TypeError", "KeyError", "ValueError", "AssertionError", "nollm.dream_geometry", "\\"):
        assert forbidden not in str(error.value)


def _tree_manifest(root) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))
