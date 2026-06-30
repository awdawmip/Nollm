"""Dream Geometry DR1 Recall Resolver.

Allowed: read-only deterministic recall digest construction over explicit DR1
universes.
Forbidden: persistence, upstream mutation, adapters, runtime access, OpenClaw,
NLP, semantic search, embeddings, vector search, or database-backed recall.
"""

from .resolver import resolve_recall
from .types import (
    EvidenceQualification,
    ProbeAtom,
    ProposalAdmission,
    ProposalReadRecord,
    RecallDigest,
    RecallDigestStatus,
    RecallPolicy,
    RecallResultItem,
    RecallUniverse,
    ResolvedRelativeSpan,
    RuntimeTimeResolution,
    TraceSemanticProjection,
    TraversalRecord,
)

__all__ = [
    "EvidenceQualification",
    "ProbeAtom",
    "ProposalAdmission",
    "ProposalReadRecord",
    "RecallDigest",
    "RecallDigestStatus",
    "RecallPolicy",
    "RecallResultItem",
    "RecallUniverse",
    "ResolvedRelativeSpan",
    "RuntimeTimeResolution",
    "TraceSemanticProjection",
    "TraversalRecord",
    "resolve_recall",
]
