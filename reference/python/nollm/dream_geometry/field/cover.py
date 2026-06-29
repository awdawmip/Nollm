"""DG2 local Coarse Cover lifecycle."""

from dataclasses import replace
from math import fsum

from nollm.dream_geometry.protocol.contracts import CoverState, GrowthBasis, TraceState

from .types import CoarseCover, CoverEligibility, CoverPolicy, CrystallizationDecision, policy_payload, stable_id


def build_local_covers(traces, policy: CoverPolicy = CoverPolicy()) -> tuple[CoarseCover, ...]:
    _reject_duplicate_trace_ids(traces)
    groups: dict[tuple[object, object], list] = {}
    for trace in traces:
        groups.setdefault((trace.cell.chart_fingerprint, trace.cell.cell_ref), []).append(trace)
    covers = []
    for (fingerprint, cell_ref), members in groups.items():
        ordered = sorted(members, key=lambda trace: trace.trace_id)
        mass = fsum(trace.mass for trace in ordered)
        provisional_mass = fsum(trace.mass for trace in ordered if trace.state is not TraceState.accepted or trace.basis is GrowthBasis.provisional_llm_generalization)
        genericity = _weighted(ordered, "genericity")
        ambiguity = _weighted(ordered, "ambiguity")
        conflict = _weighted(ordered, "conflict")
        stability = min((trace.stability_epochs for trace in ordered), default=0)
        payload = {
            "chart": str(fingerprint),
            "cell": str(cell_ref),
            "trace_ids": tuple(trace.trace_id for trace in ordered),
            "policy_id": policy.policy_id,
            "policy_version": policy.version,
            "policy_payload": policy_payload(policy),
        }
        draft = CoarseCover(
            cover_id=stable_id("cover:v2", payload),
            chart_fingerprint=fingerprint,
            support_cell=cell_ref,
            support_trace_ids=tuple(trace.trace_id for trace in ordered),
            support_shard_ids=tuple(sorted({trace.origin_shard_id for trace in ordered})),
            support_keys=tuple(sorted({trace.support_key for trace in ordered})),
            axes_present=tuple(sorted({trace.axis for trace in ordered})),
            mass=mass,
            provisional_mass=provisional_mass,
            genericity=genericity,
            ambiguity=ambiguity,
            conflict=conflict,
            stability=stability,
            state=CoverState.candidate,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            eligibility_reasons=(),
        )
        eligibility = evaluate_cover_eligibility(draft, policy, tuple(ordered))
        state = CoverState.stable if eligibility.approved else CoverState.candidate
        covers.append(replace(draft, state=state, eligibility_reasons=eligibility.reasons))
    return tuple(sorted(covers, key=lambda cover: cover.cover_id))


def evaluate_cover_eligibility(cover: CoarseCover, policy: CoverPolicy, traces=()) -> CoverEligibility:
    if cover.policy_id != policy.policy_id or cover.policy_version != policy.version:
        raise ValueError("policy identity mismatch")
    reasons: list[str] = []
    if cover.mass < policy.min_total_mass:
        reasons.append("mass_below_min_total")
    if len(cover.support_keys) < policy.min_independent_support:
        reasons.append("insufficient_independent_support")
    if len(cover.axes_present) < policy.min_axes:
        reasons.append("insufficient_axis_diversity")
    if cover.provisional_mass > 0.0:
        reasons.append("provisional_mass_present")
    if cover.genericity > policy.max_genericity:
        reasons.append("genericity_above_limit")
    if cover.ambiguity > policy.max_ambiguity:
        reasons.append("ambiguity_above_limit")
    if cover.conflict > policy.max_conflict:
        reasons.append("conflict_above_limit")
    if cover.stability < policy.min_stability:
        reasons.append("stability_below_min")
    for trace in traces:
        if not trace.basis_refs:
            reasons.append("missing_basis_refs")
            break
        if trace.cell.chart_fingerprint != cover.chart_fingerprint or trace.cell.cell_ref != cover.support_cell:
            reasons.append("cross_geometry_support")
            break
    return CoverEligibility(not reasons, tuple(reasons))


def crystallize_cover(cover: CoarseCover, decision: CrystallizationDecision) -> CoarseCover:
    if cover.state is not CoverState.stable:
        raise ValueError("only stable covers can be crystallized")
    if decision.cover_id != cover.cover_id:
        raise ValueError("decision cover_id mismatch")
    if not decision.approved:
        raise ValueError("crystallization decision must be approved")
    return replace(cover, state=CoverState.crystallized, eligibility_reasons=cover.eligibility_reasons + ("explicit_crystallization_decision",))


def _weighted(traces, attr: str) -> float:
    total = fsum(trace.mass for trace in traces)
    if total <= 0.0:
        return 0.0
    return fsum(trace.mass * getattr(trace, attr) for trace in traces) / total


def _reject_duplicate_trace_ids(traces) -> None:
    seen: set[str] = set()
    for trace in traces:
        if trace.trace_id in seen:
            raise ValueError("duplicate trace_id")
        seen.add(trace.trace_id)
