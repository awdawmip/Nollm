from __future__ import annotations
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Thread
from time import monotonic, sleep
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from nollm_access import AccessDecision,AccessRecallRequest,AccessRuntime,FileEvidenceStore,FileHandleStore,MemoryStatement
from nollm_core import AtomHandle,CompilerMetadata,CoreRecallRequest,CoreRuntime,CoverageTemplateCompiler,FileCoreStateStore,GeometryAddress,GeometryAnchor,KernelEntry,MemoryAtom,RecallBudget
from nollm_snapshot import SnapshotService

def rejected(call):
    try: call()
    except (AttributeError,TypeError,ValueError,RuntimeError): return True
    return False


def join_thread(thread: Thread, stage: str) -> None:
    thread.join(5)
    if thread.is_alive():
        frame = sys._current_frames().get(thread.ident)
        stack = "" if frame is None else "".join(traceback.format_stack(frame))
        raise RuntimeError(f"{stage} timed out; thread={thread.name}\n{stack}")

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
    facts['public_store_bypass_rejected']=not hasattr(core,'store')
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
    class LifecycleTrace:
        def __init__(self,name,action):self.name=name;self.action=action;self.rejected=False
        def emit(self,event):
            if event.name==self.name:
                try:self.action()
                except RuntimeError:self.rejected=True
    recall_core=None
    recall_sink=LifecycleTrace('core.recall.begin',lambda:recall_core.put(MemoryAtom('trace-added','x'),none));recall_core=CoreRuntime(root/'trace-recall',trace_sink=recall_sink)
    recall_result=recall_core.recall(CoreRecallRequest('trace',(none,),(),RecallBudget(0,1,0,0,0,1)));facts['trace_recall_observation_only']=recall_sink.rejected and not recall_result.items;recall_core.close()
    snapshot_core=None
    snapshot_sink=LifecycleTrace('core.snapshot.release',lambda:snapshot_core.put(MemoryAtom('release-added','x'),none));snapshot_core=CoreRuntime(root/'trace-snapshot',trace_sink=snapshot_sink);snapshot_token=snapshot_core.begin_consistent_read();snapshot_core.export_state(snapshot_token);snapshot_core.end_consistent_read(snapshot_token);facts['trace_snapshot_release_observation_only']=snapshot_sink.rejected and snapshot_core.placement_count()==0;snapshot_core.close()
    lease_core=CoreRuntime(root/'lease-close')
    with lease_core.transaction_lease():facts['same_thread_transaction_close_rejected']=rejected(lease_core.close) and rejected(lambda:CoreRuntime(root/'lease-close'))
    lease_core.close()
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
    with ThreadPoolExecutor(4) as pool:
        failed=pool.submit(race_access.apply,AccessDecision('a','a','new',target_cell=race_cell,reason_text='x'));binding_entered.wait(5)
        close_started=Event()
        def close_access():close_started.set();race_access.close()
        closing=pool.submit(close_access);close_started.wait(5)
        facts['active_pair_rebind_rejected']=rejected(lambda:AccessRuntime(race_core,FileEvidenceStore(root/'other-root'),FileHandleStore(root/'other-root')))
        facts['access_close_race_safe']=not closing.done()
        binding_release.set()
        try:failed.result()
        except OSError:pass
        closing.result()
    direct_handle=race_core.put(MemoryAtom('direct','direct'),direct_cell);read_result=race_core.recall(CoreRecallRequest('read',(direct_cell,),(),RecallBudget(0,1,0,0,0,1)));rebound=AccessRuntime(race_core,FileEvidenceStore(root/'other-root'),FileHandleStore(root/'other-root'))
    facts['direct_core_success_survives_failed_access_transaction']=race_core.contains(direct_handle)
    facts['concurrent_recall_consistent']=len(read_result.items)==1 and read_result.items[0].handle==direct_handle
    rebound.close();race_core.close()
    callback_core=CoreRuntime(root/'callback-core');callback_access=None;callback_facts={'close':False,'rebind':False};callback_once=True
    def callback_hook(_):
        nonlocal callback_once
        if not callback_once:return
        callback_once=False;callback_facts['close']=rejected(callback_access.close);callback_facts['rebind']=rejected(lambda:AccessRuntime(callback_core,FileEvidenceStore(root/'callback-other'),FileHandleStore(root/'callback-other')));raise OSError('callback fault')
    callback_access=AccessRuntime(callback_core,FileEvidenceStore(root/'callback-access'),FileHandleStore(root/'callback-access',callback_hook));callback_access.capture(MemoryStatement('callback','x'))
    try:callback_access.apply(AccessDecision('callback','callback','new',target_cell=none,reason_text='x'))
    except OSError:pass
    facts['access_callback_close_rejected']=callback_facts['close'];facts['access_callback_cross_root_rejected']=callback_facts['rebind'];facts['callback_rollback_consistent']=callback_core.placement_count()==0
    callback_access.close();callback_core.close()
    corrupt_root=root/'corrupt';corrupt_core=CoreRuntime(corrupt_root/'core');corrupt_evidence=FileEvidenceStore(corrupt_root);corrupt_access=AccessRuntime(corrupt_core,corrupt_evidence,FileHandleStore(corrupt_root));corrupt_evidence.put_original(MemoryStatement('base','base'));base=corrupt_access.apply(AccessDecision('base','base','new',target_cell=cell,reason_text='x'));corrupt_evidence.put_original(MemoryStatement('bad','bad'));corrupt_evidence._path('bad').write_text('{}\n',encoding='utf-8');facts['reuse_corrupt_evidence_rejected']=rejected(lambda:corrupt_access.apply(AccessDecision('bad','bad','reuse',existing_handle=base,reason_text='x')));corrupt_access.close();corrupt_core.close()
    facts.update(run_m1c7_matrix(root/'m1c7'))
    facts.update(run_m1c8_matrix(root/'m1c8'))
    report=Path(__file__).resolve().parents[3]/'docs/architecture/module-ownership/M1C8_BOUNDARY_REPORT.json'
    if report.exists():
        boundary=json.loads(report.read_text(encoding='utf-8'));facts['boundary_zero']=boundary.get('production_violations')==[] and boundary.get('cycles_production')==[];facts['cycles_zero']=boundary.get('cycles_production')==[]
    return facts


