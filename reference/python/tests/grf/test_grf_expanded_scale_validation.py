from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_expanded_scale_validation_reports_opq_variants() -> None:
    completed = subprocess.run([sys.executable, str(ROOT / "experiments" / "grf" / "run_mini_validation.py")], cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["dataset_items"] >= 5000
    assert payload["file_fixture_items"] >= 200
    assert {"N6_grf_capture_file_replay_fixture_policy", "N7_grf_facade_file_replay_fixture_policy", "N8_grf_facade_deterministic_policy", "N9_grf_facade_deterministic_policy_with_query_generalization"} <= set(payload["metrics"])
    n9 = payload["metrics"]["N9_grf_facade_deterministic_policy_with_query_generalization"]
    assert n9["grf_relation_storage_size"] < n9["explicit_graph_relation_storage_size"]
    assert n9["source_resolution_success_rate"] == 1.0
    assert n9["runtime_float_operation_count"] == 0
    assert n9["polygon_runtime_call_count"] == 0
