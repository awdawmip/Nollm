from __future__ import annotations

from grf_runtime_fixture import relation_field
from nollm.grf.recall import QueryProbe, RecallBudget, resolve_grf_recall


def test_every_selected_shard_has_source_fallback_ref() -> None:
    field = relation_field()
    query = QueryProbe("query_source", "source_window", "source:a", ("bridge",), RecallBudget(1, 4, 1, 1, 1, 3))
    digest = resolve_grf_recall(query, field)
    assert digest.selected_shards
    assert all(report.source_fallback_ref for report in digest.coverage_reports)
    assert digest.to_mapping()["recall_miss_scope"] == "current_explicit_grf_workset"
