from __future__ import annotations

import ast
from pathlib import Path

from nollm.dream_geometry.validation.cx2.fixtures import dg7_correspondence_fixture, valid_explicit_admission_and_recall_plan
from nollm.dream_geometry.validation.cx2.types import (
    AdmissionRequestRef,
    CaptureRef,
    CX2PlanValidationError,
    DerivedViewRef,
    ExplicitAssembly,
    PromotionDecision,
    RecallRequest,
)
from nollm.dream_geometry.validation.cx2.validator import validate_cortex_action_plan

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_cx2_rejects_global_discovery_vector_and_captured_pool() -> None:
    plan = valid_explicit_admission_and_recall_plan()
    rejected = (
        RecallRequest("opaque-query", "verification", "global_discovery", 3, 1),
        RecallRequest("opaque-query", "verification", "captured_pool", 3, 1),
    )

    for request in rejected:
        with raises_cx2("CX2_FORBIDDEN_AUTOMATION"):
            validate_cortex_action_plan(plan.__class__(**{**_plan_dict(plan), "recall_request": request}))


def test_cx2_rejects_duplicate_empty_and_inferred_assembly() -> None:
    plan = valid_explicit_admission_and_recall_plan()
    invalid = (
        ExplicitAssembly(("adm_a", "adm_a"), "host", "explicit finite set"),
        ExplicitAssembly(("",), "host", "explicit finite set"),
        ExplicitAssembly(("adm_a",), "host", "inferred related admissions"),
    )

    for assembly in invalid:
        with raises_cx2("CX2_INVALID_EXPLICIT_ASSEMBLY"):
            validate_cortex_action_plan(plan.__class__(**{**_plan_dict(plan), "explicit_assembly": assembly}))


def test_cx2_rejects_dg6_recall_influence() -> None:
    plan = valid_explicit_admission_and_recall_plan()
    for usage in ("recall_filter", "recall_rank", "recall_source", "replace_evidence"):
        with raises_cx2("CX2_FORBIDDEN_DG6_INFERENCE"):
            validate_cortex_action_plan(plan.__class__(**{**_plan_dict(plan), "derived_views": (DerivedViewRef("dg6_compacted_view", "opaque-dg6", usage),)}))


def test_cx2_c1_03_capture_ephemeral_consistency() -> None:
    valid = {
        "plan_kind": "nollm_cortex_action_plan",
        "plan_version": "1",
        "plan_id": "cx2_ephemeral_valid",
        "intent": "capture_only",
        "capture_refs": [
            {
                "capture_id": "cap_ephemeral_valid",
                "shard_id": None,
                "persistence_state": "ephemeral",
                "admission_state": "none",
                "usage_state": "tentative",
                "visibility_scope": "current_turn",
            }
        ],
        "non_inferences": _non_inferences(),
    }
    assert validate_cortex_action_plan(valid).capture_ref_count == 1

    invalid_captures = (
        CaptureRef("cap_ephemeral_admitted", None, "ephemeral", "admitted", "tentative", "current_turn"),
        CaptureRef("cap_ephemeral_visibility", None, "ephemeral", "none", "tentative", "persistent_explicit"),
        CaptureRef("cap_ephemeral_shard", "shard_ephemeral", "ephemeral", "none", "tentative", "current_turn"),
        CaptureRef("cap_ephemeral_deferred", None, "ephemeral", "deferred", "tentative", "current_turn"),
        CaptureRef("cap_ephemeral_candidate", None, "ephemeral", "candidate", "tentative", "current_turn"),
        CaptureRef("cap_ephemeral_promotion", None, "ephemeral", "promotion_requested", "tentative", "current_turn"),
        CaptureRef("cap_ephemeral_do_not", None, "ephemeral", "do_not_admit", "tentative", "current_turn"),
    )
    for capture in invalid_captures:
        with raises_cx2("CX2_INVALID_STATE_SEPARATION"):
            validate_cortex_action_plan(valid_explicit_admission_and_recall_plan().__class__(
                plan_kind="nollm_cortex_action_plan",
                plan_version="1",
                plan_id=f"cx2_{capture.capture_id}",
                intent="capture_only",
                capture_refs=(capture,),
                non_inferences=tuple(_non_inferences()),
            ))


