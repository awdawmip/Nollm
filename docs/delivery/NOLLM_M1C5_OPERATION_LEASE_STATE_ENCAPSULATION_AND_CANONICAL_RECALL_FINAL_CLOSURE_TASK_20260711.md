# Nollm M1-C5：操作租约、状态封装与 Canonical Recall 最终闭合任务书

**日期**：2026-07-11
**阶段编号**：M1-C5 — Operation Lease / State Encapsulation / Canonical Recall Final Closure
**状态**：M1-C4 Bundle 系统审核未通过后的唯一闭合任务
**输入 Bundle**：`nollm_m1c4_single_owner_kernel_public_contract_final_closure_20260711_2142eba6.bundle`
**输入 Bundle SHA-256**：`cbce4fb42bd3118deb1083d814d6265f9156a73e38c5987fb746ffe66a1eb9b2`
**输入 HEAD**：`2142eba63c0e65c5fce0a097affdf3733a2a81ed`
**输入分支**：`codex/m1c4-single-owner-kernel-public-contract-final-closure`
**建议工作分支**：`codex/m1c5-operation-lease-state-encapsulation-canonical-recall`
**主环境**：Windows 10/11 + PowerShell
**执行方式**：大跨度任务 + 内部 Gate + 普通问题就地修复 + 最终单一完整历史 Git bundle

---

# 0. 本任务定位

M1-C4 的正确成果全部保留，不得回退重做：

```text
Bundle / Git history = PASS
HEAD = 2142eba63c0e65c5fce0a097affdf3733a2a81ed
working tree = clean
Manifest = 1420 / 1420
production violations = 0
production cycles = []
nollm-core = 34 passed
nollm-snapshot = 5 passed
nollm-trace = 1 passed
nollm-access = 32 passed
M0 regression = 18 passed
architecture / forbidden / hygiene = 8 passed
geometry parity = 9 / 9 passed
M1 E2E = passed
GRF external Linux audit = 109 passed, 1 skipped
zstandard-dependent historical tests unavailable = 2
```

已实质完成：

```text
1. KernelEntry 已拒绝未知 kernel_type、零/超 Q16 weight、重复或乱序 entry flags；
2. CoverageTemplate 已拒绝重复几何目标和负 normalization residual；
3. CoreRuntime 在构造阶段对 canonical state path 声明进程内 owner；
4. 第二个 live CoreRuntime 对同一路径的普通构造会被拒绝；
5. owner registry 使用 weak reference，失败构造会释放 lease；
6. CoreRuntime 已有 close/context manager 基础；
7. Access 已建立一个活动 Core path 对一个活动 Access root 的 pair registry；
8. 相同 Core/Access pair 的多个 AccessRuntime 可共享 RLock；
9. AccessDecision 和 Core command 的大部分直接类型检查已进入活动包；
10. Recall 已在同一 CoreRuntime 的普通调用中持有 Core RLock；
11. 九模板、Canonical Evidence、one-current HandleBinding、Snapshot、Trace 和零边界结果未回退；
12. 未启动 OpenClaw Live、真实模型、Corpus、PB 长跑或远端拆仓。
```

但当前仍不得输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

原因不是旧问题重复，而是 M1-C4 的 owner/close/public-contract 实现尚未覆盖**活动操作生命周期、直接状态旁路和完整 canonical 输入**。

本任务必须一次性闭合以下问题：

```text
B1. CoreRuntime.close() 不与活动 mutation/Recall 串行；可在旧 mutation 阻塞时释放 owner，允许新 Core 写入，随后旧 mutation stale-overwrite 新状态。
B2. AccessRuntime.close() 不与活动 Access transaction 串行；可在旧事务阻塞时释放 pair，换绑另一 Access root，随后旧回滚删除新 root 已返回成功的写入。
B3. Access 跨 Store 事务只持有 Access lock；同一 CoreRuntime 的直接 Core mutation 可在 Access snapshot/action/rollback 之间成功返回，随后被失败回滚删除。
B4. begin_consistent_read() 使用 RLock，同线程可在 token 活动期间重新进入 mutation；Snapshot “冻结”并非真正只读。
B5. CoreRuntime 的公开 `store`、`cells` 和导出的可写 FileCoreStateStore/CellStore 可绕过 owner、锁和 canonical current-state API，制造 disk/runtime 分叉。
B6. `CoreRuntime.occupied_cells()` 当前调用不存在的 `CellStore._require_open()`，活动公共 API 直接失败。
B7. AccessRecallRequest 可接受重复 entry、unknown kernel 和非 canonical kernel 顺序，并在 `to_core_request()` 中静默去重；CoreRecallRequest 同样接受无语义的多种 kernel 顺序。
B8. CompilerMetadata 可接受非字符串 flags；dream_quasi approximation residual 没有 canonical 精确值或明确上界。
B9. AccessRuntime 可绑定已关闭的 CoreRuntime；Core/Access 的 closed/closing/active-operation 状态合同不完整。
B10. 可重入 TraceSink 能在 `core.batch.begin` 中执行内层 mutation，内层调用返回成功后又被外层 batch 覆盖，Trace 影响 Core correctness。
B11. M1-C4 E2E 缺少任务书要求的 17 项关键事实；Starting State、Validation Report 和 Boundary Closure 各仅 3 行，无法作为可复现验收材料。
```

