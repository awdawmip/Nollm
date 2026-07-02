"""DF1 finite FieldSnapshot and DR1 RecallUniverse assembly."""

from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.admission.errors import DA1_REPLAY_PROJECTION_MISMATCH, DA1_UNVERIFIED_CROSS_CHART_LINK, DA1Rejection
from nollm.dream_geometry.admission.orchestrator import placement_plan_from_payload
from nollm.dream_geometry.cortex import ADMISSION_CURRENT_DC1_1, CompilationDecision
from nollm.dream_geometry.field import CoverPolicy, GravityPolicy, build_local_covers, calculate_gravity_snapshot
from nollm.dream_geometry.field.types import cell_ref_key
from nollm.dream_geometry.geometry import CoverageDirection, compute_distribution
from nollm.dream_geometry.recall import ProposalAdmission, ProposalReadRecord, RecallUniverse, validate_recall_universe
from nollm.dream_geometry.recall.projection import basis_ref_key
from nollm.dream_geometry.recall.types import RecallValidationError

from .errors import (
    DF1_ADMISSION_BINDING_MISMATCH,
    DF1_ADMISSION_FINGERPRINT_CONFLICT,
    DF1_ADMISSION_REPLAY_INVALID,
    DF1_CHART_LINK_MANIFEST_INVALID,
    DF1_DUPLICATE_ADMISSION_ID,
    DF1_EMPTY_ADMISSION_SET,
    DF1_FIELD_POLICY_MISMATCH,
    DF1_GEOMETRY_PROFILE_MISMATCH,
    DF1_IMPLICIT_DISCOVERY_FORBIDDEN,
    DF1_PROJECTION_FINGERPRINT_MISMATCH,
    DF1_PROPOSAL_NOT_ACCEPTED,
    DF1_PROPOSAL_NOT_FOUND,
    DF1_SHARD_NOT_FOUND,
    DF1_UNIVERSE_CONSTRUCTION_FAILED,
    DF1_UNVERIFIED_CHART_LINK,
    DF1_UNSUPPORTED_MUTABLE_INPUT,
    DF1AssemblyError,
    reject,
)
from .types import (
    DEFAULT_FIELD_POLICY_IDENTITY,
    AdmissionManifestEntry,
    AssemblyAuditSummary,
    FieldAssemblyPolicy,
    FieldAssemblyResult,
    FiniteAdmissionSet,
    FiniteFieldSnapshot,
    policy_identity,
    record_fingerprint,
    snapshot_fingerprint_payload,
    stable_fingerprint,
)


def assemble_field_snapshot(admission_set: FiniteAdmissionSet, policy: FieldAssemblyPolicy = FieldAssemblyPolicy()) -> FieldAssemblyResult:
    _validate_policy(policy)
    _validate_admission_set_shape(admission_set)
    if policy.reject_incompatible_field_policy and admission_set.field_policy_identity != DEFAULT_FIELD_POLICY_IDENTITY:
        reject(DF1_FIELD_POLICY_MISMATCH, "field policy semantic identity mismatch")

    ordered_sources = tuple(sorted(admission_set.admissions, key=lambda item: item.admission_record.admission_id))
    _reject_duplicate_records(ordered_sources)

    manifest: list[AdmissionManifestEntry] = []
    proposal_records: list[ProposalReadRecord] = []
    traces = []
    cover_traces = []
    residuals = []
    coverage_up = []
    chart_links = []

    for source in ordered_sources:
        record = source.admission_record
        if policy.reject_incompatible_geometry_profile and record.field_profile_id != admission_set.geometry_profile_id:
            reject(DF1_GEOMETRY_PROFILE_MISMATCH, record.admission_id)
        projection = _replay_one(source, policy)
        receipt = _accepted_receipt(source, record)
        proposal = source.cortex_reader.get_growth_proposal(record.proposal_id)
        proposal_records.append(ProposalReadRecord(proposal, ProposalAdmission.current_accepted, f"df1:{record.admission_id}", receipt))
        manifest.append(
            AdmissionManifestEntry(
                record.admission_id,
                record_fingerprint(record),
                record.subject_shard_id,
                record.proposal_id,
                record.compilation_receipt_id,
                record.placement_plan_fingerprint,
                record.projection_fingerprint,
            )
        )
        traces.extend(projection.source_traces)
        traces.extend(projection.derived_traces)
        cover_traces.extend(projection.derived_traces)
        residuals.extend(projection.residuals)
        plan = _placement_plan(record)
        for placement in plan.axis_placements:
            coverage_up.append(compute_distribution(placement.source_cell, placement.fine_to_coarse_targets, CoverageDirection.fine_to_coarse))
            if placement.verified_chart_link is not None:
                chart_links.append(placement.verified_chart_link)

    replayed_traces = _unique_by_id(traces, "trace_id")
    replayed_cover_traces = _unique_by_id(cover_traces, "trace_id")
    trace_residuals = _unique_by_id(residuals, "residual_id")
    coarse_covers = build_local_covers(replayed_cover_traces, CoverPolicy())
    gravity_snapshot = calculate_gravity_snapshot(coarse_covers, GravityPolicy())
    up = _unique_distributions(coverage_up)
    down = _coverage_down_from_covers(coarse_covers, replayed_cover_traces)
    links = tuple(sorted(_unique_links(chart_links), key=str))
    snapshot = FiniteFieldSnapshot(
        "",
        admission_set.assembly_id,
        policy_identity(policy),
        admission_set.geometry_profile_id,
        admission_set.field_policy_identity,
        tuple(sorted(manifest, key=lambda item: item.admission_id)),
        replayed_traces,
        trace_residuals,
        coarse_covers,
        up,
        down,
        links,
        gravity_snapshot,
        tuple(item.admission_record.admission_id for item in ordered_sources),
    )
    snapshot = replace(snapshot, snapshot_id=stable_fingerprint(snapshot_fingerprint_payload(snapshot)))
    universe = _build_universe(snapshot, tuple(proposal_records))
    try:
        validate_recall_universe(universe, ordered_sources[0].evidence_reader)
    except Exception as exc:
        raise DF1AssemblyError(DF1_UNIVERSE_CONSTRUCTION_FAILED, str(exc)) from exc
    summary = AssemblyAuditSummary(
        admission_set.assembly_id,
        snapshot.snapshot_id,
        snapshot.source_admission_ids,
        len(snapshot.replayed_traces),
        len(snapshot.coarse_covers),
        len(snapshot.verified_chart_links),
        universe.universe_id,
        "pass",
    )
    return FieldAssemblyResult(snapshot, universe, summary)


