"""DR1 evidence qualification from DE1 usage state only."""

from __future__ import annotations

from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.protocol.contracts import UsageState

from .types import EvidenceQualification, RecallPolicy


def qualify_shard(store: MemorySubstrateStore, shard_id: str, policy: RecallPolicy) -> EvidenceQualification:
    store.get_dream_shard(shard_id)
    usage = store.get_usage_state(shard_id)
    if usage is UsageState.active:
        return EvidenceQualification(shard_id, usage.value, "primary_active", True, ("DR1_EVIDENCE_ACTIVE",))
    if usage is UsageState.tentative:
        return EvidenceQualification(
            shard_id,
            usage.value,
            "primary_tentative" if policy.include_tentative else "excluded_tentative",
            policy.include_tentative,
            ("DR1_EVIDENCE_TENTATIVE",),
        )
    if usage is UsageState.retired:
        return EvidenceQualification(shard_id, usage.value, "context_retired", False, ("DR1_EVIDENCE_RETIRED_CONTEXT_ONLY",))
    if usage is UsageState.rejected:
        return EvidenceQualification(shard_id, usage.value, "context_rejected", False, ("DR1_EVIDENCE_REJECTED_CONTEXT_ONLY",))
    raise ValueError("unsupported usage state")


__all__ = ["qualify_shard"]