M1-C5 是 M1 的最终运行时一致性闭合。完成前不得进入 M2、M3、真实模型或 OpenClaw Live。

---

# 1. 开工前最高约束

Codex 开始前必须依次读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/project/NOLLM_PROJECT_BOOK_V3_0_MODULAR_GEOMETRY_INFRASTRUCTURE_M1_20260711.md
3. 根目录 AGENTS.md
4. M1 主任务书
5. M1-C1 任务书
6. M1-C2 任务书
7. M1-C3 任务书
8. M1-C4 任务书
9. 本 M1-C5 任务书
10. Core / Access / Snapshot / Trace 模块章程
```

必须更新并遵守根目录 `AGENTS.md`，至少加入：

```text
- Current stage is M1-C5 operation-lease, state-encapsulation, and canonical-recall final closure.
- Preserve all accepted M1-C4 kernel, owner-registry, Access pair, typed-command, Snapshot, Trace, boundary, and package results.
- Core close/release is an operation serialized under the same runtime lifecycle coordinator as mutation, Recall, Snapshot, restore, and state reads.
- Access close/release is serialized under the same pair coordinator as capture, apply, recall, saved_handle, rollback, and cross-store reads.
- An Access transaction must hold a Core-owned transaction/read-write lease across Core snapshot, Core action, Binding action, and rollback; direct Core mutation cannot interleave.
- A consistent-read token is read-only even for same-thread RLock reentry; mutation and restore are rejected while the token is active.
- Trace callbacks cannot reenter Core mutation and cannot cause a successful nested operation to be lost.
- Core persistent state is writable only through CoreRuntime ownership; public Store or Cell views cannot mutate live Core state or bypass the owner lease.
- Core/Access Recall request tuples are canonical, unique, directly validated, and never silently deduplicated.
- CompilerMetadata flags are exact canonical strings and dream_quasi residual has one canonical contract.
- Do not proceed to M2, OpenClaw Live, model calls, corpus execution, PB scale, or remote GitHub work.
```

## Gate 0 PASS

```text
第一性原理和模块所有权不变；
未恢复 relation index、Python semantic placement、graph/vector/embedding；
M1-C4 正确成果全部保留；
任务范围没有扩展到 M2/M3。
```

---

# 2. 保全输入现场与外部复现

从输入 Bundle 新克隆，不得 reset、clean、改写历史或回退重做。

生成：

```text
docs/project/M1C5_STARTING_STATE.md
```

必须记录：

```text
input bundle filename / SHA-256
input branch / HEAD / status / log
M1-C4 package counts
M0 / architecture / GRF results
boundary report
zstandard 环境情况
下列外部复现的实际命令、状态和结果
```

## 2.1 occupied_cells 活动 API 失败

当前：

```python
core.occupied_cells()
```

实际：

```text
AttributeError: 'CellStore' object has no attribute '_require_open'
```

## 2.2 Snapshot token 同线程仍可 mutation

当前：

```text
token = core.begin_consistent_read()
core.put(...)  # 同线程 RLock 重入，成功
core.export_state(token) 包含新 mutation
```

这不是真正的 consistent read。

## 2.3 Access 失败回滚删除直接 Core 成功写入

确定性复现：

```text
A Access transaction：
  core_before = empty
  Core.put(A) 成功
  Binding 写入阻塞并最终失败

同一 CoreRuntime 的直接 Core 调用：
  Core.put(B) 成功并向调用方返回 Handle B

A rollback：
  import core_before

最终：
  B 已返回成功，但 B 不再存在。