def recall_universe_from_snapshot(snapshot: FiniteFieldSnapshot, proposal_records: tuple[ProposalReadRecord, ...]) -> RecallUniverse:
    return _build_universe(snapshot, proposal_records)


def _validate_policy(policy: FieldAssemblyPolicy) -> None:
    if policy.output_mode != "in_memory_only":
        reject(DF1_UNSUPPORTED_MUTABLE_INPUT, "DF1 output mode must be in_memory_only")
    if not policy.require_replay_validation:
        reject(DF1_ADMISSION_REPLAY_INVALID, "replay validation is required")


def _validate_admission_set_shape(admission_set: FiniteAdmissionSet) -> None:
    if not isinstance(admission_set, FiniteAdmissionSet):
        reject(DF1_UNSUPPORTED_MUTABLE_INPUT, "admission_set must be FiniteAdmissionSet")
    if not isinstance(admission_set.admissions, tuple):
        reject(DF1_UNSUPPORTED_MUTABLE_INPUT, "admissions must be an immutable explicit tuple")
    if not admission_set.admissions:
        reject(DF1_EMPTY_ADMISSION_SET, "admissions must be non-empty")
    if any(isinstance(item, (str, bytes)) for item in admission_set.admissions):
        reject(DF1_IMPLICIT_DISCOVERY_FORBIDDEN, "path-like admission discovery is forbidden")


def _reject_duplicate_records(sources) -> None:
    seen: dict[str, str] = {}
    for source in sources:
        admission_id = source.admission_record.admission_id
        fingerprint = record_fingerprint(source.admission_record)
        if admission_id in seen:
            if seen[admission_id] != fingerprint:
                reject(DF1_ADMISSION_FINGERPRINT_CONFLICT, admission_id)
            reject(DF1_DUPLICATE_ADMISSION_ID, admission_id)
        seen[admission_id] = fingerprint


def _replay_one(source, policy: FieldAssemblyPolicy):
    record = source.admission_record
    try:
        shard = source.evidence_reader.get_dream_shard(record.subject_shard_id)
    except Exception as exc:
        raise DF1AssemblyError(DF1_SHARD_NOT_FOUND, record.subject_shard_id) from exc
    try:
        proposal = source.cortex_reader.get_growth_proposal(record.proposal_id)
    except Exception as exc:
        raise DF1AssemblyError(DF1_PROPOSAL_NOT_FOUND, record.proposal_id) from exc
    if shard.shard_id != record.subject_shard_id or proposal.proposal_id != record.proposal_id or proposal.subject_shard_id != shard.shard_id:
        reject(DF1_ADMISSION_BINDING_MISMATCH, record.admission_id)
    _accepted_receipt(source, record)
    try:
        projection = source.replayed_projection if source.replayed_projection is not None else source.replay_validator(record)
    except DA1Rejection as exc:
        if exc.reason_codes == (DA1_REPLAY_PROJECTION_MISMATCH,):
            raise DF1AssemblyError(DF1_PROJECTION_FINGERPRINT_MISMATCH, record.admission_id) from exc
        if exc.reason_codes == (DA1_UNVERIFIED_CROSS_CHART_LINK,):
            raise DF1AssemblyError(DF1_UNVERIFIED_CHART_LINK, record.admission_id) from exc
        raise DF1AssemblyError(DF1_ADMISSION_REPLAY_INVALID, str(exc)) from exc
    except Exception as exc:
        raise DF1AssemblyError(DF1_ADMISSION_REPLAY_INVALID, str(exc)) from exc
    if projection.projection_fingerprint != record.projection_fingerprint:
        reject(DF1_PROJECTION_FINGERPRINT_MISMATCH, record.admission_id)
    try:
        _placement_plan(record)
    except DA1Rejection as exc:
        raise DF1AssemblyError(DF1_UNVERIFIED_CHART_LINK, record.admission_id) from exc
    except Exception as exc:
        raise DF1AssemblyError(DF1_CHART_LINK_MANIFEST_INVALID, record.admission_id) from exc
    return projection


