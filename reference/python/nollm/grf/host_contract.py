"""Versioned host boundary for GRF Core without terminal dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import Any

from .exporters import to_jsonable
from .facade import GRFFacade, admit_existing_placement_request_from_mapping, admit_request_from_mapping, capture_request_from_mapping, recall_query_from_mapping

CONTRACT_VERSION = "grf_host_v2"
SUPPORTED_CONTRACT_VERSIONS = ("grf_host_v1", CONTRACT_VERSION)
CAPABILITIES = ("capture", "capture_source", "place", "admit", "recall", "replay", "source_get", "revise", "retire", "validate")


class UnsupportedCapabilityError(ValueError):
    pass


@dataclass(frozen=True)
class HostRequestID:
    value: str

    def __post_init__(self) -> None:
        _require_text(self.value, "host_request_id")
        if self.value.startswith(("shard:", "placement:", "admission:")):
            raise ValueError("host_request_id cannot use a GRF identity namespace")


@dataclass(frozen=True)
class EvidenceIdentity:
    value: str

    def __post_init__(self) -> None:
        _require_namespaced_identity(self.value, "shard:", "evidence_identity")


@dataclass(frozen=True)
class PlacementIdentity:
    value: str

    def __post_init__(self) -> None:
        _require_namespaced_identity(self.value, "placement:", "placement_identity")


@dataclass(frozen=True)
class AdmissionIdentity:
    value: str

    def __post_init__(self) -> None:
        _require_namespaced_identity(self.value, "admission:", "admission_identity")


@dataclass(frozen=True)
class GRFHostRequest:
    contract_version: str
    host_request_id: HostRequestID
    capability: str
    payload: dict[str, Any]
    evidence_identity: EvidenceIdentity | None = None
    placement_identity: PlacementIdentity | None = None
    admission_identity: AdmissionIdentity | None = None

    def __post_init__(self) -> None:
        if self.contract_version not in SUPPORTED_CONTRACT_VERSIONS:
            raise ValueError("unsupported GRF host contract version")
        if not isinstance(self.host_request_id, HostRequestID):
            raise TypeError("host_request_id must be HostRequestID")
        _require_text(self.capability, "capability")
        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a mapping")
        if self.evidence_identity is not None and not isinstance(self.evidence_identity, EvidenceIdentity):
            raise TypeError("evidence_identity must be EvidenceIdentity")
        if self.placement_identity is not None and not isinstance(self.placement_identity, PlacementIdentity):
            raise TypeError("placement_identity must be PlacementIdentity")
        if self.admission_identity is not None and not isinstance(self.admission_identity, AdmissionIdentity):
            raise TypeError("admission_identity must be AdmissionIdentity")
        _validate_capability_identities(self)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "GRFHostRequest":
        if not isinstance(payload, dict):
            raise TypeError("host request must be a mapping")
        return cls(
            _mapping_text(payload, "contract_version"),
            HostRequestID(_mapping_text(payload, "host_request_id")),
            _mapping_text(payload, "capability"),
            _mapping_payload(payload),
            _identity_from_mapping(payload, "evidence_identity", EvidenceIdentity),
            _identity_from_mapping(payload, "placement_identity", PlacementIdentity),
            _identity_from_mapping(payload, "admission_identity", AdmissionIdentity),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "host_request_id": self.host_request_id.value,
            "capability": self.capability,
            "payload": to_jsonable(self.payload),
            "evidence_identity": None if self.evidence_identity is None else self.evidence_identity.value,
            "placement_identity": None if self.placement_identity is None else self.placement_identity.value,
            "admission_identity": None if self.admission_identity is None else self.admission_identity.value,
        }


@dataclass(frozen=True)
class GRFHostResponse:
    contract_version: str
    host_request_id: HostRequestID
    capability: str
    ok: bool
    result: dict[str, object] | None
    error_code: str | None
    evidence_identity: EvidenceIdentity | None
    placement_identity: PlacementIdentity | None
    admission_identity: AdmissionIdentity | None
    core_latency_ns: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "host_request_id": self.host_request_id.value,
            "capability": self.capability,
            "ok": self.ok,
            "result": self.result,
            "error_code": self.error_code,
            "evidence_identity": None if self.evidence_identity is None else self.evidence_identity.value,
            "placement_identity": None if self.placement_identity is None else self.placement_identity.value,
            "admission_identity": None if self.admission_identity is None else self.admission_identity.value,
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

    def declaration(self, contract_version: str = CONTRACT_VERSION) -> dict[str, object]:
        if contract_version not in SUPPORTED_CONTRACT_VERSIONS:
            raise ValueError("unsupported GRF host contract version")
        return {"contract_version": contract_version, "capabilities": self._supported}


class GRFHostService:
    """Only contract-mediated entrypoint for host adapters."""

    def __init__(self, workspace: Path, capabilities: CapabilityRegistry | None = None) -> None:
        self._facade = GRFFacade(workspace)
        self._capabilities = capabilities or CapabilityRegistry()

    def handle(self, request: GRFHostRequest) -> GRFHostResponse:
        started = perf_counter_ns()
        try:
            self._capabilities.require(request.capability)
            result, evidence, placement, admission = self._dispatch(request)
            return GRFHostResponse(request.contract_version, request.host_request_id, request.capability, True, result, None, _evidence(evidence), _placement(placement), _admission(admission), perf_counter_ns() - started)
        except (FileNotFoundError, UnsupportedCapabilityError, ValueError, TypeError) as exc:
            return GRFHostResponse(request.contract_version, request.host_request_id, request.capability, False, None, type(exc).__name__, request.evidence_identity, request.placement_identity, request.admission_identity, perf_counter_ns() - started)

    def _dispatch(self, request: GRFHostRequest) -> tuple[dict[str, object], str | None, str | None, str | None]:
        if request.capability == "capture":
            receipt = self._facade.capture(capture_request_from_mapping(request.payload))
            return to_jsonable(receipt), receipt.shard_id, None, None
        if request.capability == "capture_source":
            path = Path(_mapping_text(request.payload, "path"))
            result = self._facade.capture_source(path, _mapping_text(request.payload, "recorded_at"))
            return to_jsonable(result), None, None, None
        if request.capability == "place":
            shard_id, source_window_id, policy_hint, recorded_at = admit_request_from_mapping(request.payload)
            if request.evidence_identity is None or request.evidence_identity.value != shard_id:
                raise ValueError("evidence_identity must match placed shard_id")
            outcome = self._facade.place(shard_id, source_window_id, policy_hint, recorded_at)
            placement = None if outcome.placement_record is None else outcome.placement_record.placement_id
            return to_jsonable(outcome), shard_id, placement, None
        if request.capability == "admit":
            shard_id, cell, placement_id, recorded_at, admitted_by = admit_existing_placement_request_from_mapping(request.payload)
            if request.evidence_identity is None or request.evidence_identity.value != shard_id:
                raise ValueError("evidence_identity must match admitted shard_id")
            if request.placement_identity is None or request.placement_identity.value != placement_id:
                raise ValueError("placement_identity must match admitted placement_id")
            admission = self._facade.admit_existing_placement(shard_id, cell, placement_id, recorded_at, admitted_by)
            return to_jsonable(admission), shard_id, placement_id, admission.admission_id
        if request.capability in ("recall", "replay"):
            query = recall_query_from_mapping(request.payload)
            _validate_query_identity(request, query.entry_mode, query.entry_ref)
            digest = self._facade.recall(query) if request.capability == "recall" else self._facade.replay(query)
            return to_jsonable(digest), _value(request.evidence_identity), _value(request.placement_identity), _value(request.admission_identity)
        if request.capability == "source_get":
            if request.evidence_identity is None:
                raise ValueError("source_get requires evidence_identity")
            return {"content": self._facade.get_source(request.evidence_identity.value)}, request.evidence_identity.value, None, None
        if request.capability == "revise":
            result = self._facade.revise(Path(_mapping_text(request.payload, "path")), _mapping_text(request.payload, "recorded_at"))
            return to_jsonable(result), None, None, None
        if request.capability == "retire":
            result = self._facade.retire(_mapping_text(request.payload, "source_id"))
            return to_jsonable(result), None, None, None
        if request.capability == "validate":
            return to_jsonable(self._facade.validate_workspace()), None, None, None
        raise AssertionError("capability registry and dispatcher disagree")


def _validate_query_identity(request: GRFHostRequest, entry_mode: str, entry_ref: object) -> None:
    identities = (request.evidence_identity, request.placement_identity, request.admission_identity)
    required = {
        "shard_id": (request.evidence_identity, "evidence_identity"),
        "placement_id": (request.placement_identity, "placement_identity"),
        "admission_id": (request.admission_identity, "admission_identity"),
    }.get(entry_mode)
    if required is None:
        if any(item is not None for item in identities):
            raise ValueError("non-identity query mode cannot declare GRF identities")
        return
    identity, label = required
    if identity is None:
        raise ValueError(f"{entry_mode} query requires {label}")
    if entry_ref != identity.value:
        raise ValueError("query identity does not match contract namespace")
    if sum(item is not None for item in identities) != 1:
        raise ValueError("identity query must declare exactly one GRF identity")


def _validate_capability_identities(request: GRFHostRequest) -> None:
    identities = (request.evidence_identity, request.placement_identity, request.admission_identity)
    if request.capability in ("capture", "capture_source", "revise", "retire", "validate") and any(item is not None for item in identities):
        raise ValueError(f"{request.capability} cannot declare GRF identities")
    if request.capability == "source_get":
        if request.evidence_identity is None or request.placement_identity is not None or request.admission_identity is not None:
            raise ValueError("source_get requires exactly evidence_identity")
    if request.capability == "place":
        if request.evidence_identity is None:
            raise ValueError("place requires evidence_identity")
        if request.placement_identity is not None or request.admission_identity is not None:
            raise ValueError("place cannot predeclare output identities")
    if request.capability == "admit":
        if request.evidence_identity is None or request.placement_identity is None:
            raise ValueError("admit requires evidence_identity and placement_identity")
        if request.admission_identity is not None:
            raise ValueError("admit cannot predeclare admission_identity")


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")


def _require_namespaced_identity(value: str, prefix: str, label: str) -> None:
    _require_text(value, label)
    if not value.startswith(prefix):
        raise ValueError(f"{label} has invalid namespace")


def _mapping_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{key} must be non-empty text")
    return value


def _mapping_payload(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("payload")
    if not isinstance(value, dict):
        raise TypeError("payload must be a mapping")
    return dict(value)


def _identity_from_mapping(payload: dict[str, Any], key: str, identity_type):
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("identity must be text or null")
    return identity_type(value)


def _value(identity: object | None) -> str | None:
    return None if identity is None else identity.value


def _evidence(value: str | None) -> EvidenceIdentity | None:
    return None if value is None else EvidenceIdentity(value)


def _placement(value: str | None) -> PlacementIdentity | None:
    return None if value is None else PlacementIdentity(value)


def _admission(value: str | None) -> AdmissionIdentity | None:
    return None if value is None else AdmissionIdentity(value)
