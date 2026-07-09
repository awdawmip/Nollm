from __future__ import annotations

from grf_runtime_fixture import relation_field
from nollm.grf.coverage_template import COVERAGE_DOWN, COVERAGE_UP
from nollm.grf.recall import QueryProbe, RecallBudget, resolve_grf_recall


def test_coverage_report_contains_path_drift_and_fallback() -> None:
    field = relation_field()
    query = QueryProbe("query_a", "shard_id", "shard_a", (COVERAGE_UP, COVERAGE_DOWN), RecallBudget(2, 4, 2, 1, 0, 3))
    digest = resolve_grf_recall(query, field)
    reports = {report.result: report for report in digest.coverage_reports}
    assert reports["shard_b"].path
    assert reports["shard_b"].drift["steps"] >= 1
    assert reports["shard_b"].source_fallback_ref == "source:b"
    assert reports["shard_b"].to_mapping()["path"][0]["path_is_not_proof"] is True
