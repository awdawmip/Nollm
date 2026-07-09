from __future__ import annotations

from grf_runtime_fixture import relation_field
from nollm.grf.coverage_template import COVERAGE_DOWN, COVERAGE_UP
from nollm.grf.recall import QueryProbe, RecallBudget, resolve_grf_recall
from nollm.grf.replay import replay_recall
from nollm.grf.storage import GRFFileStore


def test_replayed_recall_matches_selected_shards_and_path_classes(tmp_path) -> None:
    field = relation_field()
    store = GRFFileStore(tmp_path)
    for idx, placement in enumerate(field.placements):
        store.write_placement_record(placement, f"2026-07-09T10:00:0{idx}+08:00")
    for bridge in field.bridge_kernels:
        store.write_bridge_kernel(bridge)
    query = QueryProbe("query_a", "shard_id", "shard_a", (COVERAGE_UP, COVERAGE_DOWN), RecallBudget(2, 4, 2, 1, 0, 3))
    memory = resolve_grf_recall(query, field)
    replayed = replay_recall(query, tmp_path, "2026-07-09T10:00:10+08:00")
    assert replayed.selected_shards == memory.selected_shards
    assert _path_classes(replayed) == _path_classes(memory)
    assert all(report.source_fallback_ref for report in replayed.coverage_reports)


def _path_classes(digest) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple((report.result, tuple(path.kernel_type for path in report.path)) for report in digest.coverage_reports)
