"""Shared adapter operation surface; methods only forward contract mappings."""

from __future__ import annotations

from typing import Any, Protocol


class GRFAdapter(Protocol):
    def handle_mapping(self, payload: dict[str, Any]) -> dict[str, object]: ...
    def capture(self, payload: dict[str, Any]) -> dict[str, object]: ...
    def place(self, payload: dict[str, Any]) -> dict[str, object]: ...
    def admit(self, payload: dict[str, Any]) -> dict[str, object]: ...
    def recall(self, payload: dict[str, Any]) -> dict[str, object]: ...
    def validate(self, payload: dict[str, Any]) -> dict[str, object]: ...


class GRFAdapterOperations:
    def capture(self, payload: dict[str, Any]) -> dict[str, object]:
        return self._forward("capture", payload)

    def place(self, payload: dict[str, Any]) -> dict[str, object]:
        return self._forward("place", payload)

    def admit(self, payload: dict[str, Any]) -> dict[str, object]:
        return self._forward("admit", payload)

    def recall(self, payload: dict[str, Any]) -> dict[str, object]:
        return self._forward("recall", payload)

    def validate(self, payload: dict[str, Any]) -> dict[str, object]:
        return self._forward("validate", payload)

    def _forward(self, capability: str, payload: dict[str, Any]) -> dict[str, object]:
        if payload.get("capability") != capability:
            return {"contract_version": "grf_host_v1", "ok": False, "error_code": "adapter_capability_mismatch"}
        return self.handle_mapping(payload)
