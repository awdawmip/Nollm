"""Strict finite RecallUniverse validation for DR1."""

from __future__ import annotations

from nollm.dream_geometry.cortex.types import CompilationDecision, payload_fingerprint
from math import isfinite

from nollm.dream_geometry.evidence import MemorySubstrateStore, canonical_json
from nollm.dream_geometry.field.types import CoverPolicy, cell_ref_key, policy_fingerprint
from nollm.dream_geometry.geometry.coverage import CoverageDirection, PartitionValidationError, validate_nonoverlapping_partition
from nollm.dream_geometry.protocol.contracts import CoverState, TraceState

from .projection import projection_for_trace
from .types import ProposalAdmission, RecallUniverse, RecallValidationError, ValidatedRecallUniverse


def validate_recall_universe(universe: RecallUniverse, evidence_reader: MemorySubstrateStore) -> ValidatedRecallUniverse:
    _reject_duplicate([record.proposal.proposal_id for record in universe.proposal_records], "DR1_DUPLICATE_PROPOSAL_ID")
    _reject_duplicate([trace.trace_id for trace in universe.traces], "DR1_DUPLICATE_TRACE_ID")
    _reject_duplicate([cover.cover_id for cover in universe.covers], "DR1_DUPLICATE_COVER_ID")
    _reject_duplicate([item.compaction_id for item in universe.trace_compactions], "DR1_DUPLICATE_COMPACTION_ID")
    _validate_compactions(universe)
    _validate_proposal_records(universe)
    _validate_cover_policies(universe)
    _validate_coverage(universe)
    _validate_context_records(universe, evidence_reader)
    current_records = tuple(record for record in universe.proposal_records if record.admission is ProposalAdmission.current_accepted)
    legacy_records = tuple(record for record in universe.proposal_records if record.admission is ProposalAdmission.legacy_dc1_read_only)
    legacy_proposal_ids = {record.proposal.proposal_id for record in legacy_records}
    projections = []
    for trace in sorted(universe.traces, key=lambda item: item.trace_id):
        try:
            evidence_reader.get_dream_shard(trace.origin_shard_id)
        except Exception as exc:
            raise RecallValidationError("DR1_TRACE_ORIGIN_SHARD_MISSING", trace.trace_id) from exc
        if trace.state is not TraceState.accepted:
            continue
        if trace.proposal_id in legacy_proposal_ids and trace.proposal_id not in {record.proposal.proposal_id for record in current_records}:
            continue
        projection = projection_for_trace(trace, current_records)
        if projection is None:
            raise RecallValidationError("DR1_TRACE_STEP_BINDING_MISSING", trace.trace_id)
        projections.append(projection)
    _validate_covers(universe)
    return ValidatedRecallUniverse(universe, current_records, legacy_records, tuple(projections), ())


def _validate_proposal_records(universe: RecallUniverse) -> None:
    for record in universe.proposal_records:
        if record.admission is ProposalAdmission.legacy_dc1_read_only:
            continue
        if record.admission is not ProposalAdmission.current_accepted:
            raise RecallValidationError("DR1_UNKNOWN_PROPOSAL_ADMISSION", record.proposal.proposal_id)
        receipt = record.receipt
        if receipt is None:
            raise RecallValidationError("DR1_PROPOSAL_RECEIPT_MISSING", record.proposal.proposal_id)
        if receipt.kind != "growth":
            raise RecallValidationError("DR1_PROPOSAL_RECEIPT_KIND_INVALID", receipt.receipt_id)
        if receipt.decision is not CompilationDecision.accepted:
            raise RecallValidationError("DR1_PROPOSAL_RECEIPT_NOT_ACCEPTED", receipt.receipt_id)
        if receipt.proposal_id != record.proposal.proposal_id:
            raise RecallValidationError("DR1_PROPOSAL_RECEIPT_ID_MISMATCH", receipt.receipt_id)
        if receipt.normalized_payload_fingerprint != payload_fingerprint(record.proposal):
            raise RecallValidationError("DR1_PROPOSAL_RECEIPT_FINGERPRINT_MISMATCH", receipt.receipt_id)


