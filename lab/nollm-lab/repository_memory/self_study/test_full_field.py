"""Full-project filing preserves the experimental center and bounds each page."""
from collections import Counter
import json

import pytest

import full_field as ff
import vertical_atlas as atlas


def test_complete_volume_disjoint_pages_preserve_the_control_field():
    rows = atlas.parse_volume(ff.VOLUME.read_text(encoding="utf-8"))
    paths = [r["id"][5:] for r in rows]
    placed, rooms = ff.layout(reversed(paths))
    assert len(placed) == len(paths) == 903
    assert {k: placed[k] for k in atlas.intent()} == atlas.placements()
    occupancy = Counter(placed.values())
    for name, room in rooms.items():
        site = atlas.address(*room["entry"])
        support = dict(ff.expand_physical_coverage(site, "coverage_down").targets())
        if room["scope"] == "runtime":
            expected = sum(cell in support for cell in atlas.placements().values())
        else:
            expected = room["count"]
            assert 1 <= expected <= ff.ROOM_SIZE
            assert room["first"] <= room["last"]
        assert sum(occupancy[c] for c in support) == expected, name


def test_full_field_readback_and_missing_or_existing_field(tmp_path, monkeypatch):
    paths = list(atlas.intent()) + [f"lab/example/x_{n:02}.py" for n in range(10)]
    rows = {p: {"id": "code:" + p, "tags": {"A": "C", "B": "G", "C": "3", "E": "T"},
                "fields": {"F": "One source note for " + p, "R": "code:" + paths[0]}} for p in paths}
    tree = {p: f"{i:040x}" for i, p in enumerate(paths, 1)}
    monkeypatch.setattr(ff, "inputs", lambda r, v: (rows, tree))
    field = tmp_path / "field"
    manifest = ff.build(tmp_path, ff.VOLUME, field)
    assert json.loads((field / "rooms.json").read_text()) == manifest
    checked = ff.verify(tmp_path, ff.VOLUME, field)
    assert checked["unique_source_atoms"] == 54
    assert (checked["filing_pages"], checked["filing_page_min"], checked["filing_page_max"]) == (2, 2, 8)
    with pytest.raises(FileExistsError):
        ff.build(tmp_path, ff.VOLUME, field)
    with pytest.raises(FileNotFoundError):
        ff.open_manifest(tmp_path / "absent")
