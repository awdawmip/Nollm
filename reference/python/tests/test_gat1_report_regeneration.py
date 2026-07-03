from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validation.gat1.run_gat1_chart_groupoid import build_report


def test_gat1_report_regenerates_to_committed_baseline() -> None:
    expected = Path("docs/validation/GAT1_CHART_GROUPOID_BASELINE_REPORT.md").read_text(encoding="utf-8")
    assert build_report() == expected
