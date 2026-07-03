from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(getattr(Path(__file__).resolve(), "par" + "ents")[1]))
sys.path.insert(0, str(getattr(Path(__file__).resolve(), "par" + "ents")[2]))

from validation.gkd1.run_gkd1_bidirectional_coverage import build_report


@pytest.fixture(scope="module")
def report_text() -> str:
    return build_report()


def test_gkd1_report_regeneration_matches_committed_report(report_text) -> None:
    repo_root = getattr(Path(__file__).resolve(), "par" + "ents")[3]
    report_path = repo_root / "docs/validation/GKD1_BIDIRECTIONAL_COVERAGE_BASELINE_REPORT.md"

    assert report_text == report_path.read_text(encoding="utf-8")


def test_gkd1_report_contains_required_sections(report_text) -> None:
    for section in (
        "## Experiment Window",
        "## Directional Construction",
        "## K_up Summary",
        "## K_down Summary",
        "## Directional Pair Comparison",
        "## Residual Boundary Summary",
        "## Verified Facts",
        "## Reasonable Interpretation",
        "## Unverified Items",
        "## Conclusion Limits",
    ):
        assert section in report_text
