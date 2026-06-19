from __future__ import annotations

import json
import shutil
from pathlib import Path

from nollm.openclaw_memory_adapter import (
    FORBIDDEN_SEMANTICS,
    SCHEMA,
    build_openclaw_memory_fixture_report,
    parse_openclaw_memory_workspace,
)


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "examples/openclaw_memory_fixture"


def test_openclaw_memory_fixture_parses_deterministically() -> None:
    first = parse_openclaw_memory_workspace(FIXTURE)
    second = parse_openclaw_memory_workspace(FIXTURE)

    assert first.to_record() == second.to_record()
    assert first.chunk_count > 0
    assert [chunk.memory_id for chunk in first.chunks] == [chunk.memory_id for chunk in second.chunks]


def test_openclaw_memory_chunks_have_posix_paths_and_line_ranges() -> None:
    index = parse_openclaw_memory_workspace(FIXTURE)

    for chunk in index.chunks:
        assert "\\" not in chunk.source_path
        assert chunk.line_range[0] >= 1
        assert chunk.line_range[0] <= chunk.line_range[1]
        assert chunk.text.strip() == chunk.text
        assert len(chunk.source_sha256) == 64
        assert len(chunk.chunk_sha256) == 64


def test_openclaw_memory_source_roles_are_assigned() -> None:
    index = parse_openclaw_memory_workspace(FIXTURE)
    roles = {(chunk.source_path, chunk.source_role) for chunk in index.chunks}

    assert ("MEMORY.md", "durable_memory") in roles
    assert ("memory/2026-06-19.md", "daily_memory") in roles
    assert ("DREAMS.md", "dreams") in roles
    assert index.source_files == ("MEMORY.md", "memory/2026-06-19.md", "DREAMS.md")


def test_openclaw_memory_parser_does_not_mutate_source_files() -> None:
    before = {
        path.relative_to(FIXTURE).as_posix(): path.read_bytes()
        for path in [FIXTURE / "MEMORY.md", FIXTURE / "DREAMS.md", FIXTURE / "memory/2026-06-19.md"]
    }

    parse_openclaw_memory_workspace(FIXTURE)

    after = {
        path.relative_to(FIXTURE).as_posix(): path.read_bytes()
        for path in [FIXTURE / "MEMORY.md", FIXTURE / "DREAMS.md", FIXTURE / "memory/2026-06-19.md"]
    }
    assert before == after
    assert not (FIXTURE / ".nollm-memory").exists()


def test_openclaw_memory_report_schema_and_forbidden_semantics() -> None:
    report = build_openclaw_memory_fixture_report(ROOT, FIXTURE)

    assert report["schema"] == SCHEMA
    assert report["ok"] is True
    assert report["workspace"] == "examples/openclaw_memory_fixture"
    assert report["chunk_count"] == len(report["chunks"])
    assert report["source_files"] == ["MEMORY.md", "memory/2026-06-19.md", "DREAMS.md"]
    assert report["source_roles_present"] == ["durable_memory", "daily_memory", "dreams"]
    assert report["forbidden_semantics"] == FORBIDDEN_SEMANTICS
    assert all(value is False for value in report["forbidden_semantics"].values())
    json.dumps(report, sort_keys=True)


def test_openclaw_memory_parser_tolerates_missing_optional_dreams(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(FIXTURE, workspace)
    (workspace / "DREAMS.md").unlink(missing_ok=True)

    index = parse_openclaw_memory_workspace(workspace)

    assert index.chunk_count > 0
    assert "DREAMS.md" not in index.source_files
    assert not any(chunk.source_role == "dreams" for chunk in index.chunks)
