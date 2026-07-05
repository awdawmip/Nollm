"""Canonical HX1 serialization."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from nollm.dream_geometry.admission import fingerprint as admission_fingerprint
from nollm.dream_geometry.admission import placement_plan_payload
from nollm.dream_geometry.capture.policy import policy_fingerprint
from nollm.dream_geometry.cortex import canonical_payload as cortex_payload


def canonical_json(value: object) -> str:
    return json.dumps(_normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def stable_fingerprint(value: object) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


def receipt_to_mapping(receipt: object) -> dict[str, Any]:
    return json.loads(canonical_json(receipt))


def execution_input_fingerprint(plan: object, bindings: object, context: object) -> str:
    return stable_fingerprint(
        {
            "kind": "nollm_hx1_execution_input",
            "plan": _plan_payload(plan),
            "bindings": _bindings_payload(bindings),
            "context": _context_payload(context),
        }
    )


def _plan_payload(plan: object) -> dict[str, Any]:
    return _normalize(plan)


def _bindings_payload(bindings: object) -> dict[str, Any]:
    return {
        "capture_bindings": tuple(_capture_binding_payload(binding) for binding in getattr(bindings, "capture_bindings", ())),
        "admission_bindings": tuple(_admission_binding_payload(binding) for binding in getattr(bindings, "admission_bindings", ())),
        "recall_binding": _recall_binding_payload(getattr(bindings, "recall_binding", None)),
        "dg6_binding": _dg6_binding_payload(getattr(bindings, "dg6_binding", None)),
    }


def _capture_binding_payload(binding: object) -> dict[str, Any]:
    request = binding.request
    origin = request.origin
    return {
        "capture_id": binding.capture_id,
        "request_capture_id": request.capture_id,
        "request_content_sha256": _sha256_text(request.content),
        "origin_kind": origin.kind.value,
        "origin_reference_sha256": _optional_sha256(origin.reference),
        "origin_context_reference_sha256": _optional_sha256(origin.context_reference),
        "origin_role_label_sha256": _optional_sha256(origin.role_label),
        "recorded_at": request.recorded_at,
        "context_refs": request.context_refs,
        "visibility_scope": request.requested_visibility_scope.value,
        "deferred_candidate_request": {
            "requested": request.deferred_candidate_request.requested,
            "trigger_refs": tuple(trigger.value for trigger in request.deferred_candidate_request.trigger_refs),
        },
        "diagnostic_retention_until": request.diagnostic_retention_until,
        "capture_policy_fingerprint": policy_fingerprint(binding.policy),
    }


def _admission_binding_payload(binding: object) -> dict[str, Any]:
    decision = binding.decision
    request = binding.request
    return {
        "request_id": binding.request_id,
        "decision_id": binding.decision_id,
        "candidate_id": binding.candidate_id,
        "actual_candidate_id": binding.actual_candidate_id,
        "admission_id": binding.admission_id,
        "member_id": binding.member_id,
        "declared_shard_id": binding.declared_shard_id,
        "decision": {
            "decision_id": decision.decision_id,
            "candidate_id": decision.candidate_id,
            "shard_id": decision.shard_id,
            "decision": decision.decision.value,
            "reasons": tuple(reason.value for reason in decision.reasons),
            "decided_by": decision.decided_by.value,
            "recorded_at": decision.recorded_at,
            "next_action": decision.next_action,
        },
        "admission_request": {
            "admission_id": request.admission_id,
            "subject_shard_id": request.dream_shard.shard_id,
            "growth_submission_sha256": _sha256_json(request.growth_submission),
            "placement_plan_id": request.placement_plan.plan_id,
            "placement_plan_fingerprint": admission_fingerprint(placement_plan_payload(request.placement_plan)),
            "recorded_at": request.recorded_at,
            "contract_version": request.contract_version,
        },
        "proposal_ref": binding.proposal_ref,
        "placement_plan_ref": binding.placement_plan_ref,
    }


def _recall_binding_payload(binding: object | None) -> dict[str, Any] | None:
    if binding is None:
        return None
    invocation = binding.invocation
    return {
        "query_ref": binding.query_ref,
        "admitted_workset_ref": binding.admitted_workset_ref,
        "invocation_request_id": invocation.request_id,
        "invocation_operation": invocation.operation,
        "compiled_probe_id": invocation.query_probe.probe_id,
        "compiled_probe_fingerprint": stable_fingerprint(cortex_payload(invocation.query_probe)),
    }


def _dg6_binding_payload(binding: object | None) -> dict[str, Any] | None:
    if binding is None:
        return None
    return {"view_ref": binding.view_ref, "verification_only": binding.verification_only}


def _context_payload(context: object) -> dict[str, Any]:
    return {
        "recorded_at": context.recorded_at,
        "batch_window_id": context.batch_window_id,
        "batch_policy_id": context.batch_policy_id,
        "batch_source_ref": context.batch_source_ref,
        "finite_set_id": context.finite_set_id,
        "enable_dg6_verification": context.enable_dg6_verification,
    }


def _sha256_text(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _optional_sha256(value: str | None) -> str | None:
    return None if value is None else _sha256_text(value)


def _sha256_json(value: object) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalize(value: object) -> object:
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return "<path>"
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_normalize(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return format(value, ".17g")
    return str(value)


__all__ = ["canonical_json", "execution_input_fingerprint", "receipt_to_mapping", "stable_fingerprint"]
