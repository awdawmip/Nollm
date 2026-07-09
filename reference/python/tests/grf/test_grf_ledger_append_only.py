from __future__ import annotations

import pytest

from grf_runtime_fixture import placement
from nollm.grf.storage import GRFFileStore


def test_duplicate_same_bytes_idempotent_and_different_bytes_rejected(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    first = placement("shard_a", "patch_a", 1, 0, 0, "source:a")
    second = placement("shard_a", "patch_a", 1, 1, 0, "source:a")
    path = store.write_placement_record(first)
    before = path.read_bytes()
    assert store.write_placement_record(first) == path
    assert path.read_bytes() == before
    with pytest.raises(FileExistsError):
        store.write_placement_record(second)
    assert path.read_bytes() == before