```

## 2.4 Core close race 导致旧 owner stale-overwrite 新 owner

确定性复现：

```text
old Core mutation 在 FileCoreStateStore.before_replace 中阻塞；
另一线程调用 old.close()，当前立即释放 owner；
new CoreRuntime 同一路径构造成功并写入 NEW；
旧 mutation 恢复并 os.replace OLD；
new Core memory 仍为 NEW，disk 已变为 OLD；
reopen 只有 OLD，NEW 消失。
```

## 2.5 Access close race 重新制造跨 root rollback

确定性复现：

```text
Access root A 的 transaction 在 Binding replace 中阻塞；
另一线程调用 accessA.close()，当前立即释放 pair；
Access root B 对同一 Core 构造成功；
B 写入成功并返回 Handle B；
A 失败后按旧 snapshot rollback；
最终 B Core atom 消失，但 B Binding 仍存在。
```

## 2.6 公开 Store 绕过 Runtime

当前：

```text
core.store.write_document(valid_other_document)
```

结果：

```text
disk bytes != core.state_bytes()
runtime placement_count 仍为旧值
```

Core owner 没有覆盖实际文件写入口。

## 2.7 公开 CellStore 绕过 closed/read contract

当前：

```text
cells = core.cells
core.close()
cells.get(handle) 仍返回 atom
```

并且 `core.cells._cells` 与 live `core._cells` 共享可变对象。

## 2.8 Access Recall 非 canonical 输入

当前以下均被直接构造接受：

```text
重复 entry_cells；
unknown allowed_kernels；
("lateral", "bridge") 与 ("bridge", "lateral") 两种无语义差异表示。
```

`to_core_request()` 再静默 set/sort，导致 direct contract 与实际执行 contract 不一致。

## 2.9 Kernel metadata 不完整

当前：

```text
CompilerMetadata(..., flags=(1,)) 被接受；
dream_quasi CoverageTemplate 的 approximation_residual_q16=10**30 被接受。
```

## 2.10 Trace reentrant mutation 丢失

自定义 TraceSink 在 `core.batch.begin` 调用内层 `core.put(INNER)`：

```text
INNER 调用返回成功；
外层 batch 随后提交旧副本；
INNER 消失。
```

## Gate 1 PASS

```text
输入事实、缺陷和环境限制全部保全；
没有用修复后的测试覆盖初始复现；
没有把正确性缺陷降级为文档 limitation。
```

---

# 3. Gate A：Core Operation Lease 与安全 close 生命周期

核心目标：

```text
owner lease 的释放必须晚于所有活动操作结束；
操作开始后不能被 close 变成“无 owner 的旧写者”；
close 后不能再有旧操作继续执行或提交。
```

## 3.1 建立统一 Runtime 生命周期状态

在 `nollm-core` 内建立 stdlib-only 生命周期协调，至少表达：

```text
OPEN
CLOSING
CLOSED
active_operations
active_consistent_read
```

要求：

```text
1. 所有 public Core read/mutation/recall/snapshot/restore 在进入时取得 operation lease；
2. lease 在整个操作完成后释放，不能只在 `_require_open()` 时检查一次；
3. close 与 operation lease 使用同一 lock/condition；
4. close 不得在 active operation 尚未结束时释放 workspace owner；
5. 可选择：close 等待活动操作结束，或明确拒绝并要求调用方重试；
6. 不允许 close 先成功返回、旧 operation 后继续写文件；
7. CLOSING 后不接受新 operation；
8. close 幂等；
9. owner release 只发生在进入 CLOSED 后；
10. constructor failure 继续释放 owner。
```

Windows-first 环境中不得依赖 POSIX-only primitive。

## 3.2 Core transaction/read-write lease

Access 必须能通过 Core public port 持有一个**跨多次 Core 调用**的运行时事务租约，例如：

```text
with core.transaction_lease():
    core_before = core.state_bytes()
    core_action()
    binding_action()
    rollback_if_needed()
