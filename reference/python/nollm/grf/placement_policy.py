"""Deterministic GRF placement policy prototype."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .cell_address import CellAddress
from .evidence import EvidenceShardRecord
from .evidence_island import EvidenceIsland
from .fixed_point import Q16_ONE
from .local_patch import LocalPatch
from .placement import PlacementCandidate, PlacementDecision, SCORE_FIELDS
from .source_window import SourceWindowRecord

POLICY_ID = "grf_deterministic_policy_v1"
EXTENDED_SCORE_FIELDS = (*SCORE_FIELDS, "source_window_affinity_q16", "fallback_stability_q16")


@dataclass(frozen=True)
class PlacementPolicyConfig:
    policy_id: str = POLICY_ID
    profile_id: str = "eisenstein_exact_v1"
    chart_id: str = "chart_policy"
    max_candidates: int = 5
    defer_threshold_q16: int = Q16_ONE // 5
    reject_residual_threshold_q16: int = (Q16_ONE * 3) // 4
    dense_cell_threshold: int = 8


@dataclass(frozen=True)
class PlacementRankingReport:
    policy_id: str
    shard_id: str
    selected_candidate_id: str | None
    decision: str
    ranked_candidate_ids: tuple[str, ...]
    explanations: tuple[str, ...]
    score_fields: tuple[str, ...] = EXTENDED_SCORE_FIELDS
    deterministic_q16: bool = True

    def to_mapping(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "shard_id": self.shard_id,
            "selected_candidate_id": self.selected_candidate_id,
            "decision": self.decision,
            "ranked_candidate_ids": self.ranked_candidate_ids,
            "explanations": self.explanations,
            "score_fields": self.score_fields,
            "deterministic_q16": self.deterministic_q16,
            "no_embedding": True,
            "no_global_search": True,
            "no_semantic_edge": True,
        }


class PlacementCandidateGenerator:
    def __init__(self, config: PlacementPolicyConfig | None = None) -> None:
        self.config = config or PlacementPolicyConfig()

    def generate(
        self,
        shard: EvidenceShardRecord,
        window: SourceWindowRecord,
        island: EvidenceIsland | None = None,
        patch: LocalPatch | None = None,
        existing_placements: tuple[object, ...] = (),
    ) -> tuple[PlacementCandidate, ...]:
        cells = (
            _source_window_cell(window.window_id, self.config),
            _island_cell(island, self.config),
            _patch_boundary_cell(patch, self.config),
            _hash_cell(shard.shard_id, self.config),
            _density_relief_cell(existing_placements, self.config),
        )
        unique: list[CellAddress] = []
        for cell in cells:
            if cell not in unique:
                unique.append(cell)
        candidates = []
        for index, cell in enumerate(unique[: self.config.max_candidates]):
            candidate_id = f"candidate:{self.config.policy_id}:{_short(shard.shard_id)}:{index}"
            candidates.append(
                PlacementCandidate(
                    candidate_id,
                    shard.shard_id,
                    island.island_id if island is not None else f"island:policy:{_short(shard.shard_id)}",
                    patch.patch_id if patch is not None else f"patch:policy:{_short(shard.shard_id)}",
                    cell,
                    _placement_scores(index),
                    "high" if index == 0 else "medium",
                    shard.source_window_refs,
                    (shard.shard_id,),
                )
            )
        return tuple(candidates)


class GRFPlacementPolicy:
    def __init__(self, config: PlacementPolicyConfig | None = None) -> None:
        self.config = config or PlacementPolicyConfig()
        self.generator = PlacementCandidateGenerator(self.config)

    def evaluate(
        self,
        shard: EvidenceShardRecord,
        window: SourceWindowRecord,
        island: EvidenceIsland | None = None,
        patch: LocalPatch | None = None,
        existing_placements: tuple[object, ...] = (),
        false_friend_risk: bool = False,
        excessive_residual: bool = False,
        force_defer: bool = False,
    ) -> tuple[tuple[PlacementCandidate, ...], PlacementDecision, PlacementRankingReport]:
        candidates = self.generator.generate(shard, window, island, patch, existing_placements)
        ranked = tuple(sorted(candidates, key=lambda item: (-_energy(item), item.candidate_id, item.target_cell.stable_key())))
        selected = ranked[0]
        explanations = [
            "source_window_seeded_candidate generated",
            "island_centered_candidate generated",
            "patch_boundary_candidate generated",
            "deterministic_hash_fallback_candidate generated",
            "density_relief_alternative_candidate generated",
            "ranked by deterministic Q16 integer energy",
        ]
        if false_friend_risk or excessive_residual:
            reason = "false_friend_risk" if false_friend_risk else "excessive_residual"
            decision = PlacementDecision(f"decision:{self.config.policy_id}:{_short(shard.shard_id)}", selected.candidate_id, "reject", "host_rule", shard.created_at, (reason,), None, reason)
            report = PlacementRankingReport(self.config.policy_id, shard.shard_id, selected.candidate_id, "reject", tuple(item.candidate_id for item in ranked), tuple((*explanations, f"rejected:{reason}")))
            return ranked, decision, report
        dense = _cell_density(selected.target_cell, existing_placements)
        if force_defer or dense >= self.config.dense_cell_threshold or _energy(selected) < self.config.defer_threshold_q16:
            decision = PlacementDecision(f"decision:{self.config.policy_id}:{_short(shard.shard_id)}", selected.candidate_id, "defer", "host_rule", shard.created_at, ("low_confidence_or_dense_cell",), None, None)
            report = PlacementRankingReport(self.config.policy_id, shard.shard_id, selected.candidate_id, "defer", tuple(item.candidate_id for item in ranked), tuple((*explanations, "deferred:low_confidence_or_dense_cell")))
            return ranked, decision, report
        decision = PlacementDecision(f"decision:{self.config.policy_id}:{_short(shard.shard_id)}", selected.candidate_id, "place", "host_rule", shard.created_at, ("deterministic_policy_selected",), selected.target_cell, None)
        report = PlacementRankingReport(self.config.policy_id, shard.shard_id, selected.candidate_id, "place", tuple(item.candidate_id for item in ranked), tuple((*explanations, f"selected_cell:{selected.target_cell.stable_key()}")))
        return ranked, decision, report


def _placement_scores(index: int) -> dict[str, int]:
    return {
        "local_fit_q16": max(0, Q16_ONE - index * 4096),
        "density_cost_q16": index * 2048,
        "coverage_gain_q16": max(0, Q16_ONE // 2 - index * 1024),
        "stitch_potential_q16": max(0, Q16_ONE // 4 - index * 512),
        "residual_cost_q16": index * 1024,
        "compute_cost_q16": 1024 + index * 512,
    }


def extended_scores(candidate: PlacementCandidate) -> dict[str, int]:
    return {
        **candidate.scores,
        "source_window_affinity_q16": Q16_ONE if candidate.source_window_refs else 0,
        "fallback_stability_q16": Q16_ONE if candidate.evidence_refs else 0,
    }


def _energy(candidate: PlacementCandidate) -> int:
    scores = extended_scores(candidate)
    utility = scores["local_fit_q16"] + scores["coverage_gain_q16"] + scores["stitch_potential_q16"] + scores["source_window_affinity_q16"] + scores["fallback_stability_q16"]
    cost = scores["density_cost_q16"] + scores["residual_cost_q16"] + scores["compute_cost_q16"]
    return utility - cost


def _source_window_cell(window_id: str, config: PlacementPolicyConfig) -> CellAddress:
    digest = sha256(window_id.encode("utf-8")).digest()
    return CellAddress(config.profile_id, config.chart_id, 0, digest[0] % 17 - 8, digest[1] % 17 - 8)


def _island_cell(island: EvidenceIsland | None, config: PlacementPolicyConfig) -> CellAddress:
    key = "no_island" if island is None else island.island_id
    digest = sha256(key.encode("utf-8")).digest()
    return CellAddress(config.profile_id, config.chart_id, 0, digest[2] % 17 - 8, digest[3] % 17 - 8)


def _patch_boundary_cell(patch: LocalPatch | None, config: PlacementPolicyConfig) -> CellAddress:
    if patch is not None and patch.boundary_cells:
        return sorted(patch.boundary_cells, key=lambda item: item.stable_key())[0]
    digest = sha256(b"patch_boundary").digest()
    return CellAddress(config.profile_id, config.chart_id, 0, digest[4] % 17 - 8, digest[5] % 17 - 8)


def _hash_cell(shard_id: str, config: PlacementPolicyConfig) -> CellAddress:
    digest = sha256(shard_id.encode("utf-8")).digest()
    return CellAddress(config.profile_id, config.chart_id, 0, digest[6] % 17 - 8, digest[7] % 17 - 8)


def _density_relief_cell(existing_placements: tuple[object, ...], config: PlacementPolicyConfig) -> CellAddress:
    offset = len(existing_placements) % 23
    return CellAddress(config.profile_id, config.chart_id, 1, offset - 11, 11 - offset)


def _cell_density(cell: CellAddress, existing_placements: tuple[object, ...]) -> int:
    return sum(1 for item in existing_placements if getattr(getattr(item, "geometry_mark", None), "cell", None) == cell)


def _short(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:16]
