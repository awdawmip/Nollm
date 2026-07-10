from __future__ import annotations

import ast
from pathlib import Path

import pytest

from nollm.grf.host_contract import CapabilityRegistry, GRFHostRequest, GRFHostService, UnsupportedCapabilityError


def _capture(capture_id: str) -> dict[str, object]:
    return {
        "contract_version": "grf_host_v1",
        "host_request_id": f"host:{capture_id}",
        "capability": "capture",
        "payload": {
            "kind": "nollm_grf_capture_request",
            "version": "1",
            "capture_id": capture_id,
            "content": f"content for {capture_id}",
            "origin_kind": "validation_fixture",
            "source_window_refs": (f"window:{capture_id}",),
            "recorded_at": "2026-07-10T00:00:00Z",
        },
    }


def _admit(capability: str, host_id: str, shard_id: str, window_id: str) -> GRFHostRequest:
    return GRFHostRequest.from_mapping(
        {
            "contract_version": "grf_host_v1",
            "host_request_id": host_id,
            "capability": capability,
            "evidence_identity": shard_id,
            "payload": {
                "kind": "nollm_grf_admit_request",
                "version": "1",
                "shard_id": shard_id,
                "source_window_id": window_id,
                "policy_hint": {"policy_id": "validation_fixture_policy", "chart_id": "chart:grf3"},
                "recorded_at": "2026-07-10T00:00:01Z",
            },
        }
    )


def _recall(host_id: str, shard_id: str) -> GRFHostRequest:
    return GRFHostRequest.from_mapping(
        {
            "contract_version": "grf_host_v1",
            "host_request_id": host_id,
            "capability": "recall",
            "evidence_identity": shard_id,
            "payload": {
                "kind": "nollm_grf_recall_request",
                "version": "1",
                "query_id": "query:grf3",
                "entry_mode": "shard_id",
                "entry_ref": shard_id,
                "allowed_kernels": ("lateral",),
                "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1},
            },
        }
    )


def test_contract_routes_capture_place_admit_recall_replay_and_validate(tmp_path: Path) -> None:
    service = GRFHostService(tmp_path)
    captured = service.handle(GRFHostRequest.from_mapping(_capture("capture:grf3:place")))
    assert captured.ok is True
    placed = service.handle(_admit("place", "host:place", captured.evidence_identity, "window:capture:grf3:place"))
    assert placed.ok is True
    assert placed.placement_identity and placed.placement_identity.startswith("placement:")
    assert placed.admission_identity and placed.admission_identity.startswith("admission:")

    second = service.handle(GRFHostRequest.from_mapping(_capture("capture:grf3:admit")))
    admitted = service.handle(_admit("admit", "host:admit", second.evidence_identity, "window:capture:grf3:admit"))
    assert admitted.ok is True

    recall = service.handle(_recall("host:recall", captured.evidence_identity))
    replay = service.handle(GRFHostRequest.from_mapping({**_recall("host:replay", captured.evidence_identity).to_mapping(), "capability": "replay"}))
    assert recall.ok is True and replay.ok is True
    assert recall.result == replay.result
    assert recall.result["coverage_reports"][0]["source_fallback_ref"] == captured.evidence_identity
    assert service.handle(GRFHostRequest("grf_host_v1", "host:validate", "validate", {})).ok is True


def test_contract_rejects_identity_collisions_and_unsupported_capabilities(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot use a GRF identity namespace"):
        GRFHostRequest("grf_host_v1", "shard:not-a-host-request", "capture", {})
    with pytest.raises(ValueError, match="cannot equal host_request_id"):
        GRFHostRequest("grf_host_v1", "host:same", "capture", {}, "host:same")
    with pytest.raises(ValueError, match="invalid namespace"):
        GRFHostRequest("grf_host_v1", "host:wrong", "capture", {}, "terminal:wrong")
    with pytest.raises(UnsupportedCapabilityError):
        CapabilityRegistry().require("unknown")
    response = GRFHostService(tmp_path).handle(
        GRFHostRequest("grf_host_v1", "host:missing", "admit", {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": "shard:missing", "source_window_id": "window:missing", "policy_hint": {}, "recorded_at": "2026-07-10T00:00:00Z"}, "shard:missing")
    )
    assert response.ok is False and response.error_code == "FileNotFoundError"


def test_core_contract_imports_no_adapter_or_terminal() -> None:
    root = Path(__file__).resolve().parents[2] / "nollm" / "grf"
    for path in (root / "facade.py", root / "host_contract.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        names |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not ({"integrations", "openclaw", "codex", "terminal"} & names)
