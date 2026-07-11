import os
from pathlib import Path
from threading import RLock


_guard = RLock()
_locks: dict[tuple[str, ...], RLock] = {}


def _identity(path: Path) -> str:
    value = str(Path(path).resolve())
    return os.path.normcase(value) if os.name == "nt" else value


def composition_lock(access_root: Path, core_state_path: Path) -> RLock:
    key = ("composition", _identity(access_root), _identity(core_state_path))
    with _guard:
        return _locks.setdefault(key, RLock())


def workspace_lock(root: Path) -> RLock:
    key = ("workspace", _identity(root))
    with _guard:
        return _locks.setdefault(key, RLock())