def _accepted_receipt(source, record):
    try:
        view = source.cortex_reader.stored_growth_proposal(record.proposal_id)
    except Exception as exc:
        raise DF1AssemblyError(DF1_PROPOSAL_NOT_FOUND, record.proposal_id) from exc
    if view.admission != ADMISSION_CURRENT_DC1_1:
        reject(DF1_PROPOSAL_NOT_ACCEPTED, record.proposal_id)
    receipts = (source.compilation_receipt,) if source.compilation_receipt is not None else source.cortex_reader.receipts()
    for receipt in receipts:
        if receipt.receipt_id == record.compilation_receipt_id and receipt.proposal_id == record.proposal_id:
            if receipt.decision is not CompilationDecision.accepted:
                reject(DF1_PROPOSAL_NOT_ACCEPTED, record.proposal_id)
            return receipt
    reject(DF1_PROPOSAL_NOT_ACCEPTED, record.proposal_id)


def _placement_plan(record):
    try:
        return placement_plan_from_payload(record.placement_plan_payload)
    except DA1Rejection:
        raise
    except Exception as exc:
        raise DF1AssemblyError(DF1_CHART_LINK_MANIFEST_INVALID, record.admission_id) from exc


def _unique_by_id(values, attr: str):
    by_id = {}
    for value in values:
        key = getattr(value, attr)
        by_id.setdefault(key, value)
    return tuple(by_id[key] for key in sorted(by_id))


def _unique_distributions(distributions):
    by_key = {}
    for distribution in distributions:
        key = (distribution.direction.value, cell_ref_key(distribution.source_cell))
        by_key.setdefault(key, distribution)
    return tuple(by_key[key] for key in sorted(by_key))


def _unique_links(links):
    by_key = {}
    for link in links:
        key = (str(link.source_chart_fingerprint), str(link.target_chart_fingerprint))
        by_key.setdefault(key, link)
    return tuple(by_key[key] for key in sorted(by_key))


def _coverage_down_from_covers(covers, traces):
    trace_cells = {cell_ref_key(trace.cell): trace.cell for trace in traces}
    distributions = []
    for cover in covers:
        source = trace_cells.get(f"{cover.support_cell.chart_id}:{cover.support_cell.axial.q}:{cover.support_cell.axial.r}")
        target_by_ref = {cell_ref_key(trace.cell): trace.cell for trace in traces if trace.trace_id in cover.support_trace_ids}
        targets = tuple(target_by_ref[key] for key in sorted(target_by_ref))
        if source is not None and targets:
            distributions.append(compute_distribution(source, targets, CoverageDirection.coarse_to_fine))
    return _unique_distributions(distributions)


def _build_universe(snapshot: FiniteFieldSnapshot, proposal_records: tuple[ProposalReadRecord, ...]) -> RecallUniverse:
    universe_traces = tuple(_dr1_trace_view(trace, proposal_records) for trace in snapshot.replayed_traces if trace.parent_trace_id is not None)
    universe_covers = build_local_covers(universe_traces, CoverPolicy())
    universe_gravity = calculate_gravity_snapshot(universe_covers, GravityPolicy())
    universe_down = _coverage_down_from_covers(universe_covers, universe_traces)
    return RecallUniverse(
        tuple(sorted(proposal_records, key=lambda item: item.proposal.proposal_id)),
        universe_traces,
        universe_covers,
        universe_id="df1:recall_universe:" + snapshot.snapshot_id.removeprefix("sha256:")[:32],
        coverage_up=snapshot.coverage_up,
        coverage_down=universe_down,
        verified_chart_links=snapshot.verified_chart_links,
        gravity_snapshot=universe_gravity,
        cover_policy_records=(CoverPolicy(),),
    )


def _dr1_trace_view(trace, proposal_records: tuple[ProposalReadRecord, ...]):
    for record in proposal_records:
        if record.proposal.proposal_id != trace.proposal_id:
            continue
        for axis in record.proposal.axes:
            if axis.axis_id != trace.axis:
                continue
            for step in axis.ray:
                basis = step.basis.value if hasattr(step.basis, "value") else str(step.basis)
                if basis == trace.basis.value:
                    return replace(trace, basis_refs=tuple(basis_ref_key(ref) for ref in step.basis_refs))
    return trace


__all__ = ["assemble_field_snapshot", "recall_universe_from_snapshot"]
