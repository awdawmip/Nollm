from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from nollm_access import AccessDecision,AccessRuntime,FileEvidenceStore,FileHandleStore,MemoryStatement
from nollm_core import CoreRuntime,GeometryAddress,MemoryAtom

def test_access_atomic_lease_blocks_direct_core(tmp_path):
    entered,release=Event(),Event();fail=True
    def hook(_):
        nonlocal fail
        if fail:fail=False;entered.set();release.wait(5);raise OSError('fault')
    core=CoreRuntime(tmp_path/'core');store=FileHandleStore(tmp_path,hook);access=AccessRuntime(core,FileEvidenceStore(tmp_path),store);access.capture(MemoryStatement('a','a'));cell=GeometryAddress('eisenstein_exact_v1','c',0,0,0)
    with ThreadPoolExecutor(2) as pool:
        first=pool.submit(access.apply,AccessDecision('a','a','new',target_cell=cell,reason_text='x'));assert entered.wait(5)
        direct=pool.submit(core.put,MemoryAtom('b','b'),GeometryAddress('eisenstein_exact_v1','c',0,1,0));assert not direct.done();release.set()
        with pytest.raises(OSError):first.result()
        handle=direct.result()
    assert core.contains(handle)
