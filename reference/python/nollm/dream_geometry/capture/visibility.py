"""CI1 explicit physical visibility selectors."""

from __future__ import annotations

from nollm.dream_geometry.evidence import DreamShard, MemorySubstrateStore

from .errors import CI1_INVALID_REQUEST, CaptureError
from .state_store import CaptureStateStore
from .types import VisibilityScope


class CaptureVisibility:
    def __init__(self, state_store: CaptureStateStore, evidence_store: MemorySubstrateStore):
        self.state_store = state_store
        self.evidence_store = evidence_store

    def session_window_ids(self, context_ref: str) -> tuple[str, ...]:
        _require_context_ref(context_ref)
        return self.state_store.read_visibility_ids(VisibilityScope.session_window, context_ref)

    def source_window_ids(self, context_ref: str) -> tuple[str, ...]:
        _require_context_ref(context_ref)
        return self.state_store.read_visibility_ids(VisibilityScope.source_window, context_ref)

    def session_window(self, context_ref: str) -> tuple[DreamShard, ...]:
        return tuple(self.evidence_store.get_dream_shard(shard_id) for shard_id in self.session_window_ids(context_ref))

    def source_window(self, context_ref: str) -> tuple[DreamShard, ...]:
        return tuple(self.evidence_store.get_dream_shard(shard_id) for shard_id in self.source_window_ids(context_ref))

    def persistent_explicit(self, shard_ids: tuple[str, ...]) -> tuple[DreamShard, ...]:
        if not isinstance(shard_ids, tuple) or not shard_ids:
            raise CaptureError(CI1_INVALID_REQUEST, "explicit_shard_ids_required")
        seen: set[str] = set()
        ordered: list[DreamShard] = []
        for shard_id in shard_ids:
            if not isinstance(shard_id, str) or not shard_id:
                raise CaptureError(CI1_INVALID_REQUEST, "explicit_shard_id_invalid")
            if shard_id in seen:
                continue
            seen.add(shard_id)
            ordered.append(self.evidence_store.get_dream_shard(shard_id))
        return tuple(ordered)


def _require_context_ref(value: str) -> None:
    if not isinstance(value, str) or not value or any(char in value for char in ("/", "\\")):
        raise CaptureError(CI1_INVALID_REQUEST, "context_ref_invalid")


__all__ = ["CaptureVisibility"]
