"""Public prototype facade for GRF validation workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any

from .admission_bridge import GRFAdmissionBridge, GRFAdmissionBridgeResult
from .capture import GRFCaptureIngress, GRFCaptureReceipt, GRFCaptureRequest
from .cell_address import CellAddress
from .json_canonical import canonical_loads
from .ledger import GRFLedger
from .recall import QueryProbe, RecallBudget, resolve_grf_recall
from .recall_digest import RecallDigest
from .replay import replay_recall
from .source_window import SourceWindowRecord
from .storage import GRFFileStore


@dataclass(frozen=True)
class GRFWorkspaceReport:
    object_file_count: int
    ledger_event_count: int
    placement_record_count: int
    admission_record_count: int
    evidence_shard_count: int
    source_window_count: int
    warnings: tuple[str, ...]


class GRFFacade:
    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace)
        self.store = GRFFileStore(self.workspace)
        self.store.initialize_layout()

    def capture(self, request: GRFCaptureRequest) -> GRFCaptureReceipt:
        return GRFCaptureIngress(self.store).capture(request)

    def capture_text(self, capture_id: str, content: str, source_window_id: str, recorded_at: str) -> GRFCaptureReceipt:
        return self.capture(GRFCaptureRequest(capture_id, content, "imported_text", (source_window_id,), recorded_at, "grf8_text"))

    def capture_source(self, path: Path, recorded_at: str) -> object:
        """Ingest a supported local source through the public file-first workflow."""
        from .ingestion import IncrementalIngestion

        return IncrementalIngestion(self.workspace).ingest_file(path, recorded_at)

    def retire_source(self, source_id: str) -> object:
        from .ingestion import IncrementalIngestion

        return IncrementalIngestion(self.workspace).retire(source_id)

    def retire(self, source_id: str) -> object:
        """Mark an explicitly ingested source retired without deleting evidence."""
        return self.retire_source(source_id)

    def get_source(self, shard_id: str) -> str:
        """Return the retained original evidence text for an explicit shard."""
        return self.store.read_evidence_shard(shard_id).content

    def revise(self, path: Path, recorded_at: str) -> object:
        return self.capture_source(path, recorded_at)

    def snapshot(self, snapshot_root: Path) -> Path:
        target = Path(snapshot_root)
        if target.exists():
            raise FileExistsError(target)
        shutil.copytree(self.workspace, target)
        return target

    @classmethod
    def restore(cls, snapshot_root: Path, workspace: Path) -> "GRFFacade":
        source, target = Path(snapshot_root), Path(workspace)
        if target.exists():
            raise FileExistsError(target)
        shutil.copytree(source, target)
        return cls(target)

    def admit(self, shard_id: str, source_window_id: str, policy_hint: dict[str, Any], recorded_at: str) -> GRFAdmissionBridgeResult:
        shard = self.store.read_evidence_shard(shard_id)
        window = self._read_or_create_window(source_window_id, shard.source_window_refs, recorded_at)
        return GRFAdmissionBridge(self.store).admit(shard, window, policy_hint, recorded_at)

    def place(self, shard_id: str, source_window_id: str, policy_hint: dict[str, Any], recorded_at: str) -> GRFAdmissionBridgeResult:
        """Run the deterministic placement workflow and return its placement record."""
        shard = self.store.read_evidence_shard(shard_id)
        window = self._read_or_create_window(source_window_id, shard.source_window_refs, recorded_at)
        return GRFAdmissionBridge(self.store).place(shard, window, policy_hint, recorded_at)

    def admit_existing_placement(self, shard_id: str, placement_id: str, recorded_at: str, admitted_by: str) -> object:
        shard = self.store.read_evidence_shard(shard_id)
        return GRFAdmissionBridge(self.store).admit_existing_placement(shard, placement_id, recorded_at, admitted_by)

    def place_batch(self, shard_ids: tuple[str, ...], source_window_id: str, policy_hint: dict[str, Any], recorded_at: str) -> tuple[GRFAdmissionBridgeResult, ...]:
        if not shard_ids or len(set(shard_ids)) != len(shard_ids):
            raise ValueError("batch shard ids must be non-empty and unique")
        return tuple(self.place(shard_id, source_window_id, policy_hint, recorded_at) for shard_id in shard_ids)

    def re_place(self, shard_id: str, source_window_id: str, policy_hint: dict[str, Any], replacement_id: str, recorded_at: str) -> GRFAdmissionBridgeResult:
        if not replacement_id:
            raise ValueError("replacement_id is required")
        hint = dict(policy_hint)
        hint["replacement_id"] = replacement_id
        return self.place(shard_id, source_window_id, hint, recorded_at)

    def admit_batch(self, placements: tuple[tuple[str, str], ...], recorded_at: str, admitted_by: str) -> tuple[object, ...]:
        if not placements or len({placement_id for _, placement_id in placements}) != len(placements):
            raise ValueError("batch placements must be non-empty and unique")
        return tuple(self.admit_existing_placement(shard_id, placement_id, recorded_at, admitted_by) for shard_id, placement_id in placements)

    def recall(self, query: QueryProbe) -> RecallDigest:
        from .replay import rebuild_relation_field_from_files

        query = self._normalize_query(query)
        digest = resolve_grf_recall(query, rebuild_relation_field_from_files(self.workspace))
        _require_fallbacks(digest)
        return digest

    def replay_recall(self, query: QueryProbe) -> RecallDigest:
        query = self._normalize_query(query)
        digest = replay_recall(query, self.workspace)
        _require_fallbacks(digest)
        return digest

    def replay(self, query: QueryProbe) -> RecallDigest:
        return self.replay_recall(query)

    def validate_workspace(self) -> GRFWorkspaceReport:
        root = self.workspace / "grfs"
        return GRFWorkspaceReport(
            object_file_count=len(tuple(root.rglob("*.json"))),
            ledger_event_count=len(GRFLedger(self.workspace).events()),
            placement_record_count=_count_json(root / "placements" / "records"),
            admission_record_count=_count_json(root / "admissions" / "minimal_records"),
            evidence_shard_count=_count_json(root / "evidence" / "shards"),
            source_window_count=_count_json(root / "evidence" / "source_windows"),
            warnings=("prototype_facade_not_runtime_service", "no_global_graph_vector_search"),
        )

    def _read_or_create_window(self, window_id: str, refs: tuple[str, ...], recorded_at: str) -> SourceWindowRecord:
        try:
            return self.store.read_source_window(window_id)
        except FileNotFoundError:
            window = SourceWindowRecord(window_id, "validation_fixture", refs or (window_id,), recorded_at, policy_ref="validation_fixture_policy")
            self.store.write_source_window(window, recorded_at)
            return window

    def _normalize_query(self, query: QueryProbe) -> QueryProbe:
        if query.entry_mode == "admission_id":
            admission = self.store.read_minimal_admission_record(str(query.entry_ref))
            return _replace_entry(query, "shard_id", admission.shard_id)
        if query.entry_mode == "placement_id":
            placement = self.store.read_placement_record(str(query.entry_ref))
            return _replace_entry(query, "shard_id", placement.shard_id)
        if query.entry_mode == "source_window":
            shard_id = self._first_shard_for_source_window(str(query.entry_ref))
            return _replace_entry(query, "shard_id", shard_id)
        return query

    def _first_shard_for_source_window(self, source_window_id: str) -> str:
        for shard_id in _object_ids(self.workspace / "grfs" / "evidence" / "shards"):
            shard = self.store.read_evidence_shard(shard_id)
            if source_window_id in shard.source_window_refs:
                return shard.shard_id
        raise FileNotFoundError("source window has no captured shard")


def capture_request_from_mapping(payload: dict[str, Any]) -> GRFCaptureRequest:
    _require_kind(payload, "nollm_grf_capture_request")
    return GRFCaptureRequest(
        str(payload["capture_id"]),
        str(payload["content"]),
        str(payload["origin_kind"]),
        tuple(str(item) for item in payload["source_window_refs"]),
        str(payload["recorded_at"]),
        str(payload.get("policy_id", "grf_capture_default")),
    )


def admit_request_from_mapping(payload: dict[str, Any]) -> tuple[str, str, dict[str, Any], str]:
    _require_kind(payload, "nollm_grf_admit_request")
    return str(payload["shard_id"]), str(payload["source_window_id"]), dict(payload["policy_hint"]), str(payload["recorded_at"])


def admit_existing_placement_request_from_mapping(payload: dict[str, Any]) -> tuple[str, str, str, str]:
    _require_kind(payload, "nollm_grf_admit_existing_placement_request")
    return str(payload["shard_id"]), str(payload["placement_id"]), str(payload["recorded_at"]), str(payload["admitted_by"])


def recall_query_from_mapping(payload: dict[str, Any]) -> QueryProbe:
    _require_kind(payload, "nollm_grf_recall_request")
    budget = payload["budget"]
    entry_ref = payload["entry_ref"]
    if payload["entry_mode"] == "explicit_cell":
        entry_ref = CellAddress(entry_ref["profile_id"], entry_ref["chart_id"], entry_ref["layer"], entry_ref["q"], entry_ref["r"], entry_ref.get("phase"))
    return QueryProbe(
        str(payload["query_id"]),
        str(payload["entry_mode"]),
        entry_ref,
        tuple(str(item) for item in payload["allowed_kernels"]),
        RecallBudget(int(budget["max_steps"]), int(budget["beam"]), int(budget["max_layer_delta"]), int(budget["max_lateral_ring"]), int(budget["max_bridge_steps"]), int(budget["max_results"])),
    )


def load_json_request(path: Path) -> dict[str, Any]:
    return canonical_loads(Path(path).read_bytes())


def _replace_entry(query: QueryProbe, entry_mode: str, entry_ref: object) -> QueryProbe:
    return QueryProbe(query.query_id, entry_mode, entry_ref, query.allowed_kernels, query.budget)


def _object_ids(directory: Path) -> tuple[str, ...]:
    ids: list[str] = []
    if not directory.exists():
        return ()
    for path in sorted(directory.glob("*.json")):
        record = canonical_loads(path.read_bytes())
        object_id = record.get("object_id")
        if isinstance(object_id, str) and object_id:
            ids.append(object_id)
    return tuple(ids)


def _require_kind(payload: dict[str, Any], kind: str) -> None:
    if payload.get("kind") != kind or payload.get("version") != "1":
        raise ValueError("unsupported request kind/version")


def _require_fallbacks(digest: RecallDigest) -> None:
    for report in digest.coverage_reports:
        if not report.source_fallback_ref:
            raise ValueError("recall result missing source fallback")


def _count_json(path: Path) -> int:
    return len(tuple(path.glob("*.json"))) if path.exists() else 0
