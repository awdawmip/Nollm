from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf4r_failure_recovery import run_failure_recovery


def test_file_storage_host_and_identity_failures_recover_deterministically(tmp_path: Path) -> None:
    result = run_failure_recovery(tmp_path)
    assert result.passed is True
    assert result.recovery_time_ns > 0
