from __future__ import annotations

from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.coverage import validate_source_coverage
from nollm.source_spans import build_source_span_inventory, load_source_spans


def test_source_spans_cover_archive_bytes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "MEMORY.md").write_text("# A\n\n- one\n- two\n", encoding="utf-8")
    snapshot = create_archive_snapshot(workspace, tmp_path / "root")["snapshot_id"]

    report = build_source_span_inventory(tmp_path / "root", str(snapshot))
    spans = load_source_spans(tmp_path / "root", str(snapshot))
    coverage = validate_source_coverage(tmp_path / "root", str(snapshot))

    assert report["ok"] is True
    assert spans
    assert coverage["ok"] is True
    assert coverage["coverage_ratio"] == 1.0


def test_source_spans_mark_binary_unsupported(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "MEMORY.md").write_bytes(b"\xff\xfe")
    snapshot = create_archive_snapshot(workspace, tmp_path / "root")["snapshot_id"]
    build_source_span_inventory(tmp_path / "root", str(snapshot))
    coverage = validate_source_coverage(tmp_path / "root", str(snapshot))

    assert coverage["ok"] is False
    assert coverage["unsupported"] == 1

