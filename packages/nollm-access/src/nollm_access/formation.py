from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Protocol

from .statement import MemoryStatement


MAX_STATEMENTS = 1024
FORMATION_OUTCOMES = frozenset({"formed", "defer"})
FORMATION_ACTORS = frozenset({"host", "llm", "human", "fixture"})


def _required_text(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise TypeError(f"{name} must be a non-empty string")


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


@dataclass(frozen=True)
class RawEvidenceRecord:
    evidence_id: str
    content_utf8: str
    source_handle: str | None = None
    context_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required_text("evidence_id", self.evidence_id)
        _required_text("content_utf8", self.content_utf8)
        if self.source_handle is not None:
            _required_text("source_handle", self.source_handle)
        if type(self.context_refs) is not tuple or any(type(item) is not str or not item for item in self.context_refs):
            raise TypeError("context_refs must be a tuple of non-empty strings")
        if tuple(sorted(set(self.context_refs))) != self.context_refs:
            raise ValueError("context_refs must be sorted and unique")

    def to_mapping(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, "content_utf8": self.content_utf8, "source_handle": self.source_handle, "context_refs": list(self.context_refs)}

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_mapping())

    @classmethod
    def from_mapping(cls, value: object) -> "RawEvidenceRecord":
        keys = {"evidence_id", "content_utf8", "source_handle", "context_refs"}
        if type(value) is not dict or set(value) != keys or type(value["context_refs"]) is not list:
            raise ValueError("RawEvidenceRecord mapping must have exact fields")
        return cls(value["evidence_id"], value["content_utf8"], value["source_handle"], tuple(value["context_refs"]))


@dataclass(frozen=True)
class EvidenceSpan:
    evidence_id: str
    start_codepoint: int
    end_codepoint: int

    def __post_init__(self) -> None:
        _required_text("evidence_id", self.evidence_id)
        if type(self.start_codepoint) is not int or type(self.end_codepoint) is not int:
            raise TypeError("span offsets must be integers")
        if self.start_codepoint < 0 or self.start_codepoint >= self.end_codepoint:
            raise ValueError("span must satisfy 0 <= start < end")

    def stable_key(self) -> tuple[str, int, int]:
        return (self.evidence_id, self.start_codepoint, self.end_codepoint)

    def to_mapping(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, "start_codepoint": self.start_codepoint, "end_codepoint": self.end_codepoint}

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_mapping())

    @classmethod
    def from_mapping(cls, value: object) -> "EvidenceSpan":
        keys = {"evidence_id", "start_codepoint", "end_codepoint"}
        if type(value) is not dict or set(value) != keys:
            raise ValueError("EvidenceSpan mapping must have exact fields")
        return cls(value["evidence_id"], value["start_codepoint"], value["end_codepoint"])


@dataclass(frozen=True)
class StatementSelection:
    statement_id: str
    span: EvidenceSpan

    def __post_init__(self) -> None:
        _required_text("statement_id", self.statement_id)
        if type(self.span) is not EvidenceSpan:
            raise TypeError("span must be EvidenceSpan")

    def stable_key(self) -> tuple[str, int, int, str]:
        return (*self.span.stable_key(), self.statement_id)

    def to_mapping(self) -> dict[str, object]:
        return {"statement_id": self.statement_id, "span": self.span.to_mapping()}

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_mapping())

    @classmethod
    def from_mapping(cls, value: object) -> "StatementSelection":
        if type(value) is not dict or set(value) != {"statement_id", "span"}:
            raise ValueError("StatementSelection mapping must have exact fields")
        return cls(value["statement_id"], EvidenceSpan.from_mapping(value["span"]))


@dataclass(frozen=True)
class StatementFormationRequest:
    request_id: str
    evidence: tuple[RawEvidenceRecord, ...]
    max_statements: int

    def __post_init__(self) -> None:
        _required_text("request_id", self.request_id)
        if type(self.evidence) is not tuple or not self.evidence or any(type(item) is not RawEvidenceRecord for item in self.evidence):
            raise TypeError("evidence must be a non-empty tuple of RawEvidenceRecord")
        if tuple(sorted(self.evidence, key=lambda item: item.evidence_id)) != self.evidence:
            raise ValueError("evidence must be sorted by evidence_id")
        if len({item.evidence_id for item in self.evidence}) != len(self.evidence):
            raise ValueError("evidence_id values must be unique")
        if type(self.max_statements) is not int:
            raise TypeError("max_statements must be an integer")
        if not 1 <= self.max_statements <= MAX_STATEMENTS:
            raise ValueError(f"max_statements must be in 1..{MAX_STATEMENTS}")

    def to_mapping(self) -> dict[str, object]:
        return {"request_id": self.request_id, "evidence": [item.to_mapping() for item in self.evidence], "max_statements": self.max_statements}

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_mapping())

    @classmethod
    def from_mapping(cls, value: object) -> "StatementFormationRequest":
        if type(value) is not dict or set(value) != {"request_id", "evidence", "max_statements"} or type(value["evidence"]) is not list:
            raise ValueError("StatementFormationRequest mapping must have exact fields")
        return cls(value["request_id"], tuple(RawEvidenceRecord.from_mapping(item) for item in value["evidence"]), value["max_statements"])


