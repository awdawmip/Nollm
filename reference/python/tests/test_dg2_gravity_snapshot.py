from dataclasses import replace

import pytest

from nollm.dream_geometry.field import GravityPolicy, build_local_covers, calculate_gravity_snapshot
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import CoverState, GrowthBasis, TraceState
from tests.test_dg2_cover_lifecycle import _trace


def _stable_cover(*traces):
    return build_local_covers(traces)[0]


def test_dg2_g1_candidate_cover_produces_no_contribution() -> None:
    candidate = build_local_covers((_trace("t1", "generic", "s1", mass=10.0), _trace("t2", "generic", "s2", mass=10.0)))[0]
    snapshot = calculate_gravity_snapshot((candidate,))
    assert snapshot.contributions == ()


def test_dg2_g2_stable_cover_has_auditable_breakdown() -> None:
    cover = _stable_cover(_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    contribution = calculate_gravity_snapshot((cover,)).contributions[0]
    assert contribution.cover_id == cover.cover_id
    assert contribution.support_term > 0
    assert {name for name, _ in contribution.penalty_terms} == {"genericity", "ambiguity", "conflict", "congestion"}


def test_dg2_g3_order_invariance() -> None:
    first = _stable_cover(_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    second = _stable_cover(_trace("t3", "location", "s3", cell=make_hex_cell(LocalChart("cover", 0, 1.0, 0, Vec2(0, 0)), AxialCoord(2, 0))), _trace("t4", "phenomenon", "s4", cell=make_hex_cell(LocalChart("cover", 0, 1.0, 0, Vec2(0, 0)), AxialCoord(2, 0))))
    assert calculate_gravity_snapshot((first, second)).snapshot_id == calculate_gravity_snapshot((second, first)).snapshot_id


def test_dg2_1_t205_duplicate_cover_id_rejected() -> None:
    cover = _stable_cover(_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    with pytest.raises(ValueError, match="duplicate cover_id"):
        calculate_gravity_snapshot((cover, cover))


def test_dg2_g4_g5_penalties_do_not_increase_potential() -> None:
    base = _stable_cover(_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    generic = replace(base, cover_id="generic", genericity=base.genericity + 0.2)
    ambiguous = replace(base, cover_id="ambiguous", ambiguity=base.ambiguity + 0.2)
    conflicted = replace(base, cover_id="conflicted", conflict=base.conflict + 0.2)
    base_p = calculate_gravity_snapshot((base,)).contributions[0].potential
    assert calculate_gravity_snapshot((generic,)).contributions[0].potential <= base_p
    assert calculate_gravity_snapshot((ambiguous,)).contributions[0].potential <= base_p
    assert calculate_gravity_snapshot((conflicted,)).contributions[0].potential <= base_p


def test_dg2_g6_more_support_or_axes_does_not_lower_potential() -> None:
    two = _stable_cover(_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    three = _stable_cover(_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"), _trace("t3", "method", "s3"))
    assert calculate_gravity_snapshot((three,)).contributions[0].potential >= calculate_gravity_snapshot((two,)).contributions[0].potential


def test_dg2_g7_neighbor_congestion_cannot_improve_potential() -> None:
    chart = LocalChart("cover", 0, 1.0, 0, Vec2(0, 0))
    base = _stable_cover(_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    neighbor_cell = make_hex_cell(chart, AxialCoord(1, 0))
    neighbor = _stable_cover(_trace("t3", "location", "s3", cell=neighbor_cell), _trace("t4", "phenomenon", "s4", cell=neighbor_cell))
    alone = calculate_gravity_snapshot((base,)).contributions[0].potential
    crowded = next(item for item in calculate_gravity_snapshot((base, neighbor)).contributions if item.cover_id == base.cover_id).potential
    assert crowded <= alone


def test_dg2_g8_high_mass_generic_single_axis_forms_no_well() -> None:
    candidate = build_local_covers((_trace("t1", "generic", "s1", mass=100, genericity=1.0), _trace("t2", "generic", "s2", mass=100, genericity=1.0)))[0]
    assert candidate.state is CoverState.candidate
    assert calculate_gravity_snapshot((candidate,)).contributions == ()


def test_dg2_g9_policy_change_changes_snapshot_metadata() -> None:
    cover = _stable_cover(_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    first = calculate_gravity_snapshot((cover,), GravityPolicy(version="1"))
    second = calculate_gravity_snapshot((cover,), GravityPolicy(version="2"))
    assert first.policy_version != second.policy_version
    assert first.snapshot_id != second.snapshot_id