def _validate_cover_policies(universe: RecallUniverse) -> None:
    policies: dict[tuple[str, str], CoverPolicy] = {(policy.policy_id, policy.version): policy for policy in universe.cover_policy_records}
    for cover in universe.covers:
        policy = policies.get((cover.policy_id, cover.policy_version))
        if policy is None:
            raise RecallValidationError("DR1_COVER_POLICY_MISSING", cover.cover_id)
        if policy_fingerprint(policy) != cover.policy_fingerprint:
            raise RecallValidationError("DR1_COVER_POLICY_IDENTITY_MISMATCH", cover.cover_id)


def _validate_covers(universe: RecallUniverse) -> None:
    traces = {trace.trace_id: trace for trace in universe.traces}
    for cover in universe.covers:
        support_traces = []
        for trace_id in cover.support_trace_ids:
            trace = traces.get(trace_id)
            if trace is None:
                raise RecallValidationError("DR1_COVER_SUPPORT_TRACE_MISSING", cover.cover_id)
            support_traces.append(trace)
        expected_shards = tuple(sorted({trace.origin_shard_id for trace in support_traces}))
        if tuple(sorted(cover.support_shard_ids)) != expected_shards:
            raise RecallValidationError("DR1_COVER_SUPPORT_SHARD_MISMATCH", cover.cover_id)
        expected_keys = tuple(sorted(trace.support_key for trace in support_traces))
        if tuple(sorted(cover.support_keys)) != expected_keys:
            raise RecallValidationError("DR1_COVER_SUPPORT_KEY_MISMATCH", cover.cover_id)
        expected_axes = tuple(sorted({trace.axis for trace in support_traces}))
        if tuple(sorted(cover.axes_present)) != expected_axes:
            raise RecallValidationError("DR1_COVER_AXIS_MISMATCH", cover.cover_id)
        if cover.state in {CoverState.stable, CoverState.crystallized} and (cover.provisional_mass != 0.0 or len(cover.support_keys) < 2 or len(cover.axes_present) < 2):
            raise RecallValidationError("DR1_COVER_STRUCTURAL_RULE_FAILED", cover.cover_id)


def _validate_coverage(universe: RecallUniverse) -> None:
    seen_sources: set[tuple[str, str]] = set()
    for distribution in universe.coverage_up:
        if distribution.direction is not CoverageDirection.fine_to_coarse:
            raise RecallValidationError("DR1_COVERAGE_UP_DIRECTION_MISMATCH", cell_ref_key(distribution.source_cell))
        _validate_distribution(distribution, seen_sources, universe, "DR1_COVERAGE_UP_INVALID")
    for distribution in universe.coverage_down:
        if distribution.direction is not CoverageDirection.coarse_to_fine:
            raise RecallValidationError("DR1_COVERAGE_DOWN_DIRECTION_MISMATCH", cell_ref_key(distribution.source_cell))
        _validate_distribution(distribution, seen_sources, universe, "DR1_COVERAGE_DOWN_INVALID")


