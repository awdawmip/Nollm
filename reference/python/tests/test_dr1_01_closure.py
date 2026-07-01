from dataclasses import replace

import pytest

from nollm.dream_geometry.cortex.types import CompilationReceipt, QueryBudget
from nollm.dream_geometry.evidence import UsageStateTransition
from nollm.dream_geometry.field.types import CoarseCover, CoverPolicy, VerifiedChartLink
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, CoverageDistribution, CoverageResidual, ResidualReason, compute_distribution
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import CoverState, UsageState
from nollm.dream_geometry.recall import RecallDigestStatus, RecallPolicy, ResolvedRelativeSpan, RuntimeTimeResolution, resolve_recall, validate_recall_universe
from nollm.dream_geometry.recall.types import RecallValidationError

from fixtures.dr1_recall.fixture import add_synthetic_cover, build_fixture, query_probe, relative_time_resolution, with_legacy_proposal_only, with_wrong_down_direction


def _with_higher_duplicate_route_cover(universe):
    base_cover = universe.covers[0]
    source_cell = universe.traces[0].cell
    alt_cell = make_hex_cell(LocalChart("dr1:coarse", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(3, 0))
    alt_cover = replace(base_cover, cover_id="cover:zz-higher", chart_fingerprint=alt_cell.chart_fingerprint, support_cell=alt_cell)
    up = universe.coverage_up[0]
    low_kernel = replace(up.kernels[0], weight=0.25)
    high_kernel = replace(up.kernels[0], target_cell=alt_cell, weight=0.75)
    split_up = replace(up, kernels=(low_kernel, high_kernel), residual=CoverageResidual(0.0, (ResidualReason.numeric_tolerance,)), total_mass=1.0, partition_size=2)
    down = universe.coverage_down[0]
    high_down_kernel = replace(down.kernels[0], source_cell=alt_cell, target_cell=source_cell, weight=1.0)
    high_down = CoverageDistribution(
        alt_cell,
        CoverageDirection.coarse_to_fine,
        (high_down_kernel,),
        CoverageResidual(0.0, (ResidualReason.numeric_tolerance,)),
        1.0,
        1,
    )
    return replace(universe, covers=universe.covers + (alt_cover,), coverage_up=(split_up,), coverage_down=universe.coverage_down + (high_down,), gravity_snapshot=None)


def _distribution(template, source_cell, target_weights, direction):
    kernels = tuple(replace(template, source_cell=source_cell, target_cell=target, direction=direction, weight=weight) for target, weight in target_weights)
    residual = max(0.0, 1.0 - sum(weight for _, weight in target_weights))
    return CoverageDistribution(
        source_cell,
        direction,
        kernels,
        CoverageResidual(residual, (ResidualReason.numeric_tolerance,) if residual == 0.0 else (ResidualReason.outside_supplied_partition,)),
        1.0,
        len(kernels),
    )


def _split_axis_winning_family(universe):
    chart = LocalChart("dr1:family", 0, 1.0, 0.0, Vec2(0, 0))
    trace_cells = {
        "location": make_hex_cell(chart, AxialCoord(0, 0)),
        "phenomenon": make_hex_cell(chart, AxialCoord(3, 0)),
        "absolute_time": make_hex_cell(chart, AxialCoord(6, 0)),
    }
    cover_cells = {
        "cover:f0": make_hex_cell(chart, AxialCoord(0, 3)),
        "cover:f1": make_hex_cell(chart, AxialCoord(3, 3)),
        "cover:f2": make_hex_cell(chart, AxialCoord(6, 3)),
    }
    traces = tuple(replace(trace, cell=trace_cells[trace.axis]) for trace in universe.traces)
    base_cover = universe.covers[0]
    covers = tuple(
        replace(base_cover, cover_id=cover_id, chart_fingerprint=cell.chart_fingerprint, support_cell=cell)
        for cover_id, cell in cover_cells.items()
    )
    up_template = universe.coverage_up[0].kernels[0]
    down_template = universe.coverage_down[0].kernels[0]
    weights_by_axis = {
        "location": (0.8, 0.1, 0.1),
        "phenomenon": (0.1, 0.8, 0.1),
        "absolute_time": (0.1, 0.1, 0.8),
    }
    coverage_up = []
    for trace in traces:
        coverage_up.append(
            _distribution(
                up_template,
                trace.cell,
                tuple((cover.support_cell, weight) for cover, weight in zip(covers, weights_by_axis[trace.axis])),
                CoverageDirection.fine_to_coarse,
            )
        )
    coverage_down = tuple(
        _distribution(
            down_template,
            cover.support_cell,
            tuple((trace.cell, 1.0 / len(traces)) for trace in traces),
            CoverageDirection.coarse_to_fine,
        )
        for cover in covers
    )
    return replace(universe, traces=traces, covers=covers, coverage_up=tuple(coverage_up), coverage_down=coverage_down, gravity_snapshot=None)


def test_t_dr1_101_wrong_k_down_direction_rejected(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), with_wrong_down_direction(universe), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.rejected
    assert "DR1_COVERAGE_DOWN_DIRECTION_MISMATCH" in digest.warnings
    assert digest.primary_evidence == ()


def test_t_dr1_102_removed_k_down_changes_outcome(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), replace(universe, coverage_down=()), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.insufficient_evidence
    assert digest.primary_evidence == ()
    assert "DR1_K_DOWN_REQUIRED" in digest.discarded


def test_t_dr1_103_executed_residual_only_and_mass_accounting(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    extra_source = make_hex_cell(LocalChart("unused", 0, 1.0, 0.0, Vec2(20, 0)), AxialCoord(0, 0))
    extra_target = make_hex_cell(LocalChart("unused:fine", 1, 0.5, 0.0, Vec2(20, 0)), AxialCoord(0, 0))
    extra = compute_distribution(extra_source, (extra_target,), CoverageDirection.coarse_to_fine)
    normal = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    with_extra = resolve_recall(query_probe(), replace(universe, coverage_down=universe.coverage_down + (extra,)), store, runtime_time=relative_time_resolution())
    assert with_extra.unresolved_residual_mass == normal.unresolved_residual_mass
    for record in with_extra.traversal_records:
        if record.phase == "up":
            assert abs((record.mass_out + record.residual_mass) - record.mass_in) <= 1e-9


def test_t_dr1_104_budget_exhaustion_is_explicit(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    probe = replace(query_probe(), budget=QueryBudget(4, 8, 4, 0))
    digest = resolve_recall(probe, universe, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=1))
    assert digest.status is RecallDigestStatus.budget_exhausted
    assert "DR1_BUDGET_MAX_CELLS_PER_LAYER" in digest.discarded


def test_t_dr1_105_106_107_relative_time_strict_binding(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    fabricated = RuntimeTimeResolution((ResolvedRelativeSpan("not_relative_time", "not_in_query", "absolute_time", "2026-06-29", "2026-06-30T08:00:00+08:00", "caller", "bad", 0, 3, "bad"),), True)
    assert resolve_recall(query_probe(), universe, store, runtime_time=fabricated).status is RecallDigestStatus.rejected
    assert resolve_recall(query_probe(relative_time=False), universe, store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected
    duplicate = RuntimeTimeResolution(relative_time_resolution().spans * 2, True)
    assert resolve_recall(query_probe(), universe, store, runtime_time=duplicate).status is RecallDigestStatus.rejected
    partial = RuntimeTimeResolution((), False)
    deferred = resolve_recall(query_probe(), universe, store, runtime_time=partial)
    assert deferred.status is RecallDigestStatus.deferred


def test_t_dr1_108_duplicate_and_bad_receipt_rejected(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    with pytest.raises(RecallValidationError, match="DR1_DUPLICATE_PROPOSAL_ID"):
        validate_recall_universe(replace(universe, proposal_records=universe.proposal_records * 2), store)
    record = universe.proposal_records[0]
    bad_receipt = replace(record.receipt, normalized_payload_fingerprint="sha256:bad")
    bad = replace(universe, proposal_records=(replace(record, receipt=bad_receipt),))
    assert resolve_recall(query_probe(), bad, store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected
    missing = replace(universe, proposal_records=(replace(record, receipt=None),))
    assert resolve_recall(query_probe(), missing, store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected


def test_t_dr1_109_cover_policy_and_support_inconsistency_rejected(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    assert resolve_recall(query_probe(), replace(universe, cover_policy_records=()), store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected
    bad_cover = replace(universe.covers[0], support_keys=("support:absolute_time", "support:location", "support:wrong"))
    assert resolve_recall(query_probe(), replace(universe, covers=(bad_cover,)), store, runtime_time=relative_time_resolution()).status is RecallDigestStatus.rejected


def test_t_dr1_111_gravity_only_breaks_true_ties(tmp_path) -> None:
    store, proposal, universe = build_fixture(tmp_path)
    base = universe.covers[0]
    universe = replace(universe, covers=(replace(base, cover_id="cover:a"),))
    universe = add_synthetic_cover(store, proposal, universe, cover_id="cover:b", shard_id="shard:rain-b", proposal_id="proposal:rain-b", trace_prefix="trace:rain-b")
    low = replace(universe.covers[0], cover_id="cover:low")
    high = replace(universe.covers[1], cover_id="cover:high", mass=universe.covers[1].mass + 0.01)
    non_tie = resolve_recall(query_probe(), replace(universe, covers=(low, high)), store, runtime_time=relative_time_resolution())
    assert [item.cover_id for item in non_tie.primary_evidence][:2] == ["cover:high", "cover:low"]
    tie_a = replace(universe.covers[0], cover_id="cover:a")
    tie_b = replace(universe.covers[1], cover_id="cover:b")
    ignored_gravity = replace(universe.gravity_snapshot, input_cover_ids=("cover:rain",), contributions=(replace(universe.gravity_snapshot.contributions[0], cover_id="cover:b", potential=1000.0),))
    ignored = resolve_recall(query_probe(), replace(universe, covers=(tie_a, tie_b), gravity_snapshot=ignored_gravity), store, runtime_time=relative_time_resolution())
    assert ignored.gravity_guidance_applied is False
    assert "DR1_GRAVITY_SNAPSHOT_IGNORED_IDENTITY_MISMATCH" in ignored.warnings
    gravity = replace(ignored_gravity, input_cover_ids=("cover:a", "cover:b"))
    tied = resolve_recall(query_probe(), replace(universe, covers=(tie_a, tie_b), gravity_snapshot=gravity), store, runtime_time=relative_time_resolution())
    assert [item.cover_id for item in tied.primary_evidence][:2] == ["cover:b", "cover:a"]
    assert tied.gravity_guidance_applied is True


def test_t_501_unrelated_stable_cover_does_not_consume_seed_budget(tmp_path) -> None:
    store, proposal, universe = build_fixture(tmp_path)
    unrelated = add_synthetic_cover(
        store,
        proposal,
        universe,
        cover_id="cover:aaa-unrelated",
        shard_id="shard:unrelated",
        proposal_id="proposal:unrelated",
        trace_prefix="trace:unrelated",
        expressions={"location": "Dali", "phenomenon": "snow", "absolute_time": "2026-01-01"},
    )
    digest = resolve_recall(query_probe(), unrelated, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=1))
    assert digest.status is RecallDigestStatus.resolved
    assert digest.primary_evidence[0].cover_id == "cover:rain"
    assert "DR1_BUDGET_MAX_SEED_COVERS" not in digest.discarded


def test_t_502_exact_seed_candidates_exhaust_seed_budget(tmp_path) -> None:
    store, proposal, universe = build_fixture(tmp_path)
    second_cell = make_hex_cell(LocalChart("dr1:seed-budget", 0, 1.0, 0.0, Vec2(4, 0)), AxialCoord(0, 0))
    two_candidates = add_synthetic_cover(store, proposal, universe, cover_id="cover:aaa-exact", shard_id="shard:exact", proposal_id="proposal:exact", trace_prefix="trace:exact", cell=second_cell)
    digest = resolve_recall(query_probe(), two_candidates, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=1))
    assert digest.status is RecallDigestStatus.budget_exhausted
    assert "DR1_BUDGET_MAX_SEED_COVERS" in digest.discarded
    assert digest.primary_evidence


def test_f_601_same_seed_family_aggregates_shard_level_evidence(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    family = _split_axis_winning_family(universe)
    digest = resolve_recall(query_probe(), family, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=1))
    assert digest.status is RecallDigestStatus.resolved
    assert len(digest.primary_evidence) == 1
    item = digest.primary_evidence[0]
    assert item.shard_id == "shard:rain"
    assert item.matched_axes == ("absolute_time", "location", "phenomenon")
    assert item.cover_ids == ("cover:f0", "cover:f1", "cover:f2")
    assert item.cover_id == "cover:f0"
    assert len(item.route_refs) == 3
    assert any("cover:f0" in route_ref for route_ref in item.route_refs)
    assert any("cover:f1" in route_ref for route_ref in item.route_refs)
    assert any("cover:f2" in route_ref for route_ref in item.route_refs)
    assert "DR1_BUDGET_MAX_SEED_COVERS" not in digest.discarded


def test_f_602_seed_family_aggregation_is_permutation_deterministic(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    family = _split_axis_winning_family(universe)
    digest = resolve_recall(query_probe(), family, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=1))
    permuted_up = tuple(replace(distribution, kernels=tuple(reversed(distribution.kernels))) for distribution in reversed(family.coverage_up))
    permuted = replace(family, traces=tuple(reversed(family.traces)), covers=tuple(reversed(family.covers)), coverage_up=permuted_up, coverage_down=tuple(reversed(family.coverage_down)))
    again = resolve_recall(query_probe(), permuted, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=1))
    assert digest.digest_id == again.digest_id
    assert digest.primary_evidence == again.primary_evidence
    assert digest.discarded == again.discarded


def test_e_401_k_down_must_reach_trace_cell(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    down = universe.coverage_down[0]
    empty_down = CoverageDistribution(
        down.source_cell,
        down.direction,
        (),
        CoverageResidual(1.0, (ResidualReason.outside_supplied_partition,)),
        1.0,
        0,
    )
    digest = resolve_recall(query_probe(), replace(universe, coverage_down=(empty_down,)), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.insufficient_evidence
    assert digest.primary_evidence == ()


def test_e_402_low_k_up_mass_is_reported_not_renormalized(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    up = universe.coverage_up[0]
    low_kernel = replace(up.kernels[0], weight=0.001)
    low_up = replace(up, kernels=(low_kernel,), residual=CoverageResidual(0.999, (ResidualReason.threshold_truncation,)), total_mass=1.0)
    digest = resolve_recall(query_probe(), replace(universe, coverage_up=(low_up,)), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.resolved
    assert {round(record.path_mass, 6) for record in digest.traversal_records if record.phase == "up"} == {0.001}
    assert round(digest.primary_evidence[0].path_mass, 6) == 0.003


def test_e_403_k_up_must_reach_cover_support_cell(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    up = universe.coverage_up[0]
    other = make_hex_cell(LocalChart("dr1:coarse", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(3, 0))
    wrong_kernel = replace(up.kernels[0], target_cell=other)
    wrong_up = replace(up, kernels=(wrong_kernel,))
    digest = resolve_recall(query_probe(), replace(universe, coverage_up=(wrong_up,)), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.insufficient_evidence
    assert digest.primary_evidence == ()


def test_e_404_duplicate_coverage_source_rejected(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    duplicate = replace(universe, coverage_up=universe.coverage_up + universe.coverage_up)
    digest = resolve_recall(query_probe(), duplicate, store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.rejected
    assert "DR1_COVERAGE_DUPLICATE_SOURCE" in digest.warnings


def test_e_406_cross_chart_distribution_requires_verified_link(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    fine_chart = LocalChart("dr1:fine", 1, 0.5, 0.0, Vec2(0, 0))
    fine_cell = make_hex_cell(fine_chart, AxialCoord(0, 0))
    cross_down = compute_distribution(universe.covers[0].support_cell, (fine_cell,), CoverageDirection.coarse_to_fine)
    digest = resolve_recall(query_probe(), replace(universe, coverage_down=(cross_down,)), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.rejected
    assert "DR1_COVERAGE_VERIFIED_CHART_LINK_MISSING" in digest.warnings


def test_e_407_verified_cross_chart_route_is_budget_bound(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    fine_chart = LocalChart("dr1:fine", 1, 0.5, 0.0, Vec2(0, 0))
    fine_cell = make_hex_cell(fine_chart, AxialCoord(0, 0))
    traces = tuple(replace(trace, cell=fine_cell) for trace in universe.traces)
    up = compute_distribution(fine_cell, (universe.covers[0].support_cell,), CoverageDirection.fine_to_coarse)
    down = compute_distribution(universe.covers[0].support_cell, (fine_cell,), CoverageDirection.coarse_to_fine)

    class _Verified:
        state_recommendation = "verified"

    links = (
        VerifiedChartLink(fine_cell.chart_fingerprint, universe.covers[0].support_cell.chart_fingerprint, _Verified()),
        VerifiedChartLink(universe.covers[0].support_cell.chart_fingerprint, fine_cell.chart_fingerprint, _Verified()),
    )
    cross = replace(universe, traces=traces, coverage_up=(up,), coverage_down=(down,), verified_chart_links=links)
    resolved = resolve_recall(query_probe(), cross, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_lateral_hops=2))
    assert resolved.status is RecallDigestStatus.resolved
    assert resolved.primary_evidence
    digest = resolve_recall(query_probe(), cross, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(allow_verified_chart_hops=False))
    assert digest.status is RecallDigestStatus.budget_exhausted
    assert "DR1_BUDGET_MAX_LATERAL_HOPS" in digest.discarded
    capped = resolve_recall(query_probe(), cross, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_lateral_hops=1))
    assert capped.status is RecallDigestStatus.budget_exhausted
    assert "DR1_BUDGET_MAX_LATERAL_HOPS" in capped.discarded


def test_t_504_global_route_identity_keeps_max_path_mass(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    duplicate_routes = _with_higher_duplicate_route_cover(universe)
    digest = resolve_recall(query_probe(), duplicate_routes, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=2))
    assert digest.status is RecallDigestStatus.resolved
    assert digest.primary_evidence[0].cover_id == "cover:zz-higher"
    assert round(digest.primary_evidence[0].path_mass, 6) == 2.25
    assert all("cover:rain" not in route_ref for item in digest.primary_evidence for route_ref in item.route_refs)
    assert any("DR1_ROUTE_DEDUPED_GLOBAL" in item for item in digest.discarded)


def test_f_603_same_shard_same_axis_different_cells_keep_max_axis_route(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    chart = LocalChart("dr1:coarse", 0, 1.0, 0.0, Vec2(0, 0))
    second_cell = make_hex_cell(chart, AxialCoord(3, 0))
    duplicate = replace(universe.traces[0], trace_id="trace:location:second-cell", cell=second_cell, support_key="support:location:second-cell")
    cover = replace(
        universe.covers[0],
        support_trace_ids=universe.covers[0].support_trace_ids + (duplicate.trace_id,),
        support_keys=tuple(sorted(universe.covers[0].support_keys + (duplicate.support_key,))),
    )
    up_template = universe.coverage_up[0].kernels[0]
    down_template = universe.coverage_down[0].kernels[0]
    second_up = _distribution(up_template, second_cell, ((cover.support_cell, 0.5),), CoverageDirection.fine_to_coarse)
    down = _distribution(
        down_template,
        cover.support_cell,
        ((universe.traces[0].cell, 0.6), (second_cell, 0.4)),
        CoverageDirection.coarse_to_fine,
    )
    duplicate_universe = replace(universe, traces=universe.traces + (duplicate,), covers=(cover,), coverage_up=universe.coverage_up + (second_up,), coverage_down=(down,))
    digest = resolve_recall(query_probe(), duplicate_universe, store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.resolved
    assert "trace:location:second-cell" not in digest.primary_evidence[0].trace_ids
    assert any("DR1_AXIS_ROUTE_DEDUPED" in item for item in digest.discarded)


def test_f_607_single_axis_different_shards_do_not_form_multi_axis_evidence(tmp_path) -> None:
    store, proposal, universe = build_fixture(tmp_path)
    second_cell = make_hex_cell(LocalChart("dr1:coarse", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(3, 0))
    with_second = add_synthetic_cover(store, proposal, universe, cover_id="cover:unused-second", shard_id="shard:single-axis", proposal_id="proposal:single-axis", trace_prefix="trace:single-axis", cell=second_cell)
    base_location = with_second.traces[0]
    second_phenomenon = next(trace for trace in with_second.traces if trace.origin_shard_id == "shard:single-axis" and trace.axis == "phenomenon")
    support_cell = make_hex_cell(LocalChart("dr1:coarse", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(6, 0))
    mixed_cover = replace(
        with_second.covers[0],
        cover_id="cover:mixed-single-axis",
        chart_fingerprint=support_cell.chart_fingerprint,
        support_cell=support_cell,
        support_trace_ids=(base_location.trace_id, second_phenomenon.trace_id),
        support_shard_ids=tuple(sorted((base_location.origin_shard_id, second_phenomenon.origin_shard_id))),
        support_keys=tuple(sorted((base_location.support_key, second_phenomenon.support_key))),
        axes_present=tuple(sorted((base_location.axis, second_phenomenon.axis))),
    )
    up_template = universe.coverage_up[0].kernels[0]
    down_template = universe.coverage_down[0].kernels[0]
    coverage_up = (
        _distribution(up_template, base_location.cell, ((support_cell, 1.0),), CoverageDirection.fine_to_coarse),
        _distribution(up_template, second_phenomenon.cell, ((support_cell, 1.0),), CoverageDirection.fine_to_coarse),
    )
    coverage_down = (_distribution(down_template, support_cell, ((base_location.cell, 0.5), (second_phenomenon.cell, 0.5)), CoverageDirection.coarse_to_fine),)
    mixed = replace(with_second, traces=(base_location, second_phenomenon), covers=(mixed_cover,), coverage_up=coverage_up, coverage_down=coverage_down, gravity_snapshot=None)
    digest = resolve_recall(query_probe(), mixed, store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.insufficient_evidence
    assert digest.primary_evidence == ()
    assert sum("DR1_INSUFFICIENT_POST_DEDUP_AXIS_MATCH" in item for item in digest.discarded) == 2


def test_t_505_global_cell_budget_applies_across_selected_covers(tmp_path) -> None:
    store, proposal, universe = build_fixture(tmp_path)
    second_cell = make_hex_cell(LocalChart("dr1:second", 0, 1.0, 0.0, Vec2(4, 0)), AxialCoord(0, 0))
    two_cells = add_synthetic_cover(store, proposal, universe, cover_id="cover:second-cell", shard_id="shard:second-cell", proposal_id="proposal:second-cell", trace_prefix="trace:second-cell", cell=second_cell)
    probe = replace(query_probe(), budget=QueryBudget(4, 8, 4, 1))
    digest = resolve_recall(probe, two_cells, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=2))
    assert digest.status is RecallDigestStatus.budget_exhausted
    assert "DR1_BUDGET_MAX_CELLS_PER_LAYER" in digest.discarded
    assert digest.primary_evidence == ()


def test_t_506_global_accounting_is_permutation_deterministic(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    duplicate_routes = _with_higher_duplicate_route_cover(universe)
    digest = resolve_recall(query_probe(), duplicate_routes, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=2))
    permuted_up = replace(duplicate_routes.coverage_up[0], kernels=tuple(reversed(duplicate_routes.coverage_up[0].kernels)))
    permuted = replace(
        duplicate_routes,
        traces=tuple(reversed(duplicate_routes.traces)),
        covers=tuple(reversed(duplicate_routes.covers)),
        coverage_up=(permuted_up,),
        coverage_down=tuple(reversed(duplicate_routes.coverage_down)),
    )
    again = resolve_recall(query_probe(), permuted, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(max_seed_covers=2))
    assert digest.digest_id == again.digest_id
    assert digest.primary_evidence == again.primary_evidence
    assert digest.traversal_records == again.traversal_records
    assert digest.discarded == again.discarded


def test_e_414_ghost_interpretation_context_rejected(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    ghost = replace(universe.interpretation_records[0], statement="Caller supplied ghost context.")
    digest = resolve_recall(query_probe(), replace(universe, interpretation_records=(ghost,)), store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.rejected
    assert "DR1_CONTEXT_INTERPRETATION_PAYLOAD_MISMATCH" in digest.warnings


def test_e_415_interpretation_usage_policy_controls_context(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    interpretation_id = universe.interpretation_records[0].interpretation_id
    store.record_usage_transition(UsageStateTransition("state:interp:retired", interpretation_id, UsageState.tentative, UsageState.retired, ("reason:fixture",), "2026-06-30T08:02:00+08:00"))
    default_digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    assert interpretation_id not in default_digest.primary_evidence[0].context_record_ids
    included = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_retired_context=True))
    assert interpretation_id in included.primary_evidence[0].context_record_ids


def test_t_dr1_112_primary_context_evidence_partition(tmp_path) -> None:
    tentative_store, _, tentative_universe = build_fixture(tmp_path / "tentative", usage_state=UsageState.tentative)
    tentative = resolve_recall(query_probe(), tentative_universe, tentative_store, runtime_time=relative_time_resolution())
    assert tentative.primary_evidence[0].qualification.tier == "primary_tentative"
    closed = resolve_recall(query_probe(), tentative_universe, tentative_store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_tentative_primary=False))
    assert closed.primary_evidence == ()
    retired_store, _, retired_universe = build_fixture(tmp_path / "retired", usage_state=UsageState.retired)
    retired = resolve_recall(query_probe(), retired_universe, retired_store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_retired_context=True))
    assert retired.contextual_evidence[0].qualification.tier == "context_retired"
    rejected_store, _, rejected_universe = build_fixture(tmp_path / "rejected", usage_state=UsageState.rejected)
    rejected = resolve_recall(query_probe(), rejected_universe, rejected_store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_rejected_context=True))
    assert rejected.contextual_evidence[0].qualification.tier == "context_rejected"


def test_t_dr1_113_missing_shard_no_ghost_evidence(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    bad_trace = replace(universe.traces[0], trace_id="trace:missing", origin_shard_id="shard:missing")
    bad_universe = replace(universe, traces=(bad_trace,) + universe.traces[1:], covers=(replace(universe.covers[0], support_trace_ids=(bad_trace.trace_id,) + universe.covers[0].support_trace_ids[1:]),))
    digest = resolve_recall(query_probe(), bad_universe, store, runtime_time=relative_time_resolution())
    assert digest.status is RecallDigestStatus.rejected
    assert digest.primary_evidence == ()


def test_t_dr1_116_current_and_legacy_mixed_legacy_does_not_seed(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    legacy = with_legacy_proposal_only(universe).proposal_records[0]
    legacy = replace(legacy, proposal=replace(legacy.proposal, proposal_id="proposal:legacy"), source_ref="legacy")
    mixed = replace(universe, proposal_records=universe.proposal_records + (legacy,))
    digest = resolve_recall(query_probe(), mixed, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_legacy_context=True))
    assert digest.primary_evidence
    assert all(item.cover_id == "cover:rain" for item in digest.primary_evidence)
    assert "DR1_LEGACY_PROPOSALS_CONTEXT_ONLY" in digest.warnings


def test_t_dr1_115_117_deterministic_and_no_write_api(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    digest = resolve_recall(query_probe(), universe, store, runtime_time=relative_time_resolution())
    permuted = replace(universe, traces=tuple(reversed(universe.traces)), covers=tuple(reversed(universe.covers)), coverage_up=tuple(reversed(universe.coverage_up)))
    again = resolve_recall(query_probe(), permuted, store, runtime_time=relative_time_resolution())
    assert digest.primary_evidence == again.primary_evidence
    import nollm.dream_geometry.recall as recall

    assert not any(name.startswith(("write", "cache")) for name in dir(recall))
