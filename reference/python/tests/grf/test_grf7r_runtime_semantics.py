from __future__ import annotations

from experiments.grf.run_grf7r_runtime_semantics import run


def test_facade_runtime_post_commit_recovery_and_attacks(tmp_path) -> None:
    result = run(tmp_path)

    assert result["post_commit_retry_count"] == 3
    assert result["retry_identities_stable"] is True
    assert result["durable_counts_unchanged_after_cache_delete"] is True
    assert result["adapter_owns_durable_truth"] is False
    assert result["replay_deterministic_before_after_restart"] is True
    assert result["attack_rejection_count"] == result["attack_count"]
