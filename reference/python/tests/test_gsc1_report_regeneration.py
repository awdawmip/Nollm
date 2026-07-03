from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]

from validation.gsc1.run_gsc1_sparse_shard_scale_coverage import build_report


def test_gsc1_report_regenerates_to_committed_baseline() -> None:
    expected = (REPO_ROOT / "docs/validation/GSC1_SPARSE_SHARD_SCALE_COVERAGE_BASELINE_REPORT.md").read_text(encoding="utf-8")
    assert build_report() == expected


def test_gsc1_report_names_boundary_sections() -> None:
    report = build_report()

    assert "GSC1_REPORTING_NOISE_FLOOR = 1.000000e-12" in report
    assert "\u22641.000000e-12" in report
    assert "Verified Facts" in report
    assert "Reasonable Interpretation" in report
    assert "Unverified Items" in report
    assert "Conclusion Limits" in report
    assert "not a persisted DreamShard" in report
    assert "not recall input" in report
    assert "not shard equivalence" in report
    assert "No GrowthProposal, PlacementPlan, Geometry profile selection, FieldSnapshot, RecallUniverse, Query, or recall execution" in report
