"""Immutable DI1 Integration Shell typed call boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nollm.dream_geometry.cortex import CompiledQueryProbe
from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.recall import RecallPolicy, RecallUniverse, RuntimeTimeResolution

from .errors import DI1ErrorCode, ERROR_MESSAGES


MAX_REQUEST_ID_LENGTH = 128


@dataclass(frozen=True, slots=True)
class IntegrationReadContext:
    evidence_store: MemorySubstrateStore
    recall_universe: RecallUniverse
    runtime_time: RuntimeTimeResolution | None
    recall_policy: RecallPolicy


@dataclass(frozen=True, slots=True)
class RecallInvocation:
    request_id: str
    operation: str
    query_probe: CompiledQueryProbe


@dataclass(frozen=True, slots=True)
class CapabilitiesInvocation:
    request_id: str
    operation: str


@dataclass(frozen=True, slots=True)
class IntegrationResponse:
    ok: bool
    request_id: str | None
    operation: str | None
    result: dict[str, Any] | None = None
    error: dict[str, str] | None = None

    def to_mapping(self) -> dict[str, Any]:
        mapping: dict[str, Any] = {
            "ok": self.ok,
            "request_id": self.request_id,
            "operation": self.operation,
        }
        if self.ok:
            mapping["result"] = self.result
        else:
            mapping["error"] = self.error
        return mapping


def validate_request_id(request_id: object) -> bool:
    if not isinstance(request_id, str) or not request_id or len(request_id) > MAX_REQUEST_ID_LENGTH:
        return False
    return not any(ord(char) < 32 for char in request_id)


def error_response(request_id: str | None, operation: str | None, code: DI1ErrorCode) -> IntegrationResponse:
    return IntegrationResponse(
        False,
        request_id if isinstance(request_id, str) else None,
        operation if isinstance(operation, str) else None,
        error={"code": code.value, "message": ERROR_MESSAGES[code]},
    )


__all__ = [
    "CapabilitiesInvocation",
    "IntegrationReadContext",
    "IntegrationResponse",
    "MAX_REQUEST_ID_LENGTH",
    "RecallInvocation",
    "error_response",
    "validate_request_id",
]
