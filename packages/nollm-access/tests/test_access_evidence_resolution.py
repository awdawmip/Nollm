from nollm_access import AccessRecallRequest, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, RecallBudget


def test_recall_distinguishes_binding_and_payload_failures(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    core.put(MemoryAtom("orphan", "payload"), cell)
    result = access.recall(AccessRecallRequest("r", entry_cells=(cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "binding_missing"

    missing_cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 1, 0)
    missing_handle = core.put(MemoryAtom("missing", "payload"), missing_cell)
    access.handle_store.put("missing", missing_handle)
    result = access.recall(AccessRecallRequest("m", entry_cells=(missing_cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "evidence_missing"

    mismatch_cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 2, 0)
    mismatch_handle = core.put(MemoryAtom("mismatch", "core payload"), mismatch_cell)
    access.handle_store.put("mismatch", mismatch_handle)
    access.capture(MemoryStatement("mismatch", "different evidence"))
    result = access.recall(AccessRecallRequest("x", entry_cells=(mismatch_cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "evidence_payload_mismatch"
