import pytest

from nollm_access import AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, HandleBinding, MemoryStatement
from nollm_core import AtomHandle, CoreRuntime, GeometryAddress


def cell(q: int) -> GeometryAddress:
    return GeometryAddress("eisenstein_exact_v1", "chart", 0, q, 0)


def decision(statement_id: str, action: str, **values: object) -> AccessDecision:
    return AccessDecision("decision:" + statement_id, statement_id, action, reason_text="fixture", decided_by="fixture", **values)


def fail_next_write(store: FileHandleStore) -> None:
    original_write = store._write_bytes
    failed = False

    def fail_once(payload: bytes) -> None:
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("binding failure")
        original_write(payload)

    store._write_bytes = fail_once


def test_binding_failure_rolls_back_core(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("s", "payload"))
    core_before, binding_before = core.export_state_bytes(), store.state_bytes()
    fail_next_write(store)
    decision = AccessDecision("d", "s", "new", target_cell=GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0), reason_text="fixture", decided_by="fixture")
    with pytest.raises(OSError, match="binding failure"):
        access.apply(decision)
    assert core.export_state_bytes() == core_before
    assert store.state_bytes() == binding_before


def test_handle_binding_rejects_wrong_direct_constructor_types() -> None:
    handle = AtomHandle(cell(0), "atom")
    with pytest.raises(TypeError, match="exact AtomHandle"):
        HandleBinding("not-a-handle", "s")
    with pytest.raises(TypeError, match="non-empty string"):
        HandleBinding(handle, 1)
    with pytest.raises(TypeError, match="must be a tuple"):
        HandleBinding(handle, "s", ["support"])


@pytest.mark.parametrize("action", ["new", "revision_current", "revision_keep_history", "forget", "reuse"])
def test_supported_binding_failure_matrix_restores_state(tmp_path, action: str) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    existing = None
    if action in {"revision_current", "forget", "reuse"}:
        access.capture(MemoryStatement("original", "original"))
        existing = access.apply(decision("original", "new", target_cell=cell(0)))
    statement_id = "original" if action == "forget" else "candidate"
    if action != "forget":
        access.capture(MemoryStatement(statement_id, "candidate"))
    values = {}
    if action in {"new", "revision_keep_history"}:
        values["target_cell"] = cell(1)
    if action in {"revision_current", "forget", "reuse"}:
        values["existing_handle"] = existing
    core_before, binding_before = core.export_state_bytes(), store.state_bytes()
    fail_next_write(store)
    with pytest.raises(OSError, match="binding failure"):
        access.apply(decision(statement_id, action, **values))
    assert core.export_state_bytes() == core_before
    assert store.state_bytes() == binding_before


def test_shared_composition_lock_preserves_success_after_failure(tmp_path) -> None:
    core = CoreRuntime(tmp_path / "core")
    first_store = FileHandleStore(tmp_path)
    second_store = FileHandleStore(tmp_path)
    evidence = FileEvidenceStore(tmp_path)
    first = AccessRuntime(core, evidence, first_store)
    second = AccessRuntime(core, evidence, second_store)
    assert first._composition_lock is second._composition_lock
    first.capture(MemoryStatement("failed", "failed"))
    second.capture(MemoryStatement("success", "success"))
    fail_next_write(first_store)
    with pytest.raises(OSError, match="binding failure"):
        first.apply(decision("failed", "new", target_cell=cell(0)))
    handle = second.apply(decision("success", "new", target_cell=cell(1)))
    assert second.saved_handle("success") == handle
    assert core.placement_count() == 1
