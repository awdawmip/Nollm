"""Versioned host boundary for GRF Core without terminal dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import Any

from .exporters import to_jsonable
from .facade import GRFFacade, admit_request_from_mapping, capture_request_from_mapping, recall_query_from_mapping

CONTRACT_VERSION = "grf_host_v1"
CAPABILITIES = ("capture", "place", "admit", "recall", "replay", "validate")


class UnsupportedCapabilityError(ValueError):
    pass


@dataclass(frozen=True)
class GRFHostRequest:
    contract_version: str
    host_request_id: str
    capability: str
    payload: dict[str, Any]
    evidence_identity: str | None = None
    placement_identity: str | None = None
    admission_identity: str | None = None

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise ValueError("unsupported GRF host contract version")
        _require_host_request_id(self.host_request_id)
        _require_text(self.capability, "capability")
        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a mapping")
        _validate_identity(self.host_request_id, self.evidence_identity, "shard:", "evidence_identity")
        _validate_identity(self.host_request_id, self.placement_identity, "placement:", "placement_identity")
        _validate_identity(self.host_request_id, self.admission_identity, "admission:", "admission_identity")

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "GRFHostRequest":
        if not isinstance(payload, dict):
            raise TypeError("host request must be a mapping")
        return cls(
            str(payload.get("contract_version", "")),
            str(payload.get("host_request_id", "")),
            str(payload.get("capability", "")),
            dict(payload.get("payload", {})),
            _optional_text(payload.get("evidence_identity")),
            _optional_text(payload.get("placement_identity")),
            _optional_text(payload.get("admission_identity")),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "host_request_id": self.host_request_id,
            "capability": self.capability,
            "payload": to_jsonable(self.payload),
            "evidence_identity": self.evidence_identity,
            "placement_identity": self.placement_identity,
            "admission_identity": self.admission_identity,
        }


@dataclass(frozen=True)
class GRFHostResponse:
    contract_version: str
    host_request_id: str
    capability: str
    ok: bool
    result: dict[str, object] | None
    error_code: str | None
    evidence_identity: str | None
    placement_identity: str | None
    admission_identity: str | None
    core_latency_ns: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "host_request_id": self.host_request_id,
            "capability": self.capability,
            "ok": self.ok,
            "result": self.result,
            "error_code": self.error_code,
            "evidence_identity": self.evidence_identity,
            "placement_identity": self.placement_identity,
            "admission_identity": self.admission_identity,
            "core_latency_ns": self.core_latency_ns,
        }


class CapabilityRegistry:
    def __init__(self, supported: tuple[str, ...] = CAPABILITIES) -> None:
        if not supported or any(item not in CAPABILITIES for item in supported):
            raise ValueError("capability registry contains unsupported capability")
        self._supported = tuple(sorted(set(supported)))

    def supports(self, capability: str) -> bool:
        return capability in self._supported

    def require(self, capability: str) -> None:
        if not self.supports(capability):
            raise UnsupportedCapabilityError(f"unsupported capability: {capability}")

    def declaration(self) -> dict[str, object]:
        return {"contract_version": CONTRACT_VERSION, "capabilities": self._supported}


class GRFHostService:
    """Only contract-mediated entrypoint for host adapters."""

    def __init__(self, workspace: Path, capabilities: CapabilityRegistry | None = None) -> None:
        self._facade = GRFFacade(workspace)
        self._capabilities = capabilities or CapabilityRegistry()

    def handle(self, request: GRFHostRequest) -> GRFHostResponse:
        self._capabilities.require(request.capability)
        started = perf_counter_ns()
        try:
            result, evidence, placement, admission = self._dispatch(request)
            return GRFHostResponse(CONTRACT_VERSION, request.host_request_id, request.capability, True, result, None, evidence, placement, admission, perf_counter_ns() - started)
        except (FileNotFoundError, ValueError, TypeError) as exc:
            return GRFHostResponse(CONTRACT_VERSION, request.host_request_id, request.capability, False, None, type(exc).__name__, request.evidence_identity, request.placement_identity, request.admission_identity, perf_counter_ns() - started)

    def _dispatch(self, request: GRFHostRequest) -> tuple[dict[str, object], str | None, str | None, str | None]:
        if request.capability == "capture":
            receipt = self._facade.capture(capture_request_from_mapping(request.payload))
            return to_jsonable(receipt), receipt.shard_id, None, None
        if request.capability in ("place", "admit"):
            shard_id, source_window_id, policy_hint, recorded_at = admit_request_from_mapping(request.payload)
            if request.evidence_identity != shard_id:
                raise ValueError("evidence_identity must match admitted shard_id")
            outcome = self._facade.place(shard_id, source_window_id, policy_hint, recorded_at) if request.capability == "place" else self._facade.admit(shard_id, source_window_id, policy_hint, recorded_at)
            placement = None if outcome.placement_record is None else outcome.placement_record.placement_id
            admission = None if outcome.admission_record is None else outcome.admission_record.admission_id
            return to_jsonable(outcome), shard_id, placement, admission
        if request.capability in ("recall", "replay"):
            query = recall_query_from_mapping(request.payload)
            _validate_query_identity(request, query.entry_mode, query.entry_ref)
            digest = self._facade.recall(query) if request.capability == "recall" else self._facade.replay(query)
            return to_jsonable(digest), request.evidence_identity, request.placement_identity, request.admission_identity
        if request.capability == "validate":
            return to_jsonable(self._facade.validate_workspace()), None, None, None
        raise AssertionError("capability registry and dispatcher disagree")


def _validate_query_identity(request: GRFHostRequest, entry_mode: str, entry_ref: object) -> None:
    expected = {
        "shard_id": request.evidence_identity,
        "placement_id": request.placement_identity,
        "admission_id": request.admission_identity,
    }.get(entry_mode)
    if expected is not None and entry_ref != expected:
        raise ValueError("query identity does not match contract namespace")


def _validate_identity(host_request_id: str, value: str | None, prefix: str, label: str) -> None:
    if value is None:
        return
    _require_text(value, label)
    if value == host_request_id:
        raise ValueError(f"{label} cannot equal host_request_id")
    if not value.startswith(prefix):
        raise ValueError(f"{label} has invalid namespace")


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")


def _require_host_request_id(value: str) -> None:
    _require_text(value, "host_request_id")
    if value.startswith(("shard:", "placement:", "admission:")):
        raise ValueError("host_request_id cannot use a GRF identity namespace")


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("identity must be text or null")
    return value
