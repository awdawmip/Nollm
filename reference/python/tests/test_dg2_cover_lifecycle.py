from dataclasses import replace

import pytest

from nollm.dream_geometry.field import CoverPolicy, CrystallizationDecision, build_local_covers, crystallize_cover, evaluate_cover_eligibility
from nollm.dream_geometry.field.types import CoarseCover, GrowthTrace
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


def test_dg2_1_t202_policy_cannot_relax_structural_floors() -> None:
    with pytest.raises(ValueError, match="min_independent_support"):
        CoverPolicy(min_independent_support=1)
    with pytest.raises(ValueError, match="min_axes"):
        CoverPolicy(min_axes=1)
    with pytest.raises(ValueError, match="max_provisional_mass"):
        CoverPolicy(max_provisional_mass=0.1)


def test_dg2_1_t203_provisional_never_crystallizes() -> None:
    cover = build_local_covers(
        (
            _trace("t1", "location", "s1"),
            _trace("t2", "phenomenon", "s2", basis=GrowthBasis.provisional_llm_generalization, basis_refs=("basis",), state=TraceState.proposed),
        )
    )[0]
    assert cover.state is CoverState.candidate
    assert "provisional_mass_present" in cover.eligibility_reasons
    with pytest.raises(ValueError, match="stable covers"):
        crystallize_cover(cover, CrystallizationDecision("d-provisional", cover.cover_id, True, "operator", ("basis",)))


def test_dg2_1_t204_duplicate_trace_id_rejected_for_covers() -> None:
    trace = _trace("same", "location", "s1")
    with pytest.raises(ValueError, match="duplicate trace_id"):
        build_local_covers((trace, trace))
    forged = replace(trace, axis="phenomenon", support_key="s2")
    with pytest.raises(ValueError, match="duplicate trace_id"):
        build_local_covers((trace, forged))


def test_dg2_1_t206_policy_identity_enters_cover_id() -> None:
    traces = (_trace("t1", "location", "s1", mass=0.3), _trace("t2", "phenomenon", "s2", mass=0.3))
    strict = build_local_covers(traces, CoverPolicy(policy_id="strict", version="1", min_total_mass=1.0))[0]
    loose = build_local_covers(traces, CoverPolicy(policy_id="loose", version="1", min_total_mass=0.1))[0]
    assert strict.cover_id != loose.cover_id
    assert strict.policy_id == "strict"
    assert loose.policy_id == "loose"
    assert strict.state != loose.state


def test_dg2_1_t206_policy_semantics_enter_cover_id() -> None:
    traces = (_trace("t1", "location", "s1", mass=0.3), _trace("t2", "phenomenon", "s2", mass=0.3))
    lower = build_local_covers(traces, CoverPolicy(policy_id="same", version="1", min_total_mass=0.1))[0]
    higher = build_local_covers(traces, CoverPolicy(policy_id="same", version="1", min_total_mass=1.0))[0]
    assert lower.cover_id != higher.cover_id


def test_dg2_1_t207_policy_mismatch_rejected() -> None:
    traces = (_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s2"))
    cover = build_local_covers(traces, CoverPolicy(policy_id="strict", version="1"))[0]
    with pytest.raises(ValueError, match="policy identity mismatch"):
        evaluate_cover_eligibility(cover, CoverPolicy(policy_id="loose", version="1"), traces)


def test_dg2_2_t210_forged_stable_provisional_cover_rejected() -> None:
    candidate = build_local_covers(
        (
            _trace("t1", "location", "s1"),
            _trace("t2", "phenomenon", "s2", basis=GrowthBasis.provisional_llm_generalization, state=TraceState.proposed),
        )
    )[0]
    assert candidate.state is CoverState.candidate
    with pytest.raises(ValueError, match="provisional"):
        replace(candidate, state=CoverState.stable)
    forged = _forge_cover(candidate, state=CoverState.stable)
    with pytest.raises(ValueError, match="provisional"):
        crystallize_cover(forged, CrystallizationDecision("d-forged-provisional", forged.cover_id, True, "operator", ("basis",)))


def test_dg2_2_t211_forged_stable_single_support_or_axis_rejected() -> None:
    single_support = build_local_covers((_trace("t1", "location", "s1"), _trace("t2", "phenomenon", "s1")))[0]
    single_axis = build_local_covers((_trace("t3", "generic", "s1"), _trace("t4", "generic", "s2")))[0]
    with pytest.raises(ValueError, match="support"):
        replace(single_support, state=CoverState.stable)
    with pytest.raises(ValueError, match="axis"):
        replace(single_axis, state=CoverState.stable)
    with pytest.raises(ValueError, match="support"):
        replace(single_support, state=CoverState.crystallized)
    with pytest.raises(ValueError, match="axis"):
        replace(single_axis, state=CoverState.crystallized)
    with pytest.raises(ValueError, match="support"):
        crystallize_cover(_forge_cover(single_support, state=CoverState.stable), CrystallizationDecision("d-support", single_support.cover_id, True, "operator", ("basis",)))
    with pytest.raises(ValueError, match="axis"):
        crystallize_cover(_forge_cover(single_axis, state=CoverState.stable), CrystallizationDecision("d-axis", single_axis.cover_id, True, "operator", ("basis",)))


def test_dg2_2_t212_policy_semantic_mismatch_rejected() -> None:
    traces = (_trace("t1", "location", "s1", mass=0.3), _trace("t2", "phenomenon", "s2", mass=0.3))
    strict_policy = CoverPolicy(policy_id="same", version="1", min_total_mass=1.0)
    loose_policy = CoverPolicy(policy_id="same", version="1", min_total_mass=0.1)
    cover = build_local_covers(traces, strict_policy)[0]
    loose_cover = build_local_covers(traces, loose_policy)[0]
    assert strict_policy.policy_fingerprint != loose_policy.policy_fingerprint
    assert cover.policy_fingerprint == strict_policy.policy_fingerprint
    assert cover.cover_id != loose_cover.cover_id
    with pytest.raises(ValueError, match="policy identity mismatch"):
        evaluate_cover_eligibility(cover, loose_policy, traces)


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


def _forge_cover(cover: CoarseCover, **changes) -> CoarseCover:
    values = {field: getattr(cover, field) for field in cover.__dataclass_fields__}
    values.update(changes)
    forged = object.__new__(CoarseCover)
    for field, value in values.items():
        object.__setattr__(forged, field, value)
    return forged
