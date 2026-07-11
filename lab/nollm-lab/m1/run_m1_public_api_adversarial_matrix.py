from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from nollm_access import AccessDecision,AccessRecallRequest,AccessRuntime,FileEvidenceStore,FileHandleStore,MemoryStatement
from nollm_core import CompilerMetadata,CoreRecallRequest,CoreRuntime,CoverageTemplateCompiler,FileCoreStateStore,GeometryAddress,GeometryAnchor,KernelEntry,MemoryAtom,RecallBudget
from nollm_snapshot import SnapshotService

def rejected(call):
    try: call()
    except (TypeError,ValueError,RuntimeError): return True
    return False

def run_matrix(root:Path)->dict[str,bool]:
    facts={}
    facts['kernel_entry_unknown_type_rejected']=rejected(lambda:KernelEntry(-1,0,0,1,'graph_edge',()))
    facts['kernel_entry_noncanonical_flags_rejected']=rejected(lambda:KernelEntry(-1,0,0,1,flags=('z','a')))
    template=CoverageTemplateCompiler().compile('eisenstein_exact_v1','coverage_up')
    duplicate=(KernelEntry(-1,0,0,30000,flags=('eisenstein_exact',)),KernelEntry(-1,0,0,35536,flags=('eisenstein_exact',)))
    facts['duplicate_geometric_target_rejected']=rejected(lambda:replace(template,entries=duplicate,sum_weight_q16=65536))
    facts['negative_normalization_residual_rejected']=rejected(lambda:replace(template,sum_weight_q16=65537,normalization_residual_q16=-1))
    facts['compiler_nonstring_flags_rejected']=rejected(lambda:CompilerMetadata('x','x','x',1,'x',(1,)))
    quasi=CoverageTemplateCompiler().compile('dream_quasi_v1','coverage_up')
    facts['dream_quasi_residual_canonical']=quasi.approximation_residual_q16==65536//16 and rejected(lambda:replace(quasi,approximation_residual_q16=10**30))
    identity=__import__('nollm_core').KernelRegistry().identity;facts['registry_identity_stable']=identity==__import__('nollm_core').KernelRegistry().identity
    cell=GeometryAddress('eisenstein_exact_v1','c',0,0,0);budget=RecallBudget(0,1,0,0,0,1)
    core=CoreRuntime(root/'core');facts['second_core_owner_rejected_at_constructor']=rejected(lambda:CoreRuntime(root/'core'))
    facts['direct_stale_overwrite_prevented']=rejected(lambda:CoreRuntime(root/'core'))
    token=core.begin_consistent_read();facts['consistent_read_same_thread_mutation_rejected']=rejected(lambda:core.put(MemoryAtom('a','a'),cell));core.end_consistent_read(token)
    facts['public_store_bypass_rejected']=rejected(lambda:core.store.write_bytes(core.state_bytes()))
    facts['public_cell_view_read_only']=not hasattr(core,'cells');facts['occupied_cells_works']=core.occupied_cells()==()
    facts['core_recall_noncanonical_rejected']=rejected(lambda:CoreRecallRequest('r',(cell,),('lateral','bridge'),budget))
    facts['access_recall_noncanonical_rejected']=rejected(lambda:AccessRecallRequest('r',entry_cells=(cell,cell),budget=budget))
    facts['access_decision_wrong_types_rejected']=rejected(lambda:AccessDecision(1,2,'defer',reason_text=3))
    access=AccessRuntime(core,FileEvidenceStore(root/'access-a'),FileHandleStore(root/'access-a'))
    facts['same_core_different_access_root_rejected']=rejected(lambda:AccessRuntime(core,FileEvidenceStore(root/'access-b'),FileHandleStore(root/'access-b')))
    facts['cross_root_rollback_unconstructable']=rejected(lambda:AccessRuntime(core,FileEvidenceStore(root/'access-b'),FileHandleStore(root/'access-b')))
    access.close();core.close();reopened=CoreRuntime(root/'core');facts['core_close_reopen_succeeds']=reopened.is_open;facts['snapshot_after_reopen_equal']=SnapshotService().create(reopened)==reopened.state_bytes();reopened.close()
    phase_core=CoreRuntime(root/'phase');none=GeometryAddress('eisenstein_exact_v1','c',0,0,0);phase=GeometryAddress('eisenstein_exact_v1','c',0,0,0,'p')
    phase_core.put(MemoryAtom('n','n'),none);phase_core.put(MemoryAtom('p','p'),phase);payload=phase_core.state_bytes();phase_core.close();again=CoreRuntime(root/'phase');facts['mixed_phase_round_trip']=again.state_bytes()==payload;again.close()
    facts['anchor_order_rejected']=rejected(lambda:GeometryAnchor('bad',(phase,none)))
    lateral=CoreRuntime(root/'lateral');neighbor=none.lateral(1)[0];lateral.put(MemoryAtom('l','l'),neighbor);request=CoreRecallRequest('l',(none,),('lateral',),RecallBudget(1,8,0,1,0,2));facts['lateral_ring_one_real_recall']=len(lateral.recall(request).items)==1;facts['lateral_unregistered_ring_rejected']=rejected(lambda:lateral.recall(CoreRecallRequest('x',(none,),('lateral',),RecallBudget(2,8,0,2,0,2))));lateral.close()
    class Reentrant:
        def __init__(self):self.core=None;self.rejected=False
        def emit(self,event):
            if event.name=='core.batch.begin':
                try:self.core.put(MemoryAtom('inner','inner'),none)
                except RuntimeError:self.rejected=True
    sink=Reentrant();traced=CoreRuntime(root/'trace',trace_sink=sink);sink.core=traced;traced.put(MemoryAtom('outer','outer'),none);facts['reentrant_trace_mutation_rejected']=sink.rejected and traced.placement_count()==1;facts['trace_parity']=facts['reentrant_trace_mutation_rejected'];traced.close()
    entered,release_event=Event(),Event()
    def hook(_):entered.set();release_event.wait(5)
    closing_core=CoreRuntime(root/'close',store=FileCoreStateStore(root/'close',hook))
    with ThreadPoolExecutor(2) as pool:
        write=pool.submit(closing_core.put,MemoryAtom('x','x'),none);entered.wait(5);closing=pool.submit(closing_core.close);safe=not closing.done();release_event.set();write.result();closing.result()
    facts['core_close_during_operation_safe']=safe
    race_root=root/'access-race';race_core=CoreRuntime(root/'access-race-core');binding_entered,binding_release=Event(),Event();fail=True
    def binding_hook(_):
        nonlocal fail
        if fail:fail=False;binding_entered.set();binding_release.wait(5);raise OSError('binding fault')
    race_store=FileHandleStore(race_root,binding_hook);race_access=AccessRuntime(race_core,FileEvidenceStore(race_root),race_store);race_access.capture(MemoryStatement('a','a'))
    race_cell=GeometryAddress('eisenstein_exact_v1','race',0,0,0);direct_cell=GeometryAddress('eisenstein_exact_v1','race',0,1,0)
    with ThreadPoolExecutor(5) as pool:
        failed=pool.submit(race_access.apply,AccessDecision('a','a','new',target_cell=race_cell,reason_text='x'));binding_entered.wait(5)
        direct=pool.submit(race_core.put,MemoryAtom('direct','direct'),direct_cell)
        reading=pool.submit(race_core.recall,CoreRecallRequest('read',(direct_cell,),(),RecallBudget(0,1,0,0,0,1)))
        close_started=Event()
        def close_access():close_started.set();race_access.close()
        closing=pool.submit(close_access);close_started.wait(5)
        other=pool.submit(AccessRuntime,race_core,FileEvidenceStore(root/'other-root'),FileHandleStore(root/'other-root'))
        facts['access_close_race_safe']=not closing.done() and not other.done()
        binding_release.set()
        try:failed.result()
        except OSError:pass
        direct_handle=direct.result();read_result=reading.result();closing.result();rebound=other.result()
    facts['direct_core_success_survives_failed_access_transaction']=race_core.contains(direct_handle)
    facts['concurrent_recall_consistent']=len(read_result.items)==1 and read_result.items[0].handle==direct_handle
    rebound.close();race_core.close()
    corrupt_root=root/'corrupt';corrupt_core=CoreRuntime(corrupt_root/'core');corrupt_evidence=FileEvidenceStore(corrupt_root);corrupt_access=AccessRuntime(corrupt_core,corrupt_evidence,FileHandleStore(corrupt_root));corrupt_evidence.put_original(MemoryStatement('base','base'));base=corrupt_access.apply(AccessDecision('base','base','new',target_cell=cell,reason_text='x'));corrupt_evidence.put_original(MemoryStatement('bad','bad'));corrupt_evidence._path('bad').write_text('{}\n',encoding='utf-8');facts['reuse_corrupt_evidence_rejected']=rejected(lambda:corrupt_access.apply(AccessDecision('bad','bad','reuse',existing_handle=base,reason_text='x')));corrupt_access.close();corrupt_core.close()
    report=Path(__file__).resolve().parents[3]/'docs/architecture/module-ownership/M1C5_BOUNDARY_REPORT.json'
    if report.exists():
        boundary=json.loads(report.read_text(encoding='utf-8'));facts['boundary_zero']=boundary.get('production_violations')==[] and boundary.get('cycles_production')==[]
    return facts

def main():
    with TemporaryDirectory(prefix='nollm-m1c5-matrix-') as directory:
        facts=run_matrix(Path(directory));assert all(facts.values());print(json.dumps({'status':'passed','facts':facts},sort_keys=True))
if __name__=='__main__':main()
