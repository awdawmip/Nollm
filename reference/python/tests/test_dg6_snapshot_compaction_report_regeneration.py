from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from validation.dg6.run_dg6_validation import build_report


def test_dg6_19_report_matches_committed_copy_and_fresh_processes() -> None:
    report = build_report()
    committed = Path("docs/validation/DG6_ISOLATED_SNAPSHOT_COMPACTION_ADAPTER_REPORT.md").read_text(encoding="utf-8")
    assert report == committed

    command = [sys.executable, "validation/dg6/run_dg6_validation.py", "--stdout"]
    first = subprocess.run(command, check=True, capture_output=True, text=True, timeout=60).stdout
    second = subprocess.run(command, check=True, capture_output=True, text=True, timeout=60).stdout
    assert first == second == committed
