import pytest

from nollm_access import AccessMemoryLoop, FileHandleStore, FileStatementStore, MemoryStatement


CELL = {"profile_id": "eisenstein_exact_v1", "chart_id": "default", "layer": 0, "q": 0, "r": 0, "phase": None}
MOVED_CELL = {"profile_id": "eisenstein_exact_v1", "chart_id": "default", "layer": 0, "q": 1, "r": 0, "phase": None}


def placement(statement_id: str, action: str, *, handle: dict[str, object] | None = None, cell: dict[str, object] | None = CELL) -> dict[str, object]:
    decision = {"statement_id": statement_id, "action": action, "reason_text": "explicit fixture decision"}
    if cell is not None:
        decision["target_cell"] = cell
    if handle is not None:
        decision["existing_handle"] = handle
    return {"schema_version": "nollm_openclaw_placement_v1", "outcome": "apply", "decision": decision}


def test_revision_replaces_current_binding_and_recall_after_reopen(tmp_path) -> None:
    old = MemoryStatement("meeting:tuesday", "Project weekly meeting is Tuesday at 9 AM.")
    new = MemoryStatement("meeting:thursday", "Project weekly meeting is Thursday at 3 PM; Tuesday is cancelled.")
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.apply_placement(old, placement(old.statement_id, "new"), "new")
        revised = loop.apply_placement(new, placement(new.statement_id, "revision_current", handle=first["handle"], cell=None), "revision")
        assert revised["handle"] == first["handle"]
        assert loop.binding(new.statement_id)["current_statement_id"] == new.statement_id
        with pytest.raises(KeyError):
            loop.binding(old.statement_id)
    with AccessMemoryLoop(tmp_path) as reopened:
        recalled = reopened.local_context([revised["handle"]["geometry_address"]], "reopen")
    assert [(item["statement_id"], item["content_utf8"]) for item in recalled] == [(new.statement_id, new.content_utf8)]


def test_duplicate_reuses_current_and_similar_distinct_creates_new_binding(tmp_path) -> None:
    current = MemoryStatement("meeting:thursday", "Project weekly meeting is Thursday at 3 PM.")
    distinct = MemoryStatement("review:tuesday", "Project technical review remains Tuesday at 9 AM.")
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.apply_placement(current, placement(current.statement_id, "new"), "new")
        duplicate = loop.apply_placement(current, placement(current.statement_id, "reuse", handle=first["handle"], cell=None), "duplicate")
        other = loop.apply_placement(distinct, placement(distinct.statement_id, "new", cell=MOVED_CELL), "distinct")
        assert duplicate["handle"] == first["handle"]
        assert loop.binding(current.statement_id)["handle"] == first["handle"]
        assert loop.binding(distinct.statement_id)["handle"] == other["handle"]
        assert other["handle"] != first["handle"]


def test_revision_binding_failure_restores_old_current_and_discards_new_statement(tmp_path, monkeypatch) -> None:
    old = MemoryStatement("meeting:tuesday", "Project weekly meeting is Tuesday at 9 AM.")
    new = MemoryStatement("meeting:thursday", "Project weekly meeting is Thursday at 3 PM; Tuesday is cancelled.")
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.apply_placement(old, placement(old.statement_id, "new"), "new")
        def fail(*_args: object) -> None:
            raise OSError("injected binding failure")
        monkeypatch.setattr(FileHandleStore, "revise_current", fail)
        with pytest.raises(OSError, match="injected binding failure"):
            loop.apply_placement(new, placement(new.statement_id, "revision_current", handle=first["handle"], cell=None), "revision-failure")
        assert loop.binding(old.statement_id)["current_statement_id"] == old.statement_id
        assert loop.local_context([first["handle"]["geometry_address"]], "after-failure")[0]["content_utf8"] == old.content_utf8
    assert not FileStatementStore(tmp_path).exists(new.statement_id)
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding(old.statement_id)["current_statement_id"] == old.statement_id
