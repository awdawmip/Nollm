from nollm.dream_geometry.recall import resolve_recall

from fixtures.dr1_recall.fixture import build_fixture, query_probe, relative_time_resolution, with_wrong_down_direction


def test_dr1_records_directed_coverage_residuals(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    assert digest.traversal_records
    assert digest.traversal_records[0].direction == "coarse_to_fine"
    assert digest.unresolved_residual_mass >= 0.0


def test_dr1_warns_on_wrong_down_direction_without_geometry_repair(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), with_wrong_down_direction(universe), store, runtime_time=relative_time_resolution())
    assert "DR1_COVERAGE_DOWN_DIRECTION_MISMATCH" in digest.warnings


def test_dr1_gravity_is_tie_break_metadata_not_external_selector(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    assert digest.gravity_guidance_applied is True
    assert digest.items[0].structural_score > 3.0
