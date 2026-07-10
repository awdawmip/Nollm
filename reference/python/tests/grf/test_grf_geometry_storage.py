from __future__ import annotations

from grf_runtime_fixture import placement
from nollm.grf.cell_address import CellAddress
from nollm.grf.geometry_storage import partition_id, placement_path
from nollm.grf.storage import GRFFileStore


def test_negative_cells_use_stable_integer_partitions(tmp_path) -> None:
    cell = CellAddress("eisenstein_exact_v1", "chart:negative", 0, -17, -1)
    assert partition_id(cell) == (-2, -1)
    assert partition_id(CellAddress("eisenstein_exact_v1", "chart:negative", 0, -17, -1)) == (-2, -1)
    assert "%3A" in str(placement_path(tmp_path, cell, "placement:negative"))


def test_placement_lives_at_its_declared_cell_without_route_table(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    record = placement("shard:cell", "patch:cell", 1, -17, -1, "source:cell")
    path = store.write_placement_record(record)
    assert path == placement_path(tmp_path, record.geometry_mark.cell, record.placement_id)
    assert store.read_placement_record(record.geometry_mark.cell, record.placement_id) == record
    assert not (tmp_path / "grfs" / "placements" / "records").exists()
