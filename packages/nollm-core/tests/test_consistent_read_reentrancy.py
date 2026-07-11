import pytest
from nollm_core import CoreRuntime,GeometryAddress,MemoryAtom

def test_consistent_read_rejects_same_thread_mutation(tmp_path):
    core=CoreRuntime(tmp_path);token=core.begin_consistent_read()
    with pytest.raises(RuntimeError,match='consistent read'):core.put(MemoryAtom('a','a'),GeometryAddress('eisenstein_exact_v1','c',0,0,0))
    core.end_consistent_read(token);core.close()
