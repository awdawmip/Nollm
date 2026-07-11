from __future__ import annotations
import os
from pathlib import Path
from threading import RLock

_guard=RLock(); _pairs: dict[tuple[str,str],tuple[RLock,int]]={}; _access:dict[str,str]={}; _core:dict[str,str]={}

def _id(path:Path)->str:
    value=str(path.resolve()); return os.path.normcase(value) if os.name=='nt' else value

def acquire(access_root:Path,core_path:Path)->tuple[RLock,tuple[str,str]]:
    a,c=_id(access_root),_id(core_path); key=(a,c)
    with _guard:
        if a in _access and _access[a]!=c: raise ValueError('Access root already bound to different Core workspace')
        if c in _core and _core[c]!=a: raise ValueError('Core workspace already bound to different Access root')
        lock,count=_pairs.get(key,(RLock(),0));_pairs[key]=(lock,count+1);_access[a]=c;_core[c]=a
        return lock,key

def release(key:tuple[str,str])->None:
    with _guard:
        lock,count=_pairs[key]
        if count>1:_pairs[key]=(lock,count-1);return
        _pairs.pop(key);a,c=key;_access.pop(a,None);_core.pop(c,None)

def workspace_lock(root:Path)->RLock:
    # Evidence-only operations use a stable lock without creating a coordinator lease.
    key=(_id(root),'evidence-only')
    with _guard:
        return _pairs.setdefault(key,(RLock(),0))[0]
