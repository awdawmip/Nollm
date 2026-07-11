import json

import pytest

from nollm_snapshot import SnapshotDiff, SnapshotService


def canonical(**changes: object) -> bytes:
    document = {
        "schema_version": "nollm_core_state_v1",
        "geometry_registry": {"id": "one"},
        "cells": [],
        "bridges": [],
    }
    document.update(changes)
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def test_snapshot_diff_is_deterministic_serializable_and_finite() -> None:
    left = canonical()
    right = canonical(cells=[{"address": "changed"}], bridges=[{"id": "b"}])
    first = SnapshotService().structural_diff(left, right)
    second = SnapshotService().structural_diff(left, right)
    assert first == second
    assert isinstance(first, SnapshotDiff)
    assert first.changed_top_level_sections == ("cells", "bridges")
    assert json.loads(json.dumps(first.to_mapping()))["changed_top_level_sections"] == ["cells", "bridges"]


def test_snapshot_diff_handles_non_core_bytes_without_semantic_guessing() -> None:
    result = SnapshotService().structural_diff(b"left", b"right")
    assert not result.equal
    assert result.changed_top_level_sections == ("bytes",)
    with pytest.raises(TypeError, match="must be bytes"):
        SnapshotService().structural_diff("left", b"right")
