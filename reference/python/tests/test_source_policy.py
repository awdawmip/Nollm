from __future__ import annotations

from pathlib import Path

import pytest

from nollm.source_policy import enumerate_legacy_sources, resolve_source_path, state_for_path, validate_relative_source_path


def test_openclaw_legacy_policy_enumerates_only_allowed_files(tmp_path: Path) -> None:
    (tmp_path / "MEMORY.md").write_text("m", encoding="utf-8")
    (tmp_path / "DREAMS.md").write_text("d", encoding="utf-8")
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "day.md").write_text("day", encoding="utf-8")
    (tmp_path / "other.md").write_text("no", encoding="utf-8")

    paths = [item.relative_path for item in enumerate_legacy_sources(tmp_path)]

    assert paths == ["DREAMS.md", "MEMORY.md", "memory/day.md"]
    assert state_for_path("DREAMS.md")["epistemic_state"] == "tentative"
    assert state_for_path("MEMORY.md")["epistemic_state"] == "legacy_recorded"


@pytest.mark.parametrize("bad", ["../MEMORY.md", "/abs/MEMORY.md", "archive/x.md", "other.md"])
def test_policy_rejects_unsafe_paths(bad: str) -> None:
    with pytest.raises(ValueError):
        validate_relative_source_path(bad)


def test_resolve_source_path_stays_in_workspace(tmp_path: Path) -> None:
    (tmp_path / "MEMORY.md").write_text("m", encoding="utf-8")

    assert resolve_source_path(tmp_path, "MEMORY.md") == (tmp_path / "MEMORY.md").resolve()
