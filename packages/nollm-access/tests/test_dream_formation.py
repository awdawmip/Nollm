import json

import pytest

from nollm_access import (
    ConversationMaterial,
    ConversationTurn,
    DreamFormationRequest,
    DreamFormationResult,
    DreamMemoryDraft,
    FileEvidenceStore,
    FileStatementStore,
    MemoryStatement,
    form_dream_statements,
)


def request(**budgets):
    return DreamFormationRequest(
        "request-1",
        ConversationMaterial("material-1", (ConversationTurn("user", "I prefer compact reports."),)),
        **budgets,
    )


def test_emit_allows_llm_rewrite_and_has_stable_statement_identity():
    result = DreamFormationResult(
        "result-1", "request-1", "emit",
        (DreamMemoryDraft("draft-1", "The user prefers compact reports."),), None, "llm",
    )
    first = form_dream_statements(request(), result)
    second = form_dream_statements(request(), result)
    assert first == second
    assert first[0].content_utf8 == "The user prefers compact reports."
    assert first[0].statement_id.startswith("dream:")


def test_defer_is_mutually_exclusive_and_emits_nothing():
    result = DreamFormationResult("result-1", "request-1", "defer", (), "uncertain", "llm")
    assert form_dream_statements(request(), result) == ()
    with pytest.raises(ValueError, match="defer requires"):
        DreamFormationResult("result-1", "request-1", "defer", (DreamMemoryDraft("d", "x"),), "uncertain", "llm")


def test_drafts_are_unique_canonical_and_budgeted():
    with pytest.raises(ValueError, match="canonical"):
        DreamFormationResult("r", "request-1", "emit", (DreamMemoryDraft("z", "x"), DreamMemoryDraft("a", "y")), None, "llm")
    result = DreamFormationResult("r", "request-1", "emit", (DreamMemoryDraft("a", "four"),), None, "llm")
    with pytest.raises(ValueError, match="statement exceeds"):
        form_dream_statements(request(max_statement_chars=3), result)


def test_statement_store_writes_canonical_bytes_and_reopens(tmp_path):
    statement = MemoryStatement("s", "semantic memory")
    FileStatementStore(tmp_path).put(statement)
    reopened = FileStatementStore(tmp_path)
    assert reopened.get("s") == statement
    payload = json.loads(reopened._path("s").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "nollm_access_statement_v1"


def test_statement_store_reads_legacy_evidence_and_compat_writes_new_schema(tmp_path):
    legacy = FileStatementStore(tmp_path)
    legacy_path = legacy._legacy_path("old")
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text('{"schema_version":"nollm_access_evidence_v1","statement":{"content_utf8":"old payload","context_refs":[],"source_handle":null,"statement_id":"old"}}\n', encoding="utf-8", newline="\n")
    assert legacy.get("old") == MemoryStatement("old", "old payload")
    compat = FileEvidenceStore(tmp_path)
    with pytest.warns(DeprecationWarning):
        compat.put_original(MemoryStatement("new", "new payload"))
    assert compat._path("new").read_bytes().startswith(b'{"schema_version":"nollm_access_statement_v1"')
