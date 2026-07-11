from nollm_access import AccessRecallRequest, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, RecallBudget


def test_recall_distinguishes_binding_and_payload_failures(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    evidence = FileEvidenceStore(tmp_path)
    access = AccessRuntime(core, evidence, FileHandleStore(tmp_path))
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    core.put(MemoryAtom("orphan", "payload"), cell)
    result = access.recall(AccessRecallRequest("r", entry_cells=(cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "binding_missing"

    missing_cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 1, 0)
    access.capture(MemoryStatement("missing", "payload"))
    missing_handle = access.apply(__import__('nollm_access').AccessDecision("d-missing", "missing", "new", target_cell=missing_cell, reason_text="fixture"))
    evidence._path("missing").unlink()
    result = access.recall(AccessRecallRequest("m", entry_cells=(missing_cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "evidence_missing"

    mismatch_cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 2, 0)
    access.capture(MemoryStatement("mismatch", "different evidence"))
    mismatch_handle = access.apply(__import__('nollm_access').AccessDecision("d-mismatch", "mismatch", "new", target_cell=mismatch_cell, reason_text="fixture"))
    core.replace(mismatch_handle, "core payload")
    result = access.recall(AccessRecallRequest("x", entry_cells=(mismatch_cell,), budget=RecallBudget(0, 2, 0, 0, 0, 2)))
    assert result.items[0].fallback_error == "evidence_payload_mismatch"
