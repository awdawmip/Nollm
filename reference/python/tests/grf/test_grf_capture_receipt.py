from __future__ import annotations

import pytest

from nollm.grf.capture import GRFCaptureIngress, GRFCaptureRequest
from nollm.grf.storage import GRFFileStore


def test_capture_writes_evidence_only_and_reopens_same_bytes(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    ingress = GRFCaptureIngress(store)
    request = GRFCaptureRequest("capture:1", "raw fixture content", "validation_fixture", ("window:1",), "2026-07-09T00:00:00Z")

    first = ingress.capture(request)
    second = ingress.capture(request)

    assert first.status == "captured"
    assert second.status == "captured"
    assert first.shard_id == second.shard_id
    assert store.read_evidence_shard(first.shard_id).content == "raw fixture content"
    assert not (tmp_path / "grfs" / "placements" / "records").exists()
    assert not (tmp_path / "grfs" / "admissions" / "minimal_records").exists()


def test_capture_rejects_different_bytes_without_overwrite(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    ingress = GRFCaptureIngress(store)
    first = ingress.capture(GRFCaptureRequest("capture:1", "raw fixture content", "validation_fixture", ("window:1",), "2026-07-09T00:00:00Z"))
    rejected = ingress.capture(GRFCaptureRequest("capture:1", "changed content", "validation_fixture", ("window:1",), "2026-07-09T00:00:01Z"))

    assert rejected.status == "rejected"
    assert rejected.shard_id is None
    assert store.read_evidence_shard(first.shard_id).content == "raw fixture content"


def test_invalid_capture_request_does_not_create_shard(tmp_path) -> None:
    with pytest.raises(ValueError):
        GRFCaptureRequest("capture:bad", "", "validation_fixture", ("window:1",), "2026-07-09T00:00:00Z")
    assert not tuple((tmp_path / "grfs" / "evidence" / "shards").glob("*.json"))
