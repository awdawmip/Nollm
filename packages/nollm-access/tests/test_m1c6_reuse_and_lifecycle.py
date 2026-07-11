from pathlib import Path
from threading import Event, Thread

import pytest

from nollm_access import AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress


CELL = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)


def test_binding_callback_cannot_close_or_rebind_pair(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    access = None
    rejected = []
    calls = 0

    def callback(_path: Path) -> None:
        nonlocal calls
        calls += 1
        if calls > 1:
            return
        with pytest.raises(RuntimeError, match="pair callback"):
            access.close()
        with pytest.raises(ValueError, match="different Access root"):
            AccessRuntime(core, FileEvidenceStore(tmp_path / "other"), FileHandleStore(tmp_path / "other"))
        rejected.append(True)
        raise OSError("injected")

    access = AccessRuntime(core, FileEvidenceStore(tmp_path / "a"), FileHandleStore(tmp_path / "a", callback))
    access.capture(MemoryStatement("a", "a"))
    with pytest.raises(OSError, match="injected"):
        access.apply(AccessDecision("d-a", "a", "new", target_cell=CELL, reason_text="fixture"))
    assert rejected and core.placement_count() == 0
    access.close()
    core.close()


def test_reuse_holds_core_lease_across_binding_commit(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    entered = Event()
    proceed = Event()

    def callback(_path: Path) -> None:
        entered.set()
        assert proceed.wait(5)

    armed = False
    def armed_callback(path: Path) -> None:
        if armed:
            callback(path)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path, armed_callback))
    access.capture(MemoryStatement("original", "x"))
    original = access.apply(AccessDecision("d-original", "original", "new", target_cell=CELL, reason_text="fixture"))
    armed = True
    access.capture(MemoryStatement("alias", "x"))
    result = []
    reuse = Thread(target=lambda: result.append(access.apply(AccessDecision("d-alias", "alias", "reuse", existing_handle=original, reason_text="fixture"))))
    reuse.start()
    assert entered.wait(5)
    removed = Event()
    remove = Thread(target=lambda: (core.remove(original), removed.set()))
    remove.start()
    assert not removed.wait(0.1)
    proceed.set()
    reuse.join(5)
    remove.join(5)
    assert result == [original] and removed.is_set()
    assert access.saved_handle("alias") == original
    assert not core.contains(original)
    access.close()
    core.close()


def test_constructor_close_race_never_returns_closed_core(tmp_path: Path) -> None:
    import nollm_access.runtime as runtime_module

    core = CoreRuntime(tmp_path / "core")
    entered = Event()
    proceed = Event()
    real_acquire = runtime_module.acquire

    def blocked_acquire(*args):
        entered.set()
        assert proceed.wait(5)
        return real_acquire(*args)

    runtime_module.acquire = blocked_acquire
    outcomes = []
    errors = []

    def construct() -> None:
        try:
            outcomes.append(AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path)))
        except Exception as error:
            errors.append(error)

    thread = Thread(target=construct)
    thread.start()
    assert entered.wait(5)
    core.close()
    proceed.set()
    thread.join(5)
    runtime_module.acquire = real_acquire
    assert not outcomes
    assert len(errors) == 1 and "OPEN" in str(errors[0])
    assert not core.is_open


def test_evidence_callback_cannot_close_active_access(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    backing = FileEvidenceStore(tmp_path)
    access = None
    rejected = []

    class CallbackEvidence:
        workspace = backing.workspace

        def put_original(self, statement) -> None:
            with pytest.raises(RuntimeError, match="pair callback"):
                access.close()
            rejected.append(True)
            backing.put_original(statement)

        def get_original(self, statement_id):
            return backing.get_original(statement_id)

        def exists(self, statement_id):
            return backing.exists(statement_id)

    access = AccessRuntime(core, CallbackEvidence(), FileHandleStore(tmp_path))
    access.capture(MemoryStatement("evidence", "x"))
    assert rejected and access.evidence_store.exists("evidence")
    access.close()
    core.close()
