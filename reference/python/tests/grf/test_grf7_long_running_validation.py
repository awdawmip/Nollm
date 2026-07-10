from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf7_long_running_validation import run_long_running_validation


def test_fixed_work_reliability_runs_all_operation_classes(tmp_path) -> None:
    result = run_long_running_validation(tmp_path, operation_count=1_200, checkpoint_interval=200)
    assert result.operation_count == 1_200
    assert all(count == 100 for count in result.operation_counts.values())
    assert result.error_count == result.recovery_count == 100
    assert result.snapshot_count == 6
    assert result.orphan_object_count == 0
    assert result.identity_collision_count == 0
    assert result.evidence_loss_count == 0
    assert result.replay_deterministic is True
    assert result.status == "GATE_H_FAIL"  # Full gate requires one million operations.
