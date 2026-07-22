from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from uuid import uuid4

from .evidence_anchor import ExactEvidenceSpan
from .workspace_lock import workspace_lock


PROVENANCE_SCHEMA_VERSION = "nollm_access_statement_provenance_v1"
MIGRATION_PRECISIONS = {"exact", "coarse", "legacy"}


def _text(name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise TypeError(f"{name} must be a non-empty string")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


@dataclass(frozen=True)
class ResolvedReferenceProvenance:
    reference_id: str
    kind: str
    normalized_value: str
    basis_evidence_ref_ids: tuple[str, ...]
    timestamp_basis_capture_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text("reference_id", self.reference_id)
        if self.kind not in {"temporal", "coreference", "location", "event", "other"}:
            raise ValueError("invalid resolved-reference kind")
        _text("normalized_value", self.normalized_value)
        for name, values in (("basis_evidence_ref_ids", self.basis_evidence_ref_ids), ("timestamp_basis_capture_ids", self.timestamp_basis_capture_ids)):
            if type(values) is not tuple or any(type(item) is not str or not item for item in values):
                raise TypeError(f"{name} must be a tuple of text")
            if tuple(sorted(set(values))) != values:
                raise ValueError(f"{name} must be sorted and unique")
        if not self.basis_evidence_ref_ids and not self.timestamp_basis_capture_ids:
            raise ValueError("resolved reference requires Evidence or timestamp basis")

    def to_mapping(self) -> dict[str, object]:
        return {
            "reference_id": self.reference_id,
            "kind": self.kind,
            "normalized_value": self.normalized_value,
            "basis_evidence_ref_ids": list(self.basis_evidence_ref_ids),
            "timestamp_basis_capture_ids": list(self.timestamp_basis_capture_ids),
        }

    @classmethod
    def from_mapping(cls, value: object) -> "ResolvedReferenceProvenance":
        keys = {"reference_id", "kind", "normalized_value", "basis_evidence_ref_ids", "timestamp_basis_capture_ids"}
        if type(value) is not dict or set(value) != keys or type(value["basis_evidence_ref_ids"]) is not list or type(value["timestamp_basis_capture_ids"]) is not list:
            raise ValueError("ResolvedReferenceProvenance mapping must have exact fields")
        return cls(value["reference_id"], value["kind"], value["normalized_value"], tuple(value["basis_evidence_ref_ids"]), tuple(value["timestamp_basis_capture_ids"]))


@dataclass(frozen=True)
class StatementProvenance:
    statement_id: str
    content_sha256: str
    source_capture_ids: tuple[str, ...]
    context_capture_ids: tuple[str, ...]
    evidence_spans: tuple[ExactEvidenceSpan, ...]
    resolved_references: tuple[ResolvedReferenceProvenance, ...]
    writer_schema_version: str
    writer_prompt_version: str
    created_at_epoch_ms: int
    revision_predecessor_statement_id: str | None = None
    migration_precision: str = "exact"

    def __post_init__(self) -> None:
        _text("statement_id", self.statement_id)
        if type(self.content_sha256) is not str or len(self.content_sha256) != 64:
            raise TypeError("content_sha256 must be SHA-256 text")
        for name, values in (("source_capture_ids", self.source_capture_ids), ("context_capture_ids", self.context_capture_ids)):
            if type(values) is not tuple or any(type(item) is not str or not item for item in values):
                raise TypeError(f"{name} must be a tuple of text")
            if tuple(sorted(set(values))) != values:
                raise ValueError(f"{name} must be sorted and unique")
        if set(self.source_capture_ids) & set(self.context_capture_ids):
            raise ValueError("source and context Capture IDs must be disjoint")
        if type(self.evidence_spans) is not tuple or any(type(item) is not ExactEvidenceSpan for item in self.evidence_spans):
            raise TypeError("evidence_spans must be ExactEvidenceSpan tuple")
        if type(self.resolved_references) is not tuple or any(type(item) is not ResolvedReferenceProvenance for item in self.resolved_references):
            raise TypeError("resolved_references must be provenance reference tuple")
        ref_ids = {item.evidence_ref_id for item in self.evidence_spans}
        if len(ref_ids) != len(self.evidence_spans):
            raise ValueError("evidence_ref_id values must be unique")
        if any(not set(item.basis_evidence_ref_ids) <= ref_ids for item in self.resolved_references):
            raise ValueError("resolved-reference basis must cross-link exact Evidence refs")
        available_capture_ids = set(self.source_capture_ids) | set(self.context_capture_ids)
        if any(item.capture_id not in available_capture_ids for item in self.evidence_spans):
            raise ValueError("Evidence span names an undeclared Capture")
        if any(not set(item.timestamp_basis_capture_ids) <= available_capture_ids for item in self.resolved_references):
            raise ValueError("timestamp basis names an undeclared Capture")
        _text("writer_schema_version", self.writer_schema_version)
        _text("writer_prompt_version", self.writer_prompt_version)
        if type(self.created_at_epoch_ms) is not int or self.created_at_epoch_ms < 0:
            raise TypeError("created_at_epoch_ms must be a non-negative integer")
        if self.revision_predecessor_statement_id is not None:
            _text("revision_predecessor_statement_id", self.revision_predecessor_statement_id)
        if self.migration_precision not in MIGRATION_PRECISIONS:
            raise ValueError("invalid migration_precision")
        if self.migration_precision == "exact" and not self.evidence_spans:
            raise ValueError("exact provenance requires Evidence spans")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": PROVENANCE_SCHEMA_VERSION,
            "statement_id": self.statement_id,
            "content_sha256": self.content_sha256,
            "source_capture_ids": list(self.source_capture_ids),
            "context_capture_ids": list(self.context_capture_ids),
            "evidence_spans": [item.to_mapping() for item in self.evidence_spans],
            "resolved_references": [item.to_mapping() for item in self.resolved_references],
            "writer_schema_version": self.writer_schema_version,
            "writer_prompt_version": self.writer_prompt_version,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "revision_predecessor_statement_id": self.revision_predecessor_statement_id,
            "migration_precision": self.migration_precision,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical(self.to_mapping())

    def digest(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()

    @classmethod
    def from_mapping(cls, value: object) -> "StatementProvenance":
        keys = {
            "schema_version", "statement_id", "content_sha256", "source_capture_ids", "context_capture_ids",
            "evidence_spans", "resolved_references", "writer_schema_version", "writer_prompt_version",
            "created_at_epoch_ms", "revision_predecessor_statement_id", "migration_precision",
        }
        if type(value) is not dict or set(value) != keys or value["schema_version"] != PROVENANCE_SCHEMA_VERSION:
            raise ValueError("StatementProvenance mapping must have exact fields")
        if any(type(value[name]) is not list for name in ("source_capture_ids", "context_capture_ids", "evidence_spans", "resolved_references")):
            raise TypeError("StatementProvenance collection fields must be lists")
        return cls(
            value["statement_id"], value["content_sha256"], tuple(value["source_capture_ids"]), tuple(value["context_capture_ids"]),
            tuple(ExactEvidenceSpan.from_mapping(item) for item in value["evidence_spans"]),
            tuple(ResolvedReferenceProvenance.from_mapping(item) for item in value["resolved_references"]),
            value["writer_schema_version"], value["writer_prompt_version"], value["created_at_epoch_ms"],
            value["revision_predecessor_statement_id"], value["migration_precision"],
        )


class FileStatementProvenanceStore:
    def __init__(self, root: Path) -> None:
        self._workspace = Path(root).resolve()
        self._root = self._workspace / "access" / "statement-provenance"
        self._lock = workspace_lock(self._workspace)

    @property
    def workspace(self) -> Path:
        return self._workspace

    def exists(self, statement_id: str) -> bool:
        return self._path(statement_id).is_file()

    def put(self, provenance: StatementProvenance) -> None:
        if type(provenance) is not StatementProvenance:
            raise TypeError("provenance must be StatementProvenance")
        with self._lock:
            path = self._path(provenance.statement_id)
            payload = provenance.canonical_bytes()
            if path.is_file():
                if path.read_bytes() != payload:
                    raise FileExistsError("Statement provenance already exists with different content")
                return
            _atomic_write(path, payload)

    def get(self, statement_id: str) -> StatementProvenance:
        path = self._path(statement_id)
        payload = path.read_bytes()
        value = json.loads(payload.decode("utf-8"))
        provenance = StatementProvenance.from_mapping(value)
        if provenance.statement_id != statement_id or provenance.canonical_bytes() != payload:
            raise ValueError("Statement provenance bytes or identity are noncanonical")
        return provenance

    def discard_new(self, provenance: StatementProvenance) -> bool:
        if type(provenance) is not StatementProvenance:
            raise TypeError("provenance must be StatementProvenance")
        with self._lock:
            path = self._path(provenance.statement_id)
            if not path.is_file():
                return False
            if path.read_bytes() != provenance.canonical_bytes():
                raise FileExistsError("Statement provenance exists with different content")
            path.unlink()
            return True

    def _path(self, statement_id: str) -> Path:
        _text("statement_id", statement_id)
        digest = sha256(statement_id.encode("utf-8")).hexdigest()
        return self._root / digest[:2] / f"{digest}.json"


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
