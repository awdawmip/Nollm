from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_mini_validation_reports_required_metrics() -> None:
    completed = subprocess.run([sys.executable, str(ROOT / "experiments" / "grf" / "run_mini_validation.py")], cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["note"] == "Cognee-style local baseline, not actual Cognee run"
    assert payload["dataset_items"] >= 5000
    assert payload["scale_seed"] == "grf1lm_scale_seed_v1"
    metrics = payload["metrics"]["N3_grf_plus_stitching"]
    for key in (
        "recall_correctness",
        "source_faithfulness",
        "false_stitch_rate",
        "missed_stitch_rate",
        "relation_storage_size",
        "ledger_event_count",
        "object_file_count",
        "average_kernel_fanout",
        "max_kernel_fanout",
        "runtime_float_operation_count",
        "polygon_runtime_call_count",
        "context_token_cost_estimate",
        "replay_selected_shard_delta",
        "replay_path_class_delta",
    ):
        assert key in metrics
    assert metrics["polygon_runtime_call_count"] == 0
    assert metrics["runtime_float_operation_count"] == 0
    replay = payload["metrics"]["N5_grf_file_replay"]
    assert replay["replay_selected_shard_delta"] == 0
    assert replay["replay_path_class_delta"] == 0
    n6 = payload["metrics"]["N6_grf_capture_file_replay_fixture_policy"]
    assert n6["captured_shard_count"] >= 5000
    assert n6["admitted_shard_count"] > 0
    assert n6["source_resolution_success_rate"] == 1.0
    assert n6["replay_selected_shard_delta"] == 0
    assert n6["replay_path_class_delta"] == 0
    assert n6["relation_storage_size"] < payload["metrics"]["B2_explicit_graph"]["relation_storage_size"]
    n7 = payload["metrics"]["N7_grf_facade_file_replay_fixture_policy"]
    assert n7["captured_shard_count"] >= 5000
    assert n7["source_resolution_success_rate"] == 1.0
    assert n7["replay_selected_shard_delta"] == 0
    assert n7["replay_path_class_delta"] == 0
    assert n7["relation_storage_size"] < n7["explicit_graph_relation_storage_size"]
    n8 = payload["metrics"]["N8_grf_facade_deterministic_policy"]
    n9 = payload["metrics"]["N9_grf_facade_deterministic_policy_with_query_generalization"]
    assert n8["placement_policy_variant"] == "grf_deterministic_policy_v1"
    assert n9["query_generalization_seed_count"] >= 20
    assert n9["source_resolution_success_rate"] == 1.0
    assert n9["replay_selected_shard_delta"] == 0
    assert n9["replay_path_class_delta"] == 0
    assert len(payload["limitations"]) >= 8
    assert payload["hard_conditions"]["relation_storage_not_o_n_squared_on_fixture"] is True
    assert payload["hard_conditions"]["grf_relation_storage_below_explicit_graph"] is True
