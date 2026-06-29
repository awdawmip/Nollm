"""DG2 deterministic Growth Trace propagation."""

from nollm.dream_geometry.geometry.coverage import CoverageDirection
from nollm.dream_geometry.geometry.types import GeometryTolerance
from nollm.dream_geometry.protocol.contracts import GrowthBasis, TraceState

from .types import (
    GrowthTrace,
    TracePropagationResult,
    TraceResidual,
    TraceSeed,
    VerifiedChartLink,
    cell_payload,
    cell_ref_key,
    chart_fingerprint_payload,
    float_token,
    stable_id,
)


def seed_to_trace(seed: TraceSeed) -> GrowthTrace:
    return GrowthTrace(
        trace_id=seed.trace_id,
        origin_shard_id=seed.shard_id,
        proposal_id=seed.proposal_id,
        parent_trace_id=None,
        cell=seed.source_cell,
        axis=seed.axis,
        basis=seed.basis,
        basis_refs=seed.basis_refs,
        mass=seed.mass,
        support_key=seed.support_key,
        genericity=seed.genericity,
        ambiguity=seed.ambiguity,
        conflict=seed.conflict,
        stability_epochs=seed.stability_epochs,
        state=seed.state,
        derivation_kind="seed",
        geometry_refs=(stable_id("geometry:seed", cell_payload(seed.source_cell)),),
    )


def propagate_trace(
    parent_trace: GrowthTrace,
    distribution,
    chart_link: VerifiedChartLink | None = None,
    tolerance: GeometryTolerance = GeometryTolerance(),
) -> TracePropagationResult:
    _validate_distribution(parent_trace, distribution, chart_link)
    geometry_ref = _distribution_ref(distribution)
    derived = []
    for kernel in distribution.kernels:
        mass = parent_trace.mass * kernel.weight
        if mass <= tolerance.coordinate_abs_tol:
            continue
        payload = {
            "parent_trace_id": parent_trace.trace_id,
            "target": cell_payload(kernel.target_cell),
            "direction": kernel.direction.value,
            "weight": float_token(kernel.weight),
            "distribution": geometry_ref,
        }
        derived.append(
            GrowthTrace(
                trace_id=stable_id("trace:v2", payload),
                origin_shard_id=parent_trace.origin_shard_id,
                proposal_id=parent_trace.proposal_id,
                parent_trace_id=parent_trace.trace_id,
                cell=kernel.target_cell,
                axis=parent_trace.axis,
                basis=parent_trace.basis,
                basis_refs=parent_trace.basis_refs,
                mass=mass,
                support_key=parent_trace.support_key,
                genericity=parent_trace.genericity,
                ambiguity=parent_trace.ambiguity,
                conflict=parent_trace.conflict,
                stability_epochs=parent_trace.stability_epochs,
                state=_derived_state(parent_trace),
                derivation_kind="k_up_propagation",
                geometry_refs=(geometry_ref, stable_id("kernel:v2", payload)),
            )
        )
    derived_traces = tuple(sorted(derived, key=lambda trace: trace.trace_id))
    residual_mass = parent_trace.mass * distribution.residual.mass
    residual_payload = {
        "parent_trace_id": parent_trace.trace_id,
        "source": cell_payload(parent_trace.cell),
        "mass": float_token(residual_mass),
        "reasons": tuple(reason.value for reason in distribution.residual.reasons),
        "distribution": geometry_ref,
    }
    residual = TraceResidual(
        residual_id=stable_id("trace_residual:v2", residual_payload),
        parent_trace_id=parent_trace.trace_id,
        source_cell_ref=cell_ref_key(parent_trace.cell),
        mass=residual_mass,
        reasons=tuple(reason.value for reason in distribution.residual.reasons),
        geometry_refs=(geometry_ref,),
    )
    derived_mass = sum(trace.mass for trace in derived_traces)
    accounting_error = abs(derived_mass + residual.mass - parent_trace.mass)
    limit = tolerance.coordinate_abs_tol + tolerance.coordinate_rel_tol * parent_trace.mass
    if accounting_error > limit:
        raise ValueError("trace propagation violates mass accounting")
    return TracePropagationResult(derived_traces, residual, parent_trace.mass, derived_mass, accounting_error)


def _validate_distribution(parent_trace: GrowthTrace, distribution, chart_link: VerifiedChartLink | None) -> None:
    if distribution.direction is not CoverageDirection.fine_to_coarse:
        raise ValueError("DG2 write-side propagation requires fine_to_coarse distribution")
    if distribution.source_cell.cell_ref != parent_trace.cell.cell_ref:
        raise ValueError("distribution source cell does not match parent trace")
    if distribution.source_cell.chart_fingerprint != parent_trace.cell.chart_fingerprint:
        raise ValueError("distribution source fingerprint does not match parent trace")
    target_fingerprints = {kernel.target_cell.chart_fingerprint for kernel in distribution.kernels}
    if len(target_fingerprints) > 1:
        raise ValueError("distribution targets must share one chart fingerprint")
    target_fingerprint = next(iter(target_fingerprints), parent_trace.cell.chart_fingerprint)
    if target_fingerprint != parent_trace.cell.chart_fingerprint:
        if chart_link is None:
            raise ValueError("cross-chart propagation requires verified chart link")
        if chart_link.source_chart_fingerprint != parent_trace.cell.chart_fingerprint:
            raise ValueError("chart link source fingerprint mismatch")
        if chart_link.target_chart_fingerprint != target_fingerprint:
            raise ValueError("chart link target fingerprint mismatch")


def _derived_state(parent_trace: GrowthTrace) -> TraceState:
    if parent_trace.basis is GrowthBasis.provisional_llm_generalization:
        return TraceState.proposed
    if parent_trace.state is TraceState.accepted:
        return TraceState.accepted
    return TraceState.proposed if parent_trace.state is TraceState.proposed else parent_trace.state


def _distribution_ref(distribution) -> str:
    payload = {
        "source": cell_payload(distribution.source_cell),
        "direction": distribution.direction.value,
        "kernels": tuple(
            {
                "target": cell_payload(kernel.target_cell),
                "weight": float_token(kernel.weight),
                "overlap_area": float_token(kernel.overlap_area),
            }
            for kernel in sorted(distribution.kernels, key=lambda item: cell_ref_key(item.target_cell))
        ),
        "residual": {
            "mass": float_token(distribution.residual.mass),
            "reasons": tuple(reason.value for reason in distribution.residual.reasons),
        },
    }
    return stable_id("coverage_distribution:v2", payload)
