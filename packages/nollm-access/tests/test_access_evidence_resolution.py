from nollm_access import AccessRecallRequest, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, RecallBudget


def test_recall_distinguishes_binding_and_payload_failures(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    evidence = FileEvidenceStore(tmp_path)
    access = AccessRuntime(core, evidence, FileHandleStore(tmp_path))
    cell = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    core.put(MemoryAtom("orphan", "payload"), cell)
    result = access.recall(AccessRecallRequest("r", entry_cells=(cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "binding_missing"

    missing_cell = GeometryAddress("default_dream_v1", "default", 0, 1, 0)
    access.capture(MemoryStatement("missing", "payload"))
    missing_handle = access.apply(__import__('nollm_access').AccessDecision("d-missing", "missing", "new", target_cell=missing_cell, reason_text="fixture"))
    evidence._path("missing").unlink()
    result = access.recall(AccessRecallRequest("m", entry_cells=(missing_cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "evidence_missing"

    mismatch_cell = GeometryAddress("default_dream_v1", "default", 0, 2, 0)
    access.capture(MemoryStatement("mismatch", "different evidence"))
    mismatch_handle = access.apply(__import__('nollm_access').AccessDecision("d-mismatch", "mismatch", "new", target_cell=mismatch_cell, reason_text="fixture"))
    core.replace(mismatch_handle, "core payload")
    result = access.recall(AccessRecallRequest("x", entry_cells=(mismatch_cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "evidence_payload_mismatch"


def test_recall_resolves_a_mixed_neighborhood_in_one_registry_read(tmp_path, monkeypatch):
    import pytest
    from nollm_access import AccessDecision, FileStatementStore

    cell = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    near = GeometryAddress("default_dream_v1", "default", 0, 1, 0)
    empty = GeometryAddress("default_dream_v1", "default", 0, 40, 0)
    handles = FileHandleStore(tmp_path)
    with CoreRuntime(tmp_path) as core, AccessRuntime(core, FileStatementStore(tmp_path), handles) as access:
        access.put_statement(MemoryStatement("bound", "body"))
        access.apply(AccessDecision("place", "bound", "new", target_cell=cell, reason_text="fixture"))
        orphan = core.put(MemoryAtom("orphan", "unbound"), near)
        request = AccessRecallRequest("both", entry_cells=(cell,), allowed_kernels=("lateral",),
                                      budget=RecallBudget(1, 8, 0, 1, 0, 8))
        calls = 0
        decode = FileHandleStore._decode

        def count_decodes(payload):
            nonlocal calls
            calls += 1
            return decode(payload)

        monkeypatch.setattr(FileHandleStore, "_decode", staticmethod(count_decodes))
        result = access.recall(request)
        assert calls == 1
        assert [(x.statement_id, x.evidence_utf8) for x in result.items] == [("bound", "body"), ("", None)]
        assert result.items[1].handle == orphan
        assert result.items[1].fallback_error == "binding_missing"

        handles.path.write_bytes(b"broken")
        assert access.recall(AccessRecallRequest("empty", entry_cells=(empty,))).items == ()
        with pytest.raises(ValueError):
            access.recall(request)
