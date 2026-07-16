import pytest

from nollm_access import AccessMemoryLoop, FileHandleStore, FileStatementStore, MemoryStatement, RevisionTargetExcludedError


CELL = {"profile_id": "default_dream_v1", "chart_id": "default", "layer": 0, "q": 0, "r": 0, "phase": None}


def placement(statement_id: str, action: str, candidate_id: str, *, handle: dict[str, object] | None = None) -> dict[str, object]:
    decision = {"statement_id": statement_id, "action": action, "candidate_id": candidate_id, "reason_text": "explicit fixture decision"}
    if handle is not None:
        decision["existing_handle"] = handle
    return {"schema_version": "nollm_openclaw_surface_placement_v1", "outcome": "apply", "decision": decision}


def confirmation(provisional: dict[str, object], outcome: str = "confirm_revision") -> dict[str, object]:
    confirmed = outcome == "confirm_revision"
    return {
        "schema_version": "nollm_openclaw_revision_confirmation_v1",
        "provisional_id": provisional["provisional_id"],
        "outcome": outcome,
        "relation": "same_subject_same_slot_supersedes" if confirmed else "different_subject_or_non_superseding",
    }


def workspace_bytes(root) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_revision_replaces_current_binding_and_recall_after_reopen(tmp_path) -> None:
    old = MemoryStatement("meeting:tuesday", "Project weekly meeting is Tuesday at 9 AM.")
    new = MemoryStatement("meeting:thursday", "Project weekly meeting is Thursday at 3 PM; Tuesday is cancelled.")
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.apply_placement(old, placement(old.statement_id, "expand_surface", "placement:expand:0"), "new")
        raw = placement(new.statement_id, "revision_current", "placement:existing:0", handle=first["handle"])
        provisional = loop.apply_placement(new, raw, "revision", CELL)
        assert provisional["outcome"] == "revision_confirmation_required"
        revised = loop.apply_placement(new, raw, "revision", CELL, revision_confirmation=confirmation(provisional["provisional_revision"]))
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
        first = loop.apply_placement(current, placement(current.statement_id, "expand_surface", "placement:expand:0"), "new")
        duplicate = loop.apply_placement(current, placement(current.statement_id, "reuse", "placement:existing:0", handle=first["handle"]), "duplicate", CELL)
        other = loop.apply_placement(distinct, placement(distinct.statement_id, "new_local", "placement:lateral:5"), "distinct", CELL)
        assert duplicate["handle"] == first["handle"]
        assert loop.binding(current.statement_id)["handle"] == first["handle"]
        assert loop.binding(distinct.statement_id)["handle"] == other["handle"]
        assert other["handle"] != first["handle"]


def test_reuse_with_distinct_statement_identity_verifies_supporting_binding(tmp_path) -> None:
    current = MemoryStatement("meeting:canonical", "Project weekly meeting is Thursday at 3 PM.")
    duplicate = MemoryStatement("meeting:duplicate", "Project weekly meeting is Thursday at 3 PM.")
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.apply_placement(current, placement(current.statement_id, "expand_surface", "placement:expand:0"), "new")
        reused = loop.apply_placement(
            duplicate,
            placement(duplicate.statement_id, "reuse", "placement:existing:0", handle=first["handle"]),
            "reuse", CELL,
        )
        binding = loop.binding(duplicate.statement_id)
    assert reused["handle"] == first["handle"]
    assert binding["current_statement_id"] == current.statement_id
    assert binding["supporting_statement_ids"] == [duplicate.statement_id]


def test_revision_binding_failure_restores_old_current_and_discards_new_statement(tmp_path, monkeypatch) -> None:
    old = MemoryStatement("meeting:tuesday", "Project weekly meeting is Tuesday at 9 AM.")
    new = MemoryStatement("meeting:thursday", "Project weekly meeting is Thursday at 3 PM; Tuesday is cancelled.")
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.apply_placement(old, placement(old.statement_id, "expand_surface", "placement:expand:0"), "new")
        def fail(*_args: object) -> None:
            raise OSError("injected binding failure")
        monkeypatch.setattr(FileHandleStore, "revise_current", fail)
        raw = placement(new.statement_id, "revision_current", "placement:existing:0", handle=first["handle"])
        provisional = loop.apply_placement(new, raw, "revision-failure", CELL)
        with pytest.raises(OSError, match="injected binding failure"):
            loop.apply_placement(new, raw, "revision-failure", CELL, revision_confirmation=confirmation(provisional["provisional_revision"]))
        assert loop.binding(old.statement_id)["current_statement_id"] == old.statement_id
        assert loop.local_context([first["handle"]["geometry_address"]], "after-failure")[0]["content_utf8"] == old.content_utf8
    assert not FileStatementStore(tmp_path).exists(new.statement_id)
    with AccessMemoryLoop(tmp_path) as loop:
        assert loop.binding(old.statement_id)["current_statement_id"] == old.statement_id


def test_provisional_reject_and_blacklist_are_zero_write(tmp_path) -> None:
    old = MemoryStatement("alpha:bx", "Alpha V3.9 release code is BX-3917.")
    different = MemoryStatement("caold:cr", "CAOLD broad-residue acceptance code is CR-7159.")
    with AccessMemoryLoop(tmp_path) as loop:
        first = loop.apply_placement(old, placement(old.statement_id, "expand_surface", "placement:expand:0"), "new")
        raw = placement(different.statement_id, "revision_current", "placement:existing:0", handle=first["handle"])
        before = workspace_bytes(tmp_path)
        provisional = loop.apply_placement(different, raw, "wrong-revision", CELL)
        assert provisional["outcome"] == "revision_confirmation_required"
        assert provisional["core_write_count"] == 0
        assert workspace_bytes(tmp_path) == before
        rejected = loop.apply_placement(
            different, raw, "wrong-revision", CELL,
            revision_confirmation=confirmation(provisional["provisional_revision"], "reject_revision"),
        )
        assert rejected["outcome"] == "revision_rejected"
        assert rejected["core_write_count"] == 0
        assert workspace_bytes(tmp_path) == before
        with pytest.raises(RevisionTargetExcludedError):
            loop.apply_placement(
                different, raw, "wrong-revision", CELL,
                excluded_revision_targets=[first["handle"]],
            )
        assert workspace_bytes(tmp_path) == before
        assert loop.binding(old.statement_id)["current_statement_id"] == old.statement_id
    assert not FileStatementStore(tmp_path).exists(different.statement_id)
