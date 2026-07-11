from nollm_core import CoreRuntime,GeometryAddress,MemoryAtom

class Sink:
    def __init__(self):self.core=None;self.rejected=False
    def emit(self,event):
        if event.name=='core.batch.begin':
            try:self.core.put(MemoryAtom('inner','inner'),GeometryAddress('eisenstein_exact_v1','c',0,1,0))
            except RuntimeError:self.rejected=True

def test_reentrant_mutation_rejected(tmp_path):
    sink=Sink();core=CoreRuntime(tmp_path,trace_sink=sink);sink.core=core;core.put(MemoryAtom('outer','outer'),GeometryAddress('eisenstein_exact_v1','c',0,0,0));assert sink.rejected and core.placement_count()==1
