from nollm.dream_geometry.recall import RecallDigestStatus, resolve_recall

from fixtures.dr1_recall.fixture import build_fixture, query_probe, relative_time_resolution


def test_dr1_relative_time_requires_runtime_resolution(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), universe, store)
    assert digest.status is RecallDigestStatus.deferred
    assert digest.items == ()
    assert "DEFERRED_TIME_RESOLUTION_REQUIRED" in digest.warnings


def test_dr1_relative_time_runtime_resolution_participates_as_exact_atom(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.resolved
    assert digest.items[0].matched_axes == ("absolute_time", "location", "phenomenon")
