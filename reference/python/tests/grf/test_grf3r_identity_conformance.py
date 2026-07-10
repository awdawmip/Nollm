from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from nollm.grf.capture import GRFCaptureRequest
from nollm.grf.facade import GRFFacade
from nollm.grf.host_contract import AdmissionIdentity, EvidenceIdentity, GRFHostRequest, GRFHostService, HostRequestID, PlacementIdentity
from nollm.grf.recall import QueryProbe, RecallBudget


def _capture(host_request_id: str, capture_id: str) -> GRFHostRequest:
    return GRFHostRequest.from_mapping(
        {
            "contract_version": "grf_host_v1",
            "host_request_id": host_request_id,
            "capability": "capture",
            "payload": {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": capture_id, "content": capture_id, "origin_kind": "validation_fixture", "source_window_refs": (f"window:{capture_id}",), "recorded_at": "2026-07-10T00:00:00Z"},
        }
    )


def test_identity_value_objects_are_distinct_and_capture_rejects_fake_evidence(tmp_path: Path) -> None:
    assert HostRequestID("host:shared") != EvidenceIdentity("shard:shared")
    assert EvidenceIdentity("shard:one") != EvidenceIdentity("shard:two")
    assert PlacementIdentity("placement:one") != AdmissionIdentity("admission:one")
    service = GRFHostService(tmp_path)
    first = service.handle(_capture("host:same", "capture:one"))
    second = service.handle(_capture("host:same", "capture:two"))
    assert first.ok is True and second.ok is True
    assert first.evidence_identity != second.evidence_identity

    injected = {
        "contract_version": "grf_host_v1",
        "host_request_id": "host:fake-evidence",
        "capability": "capture",
        "evidence_identity": "shard:fake",
        "payload": {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:fake", "content": "fake", "origin_kind": "validation_fixture", "source_window_refs": ("window:fake",), "recorded_at": "2026-07-10T00:00:00Z"},
    }
    try:
        GRFHostRequest.from_mapping(injected)
    except ValueError as exc:
        assert "capture cannot declare GRF identities" in str(exc)
    else:
        raise AssertionError("capture accepted injected evidence identity")
    assert not (tmp_path / "grfs" / "evidence" / "shards" / "fake.json").exists()


def test_facade_operates_without_any_host_or_adapter(tmp_path: Path) -> None:
    facade = GRFFacade(tmp_path)
    first = facade.capture(GRFCaptureRequest("capture:facade:place", "facade place", "validation_fixture", ("window:facade:place",), "2026-07-10T00:00:00Z"))
    placed = facade.place(first.shard_id, "window:facade:place", {"policy_id": "validation_fixture_policy", "chart_id": "chart:facade"}, "2026-07-10T00:00:01Z")
    second = facade.capture(GRFCaptureRequest("capture:facade:admit", "facade admit", "validation_fixture", ("window:facade:admit",), "2026-07-10T00:00:02Z"))
    admitted = facade.admit(second.shard_id, "window:facade:admit", {"policy_id": "validation_fixture_policy", "chart_id": "chart:facade"}, "2026-07-10T00:00:03Z")
    query = QueryProbe("query:facade:identity", "shard_id", first.shard_id, ("lateral",), RecallBudget(0, 1, 0, 0, 0, 1))
    assert placed.placement_record is not None and admitted.admission_record is not None
    assert facade.recall(query).to_mapping() == facade.replay(query).to_mapping()


def test_contract_mapping_rejects_nontext_identity_injection() -> None:
    with pytest.raises(TypeError, match="identity must be text or null"):
        GRFHostRequest.from_mapping({"contract_version": "grf_host_v1", "host_request_id": "host:number", "capability": "capture", "payload": {}, "evidence_identity": 7})


def test_adapter_source_has_no_direct_core_mutation_and_crash_is_translated(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    adapter_path = root / "integrations" / "adapters" / "grf_file_adapter.py"
    tree = ast.parse(adapter_path.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imports |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert imports == {"__future__", "pathlib", "time", "typing", "nollm.grf.host_contract", "grf_adapter_contract"}

    import sys

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from integrations.adapters.grf_file_adapter import GRFFileAdapter

    adapter = GRFFileAdapter(tmp_path)
    adapter._service.handle = lambda _request: (_ for _ in ()).throw(RuntimeError("injected adapter crash"))
    assert adapter.handle_mapping({"contract_version": "grf_host_v1", "host_request_id": "host:crash", "capability": "validate", "payload": {}})["error_code"] == "adapter_failure"


def test_terminal_skeletons_only_declare_contract_capabilities() -> None:
    root = Path(__file__).resolve().parents[4]
    for path in (root / "integrations" / "openclaw" / "v2-adapter" / "capabilities.json", root / "integrations" / "codex" / "adapter" / "capabilities.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload == {"contract_version": "grf_host_v1", "capabilities": ["capture", "place", "admit", "recall", "replay", "validate"], "mode": "declarative_skeleton"}
