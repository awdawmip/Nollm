from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]

from validation.gra1.run_gra1_rotation_scale_resonance import build_report


def test_gra1_report_regenerates_to_committed_baseline() -> None:
    expected = (REPO_ROOT / "docs/validation/GRA1_ROTATION_SCALE_RESONANCE_BASELINE_REPORT.md").read_text(encoding="utf-8")
    assert build_report() == expected


def test_gra1_report_names_required_boundaries() -> None:
    report = build_report()

    assert "Experiment Window" in report
    assert "Recurrence Candidates" in report
    assert "Observation Counts" in report
    assert "Classification Summary" in report
    assert "Constant-Local Findings" in report
    assert "Layer-Drift Findings" in report
    assert "Verified Facts" in report
    assert "Reasonable Interpretation" in report
    assert "Unverified Items" in report
    assert "Conclusion Limits" in report
    assert "not cover authority" in report
    assert "not parent/child structure" in report
    assert "not compression permission" in report
    assert "not recall authority" in report
    assert "does not choose, replace, deprecate, or modify ParameterSet B" in report
