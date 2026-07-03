from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validation.gpr1.run_gpr1_geometry_profile_regime import build_report


def test_gpr1_report_regenerates_to_committed_baseline() -> None:
    expected = Path("docs/validation/GPR1_GEOMETRY_PROFILE_REGIME_BASELINE_REPORT.md").read_text(encoding="utf-8")
    assert build_report() == expected
