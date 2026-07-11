from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
from threading import RLock, local


class BindingWriterCapability:
    __slots__ = ("coordinator", "generation", "active")

    def __init__(self, coordinator: "PairCoordinator") -> None:
        self.coordinator = coordinator
        self.generation = object()
        self.active = True


class PairLease:
    __slots__ = ("coordinator", "active")

    def __init__(self, coordinator: "PairCoordinator") -> None:
        self.coordinator = coordinator
        self.active = True


class PairCoordinator:
    def __init__(self, key: tuple[str, str]) -> None:
        self.key = key
        self.transaction_lock = RLock()
        self._local = local()
        self._refcount = 0
        self._binding_configuration: tuple[object, ...] | None = None
        self._binding_stores: set[object] = set()
        self.binding_capability = BindingWriterCapability(self)

    def assert_entry_allowed(self, operation: str) -> None:
        if getattr(self._local, "callback_depth", 0):
            raise RuntimeError(f"pair callback cannot enter Access {operation}")

    @contextmanager
    def callback_fence(self, kind: str):
        if getattr(self._local, "callback_depth", 0):
            raise RuntimeError("recursive pair callback is forbidden")
        self._local.callback_depth = 1
        self._local.callback_kind = kind
        try:
            yield
        finally:
            del self._local.callback_depth
            del self._local.callback_kind

    def bind_store(self, store: object) -> None:
        configuration = store.binding_configuration
        if self._binding_configuration is None:
            self._binding_configuration = configuration
        elif self._binding_configuration != configuration:
            raise ValueError("same Access pair requires compatible immutable HandleStore configuration")
        store.bind_writer(self.binding_capability, self.key)
        self._binding_stores.add(store)

    def add_ref(self) -> PairLease:
        self._refcount += 1
        return PairLease(self)

    def release_ref(self, lease: PairLease) -> bool:
        if type(lease) is not PairLease or lease.coordinator is not self:
            raise ValueError("foreign Access pair lease")
        if not lease.active:
            raise ValueError("expired Access pair lease")
        lease.active = False
        self._refcount -= 1
        if self._refcount:
            return False
        for store in tuple(self._binding_stores):
            store.unbind_writer(self.binding_capability)
        self.binding_capability.active = False
        return True


_guard = RLock()
_pairs: dict[tuple[str, str], PairCoordinator] = {}
_access: dict[str, str] = {}
_core: dict[str, str] = {}
_evidence_locks: dict[str, RLock] = {}


def _id(path: Path) -> str:
    value = str(path.resolve())
    return os.path.normcase(value) if os.name == "nt" else value


def acquire(access_root: Path, core_path: Path, handle_store: object) -> tuple[PairCoordinator, PairLease]:
    access_id, core_id = _id(access_root), _id(core_path)
    key = (access_id, core_id)
    with _guard:
        coordinator = _pairs.get(key)
        if coordinator is not None:
            coordinator.assert_entry_allowed("constructor")
        if access_id in _access and _access[access_id] != core_id:
            raise ValueError("Access root already bound to different Core workspace")
        if core_id in _core and _core[core_id] != access_id:
            raise ValueError("Core workspace already bound to different Access root")
        created = coordinator is None
        if created:
            coordinator = PairCoordinator(key)
            _pairs[key] = coordinator
        try:
            coordinator.bind_store(handle_store)
            lease = coordinator.add_ref()
        except Exception:
            if created:
                _pairs.pop(key, None)
            raise
        _access[access_id] = core_id
        _core[core_id] = access_id
        return coordinator, lease


def release(lease: PairLease) -> None:
    if type(lease) is not PairLease:
        raise ValueError("foreign Access pair lease")
    coordinator = lease.coordinator
    with _guard:
        if not coordinator.release_ref(lease):
            return
        _pairs.pop(coordinator.key, None)
        access_id, core_id = coordinator.key
        _access.pop(access_id, None)
        _core.pop(core_id, None)


def workspace_lock(root: Path) -> RLock:
    key = _id(root)
    with _guard:
        return _evidence_locks.setdefault(key, RLock())
