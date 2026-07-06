"""HCG1 file-first capture gateway."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any

from nollm.dream_geometry.capture import CaptureStateStore, CaptureVisibility, VisibilityScope
from nollm.dream_geometry.capture.errors import CaptureError
from nollm.dream_geometry.capture.policy import policy_fingerprint, request_fingerprint
from nollm.dream_geometry.evidence import DreamShard, canonical_payload
from nollm.dream_geometry.evidence import open_store as open_evidence_store
from nollm.dream_geometry.host_execution import HostCaptureBinding, HostExecutionContext, HostPlanBindings, execute_host_plan, receipt_to_mapping
from nollm.dream_geometry.host_execution.errors import HX1ExecutionError
from nollm.dream_geometry.validation.cx2.types import CaptureRef, CortexActionPlan

from .decode import decode_capture_payload, decode_read_payload, load_json_text
from .errors import (
    HCGError,
    HCG_CAPTURE_REJECTED,
    HCG_INTERNAL_ERROR,
    HCG_INVALID_REQUEST,
    HCG_READ_REJECTED,
    HCG_REOPEN_MISMATCH,
    HCG_UNSUPPORTED_CAPTURE_MODE,
    HCG_UNSUPPORTED_READ_SELECTOR,
    HCG_WORKSPACE_NOT_OWNED,
)
from .serialization import error_envelope, ok_envelope


HX1_MARKER_NAME = ".hx1_host_execution_root.json"
NON_INFERENCES = (
    "no_automatic_admission",
    "no_global_discovery",
    "no_anchor_creation",
    "no_truth_confirmation",
    "no_dg6_recall_influence",
)


def capture_from_text(workspace: Path, text: str) -> dict[str, Any]:
    request_id: str | None = None
    try:
        decoded = decode_capture_payload(load_json_text(text))
        request_id = decoded.request_id
        result = capture(workspace, decoded)
        return ok_envelope("capture", decoded.request_id, result)
    except HCGError as exc:
        return error_envelope("capture", request_id, exc.code, exc.message)
    except ValueError:
        return error_envelope("capture", request_id, HCG_INVALID_REQUEST)
    except Exception:
        return error_envelope("capture", request_id, HCG_INTERNAL_ERROR)


def read_from_text(workspace: Path, text: str) -> dict[str, Any]:
    request_id: str | None = None
    try:
        decoded = decode_read_payload(load_json_text(text))
        request_id = decoded.request_id
        result = read(workspace, decoded)
        return ok_envelope("read", decoded.request_id, result)
    except HCGError as exc:
        return error_envelope("read", request_id, exc.code, exc.message)
    except ValueError:
        return error_envelope("read", request_id, HCG_UNSUPPORTED_READ_SELECTOR)
    except Exception:
        return error_envelope("read", request_id, HCG_INTERNAL_ERROR)


def capture(workspace: Path, decoded) -> dict[str, Any]:
    workspace = Path(workspace).resolve()
    if decoded.capture_policy.persistence.value == "ephemeral" or decoded.capture_request.requested_visibility_scope is VisibilityScope.current_turn:
        raise HCGError(HCG_UNSUPPORTED_CAPTURE_MODE, "capture mode is not supported by HCG1")
    plan = CortexActionPlan(
        "nollm_cortex_action_plan",
        "1",
        "cx2_hcg1_" + _safe_plan_suffix(decoded.request_id),
        "capture_only",
        capture_refs=(
            CaptureRef(
                decoded.capture_request.capture_id,
                None,
                _planned_persistence(decoded),
                _planned_admission(decoded),
                "tentative",
                decoded.capture_request.requested_visibility_scope.value,
            ),
        ),
        non_inferences=NON_INFERENCES,
    )
    bindings = HostPlanBindings((HostCaptureBinding(decoded.capture_request.capture_id, decoded.capture_request, decoded.capture_policy),))
    context = HostExecutionContext(
        workspace,
        decoded.capture_request.recorded_at,
        batch_source_ref=_first_context(decoded.capture_request.context_refs),
        enable_dg6_verification=False,
    )
    try:
        receipt = execute_host_plan(plan, bindings, context)
    except HX1ExecutionError as exc:
        raise _hcg_from_hx1(exc) from exc
    mapping = receipt_to_mapping(receipt)
    if mapping["status"] != "completed":
        raise HCGError(HCG_CAPTURE_REJECTED, "capture was rejected")
    _remove_unexecuted_stage_scaffolding(workspace)
    identity = CaptureStateStore(workspace / "capture").read_capture_identity(decoded.capture_request.capture_id)
    if identity is None:
        raise HCGError(HCG_CAPTURE_REJECTED, "capture was rejected")
    return {
        "capture_receipt": {
            "capture_id": identity["capture_id"],
            "receipt_id": identity["receipt_id"],
            "status": identity["status"],
            "shard_id": identity["shard_id"],
            "recorded_at": decoded.capture_request.recorded_at,
            "policy_fingerprint": identity["policy_fingerprint"],
            "visibility_scope": identity["visibility_scope"],
            "deferred_candidate_id": identity["candidate_id"],
            "minimal_ledger_event_id": identity["minimal_ledger_event_id"],
            "request_fingerprint": request_fingerprint(decoded.capture_request),
        },
        "host_execution": {
            "plan_id": mapping["plan_id"],
            "status": mapping["status"],
            "completed_stages": mapping["completed_stages"],
            "work_root_marker_id": mapping["work_root_marker_id"],
            "execution_input_fingerprint": mapping["execution_input_fingerprint"],
            "output_fingerprint": mapping["output_fingerprint"],
        },
        "policy_fingerprint": policy_fingerprint(decoded.capture_policy),
    }


def read(workspace: Path, decoded) -> dict[str, Any]:
    workspace = Path(workspace).resolve()
    _require_owned_workspace(workspace)
    visibility = CaptureVisibility(CaptureStateStore(workspace / "capture"), open_evidence_store(workspace / "evidence"))
    try:
        if decoded.scope == "session_window":
            shards = visibility.session_window(decoded.context_ref or "")
        elif decoded.scope == "source_window":
            shards = visibility.source_window(decoded.context_ref or "")
        elif decoded.scope == "persistent_explicit":
            shards = visibility.persistent_explicit(decoded.shard_ids)
        else:
            raise HCGError(HCG_UNSUPPORTED_READ_SELECTOR, "read selector is not supported")
    except CaptureError as exc:
        raise HCGError(HCG_READ_REJECTED, "read was rejected") from exc
    except ValueError as exc:
        raise HCGError(HCG_READ_REJECTED, "read was rejected") from exc
    return {
        "scope": decoded.scope,
        "context_ref": decoded.context_ref,
        "shard_ids": tuple(shard.shard_id for shard in shards),
        "dream_shards": tuple(_shard_payload(shard) for shard in shards),
    }


def _require_owned_workspace(workspace: Path) -> None:
    marker = workspace / HX1_MARKER_NAME
    if not marker.exists() or not marker.is_file():
        raise HCGError(HCG_WORKSPACE_NOT_OWNED, "workspace is not owned by HCG1")
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise HCGError(HCG_WORKSPACE_NOT_OWNED, "workspace is not owned by HCG1") from exc
    if payload != {"owner": "hx1", "marker_version": "1"}:
        raise HCGError(HCG_WORKSPACE_NOT_OWNED, "workspace is not owned by HCG1")


def _hcg_from_hx1(exc: HX1ExecutionError) -> HCGError:
    if exc.reason_code == "HX1_REOPEN_MISMATCH":
        return HCGError(HCG_REOPEN_MISMATCH, "workspace receipt does not match request")
    if exc.reason_code == "HX1_WORK_ROOT_REJECTED":
        return HCGError(HCG_WORKSPACE_NOT_OWNED, "workspace is not owned by HCG1")
    if exc.reason_code in {"HX1_CAPTURE_REJECTED", "HX1_CAPTURE_STATE_MISMATCH", "HX1_INVALID_BINDINGS"}:
        return HCGError(HCG_CAPTURE_REJECTED, "capture was rejected")
    return HCGError(HCG_CAPTURE_REJECTED, "capture was rejected")


def _planned_persistence(decoded) -> str:
    if decoded.capture_request.deferred_candidate_request.requested:
        return "captured"
    if decoded.capture_policy.persistence.value in {"captured", "persistent"}:
        return "captured"
    return decoded.capture_policy.persistence.value


def _planned_admission(decoded) -> str:
    if decoded.capture_request.deferred_candidate_request.requested:
        return "candidate"
    return "none"


def _safe_plan_suffix(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:32]


def _first_context(context_refs: tuple[str, ...]) -> str:
    return context_refs[0] if context_refs else "source:hcg1"


def _shard_payload(shard: DreamShard) -> dict[str, Any]:
    return canonical_payload(shard)


def _remove_unexecuted_stage_scaffolding(workspace: Path) -> None:
    for name in ("admission", "cortex"):
        path = workspace / name
        if path.exists() and path.is_dir():
            shutil.rmtree(path)


__all__ = ["capture", "capture_from_text", "read", "read_from_text"]
