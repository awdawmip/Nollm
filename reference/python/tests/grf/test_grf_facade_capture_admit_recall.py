from __future__ import annotations

from nollm.grf.admission_bridge import resolve_source_fallback
from nollm.grf.capture import GRFCaptureRequest
from nollm.grf.coverage_template import LATERAL
from nollm.grf.facade import GRFFacade
from nollm.grf.recall import QueryProbe, RecallBudget


def test_facade_capture_admit_recall_round_trip(tmp_path) -> None:
    facade = GRFFacade(tmp_path)
    receipt = facade.capture(GRFCaptureRequest("capture:facade:1", "facade raw content", "validation_fixture", ("source:facade:1",), "2026-07-09T00:00:00Z"))
    assert receipt.status == "captured"

    admitted = facade.admit(receipt.shard_id, "source:facade:1", {"policy_id": "validation_fixture_policy", "chart_id": "chart_facade"}, "2026-07-09T00:00:01Z")
    assert admitted.admission_record is not None

    query = QueryProbe("query:facade:1", "shard_id", receipt.shard_id, (LATERAL,), RecallBudget(0, 1, 0, 1, 0, 1))
    digest = facade.recall(query)
    assert digest.selected_shards == (receipt.shard_id,)
    source = resolve_source_fallback(digest.coverage_reports[0].source_fallback_ref, facade.store)
    assert source.content == "facade raw content"

    report = facade.validate_workspace()
    assert report.evidence_shard_count == 1
    assert report.placement_record_count == 1
    assert report.admission_record_count == 1
