from nollm.dream_geometry.evidence import canonical_json
from nollm.dream_geometry.recall import resolve_recall

from fixtures.dr1_recall.fixture import build_fixture, query_probe, relative_time_resolution


def test_dr1_resolution_does_not_mutate_evidence_store(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    before = (canonical_json(store.get_dream_shard("shard:rain")), store.read_ledger(), store.state_projection())
    resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    after = (canonical_json(store.get_dream_shard("shard:rain")), store.read_ledger(), store.state_projection())
    assert after == before


def test_dr1_consumes_sealed_objects_without_recompiling_or_rebuilding_field(tmp_path) -> None:
    store, proposal, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    assert universe.proposal_records[0].proposal is proposal
    assert digest.items[0].trace_ids == ("trace:absolute_time", "trace:location", "trace:phenomenon")
