"""CI1 private state store for receipts, candidates, diagnostics, and windows."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .errors import CI1_NOT_FOUND, CaptureError
from .policy import stable_json
from .types import CandidateStatus, CandidateTrigger, CaptureErrorInfo, CaptureReceipt, CaptureStatus, DeferredAdmissionCandidate, VisibilityScope


class CaptureStateStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ("captures", "receipts", "candidates", "diagnostics", "visibility"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self._write_if_missing(self.root / "format.json", {"format_version": "ci1", "store_kind": "capture_ingress"})

    def has_any_state(self) -> bool:
        return self.root.exists() and any(self.root.iterdir())

    def read_capture_identity(self, capture_id: str) -> dict[str, Any] | None:
        path = self._capture_path(capture_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def put_capture_identity(self, payload: dict[str, Any]) -> None:
        self.ensure()
        self._atomic_write(self._capture_path(payload["capture_id"]), payload)

    def put_receipt(self, receipt: CaptureReceipt) -> None:
        self.ensure()
        self._atomic_write(self._receipt_path(receipt.receipt_id), receipt_payload(receipt))

    def get_receipt_by_capture_id(self, capture_id: str) -> CaptureReceipt:
        identity = self.read_capture_identity(capture_id)
        if identity is None or identity.get("receipt_id") is None:
            raise CaptureError(CI1_NOT_FOUND, "receipt_not_found")
        return receipt_from_payload(json.loads(self._receipt_path(identity["receipt_id"]).read_text(encoding="utf-8")))

    def put_candidate(self, candidate: DeferredAdmissionCandidate, capture_id: str) -> None:
        self.ensure()
        self._atomic_write(self._candidate_path(candidate.candidate_id), candidate_payload(candidate, capture_id))

    def get_candidate(self, candidate_id: str) -> DeferredAdmissionCandidate:
        path = self._candidate_path(candidate_id)
        if not path.exists():
            raise CaptureError(CI1_NOT_FOUND, "candidate_not_found")
        payload = json.loads(path.read_text(encoding="utf-8"))
        identity = self.read_capture_identity(payload.get("capture_id", ""))
        if identity is None or identity.get("status") != "deferred" or identity.get("candidate_id") != candidate_id:
            raise CaptureError(CI1_NOT_FOUND, "candidate_not_published")
        return candidate_from_payload(payload)

    def append_visibility(self, scope: VisibilityScope, context_refs: tuple[str, ...], capture_id: str, shard_id: str, order_key: str) -> None:
        if scope is VisibilityScope.persistent_explicit:
            return
        self.ensure()
        for context_ref in context_refs:
            path = self._visibility_path(scope, context_ref)
            payload = {"scope": scope.value, "context_ref": context_ref, "entries": []}
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
            entry = {"capture_id": capture_id, "shard_id": shard_id, "order_key": order_key}
            if entry not in payload["entries"]:
                payload["entries"].append(entry)
                payload["entries"] = sorted(payload["entries"], key=lambda item: (item["order_key"], item["capture_id"], item["shard_id"]))
                self._atomic_write(path, payload)

    def read_visibility_ids(self, scope: VisibilityScope, context_ref: str) -> tuple[str, ...]:
        path = self._visibility_path(scope, context_ref)
        if not path.exists():
            return ()
        payload = json.loads(path.read_text(encoding="utf-8"))
        seen: set[str] = set()
        ordered: list[str] = []
        for entry in sorted(payload["entries"], key=lambda item: (item["order_key"], item["capture_id"], item["shard_id"])):
            shard_id = entry["shard_id"]
            if shard_id not in seen:
                seen.add(shard_id)
                ordered.append(shard_id)
        return tuple(ordered)

    def put_diagnostic(self, payload: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._write_if_missing(self.root / "format.json", {"format_version": "ci1", "store_kind": "capture_ingress"})
        (self.root / "diagnostics").mkdir(parents=True, exist_ok=True)
        self._atomic_write(self.root / "diagnostics" / (_hash(payload["diagnostic_id"]) + ".json"), payload)

    def diagnostic_count(self) -> int:
        if not (self.root / "diagnostics").exists():
            return 0
        return sum(1 for path in (self.root / "diagnostics").iterdir() if path.is_file() and path.suffix == ".json")

    def candidate_count(self) -> int:
        if not (self.root / "candidates").exists():
            return 0
        return sum(1 for path in (self.root / "candidates").iterdir() if path.is_file() and path.suffix == ".json")

    def receipt_count(self) -> int:
        if not (self.root / "receipts").exists():
            return 0
        return sum(1 for path in (self.root / "receipts").iterdir() if path.is_file() and path.suffix == ".json")

    def _capture_path(self, capture_id: str) -> Path:
        return self.root / "captures" / (_hash(capture_id) + ".json")

    def _receipt_path(self, receipt_id: str) -> Path:
        return self.root / "receipts" / (_hash(receipt_id) + ".json")

    def _candidate_path(self, candidate_id: str) -> Path:
        return self.root / "candidates" / (_hash(candidate_id) + ".json")

    def _visibility_path(self, scope: VisibilityScope, context_ref: str) -> Path:
        if scope not in {VisibilityScope.session_window, VisibilityScope.source_window}:
            raise CaptureError(CI1_NOT_FOUND, "visibility_scope_not_persistent")
        return self.root / "visibility" / scope.value / (_hash(context_ref) + ".json")

    def _write_if_missing(self, path: Path, payload: dict[str, Any]) -> None:
        if not path.exists():
            self._atomic_write(path, payload)

    def _atomic_write(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(stable_json(payload), encoding="utf-8")
        temporary.replace(path)


def receipt_payload(receipt: CaptureReceipt) -> dict[str, Any]:
    return {
        "record_type": "capture_receipt",
        "receipt_id": receipt.receipt_id,
        "capture_id": receipt.capture_id,
        "status": receipt.status.value,
        "shard_id": receipt.shard_id,
        "recorded_at": receipt.recorded_at,
        "policy_fingerprint": receipt.policy_fingerprint,
        "visibility_scope": receipt.visibility_scope.value,
        "deferred_candidate_id": receipt.deferred_candidate_id,
        "minimal_ledger_event_id": receipt.minimal_ledger_event_id,
        "error": None if receipt.error is None else asdict(receipt.error),
    }


def receipt_from_payload(payload: dict[str, Any]) -> CaptureReceipt:
    error = payload["error"]
    return CaptureReceipt(
        payload["receipt_id"],
        payload["capture_id"],
        CaptureStatus(payload["status"]),
        payload["shard_id"],
        payload["recorded_at"],
        payload["policy_fingerprint"],
        VisibilityScope(payload["visibility_scope"]),
        payload["deferred_candidate_id"],
        payload["minimal_ledger_event_id"],
        None if error is None else CaptureErrorInfo(error["code"], error["stage"], error["message_class"]),
    )


def candidate_payload(candidate: DeferredAdmissionCandidate, capture_id: str) -> dict[str, Any]:
    return {
        "record_type": "deferred_admission_candidate",
        "capture_id": capture_id,
        "candidate_id": candidate.candidate_id,
        "shard_id": candidate.shard_id,
        "status": candidate.status.value,
        "trigger_refs": tuple(trigger.value for trigger in candidate.trigger_refs),
        "created_at": candidate.created_at,
        "policy_fingerprint": candidate.policy_fingerprint,
        "source_window_refs": candidate.source_window_refs,
        "promotion_attempt_refs": candidate.promotion_attempt_refs,
    }


def candidate_from_payload(payload: dict[str, Any]) -> DeferredAdmissionCandidate:
    return DeferredAdmissionCandidate(
        payload["candidate_id"],
        payload["shard_id"],
        CandidateStatus(payload["status"]),
        tuple(CandidateTrigger(value) for value in payload["trigger_refs"]),
        payload["created_at"],
        payload["policy_fingerprint"],
        tuple(payload["source_window_refs"]),
        tuple(payload["promotion_attempt_refs"]),
    )


def _hash(value: object) -> str:
    text = value if isinstance(value, str) else stable_json(value)
    return sha256(text.encode("utf-8")).hexdigest()


__all__ = [
    "CaptureStateStore",
    "candidate_from_payload",
    "candidate_payload",
    "receipt_from_payload",
    "receipt_payload",
]
