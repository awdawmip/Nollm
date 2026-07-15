import inspect

import pytest

from nollm_access import AccessMemoryLoop, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime


ORIGIN = {"profile_id": "default_dream_v1", "chart_id": "default", "layer": 0, "q": 0, "r": 0, "phase": None}


def placement(statement_id: str, action: str, candidate_id: str) -> dict[str, object]:
    return {
        "schema_version": "nollm_openclaw_surface_placement_v1",
        "outcome": "apply",
        "decision": {"statement_id": statement_id, "action": action, "candidate_id": candidate_id, "reason_text": "fixture"},
    }


def apply(loop: AccessMemoryLoop, statement_id: str, content: str, action: str, candidate_id: str, entry=None):
    return loop.apply_placement(
        MemoryStatement(statement_id, content),
        placement(statement_id, action, candidate_id),
        f"request:{statement_id}",
        entry,
    )


def test_candidates_are_unique_bounded_content_independent_and_have_six_laterals(tmp_path, monkeypatch):
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.placement_candidates(None, "candidates:first")
        assert [(item["candidate_id"], item["relation_kind"]) for item in first] == [("placement:expand:0", "expand_surface")]
        apply(loop, "a1", "alpha", "expand_surface", "placement:expand:0")
        monkeypatch.setattr(FileStatementStore, "get", lambda *_args: (_ for _ in ()).throw(AssertionError("candidate generation read statement text")))
        candidates = loop.placement_candidates(ORIGIN, "candidates:local")
        again = loop.placement_candidates(ORIGIN, "candidates:different-query-not-input")
    assert candidates == again
    assert len(candidates) == 8
    assert all(set(item["occupancy"]) == {"count", "band"} for item in candidates)
    assert all("density_state" not in item["occupancy"] for item in candidates)
    laterals = [item["geometry_address"] for item in candidates if item["relation_kind"] == "lateral_ring_1"]
    assert [(item["q"], item["r"]) for item in laterals] == [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def test_new_local_rejects_an_occupied_lateral_without_writing(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        first = apply(loop, "a1", "origin", "expand_surface", "placement:expand:0")
        assert set(first["operation_timing"]) == {"decision_validation_ms", "statement_persist_ms", "placement_apply_ms", "handle_bind_ms"}
        assert all(type(value) is int and value >= 0 for value in first["operation_timing"].values())
        entry = first["handle"]["geometry_address"]
        occupied = apply(loop, "a2", "occupied", "new_local", "placement:lateral:0", entry)
        with pytest.raises(ValueError, match="occupied candidate"):
            apply(loop, "bad", "must not persist", "new_local", "placement:lateral:0", entry)
    assert not FileStatementStore(tmp_path).exists("bad")
    assert occupied["core_write_count"] == 1


def test_expand_surface_is_geometry_only_and_respects_minimum_distance(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        first = apply(loop, "alpha:any-id", "alpha", "expand_surface", "placement:expand:0")
        candidate = next(item for item in loop.placement_candidates(first["handle"]["geometry_address"], "second") if item["relation_kind"] == "expand_surface")
        second = apply(loop, "same-shape-different-id", "unrelated", "expand_surface", candidate["candidate_id"], first["handle"]["geometry_address"])
    left = first["handle"]["geometry_address"]
    right = second["handle"]["geometry_address"]
    assert AccessMemoryLoop._physical_distance_squared_q32(
        AccessMemoryLoop._cell(left), AccessMemoryLoop._cell(right)
    ) >= 3 * 4 * 4 * (1 << 32)
    assert "statement" not in inspect.signature(AccessMemoryLoop._expand_surface_frontier).parameters


def test_physical_frontier_metric_rejects_nondefault_or_nonzero_layer():
    origin = AccessMemoryLoop._cell(ORIGIN)
    for invalid in (
        {**ORIGIN, "profile_id": "eisenstein_exact_v1"},
        {**ORIGIN, "layer": 1},
    ):
        with pytest.raises(ValueError, match="physical plane"):
            AccessMemoryLoop._physical_distance_squared_q32(origin, AccessMemoryLoop._cell(invalid))


def test_surface_entries_recall_separated_localities(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        a1 = apply(loop, "a1", "Alpha release window", "expand_surface", "placement:expand:0")
        a2 = apply(loop, "a2", "Alpha risk review", "new_local", "placement:lateral:0", a1["handle"]["geometry_address"])
        b1 = apply(loop, "b1", "Cafe closes at six", "expand_surface", "placement:expand:0", a1["handle"]["geometry_address"])
        alpha = loop.local_context([a1["handle"]["geometry_address"]], "recall:alpha")
        office = loop.local_context([b1["handle"]["geometry_address"]], "recall:office")
    assert {item["statement_id"] for item in alpha} == {"a1", "a2"}
    assert {item["statement_id"] for item in office} == {"b1"}


def test_candidate_rejection_and_frontier_failure_leave_no_statement(tmp_path, monkeypatch):
    with AccessMemoryLoop(tmp_path) as loop:
        with pytest.raises(ValueError, match="unavailable candidate"):
            apply(loop, "bad", "bad", "expand_surface", "invented:1")
        monkeypatch.setattr(loop, "_expand_surface_frontier", lambda *_args: (_ for _ in ()).throw(RuntimeError("full")))
        with pytest.raises(RuntimeError, match="full"):
            apply(loop, "full", "full", "expand_surface", "placement:expand:0")
    assert not FileStatementStore(tmp_path).exists("bad")
    assert not FileStatementStore(tmp_path).exists("full")


@pytest.mark.parametrize("failure_owner", ["core", "handle"])
def test_core_and_handle_failures_roll_back_without_orphan(tmp_path, monkeypatch, failure_owner):
    if failure_owner == "core":
        monkeypatch.setattr(CoreRuntime, "put", lambda *_args: (_ for _ in ()).throw(OSError("core failure")))
    else:
        monkeypatch.setattr(FileHandleStore, "put", lambda *_args: (_ for _ in ()).throw(OSError("handle failure")))
    with AccessMemoryLoop(tmp_path) as loop:
        with pytest.raises(OSError, match=f"{failure_owner} failure"):
            apply(loop, "failed", "failed", "expand_surface", "placement:expand:0")
    assert not FileStatementStore(tmp_path).exists("failed")
    with CoreRuntime(tmp_path) as core:
        assert core.placement_count() == 0
