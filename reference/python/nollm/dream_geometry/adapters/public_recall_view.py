"""Public DI1 view over sealed DR1 recall digests."""

from __future__ import annotations

from typing import Any

from nollm.dream_geometry.evidence import (
    DreamShard,
    InterpretationRecord,
    MemorySubstrateStore,
    RevisionThread,
    canonical_payload,
)
from nollm.dream_geometry.recall import RecallDigest, RecallDigestStatus, RecallResultItem

from .errors import DI1ErrorCode

PUBLIC_SELECTION_BASIS = (
    "exact_structural_projection",
    "eligible_stable_cover",
    "final_multi_axis_evidence_gate",
)

_SAFE_DIAGNOSTICS = {
    "DEFERRED_TIME_RESOLUTION_REQUIRED": "runtime_time_resolution_required",
    "DR1_NO_EXACT_QUERY_ATOMS": "no_exact_query_atoms",
    "DR1_LEGACY_PROPOSALS_CONTEXT_ONLY": "legacy_proposals_context_only",
    "DR1_BUDGET_MAX_SEED_COVERS": "budget_exhausted",
    "DR1_BUDGET_MAX_RESULT_ITEMS": "budget_exhausted",
    "DR1_BUDGET_MAX_CELLS_PER_LAYER": "budget_exhausted",
    "DR1_BUDGET_MAX_LAYERS": "budget_exhausted",
    "DR1_BUDGET_MAX_CHARTS": "budget_exhausted",
    "DR1_BUDGET_MAX_LATERAL_HOPS": "budget_exhausted",
    "DR1_INVALID_QUERY_PROBE": "invalid_query_probe",
    "DR1_POLICY_INVALID": "policy_invalid",
    "DR1_DUPLICATE_PROPOSAL_ID": "invalid_universe",
    "DR1_COVERAGE_DOWN_DIRECTION_MISMATCH": "invalid_universe",
    "DR1_COVERAGE_DUPLICATE_SOURCE": "invalid_universe",
    "DR1_COVERAGE_VERIFIED_CHART_LINK_MISSING": "invalid_universe",
}


class PublicViewError(ValueError):
    def __init__(self, code: DI1ErrorCode):
        super().__init__(code.value)
        self.code = code


def public_recall_envelope(digest: RecallDigest, store: MemorySubstrateStore) -> dict[str, Any]:
    primary = tuple(_materialize_item(item, store, "primary") for item in digest.primary_evidence)
    contextual = tuple(_materialize_item(item, store, "contextual") for item in digest.contextual_evidence)
    return {
        "kind": "nollm_recall_digest",
        "digest_id": digest.digest_id,
        "query_probe_id": digest.query_probe_id,
        "status": _status_value(digest.status),
        "ephemeral": bool(digest.ephemeral),
        "primary_evidence": list(primary),
        "contextual_evidence": list(contextual),
        "warnings": _public_diagnostics(digest.warnings),
        "discarded": _public_diagnostics(digest.discarded),
        "residual_state": "present" if float(digest.unresolved_residual_mass) > 0.0 else "none",
        "truncated": digest.status is RecallDigestStatus.budget_exhausted,
    }


def _materialize_item(item: RecallResultItem, store: MemorySubstrateStore, tier: str) -> dict[str, Any]:
    try:
        shard = store.get_dream_shard(item.shard_id)
        usage_state = store.get_usage_state(item.shard_id).value
    except Exception as exc:
        raise PublicViewError(DI1ErrorCode.evidence_unavailable) from exc
    interpretation_context, revision_context = _context_views(item, store)
    return {
        "evidence_kind": "dream_shard",
        "shard_id": shard.shard_id,
        "content": shard.content,
        "usage_state": usage_state,
        "tier": tier,
        "matched_axis_ids": list(item.matched_axes),
        "selection_basis": list(PUBLIC_SELECTION_BASIS),
        "origin": _origin_view(shard),
        "temporal_context": _temporal_view(shard),
        "interpretation_context": interpretation_context,
        "revision_context": revision_context,
    }


