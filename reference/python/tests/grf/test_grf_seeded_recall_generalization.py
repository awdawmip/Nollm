from __future__ import annotations

from nollm.grf.admission_bridge import resolve_source_fallback
from nollm.grf.capture import GRFCaptureRequest
from nollm.grf.coverage_template import LATERAL
from nollm.grf.facade import GRFFacade
from nollm.grf.recall import QueryProbe, RecallBudget


def test_seeded_recall_generalization_replay_equality_and_fallbacks(tmp_path) -> None:
    seeds = tuple(range(20))
    budget = RecallBudget(0, 1, 0, 1, 0, 1)
    for seed in seeds:
        facade = GRFFacade(tmp_path / f"seed_{seed}")
        receipt = facade.capture(GRFCaptureRequest(f"capture:seed:{seed}", f"seeded content {seed}", "validation_fixture", (f"source:seed:{seed}",), "2026-07-09T00:00:00Z"))
        result = facade.admit(receipt.shard_id, f"source:seed:{seed}", {"policy_id": "grf_deterministic_policy_v1", "chart_id": f"chart_seed_{seed}"}, "2026-07-09T00:00:01Z")
        modes = (
            ("shard_id", receipt.shard_id),
            ("island_id", result.placement_record.island_id),
            ("patch_id", result.placement_record.patch_id),
            ("source_window", f"source:seed:{seed}"),
            ("admission_id", result.admission_record.admission_id),
            ("placement_id", result.placement_record.placement_id),
        )
        mode, ref = modes[seed % len(modes)]
        query = QueryProbe(f"query:seed:{seed}", mode, ref, (LATERAL,), budget)
        digest = facade.recall(query)
        replayed = facade.replay_recall(query)
        assert digest.selected_shards == replayed.selected_shards
        assert tuple(report.coverage_class for report in digest.coverage_reports) == tuple(report.coverage_class for report in replayed.coverage_reports)
        assert digest.coverage_reports
        for report in digest.coverage_reports:
            source = resolve_source_fallback(report.source_fallback_ref, facade.store)
            assert source.content == f"seeded content {seed}"
