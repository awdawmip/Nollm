"""DA1 file-first AdmissionRecord store."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from hashlib import sha256
from typing import Callable

from nollm.dream_geometry.cortex import CortexStore
from nollm.dream_geometry.evidence import MemorySubstrateStore

from .errors import (
    DA1_ADMISSION_ID_PAYLOAD_CONFLICT,
    DA1_ADMISSION_RECORD_REFERENCE_MISSING,
    DA1_INVALID_ROOT_CONFIGURATION,
    DA1_PROPOSAL_ALREADY_ADMITTED,
    DA1_REPLAY_PROJECTION_MISMATCH,
    reject,
)
from .types import CONTRACT_VERSION, AdmissionRecord, canonical_json, canonical_payload


@dataclass(frozen=True)
class AdmissionWriteResult:
    admission_id: str
    created: bool
    idempotent: bool


class AdmissionStore:
    """Single-process, file-first DA1 store for AdmissionRecord only."""

    def __init__(
        self,
        admission_root: Path,
        evidence_store: MemorySubstrateStore,
        cortex_store: CortexStore,
        replay_validator: Callable[[AdmissionRecord], None] | None = None,
    ):
        self.root = Path(admission_root).resolve()
        self.evidence_store = evidence_store
        self.cortex_store = cortex_store
        self.records_dir = self.root / "records"
        evidence_root = Path(evidence_store.root).resolve()
        cortex_root = Path(cortex_store.root).resolve()
        if len({self.root, evidence_root, cortex_root}) != 3:
            reject(DA1_INVALID_ROOT_CONFIGURATION, "admission, evidence, and cortex roots must be distinct")
        self.root.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self._format_path = self.root / "format.json"
        self._ensure_format()
        self._validate_store(replay_validator)

    def put_admission_record(self, record: AdmissionRecord) -> AdmissionWriteResult:
        path = self._record_path(record.admission_id)
        rendered = canonical_json(record)
        if path.exists():
            if path.read_text(encoding="utf-8") != rendered:
                reject(DA1_ADMISSION_ID_PAYLOAD_CONFLICT, "same admission_id has different payload")
            return AdmissionWriteResult(record.admission_id, False, True)
        existing = self.find_by_proposal_id(record.proposal_id)
        if existing is not None and existing.admission_id != record.admission_id:
            reject(DA1_PROPOSAL_ALREADY_ADMITTED, "proposal already has an AdmissionRecord")
        _atomic_write_text(path, rendered)
        return AdmissionWriteResult(record.admission_id, True, False)

    def get_admission_record(self, admission_id: str) -> AdmissionRecord:
        path = self._record_path(admission_id)
        if not path.exists():
            raise FileNotFoundError(admission_id)
        return _record_from_payload(_read_json(path))

    def has_admission_record(self, admission_id: str) -> bool:
        return self._record_path(admission_id).exists()

    def find_by_proposal_id(self, proposal_id: str) -> AdmissionRecord | None:
        for record in self.records():
            if record.proposal_id == proposal_id:
                return record
        return None

    def records(self) -> tuple[AdmissionRecord, ...]:
        return tuple(_record_from_payload(_read_json(path)) for path in sorted(self.records_dir.glob("*.json")))

    def validate_record_references(self, record: AdmissionRecord) -> None:
        try:
            shard = self.evidence_store.get_dream_shard(record.subject_shard_id)
            proposal = self.cortex_store.get_growth_proposal(record.proposal_id)
            receipts = self.cortex_store.receipts()
        except Exception as exc:
            raise _reference_missing(exc)
        if shard.shard_id != proposal.subject_shard_id:
            reject(DA1_ADMISSION_RECORD_REFERENCE_MISSING, "record subject does not match proposal")
        if not any(receipt.receipt_id == record.compilation_receipt_id and receipt.proposal_id == record.proposal_id for receipt in receipts):
            reject(DA1_ADMISSION_RECORD_REFERENCE_MISSING, "record receipt reference missing")

    def _record_path(self, admission_id: str) -> Path:
        return self.records_dir / f"{_name_key(admission_id)}.json"

    def _ensure_format(self) -> None:
        payload = {"format_version": CONTRACT_VERSION, "store_kind": "memory_admission"}
        rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        if self._format_path.exists():
            if self._format_path.read_text(encoding="utf-8") != rendered:
                reject(DA1_INVALID_ROOT_CONFIGURATION, "unsupported admission store format")
            return
        _atomic_write_text(self._format_path, rendered)

    def _validate_store(self, replay_validator: Callable[[AdmissionRecord], None] | None) -> None:
        seen_admissions: set[str] = set()
        seen_proposals: set[str] = set()
        for path in sorted(self.records_dir.glob("*.json")):
            record = _record_from_payload(_read_json(path))
            if path != self._record_path(record.admission_id):
                reject(DA1_ADMISSION_ID_PAYLOAD_CONFLICT, "record filename does not match admission_id")
            if record.admission_id in seen_admissions:
                reject(DA1_ADMISSION_ID_PAYLOAD_CONFLICT, "duplicate admission_id")
            if record.proposal_id in seen_proposals:
                reject(DA1_PROPOSAL_ALREADY_ADMITTED, "duplicate proposal admission")
            seen_admissions.add(record.admission_id)
            seen_proposals.add(record.proposal_id)
            self.validate_record_references(record)
            if replay_validator is not None:
                try:
                    replay_validator(record)
                except Exception as exc:
                    if getattr(exc, "reason_codes", None) == (DA1_REPLAY_PROJECTION_MISMATCH,):
                        raise
                    raise


def open_store(
    admission_root: Path,
    evidence_store: MemorySubstrateStore,
    cortex_store: CortexStore,
    replay_validator: Callable[[AdmissionRecord], None] | None = None,
) -> AdmissionStore:
    return AdmissionStore(admission_root, evidence_store, cortex_store, replay_validator)


def _record_from_payload(payload: dict) -> AdmissionRecord:
    expected_keys = set(canonical_payload(AdmissionRecord(
        admission_id=payload["admission_id"],
        subject_shard_id=payload["subject_shard_id"],
        proposal_id=payload["proposal_id"],
        compilation_receipt_id=payload["compilation_receipt_id"],
        recorded_at=payload["recorded_at"],
        request_fingerprint=payload["request_fingerprint"],
        placement_plan_payload=payload["placement_plan_payload"],
        placement_plan_fingerprint=payload["placement_plan_fingerprint"],
        projection_fingerprint=payload["projection_fingerprint"],
        source_trace_ids=tuple(payload["source_trace_ids"]),
        derived_trace_ids=tuple(payload["derived_trace_ids"]),
        residual_ids=tuple(payload["residual_ids"]),
        cover_ids=tuple(payload["cover_ids"]),
        cover_state_counts=dict(payload["cover_state_counts"]),
    )).keys())
    if set(payload) != expected_keys:
        reject(DA1_ADMISSION_ID_PAYLOAD_CONFLICT, "AdmissionRecord field mismatch")
    record = AdmissionRecord(
        payload["admission_id"],
        payload["subject_shard_id"],
        payload["proposal_id"],
        payload["compilation_receipt_id"],
        payload["recorded_at"],
        payload["request_fingerprint"],
        payload["placement_plan_payload"],
        payload["placement_plan_fingerprint"],
        payload["projection_fingerprint"],
        tuple(payload["source_trace_ids"]),
        tuple(payload["derived_trace_ids"]),
        tuple(payload["residual_ids"]),
        tuple(payload["cover_ids"]),
        dict(payload["cover_state_counts"]),
        payload["field_profile_id"],
        payload["record_type"],
        payload["contract_version"],
        payload["format_version"],
    )
    if payload != json.loads(canonical_json(record)):
        reject(DA1_ADMISSION_ID_PAYLOAD_CONFLICT, "AdmissionRecord canonical payload mismatch")
    return record


def _reference_missing(exc: Exception) -> Exception:
    reject(DA1_ADMISSION_RECORD_REFERENCE_MISSING, f"record reference missing: {exc}")
    return exc


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        reject(DA1_ADMISSION_ID_PAYLOAD_CONFLICT, "AdmissionRecord payload must be object")
    return payload


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _name_key(record_id: str) -> str:
    return sha256(record_id.encode("utf-8")).hexdigest()


__all__ = ["AdmissionStore", "AdmissionWriteResult", "open_store"]
