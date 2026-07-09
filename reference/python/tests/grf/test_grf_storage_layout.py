from __future__ import annotations

from nollm.grf.storage import GRFFileStore


def test_storage_layout_is_created_under_workspace(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    store.initialize_layout()
    for relative in ("grfs/evidence/islands", "grfs/patches/local_patches", "grfs/placements/records", "grfs/admissions/minimal_records", "grfs/ledger.jsonl"):
        if relative.endswith(".jsonl"):
            assert not (tmp_path / relative).exists()
        else:
            assert (tmp_path / relative).is_dir()


def test_storage_rejects_path_traversal_ids(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    path = store.path_for("x", "../bad", "grfs/evidence/islands")
    assert path.parent == tmp_path / "grfs" / "evidence" / "islands"
    assert ".." not in path.name
    assert "/" not in path.name
    assert "\\" not in path.name
