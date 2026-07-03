from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]

from validation.grc1.run_grc1_resonance_conditioned_coverage import build_report


def test_grc1_report_regenerates_to_committed_baseline() -> None:
    expected = (REPO_ROOT / "docs/validation/GRC1_RESONANCE_CONDITIONED_COVERAGE_BASELINE_REPORT.md").read_text(encoding="utf-8")
    assert build_report() == expected


def test_grc1_report_names_required_boundaries() -> None:
    report = build_report()

    assert "Experiment Window" in report
    assert "Alignment Classification Summary" in report
    assert "Coverage Summary" in report
    assert "Exact-Center Conditional Coverage" in report
    assert "Phase-Separated Conditional Coverage" in report
    assert "Noncommensurate Control" in report
    assert "Verified Facts" in report
    assert "Reasonable Interpretation" in report
    assert "Unverified Items" in report
    assert "Conclusion Limits" in report
    assert "GRC1_REPORTING_NOISE_FLOOR = 1.000000e-12" in report
    assert "\u22641.000000e-12" in report
    assert "Exact center plus singleton coverage is not hierarchy evidence" in report
    assert "does not select, modify, replace, deprecate, or recommend replacing ParameterSet B" in report
