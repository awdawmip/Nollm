"""File-backed product Host that reaches GRF only through a replaceable adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .grf_adapter_contract import GRFAdapter
from .grf_file_adapter import GRFFileAdapter

PRODUCT_CAPABILITIES = ("capture", "place", "admit", "recall", "replay", "validate")


class GRFProductHost:
    def __init__(self, workspace: Path, host_name: str, contract_version: str = "grf_host_v2", adapter: GRFAdapter | None = None) -> None:
        if contract_version not in ("grf_host_v1", "grf_host_v2"):
            raise ValueError("unsupported product host contract version")
        self.workspace = Path(workspace)
        self.host_name = host_name
        self.contract_version = contract_version
        self.session_id = f"session:product:{host_name}:{uuid4().hex}"
        self._adapter = adapter or GRFFileAdapter(self.workspace)
        self._sequence = 0

    def negotiate(self) -> tuple[str, ...]:
        return PRODUCT_CAPABILITIES

    def capture(self, capture_id: str, content: str, source_window_id: str, recorded_at: str) -> dict[str, object]:
        return self._invoke("capture", {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": capture_id, "content": content, "origin_kind": "user_utterance", "source_window_refs": (source_window_id,), "recorded_at": recorded_at})

    def place(self, shard_id: str, source_window_id: str, recorded_at: str) -> dict[str, object]:
        return self._invoke("place", {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": shard_id, "source_window_id": source_window_id, "policy_hint": {"policy_id": "grf_deterministic_policy_v1", "chart_id": "chart:product"}, "recorded_at": recorded_at}, evidence=shard_id)

    def admit(self, shard_id: str, placement_id: str, recorded_at: str) -> dict[str, object]:
        return self._invoke("admit", {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": shard_id, "placement_id": placement_id, "recorded_at": recorded_at, "admitted_by": "host_rule"}, evidence=shard_id, placement=placement_id)

    def recall(self, entry_mode: str, entry_ref: str, identity: str) -> dict[str, object]:
        return self._query("recall", entry_mode, entry_ref, identity)

    def replay(self, entry_mode: str, entry_ref: str, identity: str) -> dict[str, object]:
        return self._query("replay", entry_mode, entry_ref, identity)

    def validate(self) -> dict[str, object]:
        return self._invoke("validate", {})

    def restart(self) -> "GRFProductHost":
        return GRFProductHost(self.workspace, self.host_name, self.contract_version)

    def _query(self, capability: str, entry_mode: str, entry_ref: str, identity: str) -> dict[str, object]:
        identities = {"evidence": None, "placement": None, "admission": None}
        key = {"shard_id": "evidence", "placement_id": "placement", "admission_id": "admission"}.get(entry_mode)
        if key is None:
            raise ValueError("product Host requires an identity-bearing query mode")
        identities[key] = identity
        payload = {"kind": "nollm_grf_recall_request", "version": "1", "query_id": f"query:product:{self.host_name}:{entry_mode}", "entry_mode": entry_mode, "entry_ref": entry_ref, "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}
        return self._invoke(capability, payload, **identities)

    def _invoke(self, capability: str, payload: dict[str, Any], evidence: str | None = None, placement: str | None = None, admission: str | None = None) -> dict[str, object]:
        if capability not in self.negotiate():
            raise ValueError("product capability not negotiated")
        self._sequence += 1
        request = {"contract_version": self.contract_version, "host_request_id": f"host:product:{self.host_name}:{self.session_id}:{self._sequence}", "capability": capability, "payload": payload, "evidence_identity": evidence, "placement_identity": placement, "admission_identity": admission}
        response = getattr(self._adapter, capability if capability != "replay" else "handle_mapping")(request)
        if response.get("ok") is not True:
            raise ProductHostError(str(response.get("error_code", "product_host_failure")))
        return response


class ProductHostError(RuntimeError):
    pass
