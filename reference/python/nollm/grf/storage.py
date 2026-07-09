"""File-first GRF object storage."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .admission import MinimalAdmissionRecord
from .bridge_kernel import BridgeKernel
from .cell_address import CellAddress
from .evidence_island import EvidenceIsland, EvidenceShardRef
from .json_canonical import canonical_dumps, canonical_loads
from .ledger import GRFLedger
from .local_patch import LocalPatch
from .placement import GeometryMark, PlacementCandidate, PlacementRecord, RejectionRecord
from .recall_digest import CoverageReport, RecallDigest, RecallPath
from .stitching import StitchProposal, StitchRecord, StitchTransform, StitchWitness

SCHEMA_VERSION = "grf_file_v1"


class GRFFileStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def initialize_layout(self) -> None:
        for relative in (
            "grfs/evidence/shards",
            "grfs/evidence/islands",
            "grfs/patches/local_patches",
            "grfs/patches/stitch/proposals",
            "grfs/patches/stitch/records",
            "grfs/patches/stitch/rejections",
            "grfs/patches/stitch/bridges",
            "grfs/placements/candidates",
            "grfs/placements/decisions",
            "grfs/placements/records",
            "grfs/placements/rejections",
            "grfs/admissions/minimal_records",
            "grfs/recalls/digests",
            "grfs/recalls/coverage_reports",
            "grfs/relation_fields/indexes",
            "grfs/manifests",
        ):
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def write_evidence_island(self, island: EvidenceIsland) -> Path:
        return self._write("evidence_island", island.island_id, island.to_mapping(), "grfs/evidence/islands")

    def read_evidence_island(self, island_id: str) -> EvidenceIsland:
        return _island_from_payload(self._read("evidence_island", island_id, "grfs/evidence/islands"))

    def write_local_patch(self, patch: LocalPatch) -> Path:
        return self._write("local_patch", patch.patch_id, patch.to_mapping(), "grfs/patches/local_patches")

    def read_local_patch(self, patch_id: str) -> LocalPatch:
        return _patch_from_payload(self._read("local_patch", patch_id, "grfs/patches/local_patches"))

    def write_stitch_proposal(self, proposal: StitchProposal) -> Path:
        return self._write("stitch_proposal", proposal.proposal_id, proposal.to_mapping(), "grfs/patches/stitch/proposals")

    def read_stitch_proposal(self, proposal_id: str) -> StitchProposal:
        return _proposal_from_payload(self._read("stitch_proposal", proposal_id, "grfs/patches/stitch/proposals"))

    def write_stitch_record(self, record: StitchRecord) -> Path:
        return self._write("stitch_record", record.stitch_id, record.to_mapping(), "grfs/patches/stitch/records")

    def read_stitch_record(self, stitch_id: str) -> StitchRecord:
        return _record_from_payload(self._read("stitch_record", stitch_id, "grfs/patches/stitch/records"))

    def write_bridge_kernel(self, bridge: BridgeKernel) -> Path:
        return self._write("bridge_kernel", bridge.bridge_id, bridge.to_mapping(), "grfs/patches/stitch/bridges")

    def read_bridge_kernel(self, bridge_id: str) -> BridgeKernel:
        return _bridge_from_payload(self._read("bridge_kernel", bridge_id, "grfs/patches/stitch/bridges"))

    def write_placement_candidate(self, candidate: PlacementCandidate) -> Path:
        return self._write("placement_candidate", candidate.candidate_id, candidate.to_mapping(), "grfs/placements/candidates")

    def read_placement_candidate(self, candidate_id: str) -> PlacementCandidate:
        return _candidate_from_payload(self._read("placement_candidate", candidate_id, "grfs/placements/candidates"))

    def write_placement_record(self, record: PlacementRecord, recorded_at: str | None = None) -> Path:
        return self._write("placement_record", record.placement_id, record.to_mapping(), "grfs/placements/records", recorded_at)

    def read_placement_record(self, placement_id: str) -> PlacementRecord:
        return _placement_from_payload(self._read("placement_record", placement_id, "grfs/placements/records"))

    def write_minimal_admission_record(self, record: MinimalAdmissionRecord, recorded_at: str | None = None) -> Path:
        return self._write("minimal_admission_record", record.admission_id, record.to_mapping(), "grfs/admissions/minimal_records", recorded_at)

    def read_minimal_admission_record(self, admission_id: str) -> MinimalAdmissionRecord:
        return _admission_from_payload(self._read("minimal_admission_record", admission_id, "grfs/admissions/minimal_records"))

    def write_recall_digest(self, digest: RecallDigest, recorded_at: str | None = None) -> Path:
        return self._write("recall_digest", digest.query_id, digest.to_mapping(), "grfs/recalls/digests", recorded_at, event_type="recall_digest_written")

    def read_recall_digest(self, query_id: str) -> RecallDigest:
        return _digest_from_payload(self._read("recall_digest", query_id, "grfs/recalls/digests"))

    def path_for(self, object_type: str, object_id: str, directory: str) -> Path:
        _safe_id(object_id)
        return self.root / directory / f"{object_id}.json"

    def _write(self, object_type: str, object_id: str, payload: dict[str, Any], directory: str, recorded_at: str | None = None, event_type: str = "object_written") -> Path:
        path = self.path_for(object_type, object_id, directory)
        record = {"schema_version": SCHEMA_VERSION, "object_type": object_type, "object_id": object_id, "payload": payload}
        data = canonical_dumps(record)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = path.read_bytes()
            if existing == data:
                if recorded_at is not None:
                    GRFLedger(self.root).append("object_reopened_same_bytes", object_type, object_id, path.relative_to(self.root), _sha256_bytes(data), recorded_at)
                return path
            if recorded_at is not None:
                GRFLedger(self.root).append("object_write_rejected_different_bytes", object_type, object_id, path.relative_to(self.root), _sha256_bytes(existing), recorded_at)
            raise FileExistsError("different bytes already exist for object id")
        path.write_bytes(data)
        if recorded_at is not None:
            GRFLedger(self.root).append(event_type, object_type, object_id, path.relative_to(self.root), _sha256_bytes(data), recorded_at)
        return path

    def _read(self, object_type: str, object_id: str, directory: str) -> dict[str, Any]:
        path = self.path_for(object_type, object_id, directory)
        record = canonical_loads(path.read_bytes())
        if record.get("schema_version") != SCHEMA_VERSION or record.get("object_type") != object_type or record.get("object_id") != object_id:
            raise ValueError("stored object schema/id mismatch")
        return record["payload"]


def _safe_id(object_id: str) -> None:
    if not isinstance(object_id, str) or object_id == "" or "/" in object_id or "\\" in object_id or ".." in object_id:
        raise ValueError("unsafe object id")


def _sha256_bytes(data: bytes) -> str:
    from hashlib import sha256

    return sha256(data).hexdigest()


def _cell(payload: dict[str, Any]) -> CellAddress:
    return CellAddress(payload["profile_id"], payload["chart_id"], payload["layer"], payload["q"], payload["r"], payload["phase"])


def _bridge_from_payload(payload: dict[str, Any]) -> BridgeKernel:
    return BridgeKernel(payload["bridge_id"], payload["from_patch"], payload["to_patch"], payload["weight_q16"], payload["bridge_class"], payload["max_steps"], payload["max_fanout"], tuple(payload["evidence_refs"]))


def _transform(payload: dict[str, Any]) -> StitchTransform:
    if payload["type"] == "translation":
        return StitchTransform.translation(payload["dq"], payload["dr"])
    if payload["type"] == "eisenstein_similarity":
        return StitchTransform.eisenstein_similarity(payload["a"], payload["b"], payload["tq"], payload["tr"])
    return StitchTransform.fixed_point_similarity(tuple(payload["matrix_q16"]), tuple(payload["translation_q16"]))


def _witness(payload: dict[str, Any]) -> StitchWitness:
    return StitchWitness(payload["type"], payload["strength_q16"], tuple(payload["refs"]), tuple(tuple(item) for item in payload["metadata"]))


def _island_from_payload(payload: dict[str, Any]) -> EvidenceIsland:
    refs = tuple(EvidenceShardRef(item["shard_id"], tuple(item["source_window_refs"]), item["trust_state"], item["usage_state"]) for item in payload["shard_refs"])
    return EvidenceIsland(payload["island_id"], refs, tuple(payload["source_window_refs"]), payload["island_reason"], payload["state"])


def _patch_from_payload(payload: dict[str, Any]) -> LocalPatch:
    return LocalPatch(payload["patch_id"], payload["island_id"], payload["chart_id"], payload["profile_id"], _cell(payload["center_cell"]), tuple(_cell(item) for item in payload["occupied_cells"]), tuple(_cell(item) for item in payload["boundary_cells"]), payload["state"], payload["density_pressure_q16"], payload["ambiguity_q16"])


def _proposal_from_payload(payload: dict[str, Any]) -> StitchProposal:
    return StitchProposal(payload["proposal_id"], payload["from_patch"], payload["to_patch"], _transform(payload["candidate_transform"]), tuple(_witness(item) for item in payload["witnesses"]), payload["confidence_q16"], payload["state"], payload["expires_at"])


def _record_from_payload(payload: dict[str, Any]) -> StitchRecord:
    return StitchRecord(payload["stitch_id"], payload["proposal_id"], payload["accepted_by"], payload["accepted_at"], payload["from_patch"], payload["to_patch"], _transform(payload["transform"]), payload["residual_q16"], _bridge_from_payload(payload["bridge_kernel"]), tuple(payload["evidence_refs"]), payload["reversible"])


def _candidate_from_payload(payload: dict[str, Any]) -> PlacementCandidate:
    return PlacementCandidate(payload["candidate_id"], payload["shard_id"], payload["island_id"], payload["patch_id"], _cell(payload["target_cell"]), dict(payload["scores"]), payload["confidence_band"], tuple(payload["source_window_refs"]), tuple(payload["evidence_refs"]))


def _mark(payload: dict[str, Any]) -> GeometryMark:
    return GeometryMark(payload["mark_id"], payload["shard_id"], payload["profile_id"], payload["chart_id"], _cell(payload["cell"]), payload["placement_method"], payload["confidence_band"], payload["uncertainty_q16"], payload["relation_field_ref"])


def _placement_from_payload(payload: dict[str, Any]) -> PlacementRecord:
    return PlacementRecord(payload["placement_id"], payload["shard_id"], payload["candidate_id"], payload["decision_id"], _mark(payload["geometry_mark"]), payload["island_id"], payload["patch_id"], tuple(payload["source_fallback_refs"]), payload["replay_profile_id"], payload["replay_template_version"], payload["deterministic"])


def _admission_from_payload(payload: dict[str, Any]) -> MinimalAdmissionRecord:
    return MinimalAdmissionRecord(payload["admission_id"], payload["shard_id"], _placement_from_payload(payload["placement_record"]), payload["admitted_at"], payload["admitted_by"], payload["state"], payload["replay_minimal"])


def _path(payload: dict[str, Any]) -> RecallPath:
    return RecallPath(_cell(payload["from_cell"]), _cell(payload["to_cell"]), payload["kernel_type"], payload["weight_q16"], payload["accumulated_score_q16"], payload["step"], tuple(payload["flags"]))


def _coverage(payload: dict[str, Any]) -> CoverageReport:
    return CoverageReport(payload["entry"], payload["result"], tuple(_path(item) for item in payload["path"]), payload["accumulated_weight_q16"], dict(payload["drift"]), payload["coverage_class"], payload["bridge_count"], payload["source_fallback_ref"])


def _digest_from_payload(payload: dict[str, Any]) -> RecallDigest:
    return RecallDigest(payload["query_id"], tuple(payload["selected_shards"]), tuple(_coverage(item) for item in payload["coverage_reports"]), tuple(payload["rejected_or_deprioritized"]), payload["budget_exhausted"], tuple(payload["warnings"]))
