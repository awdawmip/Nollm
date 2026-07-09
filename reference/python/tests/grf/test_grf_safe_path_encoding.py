from __future__ import annotations

import pytest

from nollm.grf.path_encoding import safe_object_path
from nollm.grf.storage import GRFFileStore


def test_protocol_id_is_hashed_to_path_safe_filename(tmp_path) -> None:
    object_id = "shard:ci1:abc/unsafe?"
    filename = safe_object_path("evidence_shard", object_id)
    assert filename.endswith(".json")
    assert "shard" not in filename
    assert ":" not in filename
    assert "/" not in filename
    assert "?" not in filename
    assert filename == safe_object_path("evidence_shard", object_id)
    assert filename != safe_object_path("source_window", object_id)

    path = GRFFileStore(tmp_path).path_for("evidence_shard", object_id, "grfs/evidence/shards")
    assert path.name == filename
    assert path.parent == tmp_path / "grfs" / "evidence" / "shards"


def test_safe_object_path_rejects_empty_and_nul() -> None:
    with pytest.raises(ValueError):
        safe_object_path("evidence_shard", "")
    with pytest.raises(ValueError):
        safe_object_path("evidence_shard", "bad\0id")
