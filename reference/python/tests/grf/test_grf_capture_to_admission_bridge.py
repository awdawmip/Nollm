from __future__ import annotations

from nollm.grf.admission_bridge import GRFAdmissionBridge
from nollm.grf.capture import GRFCaptureIngress, GRFCaptureRequest
from nollm.grf.cell_address import CellAddress
from nollm.grf.source_window import SourceWindowRecord
from nollm.grf.storage import GRFFileStore


def test_capture_does_not_admit_until_explicit_bridge_call(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    window = SourceWindowRecord("window:bridge:1", "validation_fixture", ("fixture:bridge",), "2026-07-09T00:00:00Z")
    store.write_source_window(window, "2026-07-09T00:00:00Z")
    receipt = GRFCaptureIngress(store).capture(GRFCaptureRequest("capture:bridge:1", "bridge raw content", "validation_fixture", (window.window_id,), "2026-07-09T00:00:01Z"))

    assert receipt.status == "captured"
    assert not tuple((tmp_path / "grfs" / "placements" / "records").glob("*.json"))
    assert not tuple((tmp_path / "grfs" / "admissions" / "minimal_records").glob("*.json"))

    shard = store.read_evidence_shard(receipt.shard_id)
    result = GRFAdmissionBridge(store).admit(
        shard,
        window,
        {"policy_id": "validation_fixture_policy", "target_cell": CellAddress("eisenstein_exact_v1", "chart_bridge", 0, 0, 0)},
        "2026-07-09T00:00:02Z",
    )

    assert result.admission_record is not None
    assert result.placement_record is not None
    assert result.placement_record.source_fallback_refs == (shard.shard_id,)
    assert result.placement_record.to_mapping()["does_not_copy_coverage_entries"] is True
    assert store.read_minimal_admission_record(result.admission_record.admission_id) == result.admission_record


def test_rejected_bridge_keeps_evidence_shard(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    window = SourceWindowRecord("window:bridge:reject", "validation_fixture", ("fixture:reject",), "2026-07-09T00:00:00Z")
    store.write_source_window(window, "2026-07-09T00:00:00Z")
    receipt = GRFCaptureIngress(store).capture(GRFCaptureRequest("capture:bridge:reject", "false friend decoy", "validation_fixture", (window.window_id,), "2026-07-09T00:00:01Z"))
    shard = store.read_evidence_shard(receipt.shard_id)

    result = GRFAdmissionBridge(store).admit(shard, window, {"policy_id": "validation_fixture_policy", "reject": True}, "2026-07-09T00:00:02Z")

    assert result.rejection_record is not None
    assert result.admission_record is None
    assert store.read_evidence_shard(shard.shard_id).content == "false friend decoy"
    assert store.read_rejection_record(result.rejection_record.rejection_id) == result.rejection_record
