from __future__ import annotations

import pytest

from integrations.adapters.grf7r_facade_runtime import FacadeRuntimeAdapter, HostRequestRegistryError, LostHostResponse


def _capture(request_id: str, content: str = "registry evidence") -> dict[str, object]:
    return {
        "contract_version": "grf_host_v2",
        "host_request_id": request_id,
        "capability": "capture",
        "payload": {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:registry:one", "content": content, "origin_kind": "validation_fixture", "source_window_refs": ("window:registry",), "recorded_at": "2026-07-10T00:00:00Z"},
        "evidence_identity": None,
        "placement_identity": None,
        "admission_identity": None,
    }


def test_durable_registry_rejects_cross_host_and_mutated_replay_after_restart(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    registry = tmp_path / "host_request_registry.jsonl"
    adapter = FacadeRuntimeAdapter(workspace, tmp_path / "events.jsonl", registry_path=registry)
    request = _capture("host:registry:one")
    with pytest.raises(LostHostResponse):
        adapter.handle("alpha", request, lose_response_after_commit=True)
    adapter.close()

    restarted = FacadeRuntimeAdapter(workspace, tmp_path / "events.jsonl", registry_path=registry)
    recovered = restarted.handle("alpha", request)
    assert recovered["ok"] is True
    assert restarted.handle("beta", request)["error_code"] == "cross_host_or_mutated_replay"
    assert restarted.handle("alpha", _capture("host:registry:one", "mutated"))["error_code"] == "cross_host_or_mutated_replay"
    assert restarted.registry.snapshot()["entry_count"] == 1


def test_registry_missing_after_committed_core_record_fails_closed(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    registry = tmp_path / "host_request_registry.jsonl"
    request = _capture("host:registry:missing")
    FacadeRuntimeAdapter(workspace, tmp_path / "events.jsonl", registry_path=registry).handle("alpha", request)
    registry.unlink()

    restarted = FacadeRuntimeAdapter(workspace, tmp_path / "events.jsonl", registry_path=registry)
    assert restarted.handle("alpha", request)["error_code"] == "ownership_unverifiable"


def test_registry_corruption_rejects_startup_and_truncated_tail_is_detected(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    registry = tmp_path / "host_request_registry.jsonl"
    adapter = FacadeRuntimeAdapter(workspace, tmp_path / "events.jsonl", registry_path=registry)
    adapter.handle("alpha", _capture("host:registry:tail"))
    adapter.close()
    with registry.open("ab") as stream:
        stream.write(b'{"schema":"truncated"')
    restarted = FacadeRuntimeAdapter(workspace, tmp_path / "events.jsonl", registry_path=registry)
    assert restarted.registry.truncated_tail_detected is True

    with registry.open("ab") as stream:
        stream.write(b"\nnot-json\n")
    with pytest.raises(HostRequestRegistryError, match="corruption"):
        FacadeRuntimeAdapter(workspace, tmp_path / "events.jsonl", registry_path=registry)
