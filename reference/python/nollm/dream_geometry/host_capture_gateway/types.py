"""HCG1 public gateway request values."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nollm.dream_geometry.capture import CapturePolicy, CaptureRequest


@dataclass(frozen=True, slots=True)
class GatewayCaptureRequest:
    request_id: str
    capture_request: CaptureRequest
    capture_policy: CapturePolicy


@dataclass(frozen=True, slots=True)
class GatewayReadRequest:
    request_id: str
    scope: str
    context_ref: str | None = None
    shard_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GatewayContext:
    workspace: Path


__all__ = ["GatewayCaptureRequest", "GatewayContext", "GatewayReadRequest"]
