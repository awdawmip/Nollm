"""Regression checks for the live Access field, directed Coverage and source bindings."""
import hashlib
import json
import subprocess

import pytest

import vertical_atlas as atlas
from aoci_rows import render_volume
from nollm_access import AccessRuntime, FileHandleStore, FileStatementStore
from nollm_core import CoreRuntime, expand_physical_coverage


def test_default_placements_reach_every_home_and_leave_shared_regions():
    sites = atlas.topic_cells()
    down = {key: dict(expand_physical_coverage(cell, "coverage_down").targets()) for key, cell in sites.items()}
    layout = atlas.placements()
    assert len(layout) == 44
    assert {cell.layer for cell in layout.values()} == {0}
    assert all(cell in down[atlas.intent()[p][0]] for p, cell in layout.items())
    assert any(sum(cell in region for region in down.values()) > 1 for cell in layout.values())
    with pytest.raises(ValueError):
        atlas.placements(dict.fromkeys(sites, next(iter(sites.values()))))


def test_cold_single_entry_reads_and_source_binding(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    # A local Git fixture keeps this regression independent of checkout depth.
    git = ["git", "-C", str(repo)]
    subprocess.run([*git, "init", "-q"], check=True)
    paths = sorted(atlas.intent())
    for p in paths:
        dest = repo / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f"# {p}\n")
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "-c", "user.name=Fixture", "-c", "user.email=test@example.test",
                    "commit", "-qm", "fixture"], check=True)
    rev = atlas.resolve(repo, "HEAD")
    monkeypatch.setattr(atlas, "SOURCE_REVISION", rev)
    tags = {"A": "C", "B": "G", "C": "3", "E": "S"}
    volume = tmp_path / "aoci.code.txt"
    volume.write_text(render_volume([
        {"id": "code:" + p, "tags": tags, "fields": {"F": "The role of " + p, "R": "code:" + paths[0]}}
        for p in paths
    ]))
    field = tmp_path / "field"
    with pytest.raises(ValueError, match="wrong AOCI volume"):
        atlas.build(repo, "HEAD", volume, field)
    assert not field.exists()
    monkeypatch.setattr(atlas, "SOURCE_VOLUME_SHA256", hashlib.sha256(volume.read_bytes()).hexdigest())
    manifest = atlas.build(repo, "HEAD", volume, field)
    assert json.loads((field / "layout.json").read_text()) == manifest
    checked = atlas.verify(repo, volume, field)
    assert checked["source_files"] == len(paths)
    assert checked["realized_intended"] < checked["intended_memberships"]
    for name, entry in atlas.topic_cells().items():
        weights = dict(expand_physical_coverage(entry, "coverage_down").targets())
        expected = {p: weights[cell] for p, cell in atlas.placements().items() if cell in weights}
        got = atlas.view(field, manifest, name, "coverage")
        assert len(got) == len(expected)
        assert {r["path"]: r["score_q16"] for r in got} == expected
        assert all(r["kernels"] == ["coverage_down"] for r in got)
        assert all(r["text"] == manifest["files"][r["path"]]["text"] for r in got)
        assert all(r["evidence_blobs"] and r["source_handle"] == rev + ":" + r["path"] for r in got)
        owners = {r["path"] for r in atlas.view(field, manifest, name, "owner")}
        assert owners == {p for p in paths if atlas.intent()[p][0] == name}
        assert atlas.view(field, manifest, name, "same_layer") == []
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        assert core.placement_count() == len(paths) and not core.bridges()
        for cell in core.occupied_cells():
            assert cell.layer == 0
            for _, atom in core.atoms_at(cell):
                statement = access.statement_store.get(atom.atom_id)
                commit, path = statement.source_handle.split(":", 1)
                assert commit == rev
                expected_paths = [path] if path == paths[0] else [path, paths[0]]
                assert statement.context_refs == tuple(f"{manifest['files'][p]['blob']}:{p}" for p in expected_paths)
    with pytest.raises(FileExistsError):
        atlas.build(repo, "HEAD", volume, field)


def test_upward_and_downward_measures_are_directional():
    path = "packages/nollm-core/src/nollm_core/physical_coverage.py"
    manifest = {"topics": {key: {"cell": atlas.coords(cell)} for key, cell in atlas.topic_cells().items()},
                "files": {path: {"cell": [0, 1, 0], "topic": "geometry"}}}
    report = atlas.impact(manifest, path)
    assert report["up_from_leaf_q16"]["geometry"] == 38229
    assert report["down_from_entry_q16"]["geometry"] == 27989
    # Renaming a physical site in an alternative layout follows that layout.
    topics = manifest["topics"]
    topics["surface"], topics["geometry"] = topics["geometry"], topics["surface"]
    assert atlas.impact(manifest, path)["down_from_entry_q16"]["surface"] == 27989
