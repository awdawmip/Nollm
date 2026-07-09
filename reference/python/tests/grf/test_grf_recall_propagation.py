from __future__ import annotations

from grf_runtime_fixture import relation_field
from nollm.grf.coverage_template import COVERAGE_DOWN, COVERAGE_UP
from nollm.grf.recall import QueryProbe, RecallBudget, resolve_grf_recall


def test_grf_recall_propagates_from_shard_id() -> None:
    field = relation_field()
    query = QueryProbe("query_a", "shard_id", "shard_a", (COVERAGE_UP, COVERAGE_DOWN), RecallBudget(2, 4, 2, 1, 0, 3))
    digest = resolve_grf_recall(query, field)
    assert "shard_a" in digest.selected_shards
    assert "shard_b" in digest.selected_shards
    assert digest.to_mapping()["not_fact_confirmation"] is True
