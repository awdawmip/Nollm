from __future__ import annotations

from pathlib import Path

from validation.ba1.run_ba1_batch_admission import build_report


def test_ba1_report_regeneration_matches_committed_baseline_except_head() -> None:
    expected = _normalize(Path(__file__).resolve().parents[3] / "docs" / "validation" / "BA1_BATCH_ADMISSION_BASELINE_REPORT.md")
    actual = _normalize_text(build_report())
    assert actual == expected


def _normalize(path: Path) -> str:
    return _normalize_text(path.read_text(encoding="utf-8"))


def _normalize_text(text: str) -> str:
    return "\n".join("<validation_head>" if line.startswith("- validation_head:") else line for line in text.splitlines()) + "\n"