@dataclass(frozen=True)
class StatementFormationDecision:
    decision_id: str
    request_id: str
    outcome: str
    selections: tuple[StatementSelection, ...]
    defer_reason: str | None
    decided_by: str

    def __post_init__(self) -> None:
        _required_text("decision_id", self.decision_id)
        _required_text("request_id", self.request_id)
        _required_text("outcome", self.outcome)
        _required_text("decided_by", self.decided_by)
        if self.outcome not in FORMATION_OUTCOMES:
            raise ValueError("unknown formation outcome")
        if self.decided_by not in FORMATION_ACTORS:
            raise ValueError("unknown formation actor")
        if type(self.selections) is not tuple or any(type(item) is not StatementSelection for item in self.selections):
            raise TypeError("selections must be a tuple of StatementSelection")
        if tuple(sorted(self.selections, key=StatementSelection.stable_key)) != self.selections:
            raise ValueError("selections must use canonical order")
        if len({item.statement_id for item in self.selections}) != len(self.selections):
            raise ValueError("statement_id values must be unique")
        if self.outcome == "formed" and (not self.selections or self.defer_reason is not None):
            raise ValueError("formed requires selections and no defer_reason")
        if self.outcome == "defer" and (self.selections or type(self.defer_reason) is not str or not self.defer_reason):
            raise ValueError("defer requires no selections and a non-empty reason")

    def to_mapping(self) -> dict[str, object]:
        return {"decision_id": self.decision_id, "request_id": self.request_id, "outcome": self.outcome, "selections": [item.to_mapping() for item in self.selections], "defer_reason": self.defer_reason, "decided_by": self.decided_by}

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_mapping())

    @classmethod
    def from_mapping(cls, value: object) -> "StatementFormationDecision":
        keys = {"decision_id", "request_id", "outcome", "selections", "defer_reason", "decided_by"}
        if type(value) is not dict or set(value) != keys or type(value["selections"]) is not list:
            raise ValueError("StatementFormationDecision mapping must have exact fields")
        return cls(value["decision_id"], value["request_id"], value["outcome"], tuple(StatementSelection.from_mapping(item) for item in value["selections"]), value["defer_reason"], value["decided_by"])


@dataclass(frozen=True)
class FormedMemoryStatement:
    statement: MemoryStatement
    provenance: EvidenceSpan
    formation_decision_id: str

    def __post_init__(self) -> None:
        if type(self.statement) is not MemoryStatement:
            raise TypeError("statement must be MemoryStatement")
        if type(self.provenance) is not EvidenceSpan:
            raise TypeError("provenance must be EvidenceSpan")
        _required_text("formation_decision_id", self.formation_decision_id)

    def to_mapping(self) -> dict[str, object]:
        return {"statement": self.statement.to_mapping(), "provenance": self.provenance.to_mapping(), "formation_decision_id": self.formation_decision_id}

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_mapping())

    @classmethod
    def from_mapping(cls, value: object) -> "FormedMemoryStatement":
        if type(value) is not dict or set(value) != {"statement", "provenance", "formation_decision_id"}:
            raise ValueError("FormedMemoryStatement mapping must have exact fields")
        return cls(MemoryStatement.from_mapping(value["statement"]), EvidenceSpan.from_mapping(value["provenance"]), value["formation_decision_id"])


class StatementFormer(Protocol):
    def form(self, request: StatementFormationRequest) -> StatementFormationDecision: ...


def validate_formation_decision(request: StatementFormationRequest, decision: StatementFormationDecision) -> None:
    if type(request) is not StatementFormationRequest or type(decision) is not StatementFormationDecision:
        raise TypeError("exact formation request and decision types are required")
    if decision.request_id != request.request_id:
        raise ValueError("request_id mismatch")
    if len(decision.selections) > request.max_statements:
        raise ValueError("selection count exceeds max_statements")
    evidence = {item.evidence_id: item for item in request.evidence}
    previous_by_evidence: dict[str, EvidenceSpan] = {}
    for selection in decision.selections:
        record = evidence.get(selection.span.evidence_id)
        if record is None:
            raise ValueError("selection references unknown evidence")
        if selection.span.end_codepoint > len(record.content_utf8):
            raise ValueError("selection span is out of range")
        if not record.content_utf8[selection.span.start_codepoint:selection.span.end_codepoint]:
            raise ValueError("selection extracts empty text")
        previous = previous_by_evidence.get(selection.span.evidence_id)
        if previous is not None and selection.span.start_codepoint < previous.end_codepoint:
            raise ValueError("selection spans overlap")
        previous_by_evidence[selection.span.evidence_id] = selection.span


def assemble_formed_statements(request: StatementFormationRequest, decision: StatementFormationDecision) -> tuple[FormedMemoryStatement, ...]:
    validate_formation_decision(request, decision)
    if decision.outcome == "defer":
        return ()
    evidence = {item.evidence_id: item for item in request.evidence}
    formed = []
    for selection in decision.selections:
        record = evidence[selection.span.evidence_id]
        content = record.content_utf8[selection.span.start_codepoint:selection.span.end_codepoint]
        statement = MemoryStatement(selection.statement_id, content, record.source_handle, record.context_refs)
        formed.append(FormedMemoryStatement(statement, selection.span, decision.decision_id))
    return tuple(formed)
