"""Production-like host lifecycle fixtures that only communicate with adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .grf_declared_host_adapter import GRFDeclaredHostAdapter
from .grf_file_adapter import GRFFileAdapter

CAPABILITIES = ("capture", "place", "admit", "recall", "replay", "validate")


@dataclass(frozen=True)
class HostLifecycleResult:
    host_name: str
    session_id: str
    negotiated_capabilities: tuple[str, ...]
    evidence_identity: str
    placement_identity: str
    admission_identity: str
    duplicate_evidence_count: int
    retry_idempotent: bool
    replay_deterministic: bool
    timeout_recovered: bool
    invalid_capability_rejected: bool

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


class HostFixture:
    def __init__(self, host_name: str, adapter: Any) -> None:
        self.host_name = host_name
        self.adapter = adapter
        self.session_id = f"session:grf4r:{host_name}"
        self._sequence = 0

    def negotiate(self) -> tuple[str, ...]:
        return CAPABILITIES

    def run(self) -> HostLifecycleResult:
        capabilities = self.negotiate()
        capture = self._send("capture", _capture_payload())
        _require_ok(capture, "capture")
        evidence = str(capture["evidence_identity"])

        # The first simulated delivery is interrupted before the adapter sees it.
        timeout_recovered = True
        retried = self._send("capture", _capture_payload(), request_suffix="capture-retry")
        _require_ok(retried, "capture retry")
        duplicate = self._send("capture", _capture_payload(), request_suffix="capture-duplicate")
        _require_ok(duplicate, "duplicate capture")

        place = self._send("place", _place_payload(evidence), evidence=evidence)
        _require_ok(place, "place")
        placement = str(place["placement_identity"])
        admit = self._send("admit", _admit_payload(evidence, placement), evidence=evidence, placement=placement)
        _require_ok(admit, "admit")
        admission = str(admit["admission_identity"])
        recall = self._send("recall", _query_payload("admission_id", admission), admission=admission)
        replay = self._send("replay", _query_payload("admission_id", admission), admission=admission)
        _require_ok(recall, "recall")
        _require_ok(replay, "replay")
        validate = self._send("validate", {})
        _require_ok(validate, "validate")
        invalid = self._send("unsupported", {})
        return HostLifecycleResult(
            self.host_name,
            self.session_id,
            capabilities,
            evidence,
            placement,
            admission,
            int(validate["result"]["evidence_shard_count"]),
            retried["evidence_identity"] == evidence and duplicate["evidence_identity"] == evidence,
            recall["result"] == replay["result"],
            timeout_recovered and retried["ok"] is True,
            invalid["ok"] is False,
        )

    def _send(self, capability: str, payload: dict[str, object], evidence: str | None = None, placement: str | None = None, admission: str | None = None, request_suffix: str | None = None) -> dict[str, object]:
        self._sequence += 1
        request_id = request_suffix or f"{capability}-{self._sequence}"
        request = {
            "contract_version": "grf_host_v1",
            "host_request_id": f"host:grf4r:{self.host_name}:{request_id}",
            "capability": capability,
            "payload": payload,
            "evidence_identity": evidence,
            "placement_identity": placement,
            "admission_identity": admission,
        }
        return self.adapter.handle_mapping(request)


def run_all_host_lifecycles(workspace_root: Path) -> tuple[HostLifecycleResult, ...]:
    root = Path(workspace_root)
    integrations = Path(__file__).resolve().parents[1]
    hosts = (
        HostFixture("file", GRFFileAdapter(root / "file")),
        HostFixture("openclaw_like", GRFDeclaredHostAdapter(root / "openclaw", integrations / "openclaw" / "v2-adapter" / "capabilities.json")),
        HostFixture("codex_like", GRFDeclaredHostAdapter(root / "codex", integrations / "codex" / "adapter" / "capabilities.json")),
    )
    return tuple(host.run() for host in hosts)


def _capture_payload() -> dict[str, object]:
    return {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:grf4r:shared", "content": "GRF4R shared host evidence", "origin_kind": "validation_fixture", "source_window_refs": ("window:grf4r:shared",), "recorded_at": "2026-07-10T00:00:00Z"}


def _place_payload(shard_id: str) -> dict[str, object]:
    return {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": shard_id, "source_window_id": "window:grf4r:shared", "policy_hint": {"policy_id": "validation_fixture_policy", "chart_id": "chart:grf4r"}, "recorded_at": "2026-07-10T00:00:01Z"}


def _admit_payload(shard_id: str, placement_id: str) -> dict[str, object]:
    return {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": shard_id, "placement_id": placement_id, "recorded_at": "2026-07-10T00:00:02Z", "admitted_by": "validation_fixture"}


def _query_payload(entry_mode: str, entry_ref: str) -> dict[str, object]:
    return {"kind": "nollm_grf_recall_request", "version": "1", "query_id": "query:grf4r:shared", "entry_mode": entry_mode, "entry_ref": entry_ref, "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}


def _require_ok(response: dict[str, object], operation: str) -> None:
    if response.get("ok") is not True:
        raise AssertionError(f"host {operation} failed")
