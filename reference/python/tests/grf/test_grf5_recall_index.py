from __future__ import annotations

from nollm.grf.performance_evolution import run_recall_index_benchmark


def test_indexed_entry_lookup_matches_linear_lookup_and_is_faster() -> None:
    metrics = run_recall_index_benchmark(10_000, 100)
    assert metrics.equivalent is True
    assert metrics.indexed_lookup_ns < metrics.linear_lookup_ns
    assert metrics.index_storage_bytes > 0