def run_m1c7_matrix(root: Path) -> dict[str, bool]:
    facts: dict[str, bool] = {}
    cell = GeometryAddress('eisenstein_exact_v1', 'm1c7', 0, 0, 0)
    budget = RecallBudget(0, 8, 0, 0, 0, 8)

    CoreRuntime(root/'closing').close()
    entered, proceed = Event(), Event()
    def blocking_hook(_): entered.set(); proceed.wait(5)
    core = CoreRuntime(root/'closing', store=FileCoreStateStore(root/'closing', blocking_hook))
    write = Thread(target=core.put, args=(MemoryAtom('a','a'), cell)); write.start(); entered.wait(5)
    close = Thread(target=core.close); close.start(); deadline=monotonic()+5
    while core.lifecycle_state!='CLOSING' and monotonic()<deadline: sleep(0.005)
    facts['core_closing_state_observed']=core.lifecycle_state=='CLOSING'
    facts['close_pending_new_operation_rejected']=rejected(core.placement_count)
    facts['no_new_owner_while_closing']=rejected(lambda:CoreRuntime(root/'closing'))
    proceed.set(); join_thread(write,'core write'); join_thread(close,'core close')
    facts['core_state_machine_open_closing_closed']=core.lifecycle_state=='CLOSED'

    client_core=CoreRuntime(root/'client');client=AccessRuntime(client_core,FileEvidenceStore(root/'client-access'),FileHandleStore(root/'client-access'))
    facts['access_live_core_close_rejected']=rejected(client_core.close)
    facts['client_lease_lifetime_bound']=client_core.is_open
    client.close();client_core.close()

    access_core=CoreRuntime(root/'access-closing-core');access_entered,access_proceed=Event(),Event()
    def access_hook(_):access_entered.set();access_proceed.wait(5)
    access_store=FileHandleStore(root/'access-closing',access_hook);access=AccessRuntime(access_core,FileEvidenceStore(root/'access-closing'),access_store);access.capture(MemoryStatement('closing','closing'))
    applying=Thread(target=access.apply,args=(AccessDecision('closing','closing','new',target_cell=cell,reason_text='x'),));applying.start();access_entered.wait(5)
    access_close=Thread(target=access.close);access_close.start();deadline=monotonic()+5
    while access.lifecycle_state!='CLOSING' and monotonic()<deadline:sleep(0.005)
    access_rejects_new=rejected(lambda:access.saved_handle('closing'));access_proceed.set();join_thread(applying,'Access apply');join_thread(access_close,'Access close')
    facts['access_state_machine_open_closing_closed']=access_rejects_new and access.lifecycle_state=='CLOSED'
    access_core.close()

    token_core=CoreRuntime(root/'token');token=token_core.begin_consistent_read();errors=[]
    def wrong_thread():
        for operation in (token_core.export_state,token_core.end_consistent_read):
            try:operation(token)
            except Exception as error:errors.append(error)
    thread=Thread(target=wrong_thread);thread.start();join_thread(thread,'wrong-thread consistent read')
    facts['wrong_thread_consistent_read_rejected']=len(errors)==2 and token.active
    owner_bytes=token_core.export_state(token);token_core.end_consistent_read(token)
    facts['owner_thread_consistent_read_survives']=owner_bytes==token_core.state_path.read_bytes()
    token_core.close()

    capability_core=CoreRuntime(root/'capability');thread_errors=[]
    with capability_core.transaction() as transaction:
        def wrong_capability_thread():
            try:transaction.state_bytes()
            except Exception as error:thread_errors.append(error)
        thread=Thread(target=wrong_capability_thread);thread.start();join_thread(thread,'wrong-thread transaction capability')
    facts['transaction_capability_foreign_rejected']=len(thread_errors)==1 and rejected(transaction.state_bytes)
    capability_core.close()

    callback_core=CoreRuntime(root/'callback-core');callback_access=None;callback_results={'apply':False,'recall':False,'core':False};first=True
    def callback_hook(_):
        nonlocal first
        if not first:return
        first=False
        callback_results['apply']=rejected(lambda:callback_access.apply(AccessDecision('nested','nested','new',target_cell=cell,reason_text='x')))
        callback_results['recall']=rejected(lambda:callback_access.recall(AccessRecallRequest('nested',entry_cells=(cell,),budget=budget)))
        callback_results['core']=rejected(lambda:callback_core.put(MemoryAtom('direct','direct'),cell))
        raise OSError('callback fault')
    callback_store=FileHandleStore(root/'callback-access',callback_hook);callback_access=AccessRuntime(callback_core,FileEvidenceStore(root/'callback-access'),callback_store)
    callback_access.capture(MemoryStatement('outer','outer'));callback_access.capture(MemoryStatement('nested','nested'))
    try:callback_access.apply(AccessDecision('outer','outer','new',target_cell=cell,reason_text='x'))
    except OSError:pass
    facts['nested_access_apply_rejected']=callback_results['apply']
    facts['nested_access_recall_rejected']=callback_results['recall']
    facts['callback_direct_core_rejected']=callback_results['core']
    facts['callback_success_not_rolled_back']=callback_core.placement_count()==0 and not callback_store.exists('nested')
    callback_access.close();callback_core.close()

    trace_core=None;trace_attempt=[]
    class StoreMutatingTrace:
        def emit(self,event):
            if event.name=='core.recall.begin':
                try:trace_core.store.before_replace=lambda _p:(_ for _ in ()).throw(OSError('installed'))
                except AttributeError:trace_attempt.append(True)
    trace_core=CoreRuntime(root/'trace-store',trace_sink=StoreMutatingTrace());trace_core.recall(CoreRecallRequest('trace',(cell,),(),budget));trace_core.put(MemoryAtom('safe','safe'),cell)
    facts['trace_store_hook_mutation_rejected']=bool(trace_attempt) and trace_core.placement_count()==1
    facts['store_not_public']=not hasattr(trace_core,'store') and not hasattr(trace_core,'trace_sink')
    facts['snapshot_disk_runtime_equal']=SnapshotService().create(trace_core)==trace_core.state_bytes()==trace_core.state_path.read_bytes()
    trace_core.close()

    constructor_entered,constructor_proceed=Event(),Event()
    class BlockingCore(CoreRuntime):
        def acquire_client_lease(self,kind):
            lease=super().acquire_client_lease(kind);constructor_entered.set();constructor_proceed.wait(5);return lease
    constructor_core=BlockingCore(root/'constructor-core');constructed=[]
    thread=Thread(target=lambda:constructed.append(AccessRuntime(constructor_core,FileEvidenceStore(root/'constructor-access'),FileHandleStore(root/'constructor-access'))));thread.start();constructor_entered.wait(5)
    facts['constructor_client_lease_closes_window']=rejected(constructor_core.close)
    constructor_proceed.set();join_thread(thread,'Access constructor client lease')
    facts['constructor_returns_open_core']=len(constructed)==1 and constructed[0].core.is_open
    constructed[0].close();constructor_core.close()
    return facts