def _validate_distribution(distribution, seen_sources: set[tuple[str, str]], universe: RecallUniverse, reason_code: str) -> None:
    source_ref = cell_ref_key(distribution.source_cell)
    source_key = (distribution.direction.value, source_ref)
    if source_key in seen_sources:
        raise RecallValidationError("DR1_COVERAGE_DUPLICATE_SOURCE", f"{distribution.direction.value}:{source_ref}")
    seen_sources.add(source_key)
    if not _finite_non_negative(distribution.residual.mass):
        raise RecallValidationError(reason_code, source_ref)
    if not _finite_non_negative(distribution.total_mass):
        raise RecallValidationError(reason_code, source_ref)
    target_refs: set[str] = set()
    kernel_mass = 0.0
    for kernel in distribution.kernels:
        if kernel.direction is not distribution.direction:
            raise RecallValidationError("DR1_COVERAGE_KERNEL_DIRECTION_MISMATCH", source_ref)
        if cell_ref_key(kernel.source_cell) != source_ref:
            raise RecallValidationError("DR1_COVERAGE_KERNEL_SOURCE_MISMATCH", source_ref)
        target_ref = cell_ref_key(kernel.target_cell)
        if target_ref in target_refs:
            raise RecallValidationError("DR1_COVERAGE_DUPLICATE_TARGET_CELL", target_ref)
        target_refs.add(target_ref)
        if not _finite_non_negative(kernel.weight):
            raise RecallValidationError(reason_code, target_ref)
        kernel_mass += float(kernel.weight)
        if kernel.source_cell.chart_fingerprint != kernel.target_cell.chart_fingerprint:
            _require_verified_chart_link(universe, kernel.source_cell.chart_fingerprint, kernel.target_cell.chart_fingerprint, target_ref)
    if distribution.kernels:
        try:
            validate_nonoverlapping_partition(tuple(kernel.target_cell for kernel in distribution.kernels))
        except PartitionValidationError as exc:
            raise RecallValidationError("DR1_COVERAGE_PARTITION_INVALID", source_ref) from exc
    if abs((kernel_mass + float(distribution.residual.mass)) - 1.0) > 1e-9:
        raise RecallValidationError("DR1_COVERAGE_MASS_ACCOUNTING_FAILED", source_ref)
    if abs(float(distribution.total_mass) - 1.0) > 1e-9:
        raise RecallValidationError("DR1_COVERAGE_TOTAL_MASS_INVALID", source_ref)


def _require_verified_chart_link(universe: RecallUniverse, source_fingerprint, target_fingerprint, detail: str) -> None:
    for link in universe.verified_chart_links:
        if link.source_chart_fingerprint == source_fingerprint and link.target_chart_fingerprint == target_fingerprint:
            return
    raise RecallValidationError("DR1_COVERAGE_VERIFIED_CHART_LINK_MISSING", detail)


def _finite_non_negative(value: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(float(value)) and float(value) >= 0.0


def _validate_context_records(universe: RecallUniverse, evidence_reader: MemorySubstrateStore) -> None:
    for interpretation in universe.interpretation_records:
        try:
            stored = evidence_reader.get_interpretation(interpretation.interpretation_id)
            evidence_reader.get_dream_shard(stored.subject_shard_id)
        except Exception as exc:
            raise RecallValidationError("DR1_CONTEXT_INTERPRETATION_MISSING", interpretation.interpretation_id) from exc
        if canonical_json(stored) != canonical_json(interpretation):
            raise RecallValidationError("DR1_CONTEXT_INTERPRETATION_PAYLOAD_MISMATCH", interpretation.interpretation_id)
    for thread in universe.revision_threads:
        try:
            stored = evidence_reader.get_revision_thread(thread.thread_id)
        except Exception as exc:
            raise RecallValidationError("DR1_CONTEXT_REVISION_MISSING", thread.thread_id) from exc
        if canonical_json(stored) != canonical_json(thread):
            raise RecallValidationError("DR1_CONTEXT_REVISION_PAYLOAD_MISMATCH", thread.thread_id)
        for member_id in thread.member_record_ids:
            try:
                evidence_reader.get_dream_shard(member_id)
                continue
            except Exception:
                pass
            try:
                evidence_reader.get_interpretation(member_id)
            except Exception as exc:
                raise RecallValidationError("DR1_CONTEXT_REVISION_MEMBER_MISSING", member_id) from exc


def _validate_compactions(universe: RecallUniverse) -> None:
    trace_ids = {trace.trace_id for trace in universe.traces}
    for compaction in universe.trace_compactions:
        if compaction.member_trace_ids != compaction.expansion_manifest:
            raise RecallValidationError("DR1_COMPACTION_MANIFEST_MISMATCH", compaction.compaction_id)
        if any(trace_id not in trace_ids for trace_id in compaction.expansion_manifest):
            raise RecallValidationError("DR1_COMPACTION_TRACE_MISSING", compaction.compaction_id)


def _reject_duplicate(values: list[str], reason_code: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise RecallValidationError(reason_code, value)
        seen.add(value)


__all__ = ["validate_recall_universe"]
