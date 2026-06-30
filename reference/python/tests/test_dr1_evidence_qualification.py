from nollm.dream_geometry.protocol.contracts import UsageState
from nollm.dream_geometry.recall import RecallPolicy, resolve_recall

from fixtures.dr1_recall.fixture import build_fixture, query_probe, relative_time_resolution


def test_dr1_active_evidence_is_primary_and_context_is_listed(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path, usage_state=UsageState.active)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    item = digest.items[0]
    assert item.qualification.tier == "primary_active"
    assert item.context_record_ids == ("interpretation:rain-context", "revision:rain")


def test_dr1_retired_evidence_is_context_only_by_policy(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path, usage_state=UsageState.retired)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    assert digest.items == ()
    assert "shard:rain:DR1_USAGE_STATE_EXCLUDED" in digest.discarded
    context_digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_retired_context=True))
    assert context_digest.items[0].qualification.tier == "context_retired"
