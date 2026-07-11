from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep

import pytest

from nollm_access import (
    AccessDecision,
    AccessRecallRequest,
    AccessRuntime,
    FileEvidenceStore,
    FileHandleStore,
    MemoryStatement,
)
from nollm_core import CoreRecallRequest, CoreRuntime, GeometryAddress, MemoryAtom, RecallBudget


CELL = GeometryAddress("eisenstein_exact_v1", "m1c7", 0, 0, 0)
BUDGET = RecallBudget(0, 8, 0, 0, 0, 8)


def decision(statement_id: str, action: str, **values) -> AccessDecision:
    return AccessDecision(f"d:{statement_id}:{action}", statement_id, action, reason_text="fixture", decided_by="fixture", **values)


def test_binding_callback_rejects_nested_access_and_direct_core(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    access = None
    rejected = []
    calls = 0

    def hook(_path: Path) -> None:
        nonlocal calls
        calls += 1
        if calls > 1:
            return
        operations = (
            lambda: access.apply(decision("b", "new", target_cell=CELL)),
            lambda: access.recall(AccessRecallRequest("nested", entry_cells=(CELL,), budget=BUDGET)),
            lambda: access.saved_handle("a"),
            lambda: core.put(MemoryAtom("direct", "x"), CELL),
            lambda: core.recall(CoreRecallRequest("nested-core", (CELL,), (), BUDGET)),
        )
        for operation in operations:
            try:
                operation()
            except RuntimeError:
                rejected.append(True)
        raise OSError("outer fault")

    store = FileHandleStore(tmp_path, hook)
    access = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    access.capture(MemoryStatement("a", "a"))
    access.capture(MemoryStatement("b", "b"))

    with pytest.raises(OSError, match="outer fault"):
        access.apply(decision("a", "new", target_cell=CELL))
    assert len(rejected) == 5
    assert core.placement_count() == 0
    assert not store.exists("a") and not store.exists("b")
    access.capture(MemoryStatement("c", "c"))
    handle = access.apply(decision("c", "new", target_cell=CELL))
    assert core.contains(handle) and access._active_operations == 0
    access.close()
    core.close()


def test_evidence_callback_rejects_nested_access_and_core(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    backing = FileEvidenceStore(tmp_path)
    access = None
    rejected = []

    class CallbackEvidence:
        workspace = backing.workspace

        def put_original(self, statement) -> None:
            for operation in (
                lambda: access.capture(statement),
                lambda: access.recall(AccessRecallRequest("nested", entry_cells=(CELL,), budget=BUDGET)),
                lambda: core.put(MemoryAtom("direct", "x"), CELL),
            ):
                try:
                    operation()
                except RuntimeError:
                    rejected.append(True)
            backing.put_original(statement)

        def get_original(self, statement_id):
            return backing.get_original(statement_id)

        def exists(self, statement_id):
            return backing.exists(statement_id)

    access = AccessRuntime(core, CallbackEvidence(), FileHandleStore(tmp_path))
    access.capture(MemoryStatement("e", "e"))
    assert len(rejected) == 3 and core.placement_count() == 0
    access.close()
    core.close()


def test_access_close_marks_closing_and_client_lease_blocks_core_close(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    entered, proceed = Event(), Event()
    backing = FileEvidenceStore(tmp_path)

    class BlockingEvidence:
        workspace = backing.workspace

        def put_original(self, statement) -> None:
            entered.set()
            assert proceed.wait(5)
            backing.put_original(statement)

        def get_original(self, statement_id):
            return backing.get_original(statement_id)

        def exists(self, statement_id):
            return backing.exists(statement_id)

    access = AccessRuntime(core, BlockingEvidence(), FileHandleStore(tmp_path))
    capturing = Thread(target=access.capture, args=(MemoryStatement("a", "a"),))
    capturing.start()
    assert entered.wait(5)
    closing = Thread(target=access.close)
    closing.start()
    deadline = monotonic() + 5
    while access.lifecycle_state != "CLOSING" and monotonic() < deadline:
        sleep(0.005)
    assert access.lifecycle_state == "CLOSING"
    with pytest.raises(RuntimeError, match="closing"):
        access.saved_handle("a")
    with pytest.raises(RuntimeError, match="client leases"):
        core.close()
    proceed.set()
    capturing.join(5)
    closing.join(5)
    assert access.lifecycle_state == "CLOSED"
    core.close()
    CoreRuntime(tmp_path / "core").close()


def test_constructor_holds_client_lease_through_return_window(tmp_path: Path) -> None:
    entered, proceed = Event(), Event()

    class BlockingCore(CoreRuntime):
        def acquire_client_lease(self, client_kind):
            lease = super().acquire_client_lease(client_kind)
            entered.set()
            assert proceed.wait(5)
            return lease

    core = BlockingCore(tmp_path / "core")
    outcomes = []
    thread = Thread(target=lambda: outcomes.append(AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))))
    thread.start()
    assert entered.wait(5)
    with pytest.raises(RuntimeError, match="client leases"):
        core.close()
    proceed.set()
    thread.join(5)
    assert len(outcomes) == 1 and outcomes[0].core.is_open
    outcomes[0].close()
    core.close()


def test_all_access_clients_must_close_before_core(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "core")
    first = AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
    second = AccessRuntime(core, FileEvidenceStore(tmp_path), FileHandleStore(tmp_path))
    first.close()
    with pytest.raises(RuntimeError, match="client leases"):
        core.close()
    second.close()
    core.close()


def test_constructor_failure_releases_pair_and_client_state(tmp_path: Path) -> None:
    class FailingCore(CoreRuntime):
        fail = True

        def acquire_client_lease(self, client_kind):
            lease = super().acquire_client_lease(client_kind)
            if self.fail:
                self.fail = False
                lease.close()
                raise RuntimeError("injected constructor failure")
            return lease

    core = FailingCore(tmp_path / "core")
    with pytest.raises(RuntimeError, match="OPEN"):
        AccessRuntime(core, FileEvidenceStore(tmp_path / "failed"), FileHandleStore(tmp_path / "failed"))
    assert not core._client_leases
    access = AccessRuntime(core, FileEvidenceStore(tmp_path / "replacement"), FileHandleStore(tmp_path / "replacement"))
    access.close()
    core.close()
