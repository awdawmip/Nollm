"""CI1 Capture Ingress public entrypoint."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from nollm.dream_geometry.evidence import DreamShard, MemorySubstrateStore, OriginDescriptor, TemporalContext
from nollm.dream_geometry.protocol.contracts import UsageState

from .errors import CI1_CAPTURE_ID_CONFLICT, CI1_COMMIT_FAILED, CaptureError
from .policy import canonical_policy_payload, canonical_request_payload, policy_fingerprint, request_fingerprint, stable_json, validate_request_policy_pair
from .state_store import CaptureStateStore
from .types import (
    CandidateStatus,
    CaptureDiagnostics,
    CaptureErrorInfo,
    CaptureLineage,
    CapturePersistence,
    CapturePolicy,
    CaptureReceipt,
    CaptureRequest,
    CaptureStatus,
    DeferredAdmissionCandidate,
    VisibilityScope,
)


class CaptureIngress:
    def __init__(self, state_root: Path):
        self.state_store = CaptureStateStore(state_root)

    def capture(self, request: CaptureRequest, policy: CapturePolicy, evidence_store: MemorySubstrateStore) -> CaptureReceipt:
        try:
            validate_request_policy_pair(request, policy)
        except CaptureError as exc:
            receipt = self._rejected_receipt(request, policy, exc)
            self._diagnostic(policy, request, receipt, success=False)
            return receipt

        request_fp = request_fingerprint(request)
        policy_fp = policy_fingerprint(policy)
        receipt_id = _id("capr", request.capture_id + "|" + request_fp + "|" + policy_fp)
        shard_id = _id("shard:ci1", request.capture_id)
        candidate_id = _id("dac", request.capture_id + "|" + policy_fp) if request.deferred_candidate_request.requested else None
        identity = self.state_store.read_capture_identity(request.capture_id)
        if identity is not None:
            if identity["request_fingerprint"] != request_fp or identity["policy_fingerprint"] != policy_fp:
                error = CaptureError(CI1_CAPTURE_ID_CONFLICT, "capture_identity_conflict")
                receipt = self._rejected_receipt(request, policy, error)
                self._diagnostic(policy, request, receipt, success=False)
                return receipt
            if identity.get("durable_receipt") is True:
                return self.state_store.get_receipt_by_capture_id(request.capture_id)
            return CaptureReceipt(
                identity["receipt_id"],
                identity["capture_id"],
                CaptureStatus(identity["status"]),
                identity["shard_id"],
                identity["recorded_at"],
                identity["policy_fingerprint"],
                VisibilityScope(identity["visibility_scope"]),
                identity["candidate_id"],
                identity["minimal_ledger_event_id"],
            )

        if policy.persistence is CapturePersistence.ephemeral:
            return CaptureReceipt(receipt_id, request.capture_id, CaptureStatus.ephemeral, None, request.recorded_at, policy_fp, request.requested_visibility_scope, None, None)

        shard = DreamShard(
            shard_id,
            request.content,
            OriginDescriptor(request.origin.kind, request.origin.reference, request.origin.context_reference, request.origin.role_label),
            TemporalContext(request.recorded_at, None, request.recorded_at, None),
            request.context_refs,
            UsageState.tentative,
        )
        try:
            write_result = evidence_store.put_dream_shard(shard)
            ledger_event_id = write_result.ledger_event_id or _ledger_event_id_for(evidence_store, shard_id)
            self.state_store.append_visibility(request.requested_visibility_scope, request.context_refs, request.capture_id, shard_id, request.capture_id)
            candidate = None
            status = CaptureStatus.captured
            if candidate_id is not None:
                candidate = DeferredAdmissionCandidate(
                    candidate_id,
                    shard_id,
                    CandidateStatus.deferred,
                    tuple(sorted(request.deferred_candidate_request.trigger_refs, key=lambda item: item.value)),
                    request.recorded_at,
                    policy_fp,
                    tuple(sorted(request.context_refs)),
                )
                self.state_store.put_candidate(candidate, request.capture_id)
                status = CaptureStatus.deferred
            durable_receipt = policy.lineage is CaptureLineage.minimal
            receipt = CaptureReceipt(receipt_id, request.capture_id, status, shard_id, request.recorded_at, policy_fp, request.requested_visibility_scope, candidate_id, ledger_event_id)
            self._diagnostic(policy, request, receipt, success=True)
            if durable_receipt:
                self.state_store.put_receipt(receipt)
            self.state_store.put_capture_identity(
                {
                    "capture_id": request.capture_id,
                    "request_fingerprint": request_fp,
                    "policy_fingerprint": policy_fp,
                    "receipt_id": receipt_id,
                    "durable_receipt": durable_receipt,
                    "status": status.value,
                    "shard_id": shard_id,
                    "candidate_id": candidate_id,
                    "recorded_at": request.recorded_at,
                    "visibility_scope": request.requested_visibility_scope.value,
                    "minimal_ledger_event_id": ledger_event_id,
                }
            )
            return receipt
        except Exception as exc:
            error = CaptureError(CI1_COMMIT_FAILED, "commit_failed")
            raise error from exc

    def _rejected_receipt(self, request: CaptureRequest, policy: CapturePolicy, error: CaptureError) -> CaptureReceipt:
        policy_fp = policy_fingerprint(policy) if isinstance(policy, CapturePolicy) else "sha256:" + "0" * 64
        capture_id = getattr(request, "capture_id", "cap_invalid")
        recorded_at = getattr(request, "recorded_at", "")
        visibility = getattr(request, "requested_visibility_scope", VisibilityScope.current_turn)
        receipt_id = _id("capr", capture_id + "|" + error.code + "|" + error.message_class)
        return CaptureReceipt(receipt_id, capture_id, CaptureStatus.rejected, None, recorded_at, policy_fp, visibility, None, None, CaptureErrorInfo(error.code, error.stage, error.message_class))

    def _diagnostic(self, policy: CapturePolicy, request: CaptureRequest, receipt: CaptureReceipt, *, success: bool) -> None:
        if policy.diagnostics is CaptureDiagnostics.off:
            return
        if success and policy.diagnostics is CaptureDiagnostics.on_failure:
            return
        payload = {
            "record_type": "capture_diagnostic",
            "diagnostic_id": _id("diag", receipt.receipt_id),
            "capture_id": request.capture_id,
            "receipt_id": receipt.receipt_id,
            "status": receipt.status.value,
            "stage": "capture",
            "message_class": "success" if success else (receipt.error.message_class if receipt.error else "failure"),
            "error_code": None if receipt.error is None else receipt.error.code,
            "policy_fingerprint": receipt.policy_fingerprint,
            "request_fingerprint": request_fingerprint(request) if isinstance(request, CaptureRequest) else None,
            "expires_at": request.diagnostic_retention_until if policy.diagnostics is CaptureDiagnostics.verbose else None,
        }
        self.state_store.put_diagnostic(payload)


def _id(prefix: str, value: str) -> str:
    return prefix + ":" + sha256(value.encode("utf-8")).hexdigest()[:32]


def _ledger_event_id_for(evidence_store: MemorySubstrateStore, shard_id: str) -> str | None:
    for event in evidence_store.read_ledger():
        if event.record_id == shard_id:
            return event.event_id
    return None


__all__ = ["CaptureIngress"]
