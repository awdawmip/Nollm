from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf_file_adapter import GRFFileAdapter
from nollm.grf.admission_bridge import resolve_source_fallback
from nollm.grf.capture import GRFCaptureRequest
from nollm.grf.facade import GRFFacade
from nollm.grf.host_contract import GRFHostRequest, GRFHostService


def _request(capability: str, host_id: str, payload: dict[str, object], evidence: str | None = None, placement: str | None = None, admission: str | None = None) -> dict[str, object]:
    return {"contract_version": "grf_host_v1", "host_request_id": host_id, "capability": capability, "payload": payload, "evidence_identity": evidence, "placement_identity": placement, "admission_identity": admission}


def _query(mode: str, ref: object) -> dict[str, object]:
    return {"kind": "nollm_grf_recall_request", "version": "1", "query_id": f"query:grf3r2:{mode}", "entry_mode": mode, "entry_ref": ref, "allowed_kernels": ("lateral",), "budget": {"max_steps": 0, "beam": 1, "max_layer_delta": 0, "max_lateral_ring": 0, "max_bridge_steps": 0, "max_results": 1}}


def test_file_adapter_executes_strict_capture_place_admit_recall_replay_e2e(tmp_path: Path) -> None:
    adapter = GRFFileAdapter(tmp_path)
    captured = adapter.handle_mapping(_request("capture", "host:e2e:capture", {"kind": "nollm_grf_capture_request", "version": "1", "capture_id": "capture:e2e", "content": "original source content", "origin_kind": "validation_fixture", "source_window_refs": ("window:e2e",), "recorded_at": "2026-07-10T00:00:00Z"}))
    assert captured["ok"] is True
    shard_id = captured["evidence_identity"]

    placed = adapter.handle_mapping(_request("place", "host:e2e:place", {"kind": "nollm_grf_admit_request", "version": "1", "shard_id": shard_id, "source_window_id": "window:e2e", "policy_hint": {"policy_id": "validation_fixture_policy", "chart_id": "chart:e2e"}, "recorded_at": "2026-07-10T00:00:01Z"}, evidence=shard_id))
    assert placed["ok"] is True and placed["placement_identity"] and placed["admission_identity"] is None
    placement_id = placed["placement_identity"]
    before_admit = GRFFacade(tmp_path).validate_workspace()
    assert before_admit.placement_record_count == 1
    assert before_admit.admission_record_count == 0

    admitted = adapter.handle_mapping(_request("admit", "host:e2e:admit", {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": shard_id, "placement_id": placement_id, "recorded_at": "2026-07-10T00:00:02Z", "admitted_by": "validation_fixture"}, evidence=shard_id, placement=placement_id))
    assert admitted["ok"] is True and admitted["admission_identity"]
    admission_id = admitted["admission_identity"]
    after_admit = GRFFacade(tmp_path).validate_workspace()
    assert after_admit.placement_record_count == 1
    assert after_admit.admission_record_count == 1

    by_shard = adapter.handle_mapping(_request("recall", "host:e2e:shard", _query("shard_id", shard_id), evidence=shard_id))
    by_placement = adapter.handle_mapping(_request("recall", "host:e2e:placement", _query("placement_id", placement_id), placement=placement_id))
    by_admission = adapter.handle_mapping(_request("replay", "host:e2e:admission", _query("admission_id", admission_id), admission=admission_id))
    assert by_shard["ok"] is True and by_placement["ok"] is True and by_admission["ok"] is True
    assert by_shard["result"]["selected_shards"] == by_placement["result"]["selected_shards"] == by_admission["result"]["selected_shards"] == [shard_id]
    fallback = by_shard["result"]["coverage_reports"][0]["source_fallback_ref"]
    assert resolve_source_fallback(fallback, GRFFacade(tmp_path).store).content == "original source content"


@pytest.mark.parametrize(
    ("mode", "identity_key", "identity_value"),
    (("shard_id", "evidence_identity", "shard:wrong"), ("placement_id", "placement_identity", "placement:wrong"), ("admission_id", "admission_identity", "admission:wrong")),
)
def test_identity_query_modes_require_exact_single_identity(tmp_path: Path, mode: str, identity_key: str, identity_value: str) -> None:
    service = GRFHostService(tmp_path)
    missing = service.handle(GRFHostRequest.from_mapping(_request("recall", f"host:missing:{mode}", _query(mode, identity_value))))
    assert missing.ok is False and missing.error_code == "ValueError"
    wrong = service.handle(GRFHostRequest.from_mapping(_request("recall", f"host:wrong:{mode}", _query(mode, identity_value), evidence="shard:other" if mode == "shard_id" else None, placement="placement:other" if mode == "placement_id" else None, admission="admission:other" if mode == "admission_id" else None)))
    assert wrong.ok is False and wrong.error_code == "ValueError"


def test_query_rejects_extraneous_and_multiple_identity_namespaces(tmp_path: Path) -> None:
    service = GRFHostService(tmp_path)
    source = service.handle(GRFHostRequest.from_mapping(_request("recall", "host:source", _query("source_window", "window:any"), evidence="shard:unrelated")))
    explicit = service.handle(GRFHostRequest.from_mapping(_request("recall", "host:cell", _query("explicit_cell", {"profile_id": "eisenstein_exact_v1", "chart_id": "chart", "layer": 0, "q": 0, "r": 0}), placement="placement:unrelated")))
    multiple = service.handle(GRFHostRequest.from_mapping(_request("recall", "host:multiple", _query("shard_id", "shard:any"), evidence="shard:any", placement="placement:other")))
    assert source.ok is False and explicit.ok is False and multiple.ok is False


def test_admit_rejects_missing_or_cross_shard_placement(tmp_path: Path) -> None:
    service = GRFHostService(tmp_path)
    missing = service.handle(GRFHostRequest.from_mapping(_request("admit", "host:missing-placement", {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": "shard:missing", "placement_id": "placement:missing", "recorded_at": "2026-07-10T00:00:00Z", "admitted_by": "validation_fixture"}, evidence="shard:missing", placement="placement:missing")))
    assert missing.ok is False and missing.error_code == "FileNotFoundError"
    facade = GRFFacade(tmp_path)
    left = facade.capture(GRFCaptureRequest("capture:left", "left", "validation_fixture", ("window:left",), "2026-07-10T00:00:00Z"))
    right = facade.capture(GRFCaptureRequest("capture:right", "right", "validation_fixture", ("window:right",), "2026-07-10T00:00:00Z"))
    placement = facade.place(left.shard_id, "window:left", {"policy_id": "validation_fixture_policy", "chart_id": "chart:cross"}, "2026-07-10T00:00:01Z").placement_record
    cross = service.handle(GRFHostRequest.from_mapping(_request("admit", "host:cross-shard", {"kind": "nollm_grf_admit_existing_placement_request", "version": "1", "shard_id": right.shard_id, "placement_id": placement.placement_id, "recorded_at": "2026-07-10T00:00:02Z", "admitted_by": "validation_fixture"}, evidence=right.shard_id, placement=placement.placement_id)))
    assert cross.ok is False and cross.error_code == "ValueError"


def test_unsupported_capability_has_a_stable_host_response(tmp_path: Path) -> None:
    response = GRFHostService(tmp_path).handle(GRFHostRequest.from_mapping(_request("unknown", "host:unsupported", {})))
    assert response.ok is False and response.error_code == "UnsupportedCapabilityError"
