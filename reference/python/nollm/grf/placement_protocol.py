"""Bounded host/LLM placement protocol; validation never infers semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cell_address import CellAddress


PLACEMENT_ACTIONS = frozenset({"reuse", "new", "revision", "stitch", "defer"})

PLACEMENT_REQUEST_SCHEMA: dict[str, object] = {
    "type": "object", "additionalProperties": False,
    "required": ["request_id", "evidence_shard_id", "candidate_cells"],
    "properties": {
        "request_id": {"type": "string"}, "evidence_shard_id": {"type": "string"},
        "session_items": {"type": "array", "maxItems": 8}, "source_revision_refs": {"type": "array", "maxItems": 8},
        "referenced_placements": {"type": "array", "maxItems": 12}, "nearby_cell_occupancy": {"type": "array", "maxItems": 6},
        "stitch_candidates": {"type": "array", "maxItems": 4}, "candidate_cells": {"type": "array", "minItems": 1, "maxItems": 12},
        "candidate_reuse_placements": {"type": "array", "maxItems": 12},
    },
}

PLACEMENT_DECISION_SCHEMA: dict[str, object] = {
    "type": "object", "additionalProperties": False,
    "required": ["decision_id", "request_id", "action", "reason"],
    "properties": {
        "decision_id": {"type": "string"}, "request_id": {"type": "string"},
        "action": {"type": "string", "enum": sorted(PLACEMENT_ACTIONS)}, "reason": {"type": "string"},
        "selected_cell": {"type": "object"}, "candidate_id": {"type": "string"}, "placement_id": {"type": "string"},
        "reuse_placement_id": {"type": "string"}, "stitch_id": {"type": "string"},
    },
}


@dataclass(frozen=True)
class NollmPlacementRequest:
    request_id: str
    evidence_shard_id: str
    candidate_cells: tuple[CellAddress, ...]
    session_items: tuple[str, ...] = ()
    source_revision_refs: tuple[str, ...] = ()
    referenced_placements: tuple[str, ...] = ()
    nearby_cell_occupancy: tuple[str, ...] = ()
    stitch_candidates: tuple[str, ...] = ()
    candidate_reuse_placements: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.request_id, "request_id")
        _text(self.evidence_shard_id, "evidence_shard_id")
        if not self.candidate_cells or len(self.candidate_cells) > 12 or any(not isinstance(cell, CellAddress) for cell in self.candidate_cells):
            raise ValueError("candidate_cells must contain 1..12 explicit CellAddress values")
        for values, maximum, label in ((self.session_items, 8, "session_items"), (self.source_revision_refs, 8, "source_revision_refs"), (self.referenced_placements, 12, "referenced_placements"), (self.nearby_cell_occupancy, 6, "nearby_cell_occupancy"), (self.stitch_candidates, 4, "stitch_candidates"), (self.candidate_reuse_placements, 12, "candidate_reuse_placements")):
            _refs(values, maximum, label)

    def to_mapping(self) -> dict[str, object]:
        return {"request_id": self.request_id, "evidence_shard_id": self.evidence_shard_id, "candidate_cells": [cell.to_mapping() for cell in self.candidate_cells], "session_items": list(self.session_items), "source_revision_refs": list(self.source_revision_refs), "referenced_placements": list(self.referenced_placements), "nearby_cell_occupancy": list(self.nearby_cell_occupancy), "stitch_candidates": list(self.stitch_candidates), "candidate_reuse_placements": list(self.candidate_reuse_placements)}


@dataclass(frozen=True)
class NollmPlacementDecision:
    decision_id: str
    request_id: str
    action: str
    reason: str
    selected_cell: CellAddress | None = None
    candidate_id: str | None = None
    placement_id: str | None = None
    reuse_placement_id: str | None = None
    stitch_id: str | None = None

    def __post_init__(self) -> None:
        _text(self.decision_id, "decision_id")
        _text(self.request_id, "request_id")
        _text(self.reason, "reason")
        if self.action not in PLACEMENT_ACTIONS:
            raise ValueError("unknown placement action")
        if self.action == "defer":
            if any(value is not None for value in (self.selected_cell, self.candidate_id, self.placement_id, self.reuse_placement_id, self.stitch_id)):
                raise ValueError("defer cannot carry mutation references")
        elif self.action == "reuse":
            _text(self.reuse_placement_id, "reuse_placement_id")
        else:
            if not isinstance(self.selected_cell, CellAddress):
                raise ValueError("mutation action requires selected_cell")
            _text(self.candidate_id, "candidate_id")
            _text(self.placement_id, "placement_id")
            if self.action == "stitch":
                _text(self.stitch_id, "stitch_id")

    def to_mapping(self) -> dict[str, object]:
        return {"decision_id": self.decision_id, "request_id": self.request_id, "action": self.action, "reason": self.reason, "selected_cell": None if self.selected_cell is None else self.selected_cell.to_mapping(), "candidate_id": self.candidate_id, "placement_id": self.placement_id, "reuse_placement_id": self.reuse_placement_id, "stitch_id": self.stitch_id}


def validate_decision(request: NollmPlacementRequest, decision: NollmPlacementDecision) -> None:
    """Validate only declared identities, candidate membership, and action shape."""
    if decision.request_id != request.request_id:
        raise ValueError("decision request_id mismatch")
    if decision.action in {"new", "revision", "stitch"} and decision.selected_cell not in request.candidate_cells:
        raise ValueError("decision cell is outside the explicit candidate set")
    if decision.action == "reuse" and decision.reuse_placement_id not in request.candidate_reuse_placements:
        raise ValueError("reuse placement is outside the explicit candidate set")
    if decision.action == "stitch" and decision.stitch_id not in request.stitch_candidates:
        raise ValueError("stitch is outside the explicit candidate set")


def decision_from_mapping(payload: dict[str, Any]) -> NollmPlacementDecision:
    cell = payload.get("selected_cell")
    selected = None if cell is None else CellAddress(str(cell["profile_id"]), str(cell["chart_id"]), int(cell["layer"]), int(cell["q"]), int(cell["r"]), cell.get("phase"))
    return NollmPlacementDecision(str(payload["decision_id"]), str(payload["request_id"]), str(payload["action"]), str(payload["reason"]), selected, _optional(payload, "candidate_id"), _optional(payload, "placement_id"), _optional(payload, "reuse_placement_id"), _optional(payload, "stitch_id"))


def _optional(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return None if value is None else str(value)


def _text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")


def _refs(values: tuple[str, ...], maximum: int, label: str) -> None:
    if not isinstance(values, tuple) or len(values) > maximum or any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{label} must be at most {maximum} non-empty refs")
