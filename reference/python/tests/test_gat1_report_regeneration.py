from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validation.gat1.run_gat1_chart_groupoid import build_report


def test_gat1_report_regenerates_to_committed_baseline() -> None:
    expected = Path("docs/validation/GAT1_CHART_GROUPOID_BASELINE_REPORT.md").read_text(encoding="utf-8")
    assert build_report() == expected


def test_gat1_c1_report_names_rendering_rule_and_boundary_sections() -> None:
    report = build_report()

    assert "GAT1_REPORTING_NOISE_FLOOR = 1.000000e-12" in report
    assert "\u22641.000000e-12" in report
    assert "Verified Facts" in report
    assert "Reasonable Interpretation" in report
    assert "Unverified Items" in report
    assert "Conclusion Limits" in report
    assert "not an overlap witness" in report
    assert "not chart merge evidence" in report
    assert "not recall traversal authorization" in report
    assert "atlas merge" in report
