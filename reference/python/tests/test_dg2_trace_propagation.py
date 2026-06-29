from dataclasses import replace

import pytest

from nollm.dream_geometry.field import TraceSeed, VerifiedChartLink, propagate_trace, seed_to_trace
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.coverage import CoverageDirection, compute_distribution
from nollm.dream_geometry.geometry.hexgrid import disk
from nollm.dream_geometry.geometry.transform import SimilarityTransform, TransformWitness, validate_transform
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import GrowthBasis, TraceState


def _chart(name: str, layer: int, side: float) -> LocalChart:
    return LocalChart(name, layer, side, 0.0, Vec2(0, 0))


def _seed(cell, trace_id: str = "seed") -> TraceSeed:
    return TraceSeed(
        trace_id=trace_id,
        shard_id=f"shard-{trace_id}",
        proposal_id="proposal",
        source_cell=cell,
        axis="location",
        basis=GrowthBasis.explicit_in_shard,
        basis_refs=("basis:1",),
        mass=1.0,
        support_key=f"support-{trace_id}",
        genericity=0.1,
        ambiguity=0.1,
        conflict=0.0,
        stability_epochs=2,
        state=TraceState.accepted,
    )


def _link(source, target) -> VerifiedChartLink:
    witnesses = (
        TransformWitness(Vec2(0, 0), Vec2(0, 0)),
        TransformWitness(Vec2(1, 0), Vec2(1, 0)),
        TransformWitness(Vec2(0, 1), Vec2(0, 1)),
    )
    validation = validate_transform(SimilarityTransform(1.0, 0.0, Vec2(0, 0)), witnesses, 1.0)
    return VerifiedChartLink(source.chart_fingerprint, target.chart_fingerprint, validation)


def test_dg2_t1_single_hop_conserves_mass_with_residual() -> None:
    chart = _chart("same", 0, 1.0)
    cell = make_hex_cell(chart, AxialCoord(0, 0))
    parent = seed_to_trace(_seed(cell))
    distribution = compute_distribution(cell, (cell,), CoverageDirection.fine_to_coarse, threshold=1.1)
    result = propagate_trace(parent, distribution)
    assert result.derived_mass + result.residual.mass == result.parent_mass
    assert result.accounting_error <= 1e-12
    assert result.residual.reasons == ("threshold_truncation",)


def test_dg2_1_t201_tiny_positive_mass_materializes() -> None:
    chart = _chart("tiny", 0, 1.0)
    cell = make_hex_cell(chart, AxialCoord(0, 0))
    parent = replace(seed_to_trace(_seed(cell)), mass=1e-13)
    distribution = compute_distribution(cell, (cell,), CoverageDirection.fine_to_coarse)
    result = propagate_trace(parent, distribution)
    assert len(result.derived_traces) == 1
    assert result.derived_traces[0].mass == 1e-13
    assert result.residual.mass == 0.0
    assert result.derived_mass + result.residual.mass == result.parent_mass
    assert result.accounting_error == 0.0


def test_dg2_t3_target_order_does_not_change_output_ids() -> None:
    fine = _chart("fine", 1, 0.5)
    coarse = _chart("coarse", 0, 1.0)
    source = make_hex_cell(fine, AxialCoord(0, 0))
    parent = seed_to_trace(_seed(source))
    targets = tuple(make_hex_cell(coarse, axial) for axial in disk(AxialCoord(0, 0), 2))
    first = propagate_trace(parent, compute_distribution(source, targets, CoverageDirection.fine_to_coarse), _link(source, targets[0]))
    second = propagate_trace(parent, compute_distribution(source, tuple(reversed(targets)), CoverageDirection.fine_to_coarse), _link(source, targets[0]))
    assert tuple(trace.trace_id for trace in first.derived_traces) == tuple(trace.trace_id for trace in second.derived_traces)
    assert tuple(trace.mass for trace in first.derived_traces) == tuple(trace.mass for trace in second.derived_traces)


def test_dg2_t4_source_cell_mismatch_rejected() -> None:
    chart = _chart("same", 0, 1.0)
    source = make_hex_cell(chart, AxialCoord(0, 0))
    other = make_hex_cell(chart, AxialCoord(1, 0))
    parent = seed_to_trace(_seed(other))
    distribution = compute_distribution(source, (source,), CoverageDirection.fine_to_coarse)
    with pytest.raises(ValueError, match="source cell"):
        propagate_trace(parent, distribution)


def test_dg2_t5_coarse_to_fine_rejected() -> None:
    chart = _chart("same", 0, 1.0)
    cell = make_hex_cell(chart, AxialCoord(0, 0))
    parent = seed_to_trace(_seed(cell))
    distribution = compute_distribution(cell, (cell,), CoverageDirection.coarse_to_fine)
    with pytest.raises(ValueError, match="fine_to_coarse"):
        propagate_trace(parent, distribution)


def test_dg2_t6_cross_chart_requires_verified_matching_link() -> None:
    fine = _chart("fine", 1, 0.5)
    coarse = _chart("coarse", 0, 1.0)
    source = make_hex_cell(fine, AxialCoord(0, 0))
    target = make_hex_cell(coarse, AxialCoord(0, 0))
    parent = seed_to_trace(_seed(source))
    distribution = compute_distribution(source, (target,), CoverageDirection.fine_to_coarse)
    with pytest.raises(ValueError, match="requires verified chart link"):
        propagate_trace(parent, distribution)
    bad_link = _link(target, source)
    with pytest.raises(ValueError, match="source fingerprint"):
        propagate_trace(parent, distribution, bad_link)


def test_dg2_t7_verified_cross_chart_link_allows_propagation() -> None:
    fine = _chart("fine", 1, 0.5)
    coarse = _chart("coarse", 0, 1.0)
    source = make_hex_cell(fine, AxialCoord(0, 0))
    target = make_hex_cell(coarse, AxialCoord(0, 0))
    parent = seed_to_trace(_seed(source))
    result = propagate_trace(parent, compute_distribution(source, (target,), CoverageDirection.fine_to_coarse), _link(source, target))
    assert result.derived_traces
    assert all(trace.parent_trace_id == parent.trace_id for trace in result.derived_traces)


def test_dg2_t8_provisional_seed_never_generates_accepted_trace() -> None:
    cell = make_hex_cell(_chart("same", 0, 1.0), AxialCoord(0, 0))
    seed = replace(_seed(cell), state=TraceState.proposed, basis=GrowthBasis.provisional_llm_generalization, basis_refs=("basis:provisional",))
    parent = seed_to_trace(seed)
    result = propagate_trace(parent, compute_distribution(cell, (cell,), CoverageDirection.fine_to_coarse))
    assert {trace.state for trace in result.derived_traces} == {TraceState.proposed}


def test_dg2_t9_recompute_is_stable_but_different_parent_changes_id() -> None:
    cell = make_hex_cell(_chart("same", 0, 1.0), AxialCoord(0, 0))
    distribution = compute_distribution(cell, (cell,), CoverageDirection.fine_to_coarse)
    first_parent = seed_to_trace(_seed(cell, "a"))
    second_parent = seed_to_trace(_seed(cell, "b"))
    first = propagate_trace(first_parent, distribution)
    repeat = propagate_trace(first_parent, distribution)
    second = propagate_trace(second_parent, distribution)
    assert first.derived_traces[0].trace_id == repeat.derived_traces[0].trace_id
    assert first.derived_traces[0].trace_id != second.derived_traces[0].trace_id
    assert first.derived_traces[0].trace_id != first_parent.trace_id
