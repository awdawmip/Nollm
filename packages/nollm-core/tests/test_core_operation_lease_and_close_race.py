from concurrent.futures import ThreadPoolExecutor
from threading import Event
from nollm_core import CoreRuntime,FileCoreStateStore,GeometryAddress,MemoryAtom

def test_close_waits_for_blocked_mutation(tmp_path):
    entered,release=Event(),Event()
    def hook(_):entered.set();release.wait(5)
    core=CoreRuntime(tmp_path,store=FileCoreStateStore(tmp_path,hook));cell=GeometryAddress('eisenstein_exact_v1','c',0,0,0)
    with ThreadPoolExecutor(2) as pool:
        mutation=pool.submit(core.put,MemoryAtom('a','a'),cell);assert entered.wait(5)
        closing=pool.submit(core.close);assert not closing.done();release.set();mutation.result();closing.result()
    reopened=CoreRuntime(tmp_path);assert reopened.placement_count()==1;reopened.close()
