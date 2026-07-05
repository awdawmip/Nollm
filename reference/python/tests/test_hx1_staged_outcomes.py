from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.validation.cx2.types import AdmissionRequestRef, CortexActionPlan, PromotionDecision
from nollm.dream_geometry.host_execution import HostPlanBindings, execute_host_plan, receipt_to_mapping

from test_hx1_trusted_host_bridge import (
    NON_INFERENCES,
    _admission_binding,
    capture_only_fixture,
    hx1_fixture,
)


def test_hx1_02_capture_only_has_no_admission_or_recall_outputs(tmp_path) -> None:
    plan, bindings, context = capture_only_fixture(tmp_path / "work")
    mapping = receipt_to_mapping(execute_host_plan(plan, bindings, context))

    assert mapping["status"] == "completed"
    assert mapping["completed_stages"] == ["capture"]
    assert mapping["admission_receipt_ids"] == []
    assert mapping["snapshot_id"] is None
    assert mapping["recall_public_envelope"] is None


def test_hx1_03_admission_only_uses_existing_deferred_candidate(tmp_path) -> None:
    plan, bindings, context = capture_only_fixture(tmp_path / "work")
    execute_host_plan(plan, bindings, context)
    admission_binding = _admission_binding("e")
    admission_plan = _admission_only_plan("e")

    mapping = receipt_to_mapping(execute_host_plan(admission_plan, HostPlanBindings(admission_bindings=(admission_binding,)), context))

    assert mapping["status"] == "completed"
    assert mapping["completed_stages"] == ["admission"]
    assert mapping["admission_receipt_ids"] == ["adm_hx1_e"]
    assert mapping["snapshot_id"] is None


def test_hx1_06_capture_is_preserved_after_admission_failure(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    first = fixture["bindings"].admission_bindings[0]
    bad_submission = dict(first.request.growth_submission)
    bad_axis = dict(bad_submission["axes"][0])
    bad_step = dict(bad_axis["ray"][0])
    bad_step["expression"] = "Jakarta"
    bad_step["basis_refs"] = ({"ref_type": "text_span", "record_id": first.request.dream_shard.shard_id, "start_char": 0, "end_char": 7, "quoted_text": "Jakarta"},)
    bad_axis["ray"] = (bad_step,)
    bad_submission["axes"] = (bad_axis,) + tuple(bad_submission["axes"][1:])
    bad_request = replace(first.request, growth_submission=bad_submission)
    bindings = replace(fixture["bindings"], admission_bindings=(replace(first, request=bad_request),) + fixture["bindings"].admission_bindings[1:])

    mapping = receipt_to_mapping(execute_host_plan(fixture["plan"], bindings, fixture["context"]))

    assert mapping["status"] == "partial"
    assert mapping["failed_stage"] == "admission"
    assert mapping["completed_stages"] == ["capture"]
    assert len(mapping["capture_receipt_views"]) == 4
    assert mapping["snapshot_id"] is None
    assert mapping["recall_public_envelope"] is None


def _admission_only_plan(label: str) -> CortexActionPlan:
    return CortexActionPlan(
        "nollm_cortex_action_plan",
        "1",
        f"cx2_hx1_admission_{label}",
        "admission",
        promotion_decisions=(
            PromotionDecision(
                f"pmd_hx1_{label}",
                f"dac_hx1_{label}",
                f"shard_hx1_{label}",
                "promote",
                ("explicit_pin", "manual_batch_selection"),
                "human_operator",
            ),
        ),
        admission_request_refs=(
            AdmissionRequestRef(
                f"admreq_hx1_{label}",
                f"pmd_hx1_{label}",
                f"shard_hx1_{label}",
                f"gp_hx1_{label}",
                f"apl_hx1_{label}",
            ),
        ),
        non_inferences=NON_INFERENCES,
    )
