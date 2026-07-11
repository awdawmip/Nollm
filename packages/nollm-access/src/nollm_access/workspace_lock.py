from __future__ import annotations

from pathlib import Path
from threading import RLock

_REGISTRY_GUARD = RLock()
_LOCKS: dict[str, RLock] = {}


def workspace_lock(root: Path) -> RLock:
    identity = str(Path(root).resolve()).casefold()
    with _REGISTRY_GUARD:
        return _LOCKS.setdefault(identity, RLock())
