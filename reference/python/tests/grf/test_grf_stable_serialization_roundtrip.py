from __future__ import annotations

import pytest

from grf_runtime_fixture import placement
from nollm.grf.json_canonical import canonical_dumps, canonical_loads, sha256_canonical
from nollm.grf.storage import GRFFileStore


def test_canonical_json_is_stable_and_rejects_float() -> None:
    payload = {"b": (2, 1), "a": {"n": 1}}
    first = canonical_dumps(payload)
    second = canonical_dumps(canonical_loads(first))
    assert first == second
    assert first.endswith(b"\n")
    assert sha256_canonical(payload) == sha256_canonical(canonical_loads(first))
    with pytest.raises(TypeError):
        canonical_dumps({"score": 1.5})


def test_placement_record_roundtrip_preserves_integer_fields(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    record = placement("shard_a", "patch_a", 1, 0, 0, "source:a")
    store.write_placement_record(record)
    loaded = store.read_placement_record(record.geometry_mark.cell, record.placement_id)
    assert loaded.to_mapping() == record.to_mapping()
    assert type(loaded.geometry_mark.cell.q) is int
