from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validation.gvr1.run_gvr1_translation_variation import build_report


def test_gvr1_report_regenerates_to_committed_baseline() -> None:
    expected = Path("docs/validation/GVR1_TRANSLATION_VARIATION_BASELINE_REPORT.md").read_text(encoding="utf-8")
    assert build_report() == expected