```

要求：

```text
Core transaction lease 使用 Core 自己的 RLock/operation lifecycle；
Access 只依赖 Core public context/port，不访问 Core private lock；
租约期间同一 CoreRuntime 的其他线程 direct mutation/read 不得插入；
同线程内部的 Core calls 可安全重入；
租约异常退出后 lock 和 active operation 必须释放；
close 不得在租约活动时释放 owner。
```

这不是数据库事务、Event Sourcing 或跨进程锁。

## 3.3 Consistent-read token 必须真正只读

在 token 活动期间：

```text
允许：export_state / end_consistent_read；
拒绝：put/remove/replace/move/bridge_add/bridge_remove/apply_batch/import_state；
同线程 RLock 重入也必须拒绝；
Trace callback 重入 mutation 也必须拒绝；
close 继续明确拒绝或等待，不能释放 owner。
```

可通过 runtime operation mode，而不是只靠 RLock 实现。

## 3.4 Core Recall 与 close/mutation

要求：

```text
Recall 从开始到结果构造持有同一 consistent operation lease；
close 不得在 Recall 中途释放 owner；
直接 mutation 不得插入 Recall；
Recall 完成后 close 才能进入 CLOSED。
```

## Gate A 测试

至少新增：

```text
test_close_cannot_release_owner_during_blocked_mutation
test_old_mutation_cannot_stale_overwrite_reopened_owner
test_close_and_reopen_preserve_disk_runtime_identity
test_operation_started_before_close_cannot_commit_after_close
test_consistent_read_rejects_same_thread_mutation
test_consistent_read_rejects_trace_reentrant_mutation
test_core_transaction_lease_serializes_direct_mutation
test_core_recall_and_close_are_lifecycle_serialized
test_failed_or_cancelled_operation_releases_lease
test_close_is_idempotent_and_constructor_failure_still_releases_owner
```

## Gate A PASS

```text
同一进程同一 workspace 在任意时刻只有一个真正可提交的 mutable owner；
close 不会产生无 owner 的活动旧写者；
Snapshot token 真正只读；
Core Recall、mutation、restore 和 close 具有明确一致的生命周期语义。
```

---

# 4. Gate B：Access 完整事务租约与安全 close

## 4.1 Access operation lease

AccessRuntime 必须为以下 public 操作建立统一 active-operation 生命周期：

```text
capture
apply
recall
saved_handle
close
```

要求：

```text
1. `_require_open()` 不能只在 acquire transaction lock 前检查一次；
2. 操作从开始到结束持有 Access operation lease；
3. close 与 operation lease 使用同一 coordinator；
4. close 不得在活动 transaction/recall/capture 中途释放 pair；
5. CLOSING 后不接受新调用；
6. close 后才允许换绑另一个 Access root；
7. AccessRuntime 构造必须立即拒绝 CLOSED/CLOSING CoreRuntime；
8. 多个相同 pair AccessRuntime 的引用计数和 close 继续正确。
```

## 4.2 Access `_atomic()` 必须同时持有 Core transaction lease

完整顺序必须在：

```text
Access pair lock
+
Core transaction lease
```

共同保护下执行：

```text
Core before snapshot
Binding before snapshot
Core action
Binding action
Core rollback
Binding rollback
```

结果：

```text
其他 Access transaction 不可插入；
同一 CoreRuntime 的 direct Core mutation 不可插入；
Core close 不可插入；
Access close 不可插入；
已返回成功的 direct Core 或 Access 写入不能被旧 rollback 删除。
```

## 4.3 Access close race 必须消失

明确复现并证明：

```text
root A transaction 阻塞时，accessA.close() 不会释放 pair；
root B 构造在 A transaction 完成和 A close 真正结束前被拒绝或阻塞；
A rollback 完成后才可安全换绑；
B 一旦返回成功，不会被 A 删除。
```

## Gate B 测试

```text
test_access_close_waits_for_or_rejects_active_transaction
test_access_close_does_not_release_pair_during_binding_failure
test_access_close_race_cannot_recreate_cross_root_rollback
test_access_atomic_lease_blocks_direct_core_mutation
test_failed_access_transaction_cannot_erase_direct_core_success
test_access_runtime_rejects_closed_or_closing_core
test_same_pair_multiple_access_runtime_close_reference_count
test_access_rebind_only_after_last_active_operation_and_lease_end
test_concurrent_recall_saved_handle_capture_and_apply_observe_complete_states
```

继续保留全部 action failure matrix 和 fatal rollback path。

## Gate B PASS

```text
Access pair 生命周期与活动操作一致；
任何成功返回的 Core/Access operation 不会被另一失败事务回滚；
同一 Core 不会因 Access close race 被临时分裂到两个 roots；
Access 只能绑定 live OPEN Core。
```

---

# 5. Gate C：Current-State 写入口封装与只读 Cell 视图

## 5.1 Core Store 不得成为旁路写入口

当前 `CoreRuntime.store` 暴露已绑定 validator 的可写 `FileCoreStateStore`，可直接修改文件而不更新运行时。

必须改为以下之一：

```text
方案 A（优先）：
  CoreRuntime 仅公开 read-only state_path / workspace_identity；
  FileCoreStateStore 作为内部实现或测试注入类型；
  已绑定 Runtime 的 write/import 需要 Runtime 私有 capability token。

方案 B：
  提供明确 Store owner lease；
  Store 写方法只有持有 CoreRuntime 私有 owner token 才能执行；
  外部直接 write_document/write_bytes 拒绝。
