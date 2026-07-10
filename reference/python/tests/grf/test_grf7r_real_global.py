from __future__ import annotations

from nollm.grf.grf7_scale_validation import run_grf7_global_scale_validation
from nollm.grf.grf7r_real_global import run_real_global_workload


def test_artifact_backed_workload_reads_content_store_and_replays(tmp_path) -> None:
    artifacts = tmp_path / "artifacts"
    run_grf7_global_scale_validation(artifacts, global_count=40, partition_size=20)

    first = run_real_global_workload(artifacts, tmp_path / "results", queries_per_partition=2, negative_checks=0)
    second = run_real_global_workload(artifacts, tmp_path / "results", queries_per_partition=2, negative_checks=0)

    assert first["artifact_inventory"]["placement_count"] == 40
    assert first["content_hash_resolution_count"] == first["query_count"] == 4
    assert second["semantic_query_digest"] == first["semantic_query_digest"]
    assert second["replay_deterministic"] is True


def test_negative_bridge_queries_are_individually_checked(tmp_path) -> None:
    artifacts = tmp_path / "artifacts"
    run_grf7_global_scale_validation(artifacts, global_count=80, partition_size=20)

    first = run_real_global_workload(artifacts, tmp_path / "results", queries_per_partition=2, negative_checks=4)
    second = run_real_global_workload(artifacts, tmp_path / "results", queries_per_partition=2, negative_checks=4)

    assert first["negative_query_count"] == 4
    assert first["negative_forbidden_bridge_hit_count"] == 0
    assert second["negative_replay_deterministic"] is True
