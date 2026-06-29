"""DE1 Memory Substrate / Epistemic Core boundary for Dream Geometry V2.

Allowed: file-first Dream Shard, interpretation, revision, usage-state, and
ledger persistence protocols.
Forbidden: entity inference, geometry coverage, gravity computation, recall
ranking, OpenClaw access, runtime calls, natural-language interpretation, or
real memory mutation.
"""

from .store import MemorySubstrateStore, WriteResult, open_store
from .types import (
    FORMAT_VERSION,
    DreamShard,
    InterpretationRecord,
    LedgerEvent,
    OriginDescriptor,
    RevisionEdge,
    RevisionThread,
    TemporalContext,
    UsageStateTransition,
    canonical_json,
    canonical_payload,
    payload_key,
    record_id,
)

__all__ = [
    "FORMAT_VERSION",
    "DreamShard",
    "InterpretationRecord",
    "LedgerEvent",
    "MemorySubstrateStore",
    "OriginDescriptor",
    "RevisionEdge",
    "RevisionThread",
    "TemporalContext",
    "UsageStateTransition",
    "WriteResult",
    "canonical_json",
    "canonical_payload",
    "open_store",
    "payload_key",
    "record_id",
]
