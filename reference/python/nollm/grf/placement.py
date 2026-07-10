"""GRF placement and geometry mark prototype objects."""

from __future__ import annotations

from dataclasses import dataclass

from .cell_address import CellAddress
from .fixed_point import Q16_ONE

CONFIDENCE_BANDS = frozenset({"low", "medium", "high"})
DECISIONS = frozenset({"place", "defer", "reject"})
DECIDED_BY = frozenset({"human", "host_rule", "validation_fixture", "llm_assisted_review", "openclaw_llm"})
REJECTION_REASONS = frozenset({"insufficient_evidence", "ambiguous_location", "false_friend_risk", "excessive_residual", "duplicate_candidate", "out_of_scope"})


@dataclass(frozen=True)
class PlacementCandidate:
    candidate_id: str
    shard_id: str
    island_id: str
    patch_id: str
    target_cell: CellAddress
    confidence_band: str
    source_window_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for label, value in (("candidate_id", self.candidate_id), ("shard_id", self.shard_id), ("island_id", self.island_id), ("patch_id", self.patch_id)):
            _require_text(value, label)
        if not isinstance(self.target_cell, CellAddress):
            raise TypeError("target_cell must be CellAddress")
        if self.confidence_band not in CONFIDENCE_BANDS:
            raise ValueError("unknown confidence_band")
        _require_text_refs(self.source_window_refs, "source_window_refs", allow_empty=True)
        _require_text_refs(self.evidence_refs, "evidence_refs")

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "shard_id": self.shard_id,
            "island_id": self.island_id,
            "patch_id": self.patch_id,
            "target_cell": self.target_cell.to_mapping(),
            "confidence_band": self.confidence_band,
            "source_window_refs": tuple(sorted(self.source_window_refs)),
            "evidence_refs": tuple(sorted(self.evidence_refs)),
        }


@dataclass(frozen=True)
class PlacementDecision:
    decision_id: str
    candidate_id: str
    decision: str
    decided_by: str
    decided_at: str
    reasons: tuple[str, ...]
    selected_cell: CellAddress | None
    rejection_reason: str | None

    def __post_init__(self) -> None:
        for label, value in (("decision_id", self.decision_id), ("candidate_id", self.candidate_id), ("decided_at", self.decided_at)):
            _require_text(value, label)
        if self.decision not in DECISIONS:
            raise ValueError("unknown placement decision")
        if self.decided_by not in DECIDED_BY:
            raise ValueError("unknown decided_by")
        _require_text_refs(self.reasons, "reasons")
        if self.decision == "place" and not isinstance(self.selected_cell, CellAddress):
            raise ValueError("place requires selected_cell")
        if self.decision == "reject" and self.rejection_reason not in REJECTION_REASONS:
            raise ValueError("reject requires rejection_reason")
        if self.decision == "defer" and self.selected_cell is not None:
            raise ValueError("defer cannot have selected_cell")

    def to_mapping(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "candidate_id": self.candidate_id,
            "decision": self.decision,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "reasons": tuple(sorted(self.reasons)),
            "selected_cell": None if self.selected_cell is None else self.selected_cell.to_mapping(),
            "rejection_reason": self.rejection_reason,
            "not_truth_confirmation": True,
        }


@dataclass(frozen=True)
class GeometryMark:
    mark_id: str
    shard_id: str
    profile_id: str
    chart_id: str
    cell: CellAddress
    placement_method: str
    confidence_band: str
    uncertainty_q16: int
    relation_field_ref: str

    def __post_init__(self) -> None:
        for label, value in (("mark_id", self.mark_id), ("shard_id", self.shard_id), ("profile_id", self.profile_id), ("chart_id", self.chart_id), ("placement_method", self.placement_method), ("relation_field_ref", self.relation_field_ref)):
            _require_text(value, label)
        if not isinstance(self.cell, CellAddress):
            raise TypeError("cell must be CellAddress")
        if self.cell.profile_id != self.profile_id or self.cell.chart_id != self.chart_id:
            raise ValueError("cell must match mark profile/chart")
        if self.confidence_band not in CONFIDENCE_BANDS:
            raise ValueError("unknown confidence_band")
        _require_q16(self.uncertainty_q16, "uncertainty_q16")

    def to_mapping(self) -> dict[str, object]:
        return {
            "mark_id": self.mark_id,
            "shard_id": self.shard_id,
            "profile_id": self.profile_id,
            "chart_id": self.chart_id,
            "cell": self.cell.to_mapping(),
            "placement_method": self.placement_method,
            "confidence_band": self.confidence_band,
            "uncertainty_q16": self.uncertainty_q16,
            "relation_field_ref": self.relation_field_ref,
            "not_fact_confirmation": True,
            "not_truth_score": True,
            "inherits_relation_field": True,
        }