def test_cx2_c1_04_admission_decision_binding() -> None:
    plan = valid_explicit_admission_and_recall_plan()
    duplicate_request = AdmissionRequestRef(
        "admreq_valid_02c",
        plan.admission_request_refs[0].decision_id,
        plan.admission_request_refs[0].shard_id,
        "opaque-host-proposal-c",
        "opaque-host-placement-c",
    )

    with raises_cx2("CX2_INVALID_ADMISSION_REQUEST"):
        validate_cortex_action_plan(plan.__class__(**{**_plan_dict(plan), "admission_request_refs": (*plan.admission_request_refs, duplicate_request)}))

    cortex_suggestion = PromotionDecision("pmd_cortex_suggestion", "dac_cortex_suggestion", "shard_cortex_suggestion", "promote", ("explicit_pin",), "cortex_suggestion")
    cortex_request = AdmissionRequestRef("admreq_cortex_suggestion", "pmd_cortex_suggestion", "shard_cortex_suggestion", "opaque-proposal", "opaque-placement")
    with raises_cx2("CX2_INVALID_ADMISSION_REQUEST"):
        validate_cortex_action_plan(plan.__class__(**{**_plan_dict(plan), "promotion_decisions": (cortex_suggestion,), "admission_request_refs": (cortex_request,)}))

    for decided_by in ("host_rule", "user", "human_operator"):
        decision = PromotionDecision(f"pmd_{decided_by}", f"dac_{decided_by}", f"shard_{decided_by}", "promote", ("explicit_pin",), decided_by)
        request = AdmissionRequestRef(f"admreq_{decided_by}", f"pmd_{decided_by}", f"shard_{decided_by}", "opaque-proposal", "opaque-placement")
        assert validate_cortex_action_plan(
            plan.__class__(**{**_plan_dict(plan), "promotion_decisions": (decision,), "admission_request_refs": (request,)})
        ).admission_request_count == 1


def test_cx2_c1_05_derived_view_and_budget_validation() -> None:
    plan = valid_explicit_admission_and_recall_plan()

    for view in (
        DerivedViewRef("dg6_compacted_view", "", "verification_only"),
        DerivedViewRef("future_magic_view", "opaque-view", "verification_only"),
        DerivedViewRef("dg6_compacted_view", "opaque-view", "recall_filter"),
        DerivedViewRef("dg6_compacted_view", "opaque-view", "unexpected_usage"),
    ):
        with raises_cx2("CX2_FORBIDDEN_DG6_INFERENCE"):
            validate_cortex_action_plan(plan.__class__(**{**_plan_dict(plan), "derived_views": (view,)}))

    for request in (
        RecallRequest("opaque-query", "verification", "explicit-finite-workset", True, 1),
        RecallRequest("opaque-query", "verification", "explicit-finite-workset", 1, True),
    ):
        with raises_cx2("CX2_INVALID_RECALL_REQUEST"):
            validate_cortex_action_plan(plan.__class__(**{**_plan_dict(plan), "recall_request": request}))


def test_cx2_dg7_correspondence_fixture_is_read_only_language() -> None:
    fixture = dg7_correspondence_fixture()

    assert fixture["assembled_admission_ids"] == ("adm_dg7_a", "adm_dg7_b")
    assert fixture["captured_only_admission_ids"] == ("adm_dg7_c",)
    assert fixture["admitted_unassembled_ids"] == ("adm_dg7_d",)
    text = str(fixture)
    assert "runtime" in text
    assert "does not run" in text


def test_cx2_validation_package_import_scan_excludes_runtime_and_network() -> None:
    roots = [
        REPO_ROOT / "reference/python/nollm/dream_geometry/validation/cx2",
        REPO_ROOT / "validation/cx2/run_cx2_conformance.py",
    ]
    forbidden = (
        "openclaw",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "sqlite3",
        "nollm.dream_geometry.capture",
        "nollm.dream_geometry.admission",
        "nollm.dream_geometry.assembly",
        "nollm.dream_geometry.recall",
        "nollm.dream_geometry.validation.dg7.runner",
    )
    imports: list[str] = []
    scanned: list[Path] = []
    for root in roots:
        paths = [root] if root.is_file() else sorted(root.glob("*.py"))
        for path in paths:
            scanned.append(path)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
    assert scanned
    assert all(path.exists() for path in scanned)
    lowered = "\n".join(imports).lower()
    for token in forbidden:
        assert token not in lowered, (token, imports)


class raises_cx2:
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        assert exc_type is CX2PlanValidationError
        assert exc.reason_code == self.reason_code
        return True


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


def _non_inferences() -> list[str]:
    return [
        "no_automatic_admission",
        "no_global_discovery",
        "no_anchor_creation",
        "no_truth_confirmation",
        "no_dg6_recall_influence",
    ]
