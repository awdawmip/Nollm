"""DG7 explicit reference runtime runner."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from nollm.dream_geometry.adapters import IntegrationReadContext, IntegrationShell
from nollm.dream_geometry.adapters.snapshot_compaction import (
    expand_snapshot_compaction_projection,
    project_snapshot_compaction,
    validate_snapshot_compaction_projection,
)
from nollm.dream_geometry.admission import MemoryAdmissionOrchestrator, open_store as open_admission_store
from nollm.dream_geometry.assembly import AdmissionReplaySource, FiniteAdmissionSet, assemble_field_snapshot
from nollm.dream_geometry.batch_admission import BatchAdmissionCoordinator
from nollm.dream_geometry.capture import CandidateStatus, CaptureIngress, CaptureStatus
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.evidence import open_store as open_evidence_store
from nollm.dream_geometry.recall import RecallDigestStatus, resolve_recall

from .scenario import (
    FIXED_SCENARIO_ID,
    admission_request,
    batch_member,
    batch_request,
    build_reference_scenario,
)
from .serialization import canonical_json
from .types import RuntimeCaptureReceiptView, RuntimeIsolationSummary, RuntimePositiveVerificationReceipt

MARKER_NAME = ".dg7_reference_runtime_root.json"
RECEIPT_NAME = ".dg7_reference_runtime_receipt.json"
RECEIPT_KIND = "nollm_dg7_reference_runtime_receipt"


class DG7RuntimeVerificationError(ValueError):
    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


def run_reference_runtime(work_root: Path, *, scenario_id: str = FIXED_SCENARIO_ID) -> RuntimePositiveVerificationReceipt:
    scenario = _load_scenario(scenario_id)
    work_root = _prepare_work_root(Path(work_root), scenario.scenario_id, scenario.scenario_version)
    cached = work_root / RECEIPT_NAME
    if cached.exists():
        return _receipt_from_mapping(json.loads(cached.read_text(encoding="utf-8")))
    before_work = _tree_manifest(work_root)
    try:
        receipt = _execute(work_root, scenario)
    except DG7RuntimeVerificationError:
        raise
    except Exception as exc:
        raise DG7RuntimeVerificationError("DG7_INVALID_SCENARIO", _stable_message(exc)) from exc
    after_work = _tree_manifest(work_root)
    forbidden_work_dirs = tuple(sorted(name for name in ("field", "assembly", "recall", "cache", "database", "global-field") if (work_root / name).exists()))
    if forbidden_work_dirs:
        raise DG7RuntimeVerificationError("DG7_UNEXPECTED_SIDE_EFFECT", "DG7 runner created forbidden work-root paths")
    if not after_work:
        raise DG7RuntimeVerificationError("DG7_UNEXPECTED_SIDE_EFFECT", "DG7 runner did not create explicit work-root evidence")
    if not before_work and MARKER_NAME not in {path for path, _digest in after_work}:
        raise DG7RuntimeVerificationError("DG7_UNEXPECTED_SIDE_EFFECT", "DG7 work-root marker missing")
    final_receipt = replace(receipt, isolation=replace(receipt.isolation, unexpected_write_paths=forbidden_work_dirs))
    cached.write_text(canonical_json(receipt_to_mapping(final_receipt)), encoding="utf-8", newline="\n")
    return final_receipt


def receipt_to_mapping(receipt: RuntimePositiveVerificationReceipt) -> dict[str, Any]:
    return json.loads(canonical_json(receipt))


def error_mapping(reason_code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "kind": "nollm_dg7_reference_runtime_error",
        "reason_code": reason_code,
        "message": _sanitize_message(message),
    }


def _receipt_from_mapping(payload: dict[str, Any]) -> RuntimePositiveVerificationReceipt:
    capture_receipts = tuple(RuntimeCaptureReceiptView(**item) for item in payload["capture_receipts"])
    isolation = RuntimeIsolationSummary(**payload["isolation"])
    return RuntimePositiveVerificationReceipt(
        receipt_kind=payload["receipt_kind"],
        scenario_id=payload["scenario_id"],
        scenario_version=payload["scenario_version"],
        status=payload["status"],
        capture_receipts=capture_receipts,
        admission_receipt_ids=tuple(payload["admission_receipt_ids"]),
        admitted_unassembled_d_admission_id=payload["admitted_unassembled_d_admission_id"],
        snapshot_id=payload["snapshot_id"],
        snapshot_source_admission_ids=tuple(payload["snapshot_source_admission_ids"]),
        snapshot_source_shard_ids=tuple(payload["snapshot_source_shard_ids"]),
        dg6_projection_id=payload["dg6_projection_id"],
        dg6_plan_id=payload["dg6_plan_id"],
        dg6_input_trace_count=payload["dg6_input_trace_count"],
        dg6_view_entry_count=payload["dg6_view_entry_count"],
        dg6_expansion_trace_ids=tuple(payload["dg6_expansion_trace_ids"]),
        recall_envelope=payload["recall_envelope"],
        c_miss_envelope=payload["c_miss_envelope"],
        isolation=isolation,
        output_fingerprint=payload["output_fingerprint"],
    )


def _execute(work_root: Path, scenario) -> RuntimePositiveVerificationReceipt:
    evidence = open_evidence_store(work_root / "evidence")
    capture = CaptureIngress(work_root / "capture")
    captured = {}
    for label, request, policy in scenario.capture_requests:
        receipt = capture.capture(request, policy, evidence)
        if receipt.status is not CaptureStatus.deferred:
            raise DG7RuntimeVerificationError("DG7_CAPTURE_REJECTED", "capture did not create deferred receipt")
        if not receipt.deferred_candidate_id:
            raise DG7RuntimeVerificationError("DG7_CAPTURE_REJECTED", "capture did not publish deferred candidate")
        captured[label] = (receipt, evidence.get_dream_shard(receipt.shard_id))

    cortex = open_cortex_store(work_root / "cortex", evidence)
    admission = open_admission_store(work_root / "admission", evidence, cortex)
    orchestrator = MemoryAdmissionOrchestrator(evidence, cortex, admission)
    coordinator = BatchAdmissionCoordinator(capture.state_store, evidence, orchestrator)
    members = []
    for label, member_id in (("a", "bam_dg7_01"), ("b", "bam_dg7_02")):
        receipt, shard = captured[label]
        candidate = capture.state_store.get_candidate(receipt.deferred_candidate_id or "")
        if candidate.status is not CandidateStatus.deferred:
            raise DG7RuntimeVerificationError("DG7_CAPTURE_REJECTED", "candidate was not deferred")
        members.append(batch_member(label, member_id, candidate.candidate_id, shard, admission_request(label, shard)))
    try:
        ba1_receipt = coordinator.submit(batch_request(tuple(members)))
    except Exception as exc:
        raise DG7RuntimeVerificationError("DG7_ADMISSION_REJECTED", _stable_message(exc)) from exc

    try:
        d_request = admission_request("d", captured["d"][1])
        d_receipt = orchestrator.admit(d_request)
    except Exception as exc:
        raise DG7RuntimeVerificationError("DG7_ADMISSION_REJECTED", _stable_message(exc)) from exc
    if d_receipt.admission_id != "adm_dg7_d":
        raise DG7RuntimeVerificationError("DG7_ADMISSION_REJECTED", "D admission id mismatch")
    _assert_admission_absent(admission, "adm_dg7_c")

    reopened_admission = open_admission_store(work_root / "admission", evidence, cortex, orchestrator.validate_replay_record)
    reopened_orchestrator = MemoryAdmissionOrchestrator(evidence, cortex, reopened_admission)
    observed_admission_ids = tuple(item.admission_receipt.admission_id for item in ba1_receipt.member_receipts)
    admission_ids = _validated_explicit_assembly_ids(
        scenario.explicit_assembly_admission_ids,
        observed_admission_ids,
        c_admission_id="adm_dg7_c",
        d_admission_id=d_receipt.admission_id,
    )
    try:
        assembly = assemble_field_snapshot(FiniteAdmissionSet("dg7_explicit_a_b_set", _admission_sources(evidence, cortex, reopened_admission, reopened_orchestrator, admission_ids)))
    except Exception as exc:
        raise DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", _stable_message(exc)) from exc

    allowed = {captured["a"][1].shard_id, captured["b"][1].shard_id}
    excluded = {captured["c"][1].shard_id, captured["d"][1].shard_id}
    snapshot_shard_ids = tuple(entry.shard_id for entry in assembly.snapshot.admission_manifest)
    if set(snapshot_shard_ids) != allowed or excluded.intersection(snapshot_shard_ids):
        raise DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", "explicit assembly set isolation failed")

    try:
        projection = project_snapshot_compaction(assembly.snapshot)
        validate_snapshot_compaction_projection(assembly.snapshot, projection)
        expanded = expand_snapshot_compaction_projection(assembly.snapshot, projection)
    except Exception as exc:
        raise DG7RuntimeVerificationError("DG7_PROJECTION_REJECTED", _stable_message(exc)) from exc

    expansion_trace_ids = tuple(trace.trace_id for trace in expanded)
    snapshot_trace_ids = tuple(trace.trace_id for trace in assembly.snapshot.replayed_traces)
    expansion_matches = expanded == assembly.snapshot.replayed_traces and expansion_trace_ids == snapshot_trace_ids
    if not expansion_matches:
        raise DG7RuntimeVerificationError("DG7_PROJECTION_REJECTED", "DG6 expansion did not match snapshot replayed traces")

    context = IntegrationReadContext(evidence, assembly.universe, None, scenario.recall_policy)
    shell = IntegrationShell()
    mapping_before_projection = shell.handle(scenario.recall_invocation, context).to_mapping()
    digest = resolve_recall(scenario.recall_invocation.query_probe, assembly.universe, evidence, policy=scenario.recall_policy)
    mapping_after_projection = shell.handle(scenario.recall_invocation, context).to_mapping()
    c_mapping = shell.handle(scenario.c_miss_invocation, context).to_mapping()
    if not mapping_after_projection["ok"] or not mapping_before_projection["ok"]:
        raise DG7RuntimeVerificationError("DG7_RECALL_REJECTED", "DI1 recall envelope was not ok")
    if mapping_after_projection != mapping_before_projection:
        raise DG7RuntimeVerificationError("DG7_RECALL_REJECTED", "DG6 projection changed DI1 envelope")
    if digest.status is not RecallDigestStatus.resolved:
        raise DG7RuntimeVerificationError("DG7_RECALL_REJECTED", "DR1 recall did not resolve A/B evidence")
    recalled = {item["shard_id"] for item in mapping_after_projection["result"]["primary_evidence"]}
    if not recalled or not recalled.issubset(allowed) or excluded.intersection(recalled):
        raise DG7RuntimeVerificationError("DG7_RECALL_REJECTED", "recall isolation failed")
    if c_mapping.get("result", {}).get("primary_evidence") != []:
        raise DG7RuntimeVerificationError("DG7_RECALL_REJECTED", "C miss envelope unexpectedly contains evidence")

    isolation = RuntimeIsolationSummary(
        captured_unadmitted_c_excluded=True,
        admitted_unassembled_d_excluded=True,
        snapshot_replayed_trace_manifest_matches_dg6_expansion=expansion_matches,
        recall_is_independent_of_dg6_view=mapping_after_projection == mapping_before_projection,
        unexpected_write_paths=(),
    )
    partial = RuntimePositiveVerificationReceipt(
        receipt_kind=RECEIPT_KIND,
        scenario_id=scenario.scenario_id,
        scenario_version=scenario.scenario_version,
        status="completed",
        capture_receipts=tuple(
            RuntimeCaptureReceiptView(
                label,
                receipt.capture_id,
                receipt.status.value,
                receipt.shard_id,
                receipt.deferred_candidate_id or "",
                receipt.visibility_scope.value,
            )
            for label, (receipt, _shard) in sorted(captured.items())
        ),
        admission_receipt_ids=tuple(item.admission_receipt.admission_id for item in ba1_receipt.member_receipts),
        admitted_unassembled_d_admission_id=d_receipt.admission_id,
        snapshot_id=assembly.snapshot.snapshot_id,
        snapshot_source_admission_ids=assembly.snapshot.source_admission_ids,
        snapshot_source_shard_ids=snapshot_shard_ids,
        dg6_projection_id=projection.projection_id,
        dg6_plan_id=projection.compression_plan.plan_id,
        dg6_input_trace_count=projection.compression_plan.input_trace_count,
        dg6_view_entry_count=projection.compacted_trace_view.entry_count,
        dg6_expansion_trace_ids=expansion_trace_ids,
        recall_envelope=mapping_after_projection["result"],
        c_miss_envelope=c_mapping["result"],
        isolation=isolation,
        output_fingerprint="",
    )
    fingerprint = "sha256:" + sha256(canonical_json(partial).encode("utf-8")).hexdigest()
    return replace(partial, output_fingerprint=fingerprint)


def _admission_sources(evidence, cortex, admission, orchestrator, admission_ids: tuple[str, ...]) -> tuple[AdmissionReplaySource, ...]:
    receipts = {receipt.receipt_id: receipt for receipt in cortex.receipts()}
    sources = []
    for admission_id in admission_ids:
        record = admission.get_admission_record(admission_id)
        sources.append(AdmissionReplaySource(record, evidence, cortex, orchestrator.replay_record, receipts[record.compilation_receipt_id], None))
    return tuple(sources)


def _validated_explicit_assembly_ids(
    declared_ids: object,
    observed_ids: tuple[str, ...],
    *,
    c_admission_id: str,
    d_admission_id: str,
) -> tuple[str, ...]:
    if not isinstance(declared_ids, tuple) or not declared_ids:
        raise DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", "explicit assembly declaration must be a non-empty tuple")
    if not all(isinstance(item, str) and item for item in declared_ids):
        raise DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", "explicit assembly declaration ids must be non-empty strings")
    if len(set(declared_ids)) != len(declared_ids):
        raise DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", "explicit assembly declaration ids must be unique")
    if c_admission_id in declared_ids:
        raise DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", "captured-only C cannot be in explicit assembly declaration")
    if d_admission_id in declared_ids:
        raise DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", "admitted-unassembled D cannot be in explicit assembly declaration")
    if observed_ids != declared_ids:
        raise DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", "BA1 admission receipts do not match the explicit assembly declaration")
    return declared_ids


def _assert_admission_absent(admission, admission_id: str) -> None:
    try:
        admission.get_admission_record(admission_id)
    except FileNotFoundError:
        return
    except Exception as exc:
        raise DG7RuntimeVerificationError("DG7_ADMISSION_REJECTED", "failed to confirm captured-only admission absence") from exc
    raise DG7RuntimeVerificationError("DG7_ADMISSION_REJECTED", "C unexpectedly has AdmissionRecord")


def _load_scenario(scenario_id: str):
    try:
        return build_reference_scenario(scenario_id)
    except Exception as exc:
        raise DG7RuntimeVerificationError("DG7_INVALID_SCENARIO", "unknown DG7 scenario") from exc


def _prepare_work_root(work_root: Path, scenario_id: str, scenario_version: str) -> Path:
    if not work_root.exists():
        work_root.mkdir(parents=True)
    if not work_root.is_dir():
        raise DG7RuntimeVerificationError("DG7_INVALID_WORK_ROOT", "work root must be a directory")
    marker = work_root / MARKER_NAME
    entries = [entry.name for entry in work_root.iterdir()]
    if entries and not marker.exists():
        raise DG7RuntimeVerificationError("DG7_INVALID_WORK_ROOT", "work root is not an empty or owned DG7 root")
    if marker.exists():
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except Exception as exc:
            raise DG7RuntimeVerificationError("DG7_INVALID_WORK_ROOT", "DG7 work root marker is unreadable") from exc
        if payload != {"scenario_id": scenario_id, "scenario_version": scenario_version}:
            raise DG7RuntimeVerificationError("DG7_INVALID_WORK_ROOT", "DG7 work root marker does not match scenario")
    else:
        marker.write_text(canonical_json({"scenario_id": scenario_id, "scenario_version": scenario_version}), encoding="utf-8", newline="\n")
    return work_root


def _tree_manifest(root: Path) -> tuple[tuple[str, str], ...]:
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))


def _stable_message(exc: Exception) -> str:
    reason = getattr(exc, "reason_code", None) or getattr(exc, "code", None)
    if reason:
        return f"lower layer rejected input: {reason}"
    return "lower layer rejected input"


def _sanitize_message(message: str) -> str:
    forbidden = ("Traceback", "AttributeError", "KeyError", "TypeError", "ValueError", "nollm.dream_geometry")
    rendered = str(message)
    if any(token in rendered for token in forbidden):
        return "DG7 structured failure"
    return rendered


__all__ = [
    "DG7RuntimeVerificationError",
    "RECEIPT_KIND",
    "error_mapping",
    "receipt_to_mapping",
    "run_reference_runtime",
]
