"""Exact DR1 query and trace projection helpers."""

from __future__ import annotations

from nollm.dream_geometry.cortex.types import CompiledGrowthProposal, CompiledQueryProbe, RuleReference, StepReference, TextSpanRef
from nollm.dream_geometry.field.types import GrowthTrace

from .types import ProbeAtom, ProposalReadRecord, RuntimeTimeResolution, TraceSemanticProjection


EXPLICIT_IN_QUERY = "explicit_in_query"


def basis_ref_key(ref: object) -> str:
    if isinstance(ref, TextSpanRef):
        return f"text_span:{ref.record_id}:{ref.start_char}:{ref.end_char}:{ref.quoted_text}"
    if isinstance(ref, RuleReference):
        return f"rule:{ref.rule_id}:{ref.rule_version}:{ref.rule_label}:{ref.source_ref or ''}"
    if isinstance(ref, StepReference):
        return f"step:{ref.input_step_id}"
    if isinstance(ref, str):
        return ref
    raise TypeError(f"unsupported basis ref type: {type(ref).__name__}")


def query_atoms(probe: CompiledQueryProbe, runtime_time: RuntimeTimeResolution | None) -> tuple[ProbeAtom, ...]:
    atoms: list[ProbeAtom] = []
    for axis in probe.axes:
        if not axis.ray:
            continue
        step = axis.ray[0]
        basis = step.basis.value if hasattr(step.basis, "value") else str(step.basis)
        if basis != EXPLICIT_IN_QUERY:
            continue
        if axis.axis_id == "relative_time":
            continue
        atoms.append(ProbeAtom(axis.axis_id, step.expression, "explicit_query", True, step.step_id))
    if runtime_time is not None:
        for span in runtime_time.spans:
            atoms.append(
                ProbeAtom(
                    span.resolved_axis_id,
                    span.resolved_expression,
                    "runtime_resolved_relative",
                    True,
                    f"{span.query_axis_id}:{span.query_expression}",
                )
            )
    return tuple(atoms)


def relative_time_required(probe: CompiledQueryProbe) -> bool:
    return any(axis.axis_id == "relative_time" for axis in probe.axes) or probe.requires_runtime_resolution


def projection_for_trace(trace: GrowthTrace, records: tuple[ProposalReadRecord, ...]) -> TraceSemanticProjection | None:
    proposal = _proposal_by_id(trace.proposal_id, records)
    if proposal is None:
        return None
    matches = []
    for axis in proposal.axes:
        if axis.axis_id != trace.axis:
            continue
        for step in axis.ray:
            basis = step.basis.value if hasattr(step.basis, "value") else str(step.basis)
            if basis != trace.basis.value:
                continue
            if tuple(basis_ref_key(ref) for ref in step.basis_refs) != trace.basis_refs:
                continue
            matches.append(step)
    if len(matches) != 1:
        return None
    step = matches[0]
    return TraceSemanticProjection(
        trace.trace_id,
        trace.proposal_id,
        trace.origin_shard_id,
        trace.axis,
        step.expression,
        step.step_id,
        trace.basis.value,
        trace.basis_refs,
    )


def _proposal_by_id(proposal_id: str, records: tuple[ProposalReadRecord, ...]) -> CompiledGrowthProposal | None:
    for record in records:
        if record.proposal.proposal_id == proposal_id:
            return record.proposal
    return None


__all__ = ["EXPLICIT_IN_QUERY", "basis_ref_key", "projection_for_trace", "query_atoms", "relative_time_required"]
