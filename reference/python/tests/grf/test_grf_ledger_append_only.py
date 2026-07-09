from __future__ import annotations

import pytest

from grf_runtime_fixture import placement
from nollm.grf.ledger import GRFLedger
from nollm.grf.storage import GRFFileStore


def test_duplicate_same_bytes_idempotent_and_different_bytes_rejected(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    first = placement("shard_a", "patch_a", 1, 0, 0, "source:a")
    second = placement("shard_a", "patch_a", 1, 1, 0, "source:a")
    path = store.write_placement_record(first)
    before = path.read_bytes()
    assert store.write_placement_record(first) == path
    assert path.read_bytes() == before


def test_ledger_records_hash_and_rejection_without_overwrite(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    first = placement("shard_a", "patch_a", 1, 0, 0, "source:a")
    second = placement("shard_a", "patch_a", 1, 1, 0, "source:a")
    path = store.write_placement_record(first, "2026-07-09T10:00:00+08:00")
    before = path.read_bytes()
    store.write_placement_record(first, "2026-07-09T10:00:01+08:00")
    with pytest.raises(FileExistsError):
        store.write_placement_record(second, "2026-07-09T10:00:02+08:00")
    assert path.read_bytes() == before
    events = GRFLedger(tmp_path).events()
    assert [event.event_type for event in events] == ["object_written", "object_reopened_same_bytes", "object_write_rejected_different_bytes"]
    assert events[0].object_sha256 == events[1].object_sha256 == events[2].object_sha256
    assert events[1].previous_event_id == events[0].event_id
    with pytest.raises(FileExistsError):
        store.write_placement_record(second)
    assert path.read_bytes() == before
