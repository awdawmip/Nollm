"""Explicit decision-to-placement bridge; Core does not infer semantics."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .admission import MinimalAdmissionRecord
from .cell_address import CellAddress
from .evidence import EvidenceShardRecord
from .evidence_island import EvidenceIsland, EvidenceShardRef
from .local_patch import LocalPatch
from .placement import GeometryMark, PlacementCandidate, PlacementDecision, PlacementRecord, RejectionRecord
from .source_window import SourceWindowRecord
from .storage import GRFFileStore


@dataclass(frozen=True)
class MissingSourceFallback:
    ref: str
    error: str = "missing_source"


@dataclass(frozen=True)
class GRFAdmissionBridgeResult:
    evidence_island: EvidenceIsland | None
    local_patch: LocalPatch | None
    placement_candidate: PlacementCandidate | None
    placement_decision: PlacementDecision
    geometry_mark: GeometryMark | None
    placement_record: PlacementRecord | None
    admission_record: MinimalAdmissionRecord | None
    rejection_record: RejectionRecord | None
    ranking_report: object | None = None


class GRFAdmissionBridge:
    def __init__(self, store: GRFFileStore) -> None:
        self.store = store

    def admit(self, shard: EvidenceShardRecord, window: SourceWindowRecord, decision: dict[str, Any], decided_at: str) -> GRFAdmissionBridgeResult:
        placed = self.place(shard, window, decision, decided_at)
        if placed.placement_record is None:
            return placed
        admission = self.admit_existing_placement(shard, placed.placement_record.placement_id, decided_at, str(decision.get("admitted_by", "openclaw_llm")))
        return GRFAdmissionBridgeResult(placed.evidence_island, placed.local_patch, placed.placement_candidate, placed.placement_decision, placed.geometry_mark, placed.placement_record, admission, None)

    def place(self, shard: EvidenceShardRecord, window: SourceWindowRecord, decision: dict[str, Any], decided_at: str) -> GRFAdmissionBridgeResult:
        action = str(decision.get("action", "defer"))
        if action not in {"place", "defer", "reject"}:
            raise ValueError("placement action must be place, defer, or reject")
        decided_by = str(decision.get("decided_by", "openclaw_llm"))
        decision_id = _required(decision, "decision_id")
        candidate_id = _required(decision, "candidate_id")
        reasons = tuple(str(item) for item in decision.get("reasons", ("host_decision",)))
        if action != "place":
            placement_decision = PlacementDecision(decision_id, candidate_id, action, decided_by, decided_at, reasons, None, str(decision.get("rejection_reason", "insufficient_evidence")) if action == "reject" else None)
            rejection = RejectionRecord(f"rejection:{_stem(decision_id)}", candidate_id, shard.shard_id, decided_at, decided_by, placement_decision.rejection_reason or "insufficient_evidence", shard.source_window_refs)
            self.store.write_rejection_record(rejection, decided_at)
            return GRFAdmissionBridgeResult(None, None, None, placement_decision, None, None, None, rejection)
        cell = _cell(decision.get("selected_cell"))
        ids = _Ids(decision_id)
        shard_ref = EvidenceShardRef(shard.shard_id, shard.source_window_refs, shard.trust_state, shard.usage_state)
        island = EvidenceIsland(ids.island_id, (shard_ref,), tuple(sorted(set((*shard.source_window_refs, window.window_id)))), "manual_group", "placed")
        patch = LocalPatch(ids.patch_id, island.island_id, cell.chart_id, cell.profile_id, cell, (cell,), (), "placed", 0, 0)
        candidate = PlacementCandidate(candidate_id, shard.shard_id, island.island_id, patch.patch_id, cell, str(decision.get("confidence_band", "medium")), shard.source_window_refs, (shard.shard_id,))
        placement_decision = PlacementDecision(decision_id, candidate_id, "place", decided_by, decided_at, reasons, cell, None)
        mark = GeometryMark(ids.mark_id, shard.shard_id, cell.profile_id, cell.chart_id, cell, "host_declared", candidate.confidence_band, int(decision.get("uncertainty_q16", 0)), str(decision.get("relation_field_ref", "field:geometry")))
        placement = PlacementRecord(_required(decision, "placement_id"), shard.shard_id, candidate_id, decision_id, mark, island.island_id, patch.patch_id, shard.source_window_refs, cell.profile_id, "geometry_native_v1", False)
        self.store.write_evidence_island(island)
        self.store.write_local_patch(patch)
        self.store.write_placement_candidate(candidate)
        self.store.write_placement_record(placement, decided_at)
        return GRFAdmissionBridgeResult(island, patch, candidate, placement_decision, mark, placement, None, None)

    def admit_existing_placement(self, shard: EvidenceShardRecord, placement_id: str, admitted_at: str, admitted_by: str) -> MinimalAdmissionRecord:
        placement = self.store.read_placement_record(placement_id)
        if placement.shard_id != shard.shard_id:
            raise ValueError("placement/shard mismatch")
        if any(record.placement_record.placement_id == placement_id for record in self.store.minimal_admission_records()):
            raise FileExistsError("placement already has an admission record")
        admission = MinimalAdmissionRecord(f"admission:{_stem(placement_id)}", shard.shard_id, placement, admitted_at, admitted_by)
        self.store.write_minimal_admission_record(admission, admitted_at)
        return admission


def resolve_source_fallback(ref: str, store: GRFFileStore) -> EvidenceShardRecord | MissingSourceFallback:
    try:
        return store.read_evidence_shard(ref)
    except FileNotFoundError:
        return MissingSourceFallback(ref)


@dataclass(frozen=True)
class _Ids:
    decision_id: str

    @property
    def stem(self) -> str:
        return _stem(self.decision_id)

    @property
    def island_id(self) -> str:
        return f"island:geometry:{self.stem}"

    @property
    def patch_id(self) -> str:
        return f"patch:geometry:{self.stem}"

    @property
    def mark_id(self) -> str:
        return f"mark:geometry:{self.stem}"


def _required(decision: dict[str, Any], key: str) -> str:
    value = decision.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"host decision requires {key}")
    return value


def _cell(value: object) -> CellAddress:
    if isinstance(value, CellAddress):
        return value
    if isinstance(value, dict):
        return CellAddress(str(value["profile_id"]), str(value["chart_id"]), int(value["layer"]), int(value["q"]), int(value["r"]), value.get("phase"))
    raise ValueError("place decision requires explicit selected_cell")


def _stem(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:24]