```

要求：

```text
外部不能通过 `core.store.write_*` 修改 live current state；
外部不能替换已绑定 semantic validator；
Core close 后旧 Store 不能继续写同一路径；
测试注入 before_replace 仍可通过受控构造完成；
Access 只读取 Core public `state_path` / workspace identity，不依赖可写 store 对象。
```

不得引入数据库或权限系统。

## 5.2 CellStore 必须是只读、无 live mutable alias 的公开视图

当前：

```text
CoreRuntime.cells 是公开对象；
CellStore._cells 与 CoreRuntime._cells 共享可变 dict；
held CellStore 在 Core close 后仍可读取；
occupied_cells() 误调用不存在方法。
```

必须：

```text
1. 修复 occupied_cells 活动 API；
2. CoreRuntime 公开查询统一经过 Runtime operation lease；
3. `core.cells` 如保留，只能返回不可变 snapshot/read-only view，不得共享可变 backing dict；
4. 如不需要公开 CellStore，移出活动 `__all__`，保留薄兼容或内部类型；
5. held view 不得成为绕过 closed Runtime 的 live state 入口；
6. 外部修改任何 view/private mapping 均不能改变 CoreRuntime current state。
```

## 5.3 状态真值不变量

对所有 public supported path 继续证明：

```text
store bytes == runtime.state_bytes() == SnapshotService.create(runtime)
```

并新增旁路负例。

## Gate C 测试

```text
test_occupied_cells_public_api_works_and_rejects_closed_runtime
test_public_cell_view_cannot_mutate_live_core_state
test_held_cell_view_does_not_bypass_closed_runtime
test_public_store_cannot_write_around_runtime_owner
test_semantic_validator_cannot_be_rebound_externally
test_closed_runtime_store_cannot_stale_write_reopened_owner
test_all_supported_writes_preserve_disk_runtime_snapshot_equality
```

## Gate C PASS

```text
CoreRuntime 是 current-state 唯一可写所有者；
FileCoreStateStore 和 CellStore 不再形成旁路；
occupied_cells 等活动公共查询可用；
accepted state 始终 disk == runtime == snapshot。
```

---

# 6. Gate D：Canonical Kernel Metadata 与 Recall 公共合同

## 6.1 CompilerMetadata 严格 flags

`CompilerMetadata.__post_init__` 必须要求：

```text
flags exact tuple[str, ...]；
每个 flag non-empty exact str；
strict sorted + unique；
bool/int/object 不得通过；
```

## 6.2 dream_quasi approximation residual 唯一合同

不得只要求 `> 0`。

基于当前权威 compiler/oracle，明确一种唯一合同，例如：

```text
dream_quasi_v1 approximation_residual_q16 == Q16_ONE // 16
其他 active profiles == 0
```

如权威旧 oracle 使用其他精确值，以 oracle 为准，但必须：

```text
有明确常量；
进入 registry identity；
直接构造与 compiler 产物一致；
拒绝任意巨大 residual。
```

九模板 parity 必须继续 9/9。

## 6.3 CoreRecallRequest canonicality

Recall 中 entry/kernel 顺序当前不影响语义，因此 direct contract 必须只有一个表示。

要求：

```text
entry_cells exact tuple[GeometryAddress,...]；
entry_cells 按 stable_key 严格排序、唯一，或在 frozen constructor 中确定性 canonicalize；
allowed_kernels exact tuple[str,...]；
allowed_kernels 使用明确 canonical order、唯一；
unknown kernel 直接拒绝；
budget exact RecallBudget；
不得在 resolver 中再静默修复 direct request。
```

优先采用“拒绝非 canonical 输入”，保持文件/Trace/测试可审计。

## 6.4 AccessRecallRequest canonicality

必须在直接构造阶段完成：

```text
entry_cells stable-key sorted + unique；
entry_handles 按 (address.stable_key, local_atom_id) sorted + unique；
allowed_kernels canonical sorted + unique；
unknown kernel 直接拒绝；
entry_cells 与 entry_handles 投影出的重复入口按明确合同拒绝或 canonicalize，不能在 to_core_request 静默 set；
list、bool、错误对象全部直接拒绝。
```

`to_core_request()` 只能做显式映射，不得承担输入清洗。

## 6.5 Public contract zero-write matrix

继续检查：

```text
AccessDecision
CoreRecallRequest
AccessRecallRequest
RecallBudget
Put/Remove/Replace/Move/Bridge commands
```

错误 direct object 必须在 Core/Evidence/Binding 任何状态变更前拒绝。

## Gate D 测试

```text
test_compiler_metadata_rejects_non_string_empty_unsorted_duplicate_flags
test_dream_quasi_residual_requires_exact_canonical_value
test_all_nine_templates_keep_full_oracle_parity
test_core_recall_request_rejects_noncanonical_entry_order
test_core_recall_request_rejects_noncanonical_kernel_order_and_duplicates
test_access_recall_request_rejects_duplicate_cells_handles_and_unknown_kernel
test_access_recall_request_does_not_silently_deduplicate_in_to_core_request
test_invalid_recall_contract_is_zero_write_and_zero_trace_commit
```

## Gate D PASS

```text
Kernel metadata 只有唯一 canonical 表示；
Recall direct contract 与实际执行合同一致；
不存在构造接受、映射时静默修复的两层语义；
M2 可依赖稳定 public request objects。
```

---

# 7. Gate E：Trace reentrancy、Snapshot 与行为回归

## 7.1 Trace Sink 不得重入修改 Core

Trace 是可选观察端口，不得导致：

```text
内层 Core mutation 返回成功；
随后被外层 operation 覆盖；
Trace 改变最终 current state。
```

可采用：

```text
Runtime operation reentrancy guard；
在 Trace callback 期间拒绝同 runtime mutation；
或将稳定事件在 commit 后安全发出，同时保证顺序和失败隔离。
```

要求：

```text
FailingTraceSink 继续不影响结果；
ReentrantTraceSink 的 mutation 明确拒绝；
外层 operation 结果与 NullTraceSink 完全一致；
Trace 不持有可写 Core capability。
```

## 7.2 Snapshot 生命周期

重新证明：

```text
create 期间 mutation（其他线程与同线程重入）均不能插入；
close 不会释放 frozen Core owner；
restore 持有完整 Core operation lease；
clone target 为独立 OPEN workspace；
closed/closing source 或 target 拒绝；
Snapshot 后 disk/runtime/snapshot byte equality。
```

## 7.3 发行与边界

继续证明：

```text
production violations = 0；
production cycles = []；
Core stdlib-only；
Access 只依赖 Core public port；
Bare/Minimal 不引用 Legacy；
旧 GRF 仅作 Lab parity oracle；
无 relation index、hash placement、graph/vector/embedding 主路径。
```

## Gate E 测试

```text
test_reentrant_trace_mutation_is_rejected_without_state_change
test_null_failing_and_reentrant_trace_have_same_outer_result
test_snapshot_blocks_same_thread_and_other_thread_mutation
test_close_cannot_release_snapshot_owner
test_restore_is_one_complete_operation_lease
test_closed_or_closing_snapshot_port_rejected
```

## Gate E PASS

```text
Trace、Snapshot、close、mutation 和 Access transaction 使用一致的运行时生命周期；
可选观察端口不改变 Core correctness；
模块边界和禁止路线未回退。
```

---

# 8. Gate F：真实升级 E2E、报告与系统性对抗矩阵

## 8.1 M1-C5 E2E 必须重写

当前 M1 E2E 仍缺少 M1-C4 任务要求的 17 项事实。不得继续在旧输出上只增加少量布尔值。

E2E 至少输出并由实际操作生成：

```text
kernel_entry_unknown_type_rejected
kernel_entry_noncanonical_flags_rejected
duplicate_geometric_target_rejected
negative_normalization_residual_rejected
compiler_nonstring_flags_rejected
dream_quasi_residual_canonical
registry_identity_stable
mixed_phase_round_trip
anchor_order_rejected
lateral_ring_one_real_recall
lateral_unregistered_ring_rejected
second_core_owner_rejected_at_constructor
direct_stale_overwrite_prevented
core_close_during_operation_safe
core_close_reopen_succeeds
consistent_read_same_thread_mutation_rejected
same_core_different_access_root_rejected
access_close_race_safe
cross_root_rollback_unconstructable
direct_core_success_survives_failed_access_transaction
concurrent_recall_consistent
access_decision_wrong_types_rejected
core_recall_noncanonical_rejected
access_recall_noncanonical_rejected
reuse_corrupt_evidence_rejected
public_store_bypass_rejected
public_cell_view_read_only
occupied_cells_works
reentrant_trace_mutation_rejected
snapshot_after_reopen_equal
trace_parity
boundary_zero
```

每项必须由实际代码路径产生，不能硬编码 `True`。

## 8.2 系统性公共 API 对抗矩阵

在最终 Gate 前新增一个无模型、无网络、短运行的 adversarial matrix，覆盖：

```text
Core public method × OPEN/CLOSING/CLOSED；
Core method × active mutation/Recall/Snapshot/transaction lease；
Access method × OPEN/CLOSING/CLOSED；
Access method × active transaction/recall/close；
Store/Cell view bypass；
Trace reentrancy；
Recall tuple ordering/duplicates/unknown values；
constructor failure / rollback failure / close race；
```

输出结构化 JSON，并纳入 Validation Report。

不得用随机不稳定测试；使用 Event/Barrier 构造确定性并发。

## 8.3 文档必须真实完整

生成/更新：

```text
docs/project/M1C5_STARTING_STATE.md
docs/validation/M1C5_OPERATION_LEASE_STATE_ENCAPSULATION_REPORT.md
docs/architecture/module-ownership/M1C5_BOUNDARY_CLOSURE.md
docs/architecture/module-ownership/M1C5_BOUNDARY_REPORT.json
```

报告不得再只有 3 行。至少包含：

```text
输入 Bundle / branch / HEAD / SHA；
外部 Linux 复现；
Windows 实际执行；
Gate A-F 逐项事实；
关键并发时序与修复后结果；
Core/Access lifecycle state machine；
Core transaction lease public contract；
Store/Cell encapsulation；
Recall canonical contract；
Snapshot/Trace；
package counts；
M0/architecture/GRF；
zstandard 精确限制；
同进程保证与跨进程/crash recovery 非目标；
M2 前置条件是否满足。
```

## Gate F PASS

```text
代码、测试、E2E、结构化矩阵和报告一致；
没有用 unit test pass 掩盖 close race、direct Core bypass 或 Store bypass；
所有 M1 接受事实可在新克隆中复现。
```

---

# 9. 独立 Package Gates

## Core

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/packages/nollm-core/src"
python -m pytest -q packages/nollm-core/tests
```

