from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf_file_adapter import GRFFileAdapter


def test_file_adapter_only_maps_contract_and_translates_errors(tmp_path: Path) -> None:
    adapter = GRFFileAdapter(tmp_path)
    response = adapter.handle_mapping(
        {
            "contract_version": "grf_host_v1",
            "host_request_id": "host:file:capture",
            "capability": "capture",
            "payload": {
                "kind": "nollm_grf_capture_request",
                "version": "1",
                "capture_id": "capture:file:1",
                "content": "file adapter content",
                "origin_kind": "validation_fixture",
                "source_window_refs": ("window:file:1",),
                "recorded_at": "2026-07-10T00:00:00Z",
            },
        }
    )
    assert response["ok"] is True
    assert response["evidence_identity"].startswith("shard:")
    assert response["adapter_latency_ns"] >= 0
    bad = adapter.handle_mapping({"contract_version": "wrong"})
    assert bad["ok"] is False
    assert bad["error_code"] == "adapter_request_error"
