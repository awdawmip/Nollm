from __future__ import annotations

from nollm.grf.admission_bridge import GRFAdmissionBridge, MissingSourceFallback, resolve_source_fallback
from nollm.grf.capture import GRFCaptureIngress, GRFCaptureRequest
from nollm.grf.cell_address import CellAddress
from nollm.grf.coverage_template import LATERAL
from nollm.grf.recall import QueryProbe, RecallBudget, resolve_grf_recall
from nollm.grf.replay import rebuild_relation_field_from_files, replay_recall
from nollm.grf.source_window import SourceWindowRecord
from nollm.grf.storage import GRFFileStore


def test_recall_digest_source_fallback_resolves_original_content(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    window = SourceWindowRecord("window:recall:1", "validation_fixture", ("fixture:recall",), "2026-07-09T00:00:00Z")
    store.write_source_window(window, "2026-07-09T00:00:00Z")
    raw_content = "Mercury planet is distinct from mercury element in this fixture."
    receipt = GRFCaptureIngress(store).capture(GRFCaptureRequest("capture:recall:1", raw_content, "validation_fixture", (window.window_id,), "2026-07-09T00:00:01Z"))
    shard = store.read_evidence_shard(receipt.shard_id)
    target = CellAddress("eisenstein_exact_v1", "chart_recall", 0, 2, -1)
    result = GRFAdmissionBridge(store).admit(shard, window, {"policy_id": "validation_fixture_policy", "target_cell": target}, "2026-07-09T00:00:02Z")

    field = rebuild_relation_field_from_files(tmp_path)
    query = QueryProbe("query:recall:1", "shard_id", shard.shard_id, (LATERAL,), RecallBudget(0, 1, 0, 1, 0, 1))
    digest = resolve_grf_recall(query, field)
    replayed = replay_recall(query, tmp_path, "2026-07-09T00:00:03Z")

    assert digest.selected_shards == (shard.shard_id,)
    assert replayed.selected_shards == digest.selected_shards
    assert tuple(report.coverage_class for report in replayed.coverage_reports) == tuple(report.coverage_class for report in digest.coverage_reports)
    fallback = resolve_source_fallback(digest.coverage_reports[0].source_fallback_ref, store)
    assert fallback == shard
    assert fallback.content == raw_content
    assert result.placement_record.source_fallback_refs == (shard.shard_id,)


def test_missing_source_fallback_returns_explicit_error(tmp_path) -> None:
    missing = resolve_source_fallback("shard:missing", GRFFileStore(tmp_path))
    assert isinstance(missing, MissingSourceFallback)
    assert missing.error == "missing_source"
