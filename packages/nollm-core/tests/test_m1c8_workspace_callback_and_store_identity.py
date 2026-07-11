from pathlib import Path

import pytest

from nollm_core import (
    CoreRecallRequest,
    CoreRuntime,
    FileCoreStateStore,
    GeometryAddress,
    MemoryAtom,
    RecallBudget,
)


CELL = GeometryAddress("eisenstein_exact_v1", "m1c8", 0, 0, 0)
REQUEST = CoreRecallRequest("m1c8", (CELL,), (), RecallBudget(0, 4, 0, 0, 0, 4))


def test_client_callback_cannot_reenter_same_or_different_lease(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path)
    first = core.acquire_client_lease("first")
    second = core.acquire_client_lease("second")
    successes = []

    def outer() -> None:
        for lease in (first, second):
            with pytest.raises(RuntimeError, match="callback"):
                lease.callback(lambda: successes.append(True))

    first.callback(outer)
    assert not successes
    assert core._active_operations == 0
    assert not hasattr(core._local, "callback_depth")
    first.close()
    second.close()
    core.close()


def test_transaction_callback_cannot_enter_client_callback(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path)
    lease = core.acquire_client_lease("access")
    successes = []
    with core.transaction() as transaction:
        with pytest.raises(RuntimeError, match="callback"):
            transaction.callback(lease.callback, lambda: successes.append(True))
    assert not successes
    assert core._active_operations == core._active_transactions == 0
    assert not hasattr(core._local, "callback_depth")
    lease.close()
    core.close()


def test_client_callback_exception_cleans_activity_and_depth(tmp_path: Path) -> None:
    core = CoreRuntime(tmp_path)
    lease = core.acquire_client_lease("access")

    def fail() -> None:
        raise OSError("callback fault")

    with pytest.raises(OSError, match="callback fault"):
        lease.callback(fail)
    assert core._active_operations == 0
    assert not hasattr(core._local, "callback_depth")
    lease.callback(lambda: None)
    lease.close()
    core.close()


def test_core_store_identity_and_runtime_state_path_are_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "core"
    store = FileCoreStateStore(workspace)
    core = CoreRuntime(workspace, store=store)
    state_path = core.state_path
    for target, name, value in (
        (store, "path", tmp_path / "redirected.json"),
        (store, "workspace", tmp_path / "redirected"),
        (core, "state_path", tmp_path / "other.json"),
        (core, "workspace", tmp_path / "other"),
    ):
        with pytest.raises(AttributeError):
            setattr(target, name, value)
    assert store.path == core.state_path == state_path
    core.close()


def test_retained_store_redirect_attempts_preserve_canonical_bytes(tmp_path: Path) -> None:
    workspace = tmp_path / "core"
    redirected = tmp_path / "redirected" / "current_state.json"
    attempts = []
    core = None

    class Sink:
        def emit(self, event) -> None:
            if event.name == "core.recall.begin":
                for name, value in (("path", redirected), ("workspace", redirected.parent)):
                    try:
                        setattr(store, name, value)
                    except AttributeError:
                        attempts.append(name)

    def hook(_temporary: Path) -> None:
        try:
            store.path = redirected
        except AttributeError:
            attempts.append("store-callback")

    store = FileCoreStateStore(workspace, hook)
    core = CoreRuntime(workspace, store=store, trace_sink=Sink())
    canonical_path = core.state_path
    core.recall(REQUEST)
    core.put(MemoryAtom("safe", "safe"), CELL)
    assert set(attempts) == {"path", "workspace", "store-callback"}
    assert core.state_path == canonical_path == store.path
    assert not redirected.exists()
    assert canonical_path.read_bytes() == core.state_bytes()
    core.close()
