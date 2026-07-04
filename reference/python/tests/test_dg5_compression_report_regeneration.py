from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_dg5_19_report_regeneration_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    _run_report(first)
    _run_report(second)
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")


def test_dg5_20_report_uses_only_view_entry_reduction_language() -> None:
    report = (REPO_ROOT / "docs/validation/DG5_EVIDENCE_PRESERVING_COMPACTION_REPORT.md").read_text(encoding="utf-8").lower()
    assert "estimated view-entry reduction" in report
    for forbidden in ("disk saved", "memory saved", "token saved", "latency reduced", "global dedup", "compressed storage"):
        assert forbidden not in report


def test_dg5_21_report_lists_required_counts_and_limits() -> None:
    report = (REPO_ROOT / "docs/validation/DG5_EVIDENCE_PRESERVING_COMPACTION_REPORT.md").read_text(encoding="utf-8")
    for required in ("input traces", "compacted members", "passthrough traces", "view entries", "estimated view-entry reduction", "lossless expansion", "Limits"):
        assert required in report


def _run_report(path: Path) -> None:
    subprocess.run(
        [sys.executable, "validation/dg5/run_dg5_validation.py", "--output", str(path)],
        cwd=REPO_ROOT,
        check=True,
        timeout=30,
    )
