"""Multi-host GRF4 conformance runner; adapters only map contract payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .grf_declared_host_adapter import GRFDeclaredHostAdapter
from .grf_file_adapter import GRFFileAdapter


def run_multi_host_conformance(workspace_root: Path) -> dict[str, object]:
    root = Path(workspace_root)
    repo = Path(__file__).resolve().parents[1]
    adapters = {
        "file": GRFFileAdapter(root / "file"),
        "openclaw_v2": GRFDeclaredHostAdapter(root / "openclaw", repo / "openclaw" / "v2-adapter" / "capabilities.json"),
        "codex": GRFDeclaredHostAdapter(root / "codex", repo / "codex" / "adapter" / "capabilities.json"),
    }
    outputs = {name: _run(adapter, name) for name, adapter in adapters.items()}
    selected = {name: value["selected_shards"] for name, value in outputs.items()}
    fallbacks = {name: value["source_fallback_ref"] for name, value in outputs.items()}
    return {"hosts": tuple(sorted(outputs)), "same_core_result": len({tuple(value) for value in selected.values()}) == 1, "same_source_fallback": len(set(fallbacks.values())) == 1, "selected": selected, "fallbacks": fallbacks}


def _run(adapter: Any, host: str) -> dict[str, object]:
    capture = adapter.handle_mapping(_request("capture", host, {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:grf4:shared", "content": "shared host source", "origin_kind": "validation_fixture", "source_window_refs": ("window:grf4:shared",), "recorded_at": "2026-07-10T00:00:00Z"}))
    if not capture.get("ok"):
        raise AssertionError("host capture failed")
    shard = capture["evidence_identity"]
    place = adapter.handle_mapping(_request("place", host, {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": shard, "source_window_id": "window:grf4:shared", "policy_hint": {"policy_id": "validation_fixture_policy", "chart_id": "chart:grf4"}, "recorded_at": "2026-07-10T00:00:01Z"}, shard))
    placement = place["placement_identity"]
    admit = adapter.handle_mapping(_request("admit", host, {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": shard, "placement_id": placement, "recorded_at": "2026-07-10T00:00:02Z", "admitted_by": "validation_fixture"}, shard, placement))
    if not admit.get("ok"):
        raise AssertionError("host admission failed")
    recall = adapter.handle_mapping(_request("recall", host, {"kind": "nollm_grf_recall_request", "version": "1", "query_id": f"query:grf4:{host}", "entry_mode": "shard_id", "entry_ref": shard, "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}, shard))
    if not recall.get("ok"):
        raise AssertionError("host recall failed")
    report = recall["result"]["coverage_reports"][0]
    return {"selected_shards": recall["result"]["selected_shards"], "source_fallback_ref": report["source_fallback_ref"]}


def _request(capability: str, host: str, payload: dict[str, object], evidence: str | None = None, placement: str | None = None) -> dict[str, object]:
    return {"contract_version": "grf_host_v1", "host_request_id": f"host:grf4:{host}:{capability}", "capability": capability, "payload": payload, "evidence_identity": evidence, "placement_identity": placement, "admission_identity": None}
