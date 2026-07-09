"""Explicit file-first GRF capture prototype."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .evidence import EvidenceShardRecord, ORIGIN_KINDS
from .storage import GRFFileStore


CAPTURE_STATUSES = frozenset({"captured", "rejected"})


@dataclass(frozen=True)
class GRFCaptureRequest:
    capture_id: str
    content: str
    origin_kind: str
    source_window_refs: tuple[str, ...]
    recorded_at: str
    policy_id: str = "grf_capture_default"

    def __post_init__(self) -> None:
        _require_text(self.capture_id, "capture_id")
        _require_text(self.content, "content")
        if self.origin_kind not in ORIGIN_KINDS:
            raise ValueError("unknown origin_kind")
        _require_refs(self.source_window_refs, "source_window_refs")
        _require_text(self.recorded_at, "recorded_at")
        _require_text(self.policy_id, "policy_id")


@dataclass(frozen=True)
class GRFCaptureReceipt:
    receipt_id: str
    capture_id: str
    status: str
    shard_id: str | None
    source_window_refs: tuple[str, ...]
    recorded_at: str
    error: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.receipt_id, "receipt_id")
        _require_text(self.capture_id, "capture_id")
        if self.status not in CAPTURE_STATUSES:
            raise ValueError("unknown capture status")
        if self.status == "captured":
            _require_text(self.shard_id, "shard_id")
        _require_refs(self.source_window_refs, "source_window_refs", allow_empty=True)
        _require_text(self.recorded_at, "recorded_at")
        if self.error is not None:
            _require_text(self.error, "error")


class GRFCaptureIngress:
    def __init__(self, store: GRFFileStore) -> None:
        self.store = store

    def capture(self, request: GRFCaptureRequest) -> GRFCaptureReceipt:
        shard_id = _capture_shard_id(request.capture_id)
        receipt_id = _receipt_id(request.capture_id, request.content)
        try:
            shard = EvidenceShardRecord(
                shard_id,
                request.content,
                request.recorded_at,
                request.origin_kind,
                request.source_window_refs,
                "host_declared",
                "captured",
            )
            self.store.write_evidence_shard(shard, request.recorded_at)
        except (FileExistsError, ValueError) as exc:
            return GRFCaptureReceipt(_receipt_id(request.capture_id, str(exc)), request.capture_id, "rejected", None, request.source_window_refs, request.recorded_at, str(exc))
        return GRFCaptureReceipt(receipt_id, request.capture_id, "captured", shard_id, request.source_window_refs, request.recorded_at)


def _capture_shard_id(capture_id: str) -> str:
    return "shard:grf:" + sha256(capture_id.encode("utf-8")).hexdigest()[:24]


def _receipt_id(capture_id: str, value: str) -> str:
    return "receipt:grf:" + sha256(f"{capture_id}\0{value}".encode("utf-8")).hexdigest()[:24]


def _require_text(value: str | None, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")


def _require_refs(values: tuple[str, ...], label: str, allow_empty: bool = False) -> None:
    if not isinstance(values, tuple) or (not allow_empty and not values) or any(not isinstance(value, str) or value == "" for value in values):
        raise ValueError(f"{label} must be a tuple of non-empty text")
