from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[3]

from validation.gcm1.run_gcm1_sparse_collision_trace_compaction import build_report


def test_gcm1_report_regenerates_to_committed_baseline() -> None:
    expected = (REPO_ROOT / "docs/validation/GCM1_SPARSE_COLLISION_TRACE_COMPACTION_BASELINE_REPORT.md").read_text(encoding="utf-8")
    assert build_report() == expected


def test_gcm1_report_names_required_boundaries() -> None:
    report = build_report()

    assert "Experiment Window" in report
    assert "Collision Witness" in report
    assert "Scenario Results" in report
    assert "Expansion Manifest Check" in report
    assert "Verified Facts" in report
    assert "Reasonable Interpretation" in report
    assert "Unverified Items" in report
    assert "Conclusion Limits" in report
    assert "collision is shared finite DG1/GSC1 support only" in report
    assert "not evidence deletion" in report
    assert "Synthetic trace is not a DreamShard" in report
    assert "not a RevisionThread" in report
