from nollm.dream_geometry.recall import RecallDigestStatus, resolve_recall

from fixtures.dr1_recall.fixture import build_fixture, query_probe, relative_time_resolution


def test_dr1_exact_projection_resolves_ephemeral_digest(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.resolved
    assert digest.ephemeral is True
    assert digest.items[0].shard_id == "shard:rain"
    assert digest.items[0].matched_axes == ("absolute_time", "location", "phenomenon")
    assert digest.metadata["storage"] == "ephemeral"


def test_dr1_generic_one_axis_query_does_not_seed_recall(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(relative_time=False, one_axis=True), universe, store)
    assert digest.items == ()
    assert "cover:rain:DR1_INSUFFICIENT_EXACT_AXIS_MATCH" in digest.discarded