新增或扩展：

```text
test_core_operation_lease_and_close_race.py
test_core_transaction_lease.py
test_consistent_read_reentrancy.py
test_core_state_encapsulation.py
test_cell_store_read_only_view.py
test_canonical_recall_contract.py
test_kernel_metadata_complete_contract.py
test_trace_reentrancy_isolation.py
```

## Snapshot

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src"
) -join ";"
python -m pytest -q packages/nollm-snapshot/tests
```

新增：

```text
same-thread mutation rejection；
close during snapshot；
restore operation lease；
closed/closing port rejection；
```

## Trace

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-trace/src"
) -join ";"
python -m pytest -q packages/nollm-trace/tests
```

新增 reentrant sink isolation。

## Access

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-access/src"
) -join ";"
python -m pytest -q packages/nollm-access/tests
```

新增：

```text
test_access_close_operation_lease.py
test_access_vs_direct_core_transaction.py
test_access_rejects_closed_core.py
test_access_recall_canonical_contract.py
test_access_close_race_cross_root.py
```

新包测试继续不得依赖：

```text
reference/python
OpenClaw
experiments
Legacy GRF private implementation
```

---

# 10. Final Gate

统一环境：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-trace/src",
  "$PWD/packages/nollm-access/src",
  "$PWD/packages/nollm-history/src",
  "$PWD/packages/nollm-audit/src",
  "$PWD/reference/python"
) -join ";"
```

