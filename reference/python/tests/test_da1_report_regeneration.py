from pathlib import Path

from nollm.dream_geometry.validation.da1_memory_admission_report import build_report


def test_a25_da1_report_regeneration_is_stable() -> None:
    expected = Path(__file__).resolve().parents[3] / "docs" / "validation" / "DA1_MEMORY_ADMISSION_BASELINE_REPORT.md"
    assert build_report() == expected.read_text(encoding="utf-8")
