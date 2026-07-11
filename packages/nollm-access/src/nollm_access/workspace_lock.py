from __future__ import annotations

from pathlib import Path
from threading import RLock

_REGISTRY_GUARD = RLock()
_LOCKS: dict[str, RLock] = {}
_CORE_OWNERS: dict[str, object] = {}
_ACCESS_CORES: dict[str, str] = {}


def workspace_lock(root: Path) -> RLock:
    identity = str(Path(root).resolve()).casefold()
    with _REGISTRY_GUARD:
        return _LOCKS.setdefault(identity, RLock())


def coordinate_workspace(access_root: Path, core: object, core_state_path: Path) -> RLock:
    access_id = str(Path(access_root).resolve()).casefold()
    core_id = str(Path(core_state_path).resolve()).casefold()
    with _REGISTRY_GUARD:
        owner = _CORE_OWNERS.get(core_id)
        if owner is not None and owner is not core:
            raise RuntimeError("canonical Core workspace already has a distinct mutable state owner")
        bound = _ACCESS_CORES.get(access_id)
        if bound is not None and bound != core_id:
            raise ValueError("Access and Core workspace identity mismatch")
        _CORE_OWNERS[core_id] = core
        _ACCESS_CORES[access_id] = core_id
        return _LOCKS.setdefault(access_id, RLock())