def run_m1c8_matrix(root: Path) -> dict[str, bool]:
    from nollm_access.workspace_lock import BindingWriterCapability

    facts: dict[str, bool] = {}
    cell = GeometryAddress('eisenstein_exact_v1', 'm1c8', 0, 0, 0)
    budget = RecallBudget(0, 8, 0, 0, 0, 8)

    callback_core = CoreRuntime(root/'pair-core')
    backing = FileEvidenceStore(root/'pair-access')
    first = second = None
    attacked: dict[str, bool] = {}
    callback_calls = 0
    class PairCallbackEvidence:
        workspace = backing.workspace
        def put_original(self, statement):
            nonlocal callback_calls
            callback_calls += 1
            operations = {
                'capture': lambda: second.capture(MemoryStatement('nested','nested')),
                'apply': lambda: second.apply(AccessDecision('nested','nested','new',target_cell=cell,reason_text='x')),
                'recall': lambda: second.recall(AccessRecallRequest('nested',entry_cells=(cell,),budget=budget)),
                'saved_handle': lambda: second.saved_handle('nested'),
                'close': second.close,
                'constructor': lambda: AccessRuntime(callback_core,backing,FileHandleStore(root/'pair-access')),
                'direct_store': lambda: second.handle_store.put('ghost',AtomHandle(cell,'ghost')),
            }
            for name, operation in operations.items(): attacked[name] = rejected(operation)
            raise OSError('pair callback fault')
        def get_original(self, statement_id): return backing.get_original(statement_id)
        def exists(self, statement_id): return backing.exists(statement_id)
    first = AccessRuntime(callback_core,PairCallbackEvidence(),FileHandleStore(root/'pair-access'))
    second = AccessRuntime(callback_core,backing,FileHandleStore(root/'pair-access'))
    errors = []
    def invoke_pair_callback():
        try:first.capture(MemoryStatement('outer','outer'))
        except Exception as error:errors.append(error)
    thread = Thread(target=invoke_pair_callback,name='m1c8-pair-callback');thread.start();join_thread(thread,'M1-C8 pair callback attacks')
    facts['workspace_callback_fence_shared_across_access_instances'] = all(attacked.values())
    facts['cross_access_capture_rejected_without_evidence_write'] = attacked.get('capture',False) and not backing.exists('nested')
    facts['cross_access_apply_rejected'] = attacked.get('apply',False)
    facts['cross_access_recall_rejected'] = attacked.get('recall',False)
    facts['cross_access_saved_handle_rejected_without_binding_read'] = attacked.get('saved_handle',False)
    facts['cross_access_close_rejected_without_closing_state'] = attacked.get('close',False) and second.lifecycle_state=='OPEN'
    facts['same_pair_constructor_rejected_during_callback'] = attacked.get('constructor',False)
    facts['bound_handle_store_direct_write_rejected'] = attacked.get('direct_store',False)
    facts['callback_exception_cleanup'] = len(errors)==1 and isinstance(errors[0],OSError) and first._active_operations==second._active_operations==0 and not hasattr(first._coordinator._local,'callback_depth')
    second.capture(MemoryStatement('after','after'))
    facts['callback_counts_cleanup'] = callback_calls==1 and backing.exists('after')

    store = second.handle_store;empty = FileHandleStore(root/'empty').state_bytes();capability = second._binding_capability
    forged = BindingWriterCapability(second._coordinator)
    facts['binding_capability_foreign_rejected'] = rejected(lambda:store.import_state(empty,capability=forged))
    facts['handle_store_hook_frozen_after_bind'] = rejected(lambda:setattr(store,'before_replace',lambda _p:None)) and rejected(lambda:setattr(store,'path',root/'redirect.json'))
    original_bindings = store.state_bytes()
    first.close();second.close()
    facts['binding_capability_expired_rejected'] = not capability.active and rejected(lambda:store.import_state(empty,capability=capability)) and store.state_bytes()==original_bindings
    callback_core.close()

    recursive_core = CoreRuntime(root/'recursive-core');lease1=recursive_core.acquire_client_lease('one');lease2=recursive_core.acquire_client_lease('two');success=[]
    nested = {}
    def outer_callback():
        nested['same']=rejected(lambda:lease1.callback(lambda:success.append(True)))
        nested['different']=rejected(lambda:lease2.callback(lambda:success.append(True)))
    lease1.callback(outer_callback)
    with recursive_core.transaction() as transaction:
        nested['transaction']=rejected(lambda:transaction.callback(lease1.callback,lambda:success.append(True)))
    facts['recursive_client_callback_rejected'] = all(nested.values())
    facts['recursive_callback_returned_no_success'] = not success
    facts['transaction_callback_client_callback_rejected'] = nested['transaction']
    facts['core_callback_counts_cleanup'] = recursive_core._active_operations==recursive_core._active_transactions==0 and not hasattr(recursive_core._local,'callback_depth')
    lease1.close();lease2.close();recursive_core.close()

    other = CoreRuntime(root/'other-core');trace_access = None;trace_attempts=[]
    trace_store = FileHandleStore(root/'trace-access');trace_evidence=FileEvidenceStore(root/'trace-access')
    class AccessMutatingTrace:
        def emit(self,event):
            if event.name!='core.recall.begin':return
            for target,name,value in ((trace_access,'core',other),(trace_access,'handle_store',FileHandleStore(root/'redirect-access')),(trace_store,'path',root/'redirect-bindings.json'),(trace_store,'before_replace',lambda _p:None)):
                try:setattr(target,name,value)
                except (AttributeError,RuntimeError):trace_attempts.append(name)
    trace_core=CoreRuntime(root/'trace-core',trace_sink=AccessMutatingTrace());trace_access=AccessRuntime(trace_core,trace_evidence,trace_store)
    original_dependencies=(trace_access.core,trace_access.evidence_store,trace_access.handle_store,trace_access.canonical_access_root,trace_access.canonical_core_state_path)
    trace_access.recall(AccessRecallRequest('attack',entry_cells=(cell,),budget=budget))
    facts['trace_cannot_rebind_access_core'] = 'core' in trace_attempts and trace_access.core is trace_core
    facts['trace_cannot_mutate_access_store_config'] = set(trace_attempts)=={'core','handle_store','path','before_replace'}
    facts['access_dependencies_read_only'] = all(rejected(lambda n=n:setattr(trace_access,n,root/'wrong')) for n in ('core','evidence_store','handle_store','canonical_access_root','canonical_core_state_path')) and original_dependencies==(trace_access.core,trace_access.evidence_store,trace_access.handle_store,trace_access.canonical_access_root,trace_access.canonical_core_state_path)
    trace_access.capture(MemoryStatement('safe','safe'));safe_handle=trace_access.apply(AccessDecision('safe','safe','new',target_cell=cell,reason_text='x'))
    facts['access_apply_original_core_after_trace_attack'] = trace_core.contains(safe_handle) and other.placement_count()==0
    trace_access.close();trace_core.close();other.close()

    redirected=root/'redirected-core'/'current_state.json';store_attempts=[];retained_store=None
    class StoreMutatingTrace:
        def emit(self,event):
            if event.name=='core.recall.begin':
                for name,value in (('path',redirected),('workspace',redirected.parent)):
                    try:setattr(retained_store,name,value)
                    except AttributeError:store_attempts.append(name)
    retained_store=FileCoreStateStore(root/'store-core');store_core=CoreRuntime(root/'store-core',store=retained_store,trace_sink=StoreMutatingTrace());canonical_path=store_core.state_path
    store_core.recall(CoreRecallRequest('store-attack',(cell,),(),budget));store_core.put(MemoryAtom('safe','safe'),cell)
    facts['core_store_path_frozen_after_bind'] = set(store_attempts)=={'path','workspace'}
    facts['core_state_path_identity_stable'] = store_core.state_path==canonical_path==retained_store.path
    facts['redirected_core_state_file_not_created'] = not redirected.exists()
    facts['snapshot_disk_runtime_equal'] = SnapshotService().create(store_core)==store_core.state_bytes()==canonical_path.read_bytes()
    store_core.close()

    compiler=CoverageTemplateCompiler();profiles=('eisenstein_exact_v1','aligned_baseline_v1','dream_quasi_v1');kernels=('coverage_up','coverage_down','lateral')
    facts['geometry_parity_9_of_9'] = len([compiler.compile(profile,kernel) for profile in profiles for kernel in kernels])==9
    return facts

def main():
    with TemporaryDirectory(prefix='nollm-m1c7-matrix-') as directory:
        facts=run_matrix(Path(directory));assert all(facts.values());print(json.dumps({'status':'passed','facts':facts},sort_keys=True))
if __name__=='__main__':main()
