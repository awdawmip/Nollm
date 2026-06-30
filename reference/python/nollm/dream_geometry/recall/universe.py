"""Strict finite RecallUniverse validation for DR1."""

from __future__ import annotations

from nollm.dream_geometry.cortex.types import CompilationDecision, payload_fingerprint
from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.field.types import CoverPolicy, cell_ref_key, policy_fingerprint
from nollm.dream_geometry.geometry.coverage import CoverageDirection
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
    for distribution in universe.coverage_up:
        if distribution.direction is not CoverageDirection.fine_to_coarse:
            raise RecallValidationError("DR1_COVERAGE_UP_DIRECTION_MISMATCH", cell_ref_key(distribution.source_cell))
    for distribution in universe.coverage_down:
        if distribution.direction is not CoverageDirection.coarse_to_fine:
            raise RecallValidationError("DR1_COVERAGE_DOWN_DIRECTION_MISMATCH", cell_ref_key(distribution.source_cell))


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
