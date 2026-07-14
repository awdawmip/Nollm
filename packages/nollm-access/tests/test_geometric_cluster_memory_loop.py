import pytest

from nollm_access import AccessMemoryLoop, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime


ORIGIN = {"profile_id": "eisenstein_exact_v1", "chart_id": "default", "layer": 0, "q": 0, "r": 0, "phase": None}


def _placement(statement_id: str, action: str, candidate_id: str) -> dict[str, object]:
    return {
        "schema_version": "nollm_openclaw_placement_v2",
        "outcome": "apply",
        "decision": {"statement_id": statement_id, "action": action, "candidate_id": candidate_id, "reason_text": "fixture"},
    }


def _apply(loop: AccessMemoryLoop, statement_id: str, content: str, action: str, candidate_id: str, anchors=None, entries=None):
    return loop.apply_placement(
        MemoryStatement(statement_id, content), _placement(statement_id, action, candidate_id),
        f"request:{statement_id}", anchors or [], entries or [],
    )


def test_candidates_are_unique_bounded_content_independent_and_have_six_laterals(tmp_path, monkeypatch):
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.placement_candidates([], [], "candidates:first")
        assert [(item["candidate_id"], item["relation_kind"]) for item in first] == [("new_cluster:0", "new_cluster")]
        _apply(loop, "a1", "alpha", "new_cluster", "new_cluster:0")
        monkeypatch.setattr(FileStatementStore, "get", lambda *_args: (_ for _ in ()).throw(AssertionError("candidate generation read statement text")))
        candidates = loop.placement_candidates([ORIGIN], [ORIGIN], "candidates:local")
        again = loop.placement_candidates([ORIGIN], [ORIGIN], "candidates:different-text-not-input")
    assert candidates == again
    assert len(candidates) == 8
    assert len({item["candidate_id"] for item in candidates}) == 8
    laterals = [item["geometry_address"] for item in candidates if item["relation_kind"] == "lateral_ring_1"]
    assert [(item["q"], item["r"]) for item in laterals] == [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def test_new_local_rejects_an_occupied_lateral_without_writing(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        a1 = _apply(loop, "a1", "anchor", "new_cluster", "new_cluster:0")
        anchors = [a1["cluster_anchor"]]
        entries = [a1["handle"]["geometry_address"]]
        occupied = _apply(loop, "a2", "occupied", "new_local", "lateral_ring_1:0", anchors, entries)
        entries.append(occupied["handle"]["geometry_address"])
        with pytest.raises(ValueError, match="occupied candidate"):
            _apply(loop, "bad", "must not persist", "new_local", "lateral_ring_1:0", anchors, entries)
    assert not (tmp_path / "access" / "statements" / "bad.json").exists()


def test_new_cluster_allocator_is_not_statement_based_and_keeps_distance(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        a = _apply(loop, "alpha:any-id", "alpha", "new_cluster", "new_cluster:0")
        candidates = loop.placement_candidates([a["cluster_anchor"]], [a["handle"]["geometry_address"]], "candidates:second")
        second = next(item for item in candidates if item["relation_kind"] == "new_cluster")
        assert second["geometry_address"]["q"] == 8
        assert second["geometry_address"]["r"] == 0
        b = _apply(loop, "same-shape-different-id", "unrelated", "new_cluster", second["candidate_id"], [a["cluster_anchor"]], [a["handle"]["geometry_address"]])
    assert b["handle"]["geometry_address"]["q"] == 8


def test_local_cluster_and_per_anchor_recall_are_geometry_isolated(tmp_path):
    with AccessMemoryLoop(tmp_path) as loop:
        a1 = _apply(loop, "a1", "Alpha release window", "new_cluster", "new_cluster:0")
        anchors = [a1["cluster_anchor"]]
        entries = [a1["handle"]["geometry_address"]]
        a2 = _apply(loop, "a2", "Alpha risk review", "new_local", "lateral_ring_1:0", anchors, entries)
        entries.append(a2["handle"]["geometry_address"])
        a3 = _apply(loop, "a3", "Alpha owner Priya", "new_local", "lateral_ring_1:1", anchors, entries)
        entries.append(a3["handle"]["geometry_address"])
        b1 = _apply(loop, "b1", "Cafe closes at six", "new_cluster", "new_cluster:0", anchors, entries)
        anchors.append(b1["cluster_anchor"])
        entries.append(b1["handle"]["geometry_address"])
        b2 = _apply(loop, "b2", "Visitor desk east", "new_local", "lateral_ring_1:0", anchors, entries)
        by_anchor = loop.per_anchor_context(anchors, "recall:isolated")
    a_ids = {item["statement_id"] for item in by_anchor[0]["statements"]}
    b_ids = {item["statement_id"] for item in by_anchor[1]["statements"]}
    assert a_ids == {"a1", "a2", "a3"}
    assert b_ids == {"b1", "b2"}
    assert len({tuple(result["handle"]["geometry_address"].values()) for result in (a1, a2, a3, b1, b2)}) >= 3


def test_candidate_rejection_and_allocator_failure_leave_no_statement(tmp_path, monkeypatch):
    with AccessMemoryLoop(tmp_path) as loop:
        with pytest.raises(ValueError, match="unavailable candidate"):
            _apply(loop, "bad", "bad", "new_cluster", "invented:1")
        monkeypatch.setattr(loop, "_allocate_cluster_anchor", lambda *_args: (_ for _ in ()).throw(RuntimeError("full")))
        with pytest.raises(RuntimeError, match="full"):
            _apply(loop, "full", "full", "new_cluster", "new_cluster:0")
    assert not list((tmp_path / "access" / "statements").rglob("*.json"))


@pytest.mark.parametrize("failure_owner", ["core", "handle"])
def test_core_and_handle_failures_roll_back_without_orphan(tmp_path, monkeypatch, failure_owner):
    if failure_owner == "core":
        monkeypatch.setattr(CoreRuntime, "put", lambda *_args: (_ for _ in ()).throw(OSError("core failure")))
    else:
        monkeypatch.setattr(FileHandleStore, "put", lambda *_args: (_ for _ in ()).throw(OSError("handle failure")))
    with AccessMemoryLoop(tmp_path) as loop:
        with pytest.raises(OSError, match=f"{failure_owner} failure"):
            _apply(loop, "failed", "failed", "new_cluster", "new_cluster:0")
    assert not list((tmp_path / "access" / "statements").rglob("*.json"))
    with CoreRuntime(tmp_path) as core:
        assert core.placement_count() == 0
