from threading import Event, Thread

import pytest

from nollm_access import AccessConsistencyError, AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, HandleBinding, MemoryStatement
from nollm_core import AtomHandle, CoreRuntime, GeometryAddress, MemoryAtom


def cell(q: int) -> GeometryAddress:
    return GeometryAddress("default_dream_v1", "default", 0, q, 0)


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
    decision = AccessDecision("d", "s", "new", target_cell=cell(0), reason_text="fixture", decided_by="fixture")
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


def test_fatal_rollback_preserves_all_diagnostics_and_poisons_runtime(tmp_path, monkeypatch) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("candidate", "candidate"))

    def fail_binding(_payload: bytes) -> None:
        raise OSError("binding write and rollback failed")

    def fail_core_rollback(_payload: bytes) -> None:
        raise PermissionError("core rollback failed")

    monkeypatch.setattr(store, "_write_bytes", fail_binding)
    monkeypatch.setattr(core, "import_state_bytes", fail_core_rollback)
    with pytest.raises(AccessConsistencyError) as raised:
        access.apply(decision("candidate", "new", target_cell=cell(0)))

    error = raised.value
    assert isinstance(error.original_error, OSError)
    assert error.commit_state == "commit_state_unknown"
    assert [failure.to_mapping() for failure in error.rollback_failures] == [
        {"component": "core", "error_type": "PermissionError", "message": "core rollback failed"},
        {"component": "binding", "error_type": "OSError", "message": "binding write and rollback failed"},
    ]
    assert access.lifecycle_state == "FAILED"
    assert access.last_commit_state == "commit_state_unknown"
    with pytest.raises(RuntimeError, match="failed"):
        access.apply(decision("candidate", "new", target_cell=cell(1)))

    core.close()
    with CoreRuntime(tmp_path / "core") as reopened_core:
        reopened = AccessRuntime(reopened_core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
        assert reopened_core.placement_count() == 1
        with pytest.raises(KeyError):
            reopened.saved_handle("candidate")


def test_base_exception_is_indeterminate_and_poisons_runtime(tmp_path, monkeypatch) -> None:
    core = CoreRuntime(tmp_path / "core")
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
    access.capture(MemoryStatement("candidate", "candidate"))

    def interrupt(*_args: object) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(core, "put", interrupt)
    with pytest.raises(KeyboardInterrupt):
        access.apply(decision("candidate", "new", target_cell=cell(0)))
    assert access.lifecycle_state == "FAILED"
    assert access.last_commit_state == "commit_state_unknown"


def test_direct_core_mutation_waits_for_complete_access_transaction(tmp_path, monkeypatch) -> None:
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("access", "access"))
    binding_entered = Event()
    release_binding = Event()
    direct_done = Event()
    original_put = store.put

    def blocked_binding(*args: object) -> None:
        binding_entered.set()
        assert release_binding.wait(5)
        original_put(*args)

    monkeypatch.setattr(store, "put", blocked_binding)
    access_thread = Thread(target=lambda: access.apply(decision("access", "new", target_cell=cell(0))))
    direct_thread = Thread(target=lambda: (core.put(MemoryAtom("direct", "direct"), cell(1)), direct_done.set()))
    access_thread.start()
    assert binding_entered.wait(5)
    direct_thread.start()
    assert not direct_done.wait(0.1)
    release_binding.set()
    access_thread.join(5)
    direct_thread.join(5)
    assert not access_thread.is_alive() and not direct_thread.is_alive()
    assert direct_done.is_set()
    assert core.placement_count() == 2
