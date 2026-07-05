"""HX1 trusted host staged execution bridge."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from nollm.dream_geometry.adapters import IntegrationReadContext, IntegrationShell
from nollm.dream_geometry.adapters.snapshot_compaction import expand_snapshot_compaction_projection, project_snapshot_compaction, validate_snapshot_compaction_projection
from nollm.dream_geometry.admission import FIELD_PROFILE_ID, MemoryAdmissionOrchestrator, open_store as open_admission_store
from nollm.dream_geometry.assembly import AdmissionReplaySource, FiniteAdmissionSet, assemble_field_snapshot
from nollm.dream_geometry.batch_admission import BatchAdmissionCoordinator, BatchAdmissionMember, BatchAdmissionRequest, BatchAdmissionWindow, BatchWindowStatus
from nollm.dream_geometry.capture import CandidateStatus, CaptureIngress, CaptureStatus
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.evidence import open_store as open_evidence_store
from nollm.dream_geometry.recall import RecallDigestStatus, resolve_recall

from .bindings import FORBIDDEN_WORK_DIRS, preflight_host_plan
from .errors import HX1ExecutionError, stable_message
from .serialization import canonical_json, execution_input_fingerprint, receipt_to_mapping, stable_fingerprint
from .types import CaptureReceiptView, HostExecutionContext, HostExecutionReceipt, HostPlanBindings


MARKER_NAME = ".hx1_host_execution_root.json"
RECEIPT_PREFIX = ".hx1_host_execution_receipt_"
RECEIPT_KIND = "nollm_hx1_host_execution_receipt"


def execute_host_plan(plan, bindings: HostPlanBindings, context: HostExecutionContext) -> HostExecutionReceipt:
    summary, normalized = preflight_host_plan(plan, bindings, context)
    try:
        input_fingerprint = execution_input_fingerprint(normalized, bindings, context)
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        raise HX1ExecutionError("HX1_INVALID_BINDINGS", "host execution inputs cannot be canonically fingerprinted") from exc
    work_root = _prepare_work_root(Path(context.work_root), summary.plan_id)
    cached = _receipt_path(work_root, summary.plan_id)
    if cached.exists():
        try:
            receipt = _receipt_from_mapping(json.loads(cached.read_text(encoding="utf-8")))
        except Exception as exc:
            raise HX1ExecutionError(
                "HX1_REOPEN_MISMATCH",
                "owned work root already contains a receipt for a different execution input",
            ) from exc
        if receipt.execution_input_fingerprint != input_fingerprint:
            raise HX1ExecutionError(
                "HX1_REOPEN_MISMATCH",
                "owned work root already contains a receipt for a different execution input",
            )
        return receipt

    try:
        receipt = _execute(normalized, bindings, context, summary.plan_id, work_root, input_fingerprint)
    except HX1ExecutionError:
        raise
    except Exception as exc:
        raise HX1ExecutionError("HX1_INVALID_PLAN", stable_message(exc)) from exc

    forbidden = tuple(sorted(name for name in FORBIDDEN_WORK_DIRS if (work_root / name).exists()))
    if forbidden:
        raise HX1ExecutionError("HX1_UNEXPECTED_SIDE_EFFECT", "HX1 created forbidden work-root paths")
    cached.write_text(canonical_json(receipt_to_mapping(receipt)), encoding="utf-8", newline="\n")
    return receipt


def _execute(plan, bindings: HostPlanBindings, context: HostExecutionContext, plan_id: str, work_root: Path, input_fingerprint: str) -> HostExecutionReceipt:
    evidence = open_evidence_store(work_root / "evidence")
    capture = CaptureIngress(work_root / "capture")
    cortex = open_cortex_store(work_root / "cortex", evidence)
    admission, orchestrator = _open_admission_and_orchestrator(work_root / "admission", evidence, cortex)
    coordinator = BatchAdmissionCoordinator(capture.state_store, evidence, orchestrator)

    completed: list[str] = []
    capture_views: list[CaptureReceiptView] = []
    admission_ids: tuple[str, ...] = ()
    assembly = None
    dg6_projection_id = None
    recall_envelope = None

    if plan.intent in {"capture_only", "mixed_explicit"}:
        try:
            capture_views = _run_capture_stage(plan, bindings, capture, evidence)
            completed.append("capture")
        except HX1ExecutionError:
            raise
        except Exception as exc:
            raise HX1ExecutionError("HX1_CAPTURE_REJECTED", stable_message(exc), failed_stage="capture") from exc
        if plan.intent == "capture_only":
            return _final_receipt(plan, input_fingerprint, "completed", tuple(completed), None, tuple(capture_views), (), (), None, (), None, None, None)

    if plan.intent in {"admission", "mixed_explicit"}:
        try:
            admission_ids = _run_admission_stage(plan, bindings, context, capture, coordinator)
            _validate_runtime_admission_ids(plan, admission_ids)
            completed.append("admission")
        except HX1ExecutionError as exc:
            if completed:
                return _final_receipt(plan, input_fingerprint, "partial", tuple(completed), "admission", tuple(capture_views), admission_ids, _assembly_ids(plan), None, (), None, None, str(exc))
            raise
        except Exception as exc:
            if completed:
                return _final_receipt(plan, input_fingerprint, "partial", tuple(completed), "admission", tuple(capture_views), admission_ids, _assembly_ids(plan), None, (), None, None, "admission stage rejected after capture")
            raise HX1ExecutionError("HX1_ADMISSION_REJECTED", stable_message(exc), failed_stage="admission") from exc
        if plan.intent == "admission":
            return _final_receipt(plan, input_fingerprint, "completed", tuple(completed), None, tuple(capture_views), admission_ids, (), None, (), None, None, None)

    if plan.intent in {"recall", "mixed_explicit"}:
        try:
            assembly = _run_assembly_stage(plan, bindings, context, evidence, cortex, admission, orchestrator)
            completed.append("assembly")
        except Exception as exc:
            if completed:
                return _final_receipt(plan, input_fingerprint, "partial", tuple(completed), "assembly", tuple(capture_views), admission_ids, _assembly_ids(plan), None, (), None, None, "assembly stage rejected after admission")
            raise HX1ExecutionError("HX1_ASSEMBLY_REJECTED", stable_message(exc), failed_stage="assembly") from exc

        try:
            before = _run_recall(plan, bindings, context, evidence, assembly)
            if context.enable_dg6_verification and bindings.dg6_binding is not None:
                projection = project_snapshot_compaction(assembly.snapshot)
                validate_snapshot_compaction_projection(assembly.snapshot, projection)
                if tuple(expand_snapshot_compaction_projection(assembly.snapshot, projection)) != assembly.snapshot.replayed_traces:
                    raise HX1ExecutionError("HX1_PROJECTION_REJECTED", "DG6 expansion mismatch", failed_stage="projection")
                dg6_projection_id = projection.projection_id
            after = _run_recall(plan, bindings, context, evidence, assembly)
            if before != after:
                raise HX1ExecutionError("HX1_RECALL_REJECTED", "DG6 projection changed DI1 envelope", failed_stage="recall")
            recall_envelope = after
            completed.append("recall")
        except HX1ExecutionError as exc:
            return _final_receipt(plan, input_fingerprint, "partial", tuple(completed), exc.failed_stage or "recall", tuple(capture_views), admission_ids, _assembly_ids(plan), assembly.snapshot.snapshot_id, assembly.snapshot.source_admission_ids, dg6_projection_id, None, str(exc))
        except Exception as exc:
            return _final_receipt(plan, input_fingerprint, "partial", tuple(completed), "recall", tuple(capture_views), admission_ids, _assembly_ids(plan), assembly.snapshot.snapshot_id, assembly.snapshot.source_admission_ids, dg6_projection_id, None, "recall stage rejected after assembly")
        return _final_receipt(plan, input_fingerprint, "completed", tuple(completed), None, tuple(capture_views), admission_ids, _assembly_ids(plan), assembly.snapshot.snapshot_id, assembly.snapshot.source_admission_ids, dg6_projection_id, recall_envelope, None)

    raise HX1ExecutionError("HX1_UNSUPPORTED_INTENT", "unsupported HX1 plan intent")


def _run_capture_stage(plan, bindings: HostPlanBindings, capture: CaptureIngress, evidence) -> list[CaptureReceiptView]:
    refs = {ref.capture_id: ref for ref in plan.capture_refs}
    views = []
    for binding in bindings.capture_bindings:
        receipt = capture.capture(binding.request, binding.policy, evidence)
        ref = refs[binding.capture_id]
        if receipt.status is CaptureStatus.rejected:
            raise HX1ExecutionError("HX1_CAPTURE_REJECTED", "capture stage rejected", failed_stage="capture")
        if receipt.status.value != ref.persistence_state and not (ref.persistence_state == "captured" and receipt.status is CaptureStatus.deferred):
            raise HX1ExecutionError("HX1_CAPTURE_STATE_MISMATCH", "capture state did not match plan", failed_stage="capture")
        if ref.admission_state in {"deferred", "candidate", "promotion_requested"} and not receipt.deferred_candidate_id:
            raise HX1ExecutionError("HX1_CAPTURE_STATE_MISMATCH", "planned deferred capture did not publish candidate", failed_stage="capture")
        views.append(
            CaptureReceiptView(
                receipt.capture_id,
                receipt.status.value,
                receipt.shard_id or "",
                receipt.deferred_candidate_id or "",
                receipt.visibility_scope.value,
            )
        )
    return views


def _run_admission_stage(plan, bindings: HostPlanBindings, context: HostExecutionContext, capture: CaptureIngress, coordinator: BatchAdmissionCoordinator) -> tuple[str, ...]:
    members = []
    for binding in bindings.admission_bindings:
        candidate_id = binding.actual_candidate_id or binding.candidate_id
        candidate = capture.state_store.get_candidate(candidate_id)
        if candidate.status is not CandidateStatus.deferred or candidate.shard_id != binding.request.dream_shard.shard_id:
            raise HX1ExecutionError("HX1_ADMISSION_STATE_MISMATCH", "candidate binding did not match capture state", failed_stage="admission")
        members.append(BatchAdmissionMember(binding.member_id, candidate_id, binding.decision, binding.request))
    if not members:
        return ()
    window = BatchAdmissionWindow(
        context.batch_window_id,
        tuple(sorted(member.admission_request.dream_shard.shard_id for member in members)),
        (context.batch_source_ref,),
        context.recorded_at,
        None,
        context.batch_policy_id,
        FIELD_PROFILE_ID,
        BatchWindowStatus.ready_for_selection,
    )
    receipt = coordinator.submit(BatchAdmissionRequest(window, tuple(members), context.recorded_at))
    return tuple(member.admission_receipt.admission_id for member in receipt.member_receipts)


def _open_admission_and_orchestrator(admission_root: Path, evidence, cortex):
    if (admission_root / "records").exists() and any((admission_root / "records").glob("*.json")):
        replay_only = MemoryAdmissionOrchestrator(evidence, cortex, _ReplayValidatedReferences())
        admission = open_admission_store(admission_root, evidence, cortex, replay_only.validate_replay_record)
    else:
        admission = open_admission_store(admission_root, evidence, cortex)
    return admission, MemoryAdmissionOrchestrator(evidence, cortex, admission)


class _ReplayValidatedReferences:
    def validate_record_references(self, record) -> None:
        return None


def _validate_runtime_admission_ids(plan, actual_admission_ids: tuple[str, ...]) -> None:
    if plan.intent == "mixed_explicit" and actual_admission_ids != _assembly_ids(plan):
        raise HX1ExecutionError(
            "HX1_ADMISSION_STATE_MISMATCH",
            "mixed explicit actual admission ids must exactly equal explicit assembly ids",
            failed_stage="admission",
        )


def _run_assembly_stage(plan, bindings: HostPlanBindings, context: HostExecutionContext, evidence, cortex, admission, orchestrator):
    ids = _assembly_ids(plan)
    sources = _admission_sources(evidence, cortex, admission, orchestrator, ids)
    return assemble_field_snapshot(FiniteAdmissionSet(context.finite_set_id, sources))


def _run_recall(plan, bindings: HostPlanBindings, context: HostExecutionContext, evidence, assembly) -> dict[str, Any]:
    if bindings.recall_binding is None:
        raise HX1ExecutionError("HX1_RECALL_REJECTED", "recall binding missing", failed_stage="recall")
    integration_context = IntegrationReadContext(evidence, assembly.universe, None, context_recall_policy(plan, context))
    mapping = IntegrationShell().handle(bindings.recall_binding.invocation, integration_context).to_mapping()
    if not mapping.get("ok"):
        raise HX1ExecutionError("HX1_RECALL_REJECTED", "DI1 recall envelope was not ok", failed_stage="recall")
    digest = resolve_recall(bindings.recall_binding.invocation.query_probe, assembly.universe, evidence, policy=context_recall_policy(plan, context))
    if digest.status is not RecallDigestStatus.resolved:
        raise HX1ExecutionError("HX1_RECALL_REJECTED", "DR1 recall did not resolve", failed_stage="recall")
    return mapping["result"]


def context_recall_policy(plan, context):
    from nollm.dream_geometry.recall import RecallPolicy

    return RecallPolicy(max_seed_covers=plan.recall_request.max_cards, max_lateral_hops=plan.recall_request.max_layers)


def _admission_sources(evidence, cortex, admission, orchestrator, admission_ids: tuple[str, ...]) -> tuple[AdmissionReplaySource, ...]:
    receipts = {receipt.receipt_id: receipt for receipt in cortex.receipts()}
    sources = []
    for admission_id in admission_ids:
        record = admission.get_admission_record(admission_id)
        sources.append(AdmissionReplaySource(record, evidence, cortex, orchestrator.replay_record, receipts[record.compilation_receipt_id], None))
    return tuple(sources)


def _assembly_ids(plan) -> tuple[str, ...]:
    return () if plan.explicit_assembly is None else plan.explicit_assembly.admission_ids


def _final_receipt(plan, input_fingerprint, status, completed, failed, capture_views, admission_ids, explicit_ids, snapshot_id, snapshot_ids, dg6_id, recall_envelope, partial_message) -> HostExecutionReceipt:
    partial = HostExecutionReceipt(
        RECEIPT_KIND,
        plan.plan_id,
        plan.intent,
        status,
        completed,
        failed,
        capture_views,
        admission_ids,
        explicit_ids,
        snapshot_id,
        snapshot_ids,
        dg6_id,
        recall_envelope,
        partial_message,
        "hx1:" + plan.plan_id,
        input_fingerprint,
        "",
    )
    return replace(partial, output_fingerprint=stable_fingerprint(partial))


def _prepare_work_root(work_root: Path, plan_id: str) -> Path:
    work_root.mkdir(parents=True, exist_ok=True)
    marker = work_root / MARKER_NAME
    payload = {"owner": "hx1", "marker_version": "1"}
    if marker.exists():
        existing = json.loads(marker.read_text(encoding="utf-8"))
        if existing != payload:
            raise HX1ExecutionError("HX1_WORK_ROOT_REJECTED", "work root marker mismatch")
    elif any(work_root.iterdir()):
        raise HX1ExecutionError("HX1_WORK_ROOT_REJECTED", "work root must be empty or owned by HX1")
    else:
        marker.write_text(canonical_json(payload), encoding="utf-8", newline="\n")
    return work_root


def _receipt_path(work_root: Path, plan_id: str) -> Path:
    suffix = sha256(plan_id.encode("utf-8")).hexdigest()[:16]
    return work_root / f"{RECEIPT_PREFIX}{suffix}.json"


def _receipt_from_mapping(payload: dict[str, Any]) -> HostExecutionReceipt:
    return HostExecutionReceipt(
        payload["receipt_kind"],
        payload["plan_id"],
        payload["plan_intent"],
        payload["status"],
        tuple(payload["completed_stages"]),
        payload["failed_stage"],
        tuple(CaptureReceiptView(**item) for item in payload["capture_receipt_views"]),
        tuple(payload["admission_receipt_ids"]),
        tuple(payload["explicit_assembly_admission_ids"]),
        payload["snapshot_id"],
        tuple(payload["snapshot_source_admission_ids"]),
        payload["dg6_projection_id"],
        payload["recall_public_envelope"],
        payload["partial_outcome_message"],
        payload["work_root_marker_id"],
        payload["execution_input_fingerprint"],
        payload["output_fingerprint"],
    )


__all__ = ["execute_host_plan", "receipt_to_mapping"]
