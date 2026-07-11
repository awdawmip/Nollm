from __future__ import annotations
import os, weakref
from pathlib import Path
from threading import RLock

_guard=RLock(); _owners: dict[str, weakref.ReferenceType[object]]={}

def identity(path: Path) -> str:
    value=str(Path(path).resolve())
    return os.path.normcase(value) if os.name=='nt' else value

def claim(path: Path, owner: object) -> str:
    key=identity(path)
    with _guard:
        current=_owners.get(key)
        if current is not None and current() is not None:
            raise RuntimeError('canonical Core workspace already has a live mutable owner')
        _owners[key]=weakref.ref(owner,lambda ref,k=key:_release_dead(k,ref))
    return key

def release(key: str, owner: object) -> None:
    with _guard:
        current=_owners.get(key)
        if current is not None and current() is owner: _owners.pop(key,None)

def _release_dead(key: str, ref: weakref.ReferenceType[object]) -> None:
    with _guard:
        if _owners.get(key) is ref: _owners.pop(key,None)
