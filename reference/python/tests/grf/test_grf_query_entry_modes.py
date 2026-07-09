from __future__ import annotations

from nollm.grf.admission_bridge import resolve_source_fallback
from nollm.grf.capture import GRFCaptureRequest
from nollm.grf.coverage_template import LATERAL
from nollm.grf.facade import GRFFacade
from nollm.grf.recall import QueryProbe, RecallBudget


def test_facade_recall_supports_all_public_entry_modes(tmp_path) -> None:
    facade = GRFFacade(tmp_path)
    receipt = facade.capture(GRFCaptureRequest("capture:entry:modes", "entry mode content", "validation_fixture", ("source:entry:modes",), "2026-07-09T00:00:00Z"))
    result = facade.admit(receipt.shard_id, "source:entry:modes", {"policy_id": "grf_deterministic_policy_v1"}, "2026-07-09T00:00:01Z")
    placement = result.placement_record
    admission = result.admission_record
    budget = RecallBudget(0, 1, 0, 1, 0, 1)
    entries = (
        ("explicit_cell", placement.geometry_mark.cell),
        ("shard_id", receipt.shard_id),
        ("island_id", placement.island_id),
        ("patch_id", placement.patch_id),
        ("source_window", "source:entry:modes"),
        ("admission_id", admission.admission_id),
        ("placement_id", placement.placement_id),
    )

    for mode, ref in entries:
        digest = facade.recall(QueryProbe(f"query:{mode}", mode, ref, (LATERAL,), budget))
        assert digest.selected_shards == (receipt.shard_id,)
        source = resolve_source_fallback(digest.coverage_reports[0].source_fallback_ref, facade.store)
        assert source.content == "entry mode content"
