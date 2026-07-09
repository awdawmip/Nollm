from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_mini_validation_reports_required_metrics() -> None:
    completed = subprocess.run([sys.executable, str(ROOT / "experiments" / "grf" / "run_mini_validation.py")], cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["note"] == "Cognee-style local baseline, not actual Cognee run"
    metrics = payload["metrics"]["N3_grf_plus_stitching"]
    for key in (
        "recall_correctness",
        "source_faithfulness",
        "false_stitch_rate",
        "missed_stitch_rate",
        "relation_storage_size",
        "average_kernel_fanout",
        "runtime_float_operation_count",
        "polygon_runtime_call_count",
        "context_token_cost_estimate",
    ):
        assert key in metrics
    assert metrics["polygon_runtime_call_count"] == 0
    assert metrics["runtime_float_operation_count"] == 0
    assert payload["hard_conditions"]["relation_storage_not_o_n_squared_on_fixture"] is True
