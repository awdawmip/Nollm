"""Evidence islands for GRF stitching prototypes."""

from __future__ import annotations

from dataclasses import dataclass, replace

ISLAND_STATES = frozenset({"floating", "patch_candidate", "placed", "stitch_candidate", "stitched", "archived"})
ISLAND_REASONS = frozenset({"same_session_window", "same_source_document", "same_task_residue", "manual_group", "validation_fixture"})
_ISLAND_TRANSITIONS = {
    "floating": frozenset({"patch_candidate", "archived"}),
    "patch_candidate": frozenset({"placed", "archived"}),
    "placed": frozenset({"stitch_candidate", "archived"}),
    "stitch_candidate": frozenset({"stitched", "archived"}),
    "stitched": frozenset({"archived"}),
    "archived": frozenset(),
}


@dataclass(frozen=True, order=True)
class EvidenceShardRef:
    shard_id: str
    source_window_refs: tuple[str, ...]
    trust_state: str
    usage_state: str

    def __post_init__(self) -> None:
        if not isinstance(self.shard_id, str) or self.shard_id == "":
            raise ValueError("shard_id must be non-empty text")
        if not isinstance(self.source_window_refs, tuple) or any(not isinstance(ref, str) for ref in self.source_window_refs):
            raise TypeError("source_window_refs must be a tuple of text")
        if not isinstance(self.trust_state, str) or self.trust_state == "":
            raise ValueError("trust_state must be non-empty text")
        if not isinstance(self.usage_state, str) or self.usage_state == "":
            raise ValueError("usage_state must be non-empty text")

    def to_mapping(self) -> dict[str, object]:
        return {
            "shard_id": self.shard_id,
            "source_window_refs": tuple(sorted(self.source_window_refs)),
            "trust_state": self.trust_state,
            "usage_state": self.usage_state,
        }


@dataclass(frozen=True)
class EvidenceIsland:
    island_id: str
    shard_refs: tuple[EvidenceShardRef, ...]
    source_window_refs: tuple[str, ...]
    island_reason: str
    state: str

    def __post_init__(self) -> None:
        if not isinstance(self.island_id, str) or self.island_id == "":
            raise ValueError("island_id must be non-empty text")
        if not self.shard_refs:
            raise ValueError("shard_refs cannot be empty")
        ids = [ref.shard_id for ref in self.shard_refs]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate shard_id")
        if not isinstance(self.source_window_refs, tuple) or any(not isinstance(ref, str) for ref in self.source_window_refs):
            raise TypeError("source_window_refs must be a tuple of text")
        if self.island_reason not in ISLAND_REASONS:
            raise ValueError("unknown island_reason")
        if self.state not in ISLAND_STATES:
            raise ValueError("unknown island state")

    def transition(self, next_state: str) -> "EvidenceIsland":
        if next_state not in _ISLAND_TRANSITIONS[self.state]:
            raise ValueError("invalid island state transition")
        return replace(self, state=next_state)

    def to_mapping(self) -> dict[str, object]:
        return {
            "island_id": self.island_id,
            "shard_refs": tuple(ref.to_mapping() for ref in sorted(self.shard_refs, key=lambda item: item.shard_id)),
            "source_window_refs": tuple(sorted(self.source_window_refs)),
            "island_reason": self.island_reason,
            "state": self.state,
            "not_topic_folder": True,
            "not_truth_owner": True,
        }
