import json

import pytest

from nollm_access import FileEvidenceStore, FileStatementStore, MemoryStatement


def test_evidence_accepts_json_formatting_and_rejects_extra_fields(tmp_path) -> None:
    store = FileEvidenceStore(tmp_path)
    store.put_original(MemoryStatement("s", "payload"))
    path = store._path("s")
    value = json.loads(path.read_bytes())
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    assert store.get_original("s") == MemoryStatement("s", "payload")
    store.put_original(MemoryStatement("s", "payload"))
    value["extra"] = 1
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        store.get_original("s")


@pytest.mark.parametrize("legacy", [False, True])
def test_statement_identity_content_and_sources_survive_json_formatting(tmp_path, legacy) -> None:
    store = FileStatementStore(tmp_path)
    statement = MemoryStatement("version-1", "原始表达", "commit:path#L1-L2", ("commit:context#L3-L4",))
    path = store._legacy_path(statement.statement_id) if legacy else store._path(statement.statement_id)
    schema = "nollm_access_evidence_v1" if legacy else "nollm_access_statement_v1"
    value = {"schema_version": schema, "statement": statement.to_mapping()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    assert store.get(statement.statement_id) == statement
    store.put(statement)
    with pytest.raises(FileExistsError, match="different content"):
        store.put(MemoryStatement(statement.statement_id, "changed", statement.source_handle, statement.context_refs))
    with pytest.raises(FileExistsError, match="different content"):
        store.discard_new(MemoryStatement(statement.statement_id, "changed"))
    assert store.get(statement.statement_id) == statement

    value["statement"]["statement_id"] = "another-version"
    value["schema_version"] = "nollm_access_statement_v1"
    store._path(statement.statement_id).write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="identity"):
        store.get(statement.statement_id)
