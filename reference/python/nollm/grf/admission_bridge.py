"""Explicit GRF capture-to-admission bridge prototype."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any

from .admission import MinimalAdmissionRecord
from .cell_address import CellAddress
from .evidence import EvidenceShardRecord
from .evidence_island import EvidenceIsland, EvidenceShardRef
from .fixed_point import Q16_ONE
from .local_patch import LocalPatch
from .placement import GeometryMark, PlacementCandidate, PlacementDecision, PlacementRecord, RejectionRecord, SCORE_FIELDS
from .placement_policy import GRFPlacementPolicy, POLICY_ID as DETERMINISTIC_POLICY_ID, PlacementRankingReport
from .source_window import SourceWindowRecord
from .storage import GRFFileStore


@dataclass(frozen=True)
class MissingSourceFallback:
    ref: str
    error: str = "missing_source"


@dataclass(frozen=True)
class GRFAdmissionBridgeResult:
    evidence_island: EvidenceIsland
    local_patch: LocalPatch
    placement_candidate: PlacementCandidate
    placement_decision: PlacementDecision
    geometry_mark: GeometryMark | None
    placement_record: PlacementRecord | None
    admission_record: MinimalAdmissionRecord | None
    rejection_record: RejectionRecord | None
    ranking_report: PlacementRankingReport | None = None


class GRFAdmissionBridge:
    def __init__(self, store: GRFFileStore) -> None:
        self.store = store

    def admit(self, shard: EvidenceShardRecord, window: SourceWindowRecord, policy_hint: dict[str, Any], decided_at: str) -> GRFAdmissionBridgeResult:
        """Legacy direct convenience: place then admit the resulting placement."""
        placed = self.place(shard, window, policy_hint, decided_at)
        if placed.placement_record is None:
            return placed
        admission = self.admit_existing_placement(shard, placed.placement_record.placement_id, decided_at, "validation_fixture")
        return replace(placed, admission_record=admission)

    def place(self, shard: EvidenceShardRecord, window: SourceWindowRecord, policy_hint: dict[str, Any], decided_at: str) -> GRFAdmissionBridgeResult:
        policy_id = policy_hint.get("policy_id", DETERMINISTIC_POLICY_ID)
        if policy_id == DETERMINISTIC_POLICY_ID:
            return self._place_deterministic(shard, window, policy_hint, decided_at)
        if policy_id != "validation_fixture_policy":
            raise ValueError("GRFAdmissionBridge only supports grf_deterministic_policy_v1 and validation_fixture_policy")

        target_cell = _target_cell(shard, policy_hint)
        ids = _BridgeIds(shard.shard_id + str(policy_hint.get("replacement_id", "")))
        shard_ref = EvidenceShardRef(shard.shard_id, shard.source_window_refs, shard.trust_state, shard.usage_state)
        island = EvidenceIsland(ids.island_id, (shard_ref,), tuple(sorted(set((*shard.source_window_refs, window.window_id)))), "validation_fixture", "placed")
        patch = LocalPatch(ids.patch_id, island.island_id, target_cell.chart_id, target_cell.profile_id, target_cell, (target_cell,), (), "placed", 0, 0)
        candidate = PlacementCandidate(ids.candidate_id, shard.shard_id, island.island_id, patch.patch_id, target_cell, _scores(policy_hint), _confidence(policy_hint), shard.source_window_refs, (shard.shard_id,))

        if policy_hint.get("reject"):
            decision = PlacementDecision(ids.decision_id, candidate.candidate_id, "reject", "validation_fixture", decided_at, ("validation_fixture_rejected",), None, "false_friend_risk")
            rejection = RejectionRecord(ids.rejection_id, candidate.candidate_id, shard.shard_id, decided_at, "validation_fixture", "false_friend_risk", (shard.shard_id,))
            self.store.write_evidence_island(island)
            self.store.write_local_patch(patch)
            self.store.write_placement_candidate(candidate)
            self.store.write_rejection_record(rejection, decided_at)
            return GRFAdmissionBridgeResult(island, patch, candidate, decision, None, None, None, rejection)

        decision = PlacementDecision(ids.decision_id, candidate.candidate_id, "place", "validation_fixture", decided_at, ("validation_fixture_policy",), target_cell, None)
        mark = GeometryMark(ids.mark_id, shard.shard_id, target_cell.profile_id, target_cell.chart_id, target_cell, "validation_fixture_policy", candidate.confidence_band, 0, "rf:grf1ik")
        placement = PlacementRecord(ids.placement_id, shard.shard_id, candidate.candidate_id, decision.decision_id, mark, island.island_id, patch.patch_id, (shard.shard_id,), target_cell.profile_id, "grf1ik_validation_v1")
        self.store.write_evidence_island(island)
        self.store.write_local_patch(patch)
        self.store.write_placement_candidate(candidate)
        self.store.write_placement_record(placement, decided_at)
        return GRFAdmissionBridgeResult(island, patch, candidate, decision, mark, placement, None, None)

    def admit_existing_placement(self, shard: EvidenceShardRecord, placement_id: str, admitted_at: str, admitted_by: str) -> MinimalAdmissionRecord:
        placement = self.store.read_placement_record(placement_id)
        if placement.shard_id != shard.shard_id:
            raise ValueError("placement/shard mismatch")
        if not placement.source_fallback_refs:
            raise ValueError("placement missing source fallback refs")
        conflicts = [record for record in self.store.minimal_admission_records() if record.placement_record.placement_id == placement_id]
        if conflicts:
            raise FileExistsError("placement already has an admission record")
        admission = MinimalAdmissionRecord(_BridgeIds(shard.shard_id).admission_id, shard.shard_id, placement, admitted_at, admitted_by)
        self.store.write_minimal_admission_record(admission, admitted_at)
        return admission

    def _place_deterministic(self, shard: EvidenceShardRecord, window: SourceWindowRecord, policy_hint: dict[str, Any], decided_at: str) -> GRFAdmissionBridgeResult:
        target_cell = _target_cell(shard, {"policy_id": "validation_fixture_policy", "chart_id": policy_hint.get("chart_id", "chart_policy")})
        ids = _BridgeIds(shard.shard_id + str(policy_hint.get("replacement_id", "")))
        shard_ref = EvidenceShardRef(shard.shard_id, shard.source_window_refs, shard.trust_state, shard.usage_state)
        island = EvidenceIsland(ids.island_id, (shard_ref,), tuple(sorted(set((*shard.source_window_refs, window.window_id)))), "validation_fixture", "placed")
        patch = LocalPatch(ids.patch_id, island.island_id, target_cell.chart_id, target_cell.profile_id, target_cell, (target_cell,), (), "placed", 0, 0)
        ranked, decision, report = GRFPlacementPolicy().evaluate(
            shard,
            window,
            island,
            patch,
            (),
            false_friend_risk=bool(policy_hint.get("false_friend_risk") or policy_hint.get("reject")),
            excessive_residual=bool(policy_hint.get("excessive_residual")),
            force_defer=bool(policy_hint.get("defer")),
        )
        replacement_id = str(policy_hint.get("replacement_id", ""))
        if replacement_id:
            # The policy intentionally derives its canonical ranking from the
            # shard. Re-placement retains that ranking but must not overwrite
            # its previous persisted candidate or decision records.
            ranked = tuple(replace(item, candidate_id=f"{item.candidate_id}:{ids.stem}") for item in ranked)
            selected_candidate_id = ranked[0].candidate_id
            decision = replace(
                decision,
                decision_id=f"{decision.decision_id}:{ids.stem}",
                candidate_id=selected_candidate_id,
            )
            report = replace(
                report,
                selected_candidate_id=selected_candidate_id,
                ranked_candidate_ids=tuple(item.candidate_id for item in ranked),
            )
        candidate = ranked[0]
        if decision.decision == "reject":
            rejection = RejectionRecord(ids.rejection_id, candidate.candidate_id, shard.shard_id, decided_at, "host_rule", decision.rejection_reason or "false_friend_risk", (shard.shard_id,))
            self.store.write_evidence_island(island)
            self.store.write_local_patch(patch)
            self.store.write_placement_candidate(candidate)
            self.store.write_rejection_record(rejection, decided_at)
            return GRFAdmissionBridgeResult(island, patch, candidate, decision, None, None, None, rejection, report)
        if decision.decision == "defer":
            rejection = RejectionRecord(ids.rejection_id, candidate.candidate_id, shard.shard_id, decided_at, "host_rule", "insufficient_evidence", (shard.shard_id,))
            self.store.write_evidence_island(island)
            self.store.write_local_patch(patch)
            self.store.write_placement_candidate(candidate)
            self.store.write_rejection_record(rejection, decided_at)
            return GRFAdmissionBridgeResult(island, patch, candidate, decision, None, None, None, rejection, report)
        mark = GeometryMark(ids.mark_id, shard.shard_id, candidate.target_cell.profile_id, candidate.target_cell.chart_id, candidate.target_cell, DETERMINISTIC_POLICY_ID, candidate.confidence_band, 0, "rf:grf1opq")
        placement = PlacementRecord(ids.placement_id, shard.shard_id, candidate.candidate_id, decision.decision_id, mark, island.island_id, patch.patch_id, (shard.shard_id,), candidate.target_cell.profile_id, "grf1opq_policy_v1")
        self.store.write_evidence_island(island)
        self.store.write_local_patch(patch)
        self.store.write_placement_candidate(candidate)
        self.store.write_placement_record(placement, decided_at)
        return GRFAdmissionBridgeResult(island, patch, candidate, decision, mark, placement, None, None, report)


def resolve_source_fallback(ref: str, store: GRFFileStore) -> EvidenceShardRecord | MissingSourceFallback:
    try:
        return store.read_evidence_shard(ref)
    except FileNotFoundError:
        return MissingSourceFallback(ref)


@dataclass(frozen=True)
class _BridgeIds:
    shard_id: str

    @property
    def stem(self) -> str:
        return sha256(self.shard_id.encode("utf-8")).hexdigest()[:24]

    @property
    def island_id(self) -> str:
        return f"island:grf1ik:{self.stem}"

    @property
    def patch_id(self) -> str:
        return f"patch:grf1ik:{self.stem}"

    @property
    def candidate_id(self) -> str:
        return f"candidate:grf1ik:{self.stem}"

    @property
    def decision_id(self) -> str:
        return f"decision:grf1ik:{self.stem}"

    @property
    def mark_id(self) -> str:
        return f"mark:grf1ik:{self.stem}"

    @property
    def placement_id(self) -> str:
        return f"placement:grf1ik:{self.stem}"

    @property
    def admission_id(self) -> str:
        return f"admission:grf1ik:{self.stem}"

    @property
    def rejection_id(self) -> str:
        return f"rejection:grf1ik:{self.stem}"


def _target_cell(shard: EvidenceShardRecord, policy_hint: dict[str, Any]) -> CellAddress:
    target = policy_hint.get("target_cell")
    if isinstance(target, CellAddress):
        return target
    if isinstance(target, dict):
        return CellAddress(target["profile_id"], target["chart_id"], target["layer"], target["q"], target["r"], target.get("phase"))
    digest = sha256(shard.shard_id.encode("utf-8")).digest()
    q = int(digest[0] % 11) - 5
    r = int(digest[1] % 11) - 5
    return CellAddress("eisenstein_exact_v1", str(policy_hint.get("chart_id", "chart_validation")), 0, q, r)


def _confidence(policy_hint: dict[str, Any]) -> str:
    if policy_hint.get("target_cell") is not None:
        return "high"
    return str(policy_hint.get("confidence_band", "medium"))


def _scores(policy_hint: dict[str, Any]) -> dict[str, int]:
    base = {field: 0 for field in SCORE_FIELDS}
    if policy_hint.get("target_cell") is not None:
        base["local_fit_q16"] = Q16_ONE
        base["coverage_gain_q16"] = Q16_ONE // 2
    else:
        base["local_fit_q16"] = Q16_ONE // 2
        base["compute_cost_q16"] = Q16_ONE // 4
    return base
