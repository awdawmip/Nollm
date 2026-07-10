from __future__ import annotations

from experiments.grf.run_grf7r4_snapshot_replay_validation import run


def test_snapshot_replay_uses_independent_restore_and_detects_controls(tmp_path) -> None:
    result = run(tmp_path)
    assert result["independent_restore_directory"] is True
    assert result["passed"] is True
    assert all(item["pass"] for item in result["predicates"])
    assert all(result["negative_controls"].values())