执行：

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py --report docs/architecture/module-ownership/M1C5_BOUNDARY_REPORT.json

python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests
python -m pytest -q packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests

python -m pytest -q reference/python/tests/m0
python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py

python -m pytest -q reference/python/tests/grf
python lab/nollm-lab/m1/run_geometry_parity.py
python lab/nollm-lab/m1/run_m1_minimal_e2e.py
python lab/nollm-lab/m1/run_m1_public_api_adversarial_matrix.py

python -m compileall -q `
  packages/nollm-core/src `
  packages/nollm-snapshot/src `
  packages/nollm-trace/src `
  packages/nollm-access/src

git diff --check
git status --short
```

如环境仅缺 `zstandard`，允许精确排除：

```text
reference/python/tests/grf/test_grf7r2_evidence_pack.py
reference/python/tests/grf/test_grf7r3_compact_evidence.py
```

并单独报告：

```text
109 passed, 1 skipped；
GRF7R3 compact capsule 可作为抽样历史审计材料；
不要求上传 1GB 以上 GRF7R2 原包；
不得扩大排除范围。
```

---

# 11. M1-C5 接受条件

只有全部满足，才可输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

条件：

```text
1. M1-C4 的 KernelEntry、duplicate-target、owner registry、Access pair、typed commands、九模板、Evidence、Binding、Snapshot、Trace 和零边界成果全部保留；
2. Core public operations 全部使用统一 operation lease；
3. close 不会在活动 mutation/Recall/Snapshot/restore/transaction 中释放 owner；
4. 旧 operation 不会在 close/reopen 后 stale-overwrite 新 owner；
5. Access public operations 全部使用统一 operation lease；
6. Access close 不会在活动 transaction/recall/capture 中释放 pair；
7. Access `_atomic()` 全程持有 Core transaction lease；
8. 失败 Access rollback 不会删除同 CoreRuntime 已返回成功的 direct Core 写入；
9. 同线程 mutation 在 consistent-read token 活动时拒绝；
10. Trace callback reentrant mutation 拒绝且不改变外层结果；
11. AccessRuntime 拒绝 CLOSED/CLOSING Core；
12. public Store 不能绕过 CoreRuntime 修改 live current-state 文件；
13. semantic validator 不能被外部重绑后旁路写入；
14. Cell public view 只读、无 live mutable alias；
15. occupied_cells 活动 API 正常并服从 closed contract；
16. accepted state 始终 disk == runtime == snapshot；
17. CompilerMetadata flags 为 exact canonical strings；
18. dream_quasi approximation residual 使用唯一明确合同；
19. 九模板 parity 仍为 9/9；
20. CoreRecallRequest entry/kernel tuples canonical、unique、unknown 拒绝；
21. AccessRecallRequest entry cells/handles/kernels canonical、unique、unknown 拒绝；
22. to_core_request 不再静默去重或修复非法 direct input；
23. AccessDecision/Recall/Commands 错误对象继续零写拒绝；
24. Core/Access close race、direct Core interleave、Store bypass 和 Trace reentrancy 均有确定性负例测试；
25. Snapshot create/restore/clone 与 operation lifecycle 一致；
26. FailingTraceSink 与 ReentrantTraceSink 均不改变外层正确结果；
27. M1-C5 E2E 至少输出本任务列出的结构化实际事实；
28. public API adversarial matrix 全部通过；
29. Starting State、Validation Report、Boundary Closure 真实完整，不是三行摘要；
30. production violations = 0；
31. production cycles = []；
32. Bare/Minimal 不引用 Legacy；
33. M0、架构和主要 GRF 回归保持；
34. OpenClaw Live、模型、Corpus、PB 长跑、远端拆仓未启动；
35. AGENTS.md 已更新并遵守；
36. 所有修改已 commit；
37. 工作树干净；
38. 最终只交一个包含完整历史并已验证的 Git bundle。
```

---

# 12. 明确非目标

M1-C5 不做：

```text
M2 MemoryStatement Formation Corpus；
M3 PlacementDecision Corpus；
真实 LLM；
OpenClaw Live；
语义质量评测；
History/Audit 产品化；
PB/1M 压测；
跨进程文件锁；
数据库/Event Sourcing；
分布式事务；
进程崩溃恢复协议；
远端 GitHub 拆仓；
Graph/Vector/Embedding；
全局 identity/source/topic relation index；
Evidence Capsule/Merkle/供应链安全。
```

---

# 13. 真实停止条件

只有以下情况可停止并返回：

```text
1. Core operation lease 必须引入 Access 反向依赖；
2. stdlib-only 同进程 lifecycle 无法在不引入数据库/daemon 的情况下实现；
3. Core transaction lease 与 Snapshot consistent-read 合同存在不可调和冲突；
4. Store 写入口封装会真实破坏必要的 Snapshot/测试注入能力且无 capability 方案；
5. Recall canonical contract 与现有 9/9 几何 oracle 真实冲突；
6. 大规模环境故障无法定位。
```

不要因以下问题停止：

```text
需要增加 operation state/Condition/context manager；
需要把 CoreRuntime.store 改为私有并公开 state_path；
需要调整 Access 使用 Core public transaction lease；
需要移除/收窄 CellStore 活动导出；
需要扩充 E2E 和验证报告；
需要新增确定性并发测试；
测试数量明显增加；
文档或目录小调整。
```

---

# 14. 建议内部 Checkpoint

```text
Gate 0-1:
  docs(m1c5): preserve operation lease and state bypass blockers

