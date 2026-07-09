"""Minimal GRF admission record."""

from __future__ import annotations

from dataclasses import dataclass

from .placement import PlacementRecord

ADMISSION_STATES = frozenset({"admitted", "superseded", "rejected"})
ADMITTED_BY = frozenset({"human", "host_rule", "validation_fixture", "llm_assisted_review"})


@dataclass(frozen=True)
class MinimalAdmissionRecord:
    admission_id: str
    shard_id: str
    placement_record: PlacementRecord
    admitted_at: str
    admitted_by: str
    state: str = "admitted"
    replay_minimal: bool = True

    def __post_init__(self) -> None:
        for label, value in (("admission_id", self.admission_id), ("shard_id", self.shard_id), ("admitted_at", self.admitted_at)):
            if not isinstance(value, str) or value == "":
                raise ValueError(f"{label} must be non-empty text")
        if not isinstance(self.placement_record, PlacementRecord):
            raise TypeError("placement_record must be PlacementRecord")
        if self.placement_record.shard_id != self.shard_id:
            raise ValueError("placement shard mismatch")
        if self.admitted_by not in ADMITTED_BY:
            raise ValueError("unknown admitted_by")
        if self.state not in ADMISSION_STATES:
            raise ValueError("unknown admission state")
        if type(self.replay_minimal) is not bool:
            raise TypeError("replay_minimal must be bool")

    def to_mapping(self) -> dict[str, object]:
        return {
            "admission_id": self.admission_id,
            "shard_id": self.shard_id,
            "placement_record": self.placement_record.to_mapping(),
            "admitted_at": self.admitted_at,
            "admitted_by": self.admitted_by,
            "state": self.state,
            "replay_minimal": self.replay_minimal,
            "admission_is_not_memory_existence_proof": True,
            "coverage_edges_inherited_from_profile": True,
            "does_not_copy_coverage_edge_list": True,
            "does_not_copy_semantic_edge_list": True,
            "not_truth_confirmation": True,
        }
