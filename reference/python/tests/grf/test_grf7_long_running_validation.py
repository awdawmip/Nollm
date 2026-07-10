from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf7_long_running_validation import run_long_running


def test_fixed_work_reliability_writes_real_snapshots_and_ledger(tmp_path) -> None:
    result = run_long_running(tmp_path, operation_count=1_200, checkpoint_interval=200)
    assert result["operation_count"] == 1_200
    assert result["snapshot_count"] == 6
    assert result["snapshot_replay_equals_final_state"] is True
    assert result["recovery_count"] == result["injected_recoverable_failure_count"]
    assert result["orphan_object_count"] == 0
    assert result["identity_collision_count"] == 0
    assert result["evidence_loss_count"] == 0
