from __future__ import annotations

import json
from pathlib import Path

from nollm.archive import create_archive_snapshot
from nollm.coverage import validate_source_coverage
from nollm.source_spans import build_source_span_inventory


def test_coverage_fails_on_gap(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "MEMORY.md").write_text("alpha\n\nbeta\n", encoding="utf-8")
    snapshot = str(create_archive_snapshot(workspace, tmp_path / "root")["snapshot_id"])
    build_source_span_inventory(tmp_path / "root", snapshot)
    path = tmp_path / "root" / "archive" / "source-spans" / f"{snapshot}.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    records[0]["end_byte_exclusive"] -= 1
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")

    report = validate_source_coverage(tmp_path / "root", snapshot)

    assert report["ok"] is False
    assert report["uncovered_source_spans"] > 0