@dataclass(frozen=True)
class PlacementRecord:
    placement_id: str
    shard_id: str
    candidate_id: str
    decision_id: str
    geometry_mark: GeometryMark
    island_id: str
    patch_id: str
    source_fallback_refs: tuple[str, ...]
    replay_profile_id: str
    replay_template_version: str
    deterministic: bool = True

    def __post_init__(self) -> None:
        for label, value in (("placement_id", self.placement_id), ("shard_id", self.shard_id), ("candidate_id", self.candidate_id), ("decision_id", self.decision_id), ("island_id", self.island_id), ("patch_id", self.patch_id), ("replay_profile_id", self.replay_profile_id), ("replay_template_version", self.replay_template_version)):
            _require_text(value, label)
        if not isinstance(self.geometry_mark, GeometryMark):
            raise TypeError("geometry_mark must be GeometryMark")
        if self.geometry_mark.shard_id != self.shard_id:
            raise ValueError("geometry mark shard mismatch")
        if self.replay_profile_id != self.geometry_mark.profile_id:
            raise ValueError("replay_profile_id must match geometry mark")
        _require_text_refs(self.source_fallback_refs, "source_fallback_refs")
        if type(self.deterministic) is not bool:
            raise TypeError("deterministic must be bool")

    def to_mapping(self) -> dict[str, object]:
        return {
            "placement_id": self.placement_id,
            "shard_id": self.shard_id,
            "candidate_id": self.candidate_id,
            "decision_id": self.decision_id,
            "geometry_mark": self.geometry_mark.to_mapping(),
            "island_id": self.island_id,
            "patch_id": self.patch_id,
            "source_fallback_refs": tuple(sorted(self.source_fallback_refs)),
            "replay_profile_id": self.replay_profile_id,
            "replay_template_version": self.replay_template_version,
            "deterministic": self.deterministic,
            "does_not_copy_coverage_entries": True,
        }


@dataclass(frozen=True)
class RejectionRecord:
    rejection_id: str
    candidate_id: str
    shard_id: str
    rejected_at: str
    rejected_by: str
    reason: str
    source_fallback_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for label, value in (("rejection_id", self.rejection_id), ("candidate_id", self.candidate_id), ("shard_id", self.shard_id), ("rejected_at", self.rejected_at)):
            _require_text(value, label)
        if self.rejected_by not in DECIDED_BY:
            raise ValueError("unknown rejected_by")
        if self.reason not in REJECTION_REASONS:
            raise ValueError("unknown rejection reason")
        _require_text_refs(self.source_fallback_refs, "source_fallback_refs")

    def to_mapping(self) -> dict[str, object]:
        return {
            "rejection_id": self.rejection_id,
            "candidate_id": self.candidate_id,
            "shard_id": self.shard_id,
            "rejected_at": self.rejected_at,
            "rejected_by": self.rejected_by,
            "reason": self.reason,
            "source_fallback_refs": tuple(sorted(self.source_fallback_refs)),
        }


def _require_q16(value: int, label: str) -> None:
    if type(value) is not int or value < 0 or value > Q16_ONE:
        raise ValueError(f"{label} must be Q16 integer")


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")


def _require_text_refs(values: tuple[str, ...], label: str, allow_empty: bool = False) -> None:
    if not isinstance(values, tuple) or (not allow_empty and not values) or any(not isinstance(value, str) or value == "" for value in values):
        raise ValueError(f"{label} must be a tuple of non-empty text")
