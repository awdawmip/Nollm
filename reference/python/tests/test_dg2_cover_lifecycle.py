from dataclasses import replace

import pytest

from nollm.dream_geometry.field import CoverPolicy, CrystallizationDecision, build_local_covers, crystallize_cover
from nollm.dream_geometry.field.types import GrowthTrace
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import CoverState, GrowthBasis, TraceState


def _cell(q: int = 0):
    return make_hex_cell(LocalChart("cover", 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(q, 0))


def _trace(trace_id: str, axis: str, support: str, cell=None, **kwargs) -> GrowthTrace:
    cell = _cell() if cell is None else cell
    return GrowthTrace(
        trace_id=trace_id,
        origin_shard_id=f"shard-{support}",
        proposal_id="proposal",
        parent_trace_id="parent",
        cell=cell,
        axis=axis,
        basis=kwargs.get("basis", GrowthBasis.explicit_in_shard),
        basis_refs=("basis",),
        mass=kwargs.get("mass", 0.3),
        support_key=support,
        genericity=kwargs.get("genericity", 0.1),
        ambiguity=kwargs.get("ambiguity", 0.1),
        conflict=kwargs.get("conflict", 0.0),
        stability_epochs=kwargs.get("stability_epochs", 2),
        state=kwargs.get("state", TraceState.accepted),
        derivation_kind="synthetic",
        geometry_refs=("geometry",),
    )


def test_dg2_c1_two_axes_two_supports_become_stable() -> None:
    cover = build_local_covers((_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2")))[0]
    assert cover.state is CoverState.stable
    assert cover.support_keys == ("s1", "s2")
    assert cover.axes_present == ("location", "phenomenon")


def test_dg2_c2_single_axis_high_mass_remains_candidate() -> None:
    cover = build_local_covers((_trace("t1", "generic", "s1", mass=10.0), _trace("t2", "generic", "s2", mass=10.0)))[0]
    assert cover.state is CoverState.candidate
    assert "insufficient_axis_diversity" in cover.eligibility_reasons


def test_dg2_c3_single_support_remains_candidate() -> None:
    cover = build_local_covers((_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s1")))[0]
    assert cover.state is CoverState.candidate
    assert "insufficient_independent_support" in cover.eligibility_reasons


def test_dg2_c4_provisional_mass_blocks_stability() -> None:
    cover = build_local_covers((_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2", state=TraceState.proposed)))[0]
    assert cover.state is CoverState.candidate
    assert "provisional_mass_present" in cover.eligibility_reasons


def test_dg2_c5_all_quality_failures_are_reported() -> None:
    traces = (
        _trace("t1", "location", "s1", genericity=0.9, ambiguity=0.8, conflict=0.7, stability_epochs=0),
        _trace("t2", "phenomenon", "s2", genericity=0.9, ambiguity=0.8, conflict=0.7, stability_epochs=0),
    )
    cover = build_local_covers(traces)[0]
    assert {"genericity_above_limit", "ambiguity_above_limit", "conflict_above_limit", "stability_below_min"} <= set(cover.eligibility_reasons)


def test_dg2_c6_different_cells_do_not_merge() -> None:
    covers = build_local_covers((_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2", cell=_cell(2))))
    assert len(covers) == 2


def test_dg2_c7_c8_c9_explicit_crystallization_boundary() -> None:
    stable = build_local_covers((_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2")))[0]
    assert stable.state is CoverState.stable
    decision = CrystallizationDecision("d1", stable.cover_id, True, "operator", ("basis",))
    assert crystallize_cover(stable, decision).state is CoverState.crystallized
    with pytest.raises(ValueError):
        crystallize_cover(stable, CrystallizationDecision("d2", "other", True, "operator", ("basis",)))
    candidate = build_local_covers((_trace("t3", "location", "s1"),))[0]
    with pytest.raises(ValueError):
        crystallize_cover(candidate, decision)


def test_dg2_c10_trace_order_does_not_change_cover() -> None:
    traces = (_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    first = build_local_covers(traces)[0]
    second = build_local_covers(tuple(reversed(traces)))[0]
    assert first.cover_id == second.cover_id
    assert first.support_trace_ids == second.support_trace_ids
    assert first.state == second.state
