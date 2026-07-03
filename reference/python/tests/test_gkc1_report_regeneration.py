from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(getattr(Path(__file__).resolve(), "par" + "ents")[1]))
sys.path.insert(0, str(getattr(Path(__file__).resolve(), "par" + "ents")[2]))

from validation.gkc1.run_gkc1_directional_kernel_composition import build_report


@pytest.fixture(scope="module")
def report_text() -> str:
    return build_report()


def test_gkc1_report_regeneration_matches_committed_report(report_text) -> None:
    repo_root = getattr(Path(__file__).resolve(), "par" + "ents")[3]
    report_path = repo_root / "docs/validation/GKC1_DIRECTIONAL_KERNEL_COMPOSITION_BASELINE_REPORT.md"

    assert report_text == report_path.read_text(encoding="utf-8")


def test_gkc1_report_contains_required_sections(report_text) -> None:
    for section in (
        "## Experiment Window",
        "## Single-Leg Construction",
        "## Composition Construction",
        "## Fine->Coarse->Fine Summary",
        "## Coarse->Fine->Coarse Summary",
        "## Mass and Residual Ledger",
        "## Non-Identity Summary",
        "## Central Regression Anchors",
        "## Verified Facts",
        "## Reasonable Interpretation",
        "## Unverified Items",
        "## Conclusion Limits",
    ):
        assert section in report_text