def _context_views(item: RecallResultItem, store: MemorySubstrateStore) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    interpretations: list[dict[str, Any]] = []
    revisions: list[dict[str, Any]] = []
    for record_id in item.context_record_ids:
        if record_id.startswith("interpretation:"):
            interpretations.append(_interpretation_view(record_id, item.shard_id, store))
        elif record_id.startswith("revision:"):
            revisions.append(_revision_view(record_id, item.shard_id, store))
        else:
            raise PublicViewError(DI1ErrorCode.context_record_unavailable)
    return interpretations, revisions


def _interpretation_view(record_id: str, shard_id: str, store: MemorySubstrateStore) -> dict[str, Any]:
    try:
        record = store.get_interpretation(record_id)
        usage_state = store.get_usage_state(record.interpretation_id).value
    except Exception as exc:
        raise PublicViewError(DI1ErrorCode.context_record_unavailable) from exc
    if record.subject_shard_id != shard_id:
        raise PublicViewError(DI1ErrorCode.context_record_unavailable)
    return {
        "record_kind": "interpretation",
        "interpretation_id": record.interpretation_id,
        "subject_shard_id": record.subject_shard_id,
        "kind": _enum_value(record.kind),
        "statement": record.statement,
        "usage_state": usage_state,
        "basis_refs": list(record.basis_refs),
        "context_refs": list(record.context_refs),
        "tier": "contextual",
    }


def _revision_view(record_id: str, shard_id: str, store: MemorySubstrateStore) -> dict[str, Any]:
    try:
        thread = store.get_revision_thread(record_id)
    except Exception as exc:
        raise PublicViewError(DI1ErrorCode.context_record_unavailable) from exc
    if shard_id not in thread.member_record_ids:
        raise PublicViewError(DI1ErrorCode.context_record_unavailable)
    return {
        "record_kind": "revision_thread",
        "thread_id": thread.thread_id,
        "member_record_ids": list(thread.member_record_ids),
        "edges": [_revision_edge_view(edge) for edge in thread.edges],
        "context_refs": list(thread.context_refs),
        "tier": "contextual",
    }


def _revision_edge_view(edge: object) -> dict[str, Any]:
    payload = canonical_payload(edge)
    return {
        "from_record_id": payload["from_record_id"],
        "to_record_id": payload["to_record_id"],
        "relation": payload["relation"],
        "basis_refs": list(payload["basis_refs"]),
    }


def _origin_view(shard: DreamShard) -> dict[str, Any]:
    payload = canonical_payload(shard.origin)
    return {
        "kind": payload["kind"],
        "reference_state": _free_text_state(payload["reference"]),
        "context_reference_state": _free_text_state(payload["context_reference"]),
        "role_state": _free_text_state(payload["role_label"]),
    }


def _temporal_view(shard: DreamShard) -> dict[str, Any]:
    payload = canonical_payload(shard.temporal_context)
    return {
        "captured_at": payload["captured_at"],
        "reference_instant": payload["reference_instant"],
        "source_time_expression_state": _free_text_state(payload["source_time_expression"]),
        "locale_hint_state": _free_text_state(payload["locale_hint"]),
    }


def _public_diagnostics(values: tuple[str, ...]) -> list[str]:
    rendered = []
    for value in values:
        reason = value.rsplit(":", 1)[-1] if ":" in value else value
        rendered.append(_SAFE_DIAGNOSTICS.get(reason, "recall_diagnostic"))
    return sorted(dict.fromkeys(rendered))


def _status_value(status: RecallDigestStatus | object) -> str:
    return status.value if isinstance(status, RecallDigestStatus) else str(status)


def _enum_value(value: object) -> str:
    return getattr(value, "value", str(value))


def _free_text_state(value: object) -> str:
    return "absent" if value is None else "present_redacted"


__all__ = ["PUBLIC_SELECTION_BASIS", "PublicViewError", "public_recall_envelope"]
