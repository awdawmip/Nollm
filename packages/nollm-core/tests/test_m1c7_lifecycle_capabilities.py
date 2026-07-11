from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep

import pytest

from nollm_core import (
    CoreClientLease,
    CoreRecallRequest,
    CoreRuntime,
    CoreTransaction,
    FileCoreStateStore,
    GeometryAddress,
    MemoryAtom,
    RecallBudget,
)


CELL = GeometryAddress("eisenstein_exact_v1", "m1c7", 0, 0, 0)
REQUEST = CoreRecallRequest("r", (CELL,), (), RecallBudget(0, 4, 0, 0, 0, 4))


def wait_state(runtime: CoreRuntime, state: str) -> None:
    deadline = monotonic() + 5
    while runtime.lifecycle_state != state and monotonic() < deadline:
        sleep(0.005)
    assert runtime.lifecycle_state == state


def test_close_marks_closing_before_wait_and_rejects_new_operations(tmp_path: Path) -> None:
    CoreRuntime(tmp_path).close()
    entered, proceed = Event(), Event()

    def hook(_path: Path) -> None:
        entered.set()
        assert proceed.wait(5)

    core = CoreRuntime(tmp_path, store=FileCoreStateStore(tmp_path, hook))
    with ThreadPoolExecutor(2) as pool:
        writing = pool.submit(core.put, MemoryAtom("a", "a"), CELL)
        assert entered.wait(5)
        closing = pool.submit(core.close)
        wait_state(core, "CLOSING")
        with pytest.raises(RuntimeError, match="closing"):
            core.placement_count()
        with pytest.raises(RuntimeError, match="live mutable owner"):
            CoreRuntime(tmp_path)
        proceed.set()
        writing.result(timeout=5)
        closing.result(timeout=5)
    assert core.lifecycle_state == "CLOSED"
    CoreRuntime(tmp_path).close()


def test_client_lease_lifetime_foreign_and_double_release(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path / "a")
    other = CoreRuntime(tmp_path / "b")
    lease = core.acquire_client_lease("test")
    with pytest.raises(RuntimeError, match="client leases"):
        core.close()
    with pytest.raises(ValueError, match="foreign"):
        other.release_client_lease(lease)
    forged = CoreClientLease(core, object(), object(), "forged")
    with pytest.raises(ValueError, match="foreign"):
        core.release_client_lease(forged)
    lease.close()
    with pytest.raises(ValueError, match="expired"):
        lease.close()
    core.close()
    CoreRuntime(tmp_path / "a").close()
    other.close()


def test_transaction_capability_is_nonreentrant_thread_bound_and_expires(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path)
    errors = []
    with core.transaction() as transaction:
        handle = transaction.put(MemoryAtom("a", "a"), CELL)
        assert transaction.contains(handle)
        with pytest.raises(RuntimeError, match="reentrant public Core operation"):
            core.put(MemoryAtom("b", "b"), CELL)

        def wrong_thread() -> None:
            try:
                transaction.state_bytes()
            except Exception as error:
                errors.append(error)

        thread = Thread(target=wrong_thread)
        thread.start()
        thread.join(5)
    assert len(errors) == 1 and "wrong-thread" in str(errors[0])
    with pytest.raises(ValueError, match="expired"):
        transaction.state_bytes()
    forged = CoreTransaction(core, object(), object())
    with pytest.raises(ValueError, match="foreign"):
        forged.state_bytes()
    assert core._active_operations == core._active_transactions == 0
    core.close()


def test_wrong_thread_consistent_read_is_zero_state_change(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path)
    other = CoreRuntime(tmp_path / "other")
    token = core.begin_consistent_read()
    errors = []

    def attack() -> None:
        for operation in (core.export_state, core.end_consistent_read):
            try:
                operation(token)
            except Exception as error:
                errors.append(error)

    thread = Thread(target=attack)
    thread.start()
    thread.join(5)
    assert len(errors) == 2 and all("another thread" in str(error) for error in errors)
    assert token.active and core._read_token is token and core._active_consistent_reads == 1
    with pytest.raises(ValueError, match="foreign"):
        other.export_state(token)
    assert core.export_state(token) == core.state_path.read_bytes()
    core.end_consistent_read(token)
    with pytest.raises(ValueError, match="invalid"):
        core.end_consistent_read(token)
    core.close()
    CoreRuntime(tmp_path).close()
    other.close()


def test_store_hook_is_frozen_and_callbacks_cannot_enter_core(tmp_path: Path) -> None:
    CoreRuntime(tmp_path).close()
    core = None
    rejected = []

    def hook(_path: Path) -> None:
        operations = (
            lambda: core.put(MemoryAtom("nested", "x"), CELL),
            lambda: core.recall(REQUEST),
            core.close,
            lambda: core.acquire_client_lease("nested"),
            lambda: core.transaction().__enter__(),
        )
        for operation in operations:
            try:
                operation()
            except RuntimeError:
                rejected.append(True)

    store = FileCoreStateStore(tmp_path, hook)
    core = CoreRuntime(tmp_path, store=store)
    with pytest.raises(RuntimeError, match="frozen"):
        store.before_replace = None
    core.put(MemoryAtom("outer", "x"), CELL)
    assert len(rejected) == 5 and core.placement_count() == 1
    assert not hasattr(core, "store") and not hasattr(core, "trace_sink")
    core.close()


def test_trace_cannot_install_future_store_hook(tmp_path: Path) -> None:
    core = None
    attempts = []

    class Sink:
        def emit(self, event) -> None:
            if event.name == "core.recall.begin":
                try:
                    core.store.before_replace = lambda _path: (_ for _ in ()).throw(OSError("installed"))
                except AttributeError:
                    attempts.append(True)

    core = CoreRuntime(tmp_path, trace_sink=Sink())
    core.recall(REQUEST)
    core.put(MemoryAtom("safe", "safe"), CELL)
    assert attempts and core.placement_count() == 1
    core.close()


def test_operation_exception_releases_global_active_count(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path)
    core.put(MemoryAtom("a", "a"), CELL)
    with pytest.raises(FileExistsError):
        core.put(MemoryAtom("a", "duplicate"), CELL)
    assert core._active_operations == core._active_transactions == 0
    core.close()
