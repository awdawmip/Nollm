from __future__ import annotations

import json
from typing import get_type_hints

import pytest

from nollm_access import (
    EvidenceSpan,
    FormedMemoryStatement,
    MemoryStatement,
    RawEvidenceRecord,
    StatementFormationDecision,
    StatementFormationRequest,
    StatementFormer,
    StatementSelection,
    assemble_formed_statements,
    validate_formation_decision,
)


def evidence(content: str = "Alpha. Beta.") -> RawEvidenceRecord:
    return RawEvidenceRecord("e1", content, "source.txt", ("ctx-a", "ctx-b"))


def request(record: RawEvidenceRecord | None = None, maximum: int = 4) -> StatementFormationRequest:
    return StatementFormationRequest("r1", (record or evidence(),), maximum)


def formed(*selections: StatementSelection) -> StatementFormationDecision:
    return StatementFormationDecision("d1", "r1", "formed", tuple(selections), None, "fixture")


def selection(statement_id: str = "s1", start: int = 0, end: int = 6, evidence_id: str = "e1") -> StatementSelection:
    return StatementSelection(statement_id, EvidenceSpan(evidence_id, start, end))


def test_raw_evidence_strict_types_and_canonical_round_trip() -> None:
    record = evidence()
    assert RawEvidenceRecord.from_mapping(record.to_mapping()) == record
    assert json.loads(record.canonical_bytes()) == record.to_mapping()
    with pytest.raises(TypeError):
        RawEvidenceRecord(1, "text")
    with pytest.raises(TypeError):
        RawEvidenceRecord("e", True)
    with pytest.raises(ValueError):
        RawEvidenceRecord("e", "text", context_refs=("b", "a"))
    with pytest.raises(ValueError):
        RawEvidenceRecord.from_mapping({**record.to_mapping(), "extra": "field"})


@pytest.mark.parametrize("offset", [True, 1.5, "1"])
def test_span_rejects_non_exact_integer_offsets(offset: object) -> None:
    with pytest.raises(TypeError):
        EvidenceSpan("e1", offset, 2)


@pytest.mark.parametrize("start,end", [(-1, 1), (0, 0), (2, 1)])
def test_span_rejects_invalid_bounds(start: int, end: int) -> None:
    with pytest.raises(ValueError):
        EvidenceSpan("e1", start, end)


def test_request_requires_unique_canonical_evidence_and_bounded_limit() -> None:
    first = RawEvidenceRecord("a", "one")
    second = RawEvidenceRecord("b", "two")
    assert StatementFormationRequest("r", (first, second), 2).evidence == (first, second)
    with pytest.raises(ValueError):
        StatementFormationRequest("r", (second, first), 2)
    with pytest.raises(ValueError):
        StatementFormationRequest("r", (first, first), 2)
    with pytest.raises(TypeError):
        StatementFormationRequest("r", (first,), True)
    with pytest.raises(ValueError):
        StatementFormationRequest("r", (first,), 0)


def test_decision_state_exclusivity_and_exact_mapping() -> None:
    decision = formed(selection())
    assert StatementFormationDecision.from_mapping(decision.to_mapping()) == decision
    with pytest.raises(ValueError):
        StatementFormationDecision("d", "r1", "formed", (), None, "host")
    with pytest.raises(ValueError):
        StatementFormationDecision("d", "r1", "defer", (selection(),), "later", "human")
    with pytest.raises(ValueError):
        StatementFormationDecision("d", "r1", "defer", (), "", "llm")
    with pytest.raises(ValueError):
        StatementFormationDecision.from_mapping({**decision.to_mapping(), "target_cell": "forbidden"})


def test_selection_order_identity_and_overlap_are_rejected() -> None:
    with pytest.raises(ValueError):
        formed(selection("s2", 7, 12), selection("s1", 0, 6))
    with pytest.raises(ValueError):
        formed(selection("same", 0, 6), selection("same", 7, 12))
    decision = formed(selection("s1", 0, 6), selection("s2", 5, 12))
    with pytest.raises(ValueError, match="overlap"):
        validate_formation_decision(request(), decision)


def test_exact_span_assembly_and_inheritance_are_deterministic() -> None:
    req = request()
    decision = formed(selection("s1", 0, 6), selection("s2", 7, 12))
    first = assemble_formed_statements(req, decision)
    second = assemble_formed_statements(req, decision)
    assert first == second
    assert [item.statement.content_utf8 for item in first] == ["Alpha.", "Beta."]
    assert all(item.statement.source_handle == "source.txt" for item in first)
    assert all(item.statement.context_refs == ("ctx-a", "ctx-b") for item in first)
    assert [item.canonical_bytes() for item in first] == [item.canonical_bytes() for item in second]
    assert FormedMemoryStatement.from_mapping(first[0].to_mapping()) == first[0]


def test_unicode_offsets_are_python_codepoint_offsets() -> None:
    record = evidence("记忆🙂保持原文。")
    result = assemble_formed_statements(request(record), formed(selection(end=3)))
    assert result[0].statement.content_utf8 == "记忆🙂"


def test_unknown_out_of_range_and_request_mismatch_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_formation_decision(request(), formed(selection(evidence_id="missing")))
    with pytest.raises(ValueError, match="out of range"):
        validate_formation_decision(request(), formed(selection(end=99)))
    mismatch = StatementFormationDecision("d", "other", "formed", (selection(),), None, "host")
    with pytest.raises(ValueError, match="request_id mismatch"):
        validate_formation_decision(request(), mismatch)


def test_defer_assembles_no_statement() -> None:
    decision = StatementFormationDecision("d", "r1", "defer", (), "insufficient context", "human")
    assert assemble_formed_statements(request(), decision) == ()


def test_statement_former_protocol_has_only_the_formation_boundary() -> None:
    hints = get_type_hints(StatementFormer.form)
    assert hints == {"request": StatementFormationRequest, "return": StatementFormationDecision}


def test_existing_memory_statement_remains_the_formed_payload() -> None:
    item = assemble_formed_statements(request(), formed(selection()))[0]
    assert type(item.statement) is MemoryStatement