Gate A:
  fix(m1c5): serialize core lifecycle operations and close

Gate B:
  fix(m1c5): bind access transactions to core operation lease

Gate C:
  refactor(m1c5): encapsulate current-state store and cell views

Gate D:
  fix(m1c5): close canonical kernel metadata and recall contracts

Gate E:
  fix(m1c5): isolate trace reentrancy and snapshot lifecycle

Gate F:
  test(m1c5): close adversarial matrix reports and final end-to-end truth
```

通过内部 Gate 后直接继续，不等待外部审查。

---

# 15. 最终交付

必须：

```text
所有修改 commit；
工作树干净；
Bundle 在仓库外生成；
Bundle 包含完整历史；
验证 Bundle；
文件名包含阶段和 HEAD 短哈希；
只交一个 Git bundle。
```

建议文件名：

```text
nollm_m1c5_operation_lease_state_encapsulation_canonical_recall_20260711_<shorthead>.bundle
```

最终回复必须提供：

```text
branch / HEAD / commits
Gate A-F facts
Core/Access lifecycle state machine
close race and direct Core interleave results
Store/Cell bypass negative matrix
Kernel metadata and Recall canonical matrix
9/9 parity
E2E and adversarial matrix result
package test counts
Snapshot / Trace results
M0 / architecture / GRF regression
production boundary and cycle counts
known limitations
bundle filename and SHA-256
```

不得声称：

```text
M2 已开始；
LLM Placement 已验证；
OpenClaw 已接入；
Memory Quality 已证明；
跨进程/crash transaction 已实现；
远端仓库已拆分。
```

---

# 16. 一句话执行目标

> **把 M1-C4 的静态 owner 与 pair registry 推进为真正覆盖活动操作、close、Snapshot、Trace 和跨 Store rollback 的运行时租约；封闭公开 Store/Cell 旁路并统一 Canonical Recall 合同，使任何已返回成功的 Core/Access 操作都不会被旧事务或旧 owner 撤销，从而真正具备封板 M1 的条件。**
