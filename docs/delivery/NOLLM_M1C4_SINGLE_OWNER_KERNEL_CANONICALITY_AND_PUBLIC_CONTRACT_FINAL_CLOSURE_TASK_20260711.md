# Nollm M1-C4：单一 Core Owner、Kernel Canonicality 与公共合同最终闭合任务书

**日期**：2026-07-11
**阶段编号**：M1-C4 — Single Core Owner / Kernel Canonicality / Public Contract Final Closure
**状态**：M1-C3 Bundle 系统审核未通过后的唯一闭合任务
**输入 Bundle**：`nollm_m1c3_immutable_kernel_phase_workspace_coordinator_20260711_c0f8f57c.bundle`
**输入 Bundle SHA-256**：`a8b9c3b5983eefcca9e80a2cbd21eff6510bf7a3a2105cfb12a596dcbce7230f`
**输入 HEAD**：`c0f8f57c73050c414b021d4809c433d77f639609`
**输入分支**：`codex/m1c3-immutable-kernel-phase-workspace-coordinator`
**建议工作分支**：`codex/m1c4-single-owner-kernel-public-contract-final-closure`
**主环境**：Windows 10/11 + PowerShell
**执行方式**：大跨度任务 + 内部 Gate + 普通问题就地修复 + 最终单一完整历史 Git bundle

---

# 0. 本任务定位

M1-C3 的正确成果必须全部保留，不得回退重做：

```text
Bundle / Git history = PASS
HEAD = c0f8f57c73050c414b021d4809c433d77f639609
working tree = clean
Manifest = 1408 / 1408
production violations = 0
production cycles = []
nollm-core = 26 passed
nollm-snapshot = 5 passed
nollm-trace = 1 passed
nollm-access = 30 passed
M0 regression = 18 passed
architecture / forbidden / hygiene = 8 passed
geometry parity = 9 / 9 passed
M1 E2E = passed
GRF external Linux audit = 109 passed, 1 skipped
zstandard-dependent historical tests unavailable = 2
```

已实质完成：

```text
1. 三 profile × up/down/lateral 九模板进入活动 Core；
2. KernelRegistry 的普通公开赋值和 Mapping alias 已被阻断；
3. mixed None/string phase 已使用 stable_key；
4. GeometryAnchor cells 已要求稳定排序和唯一；
5. 活动 Recall 明确只支持 lateral ring 0/1，ring>1 拒绝；
6. 同一 Access root + 同一 CoreRuntime 的 Access 读写使用共享 RLock；
7. reuse 在写 supporting binding 前读取 canonical Evidence；
8. Canonical Evidence、one-current HandleBinding、异常回滚和零依赖边界继续成立；
9. Snapshot、Trace、Bare/Minimal 和 Legacy 隔离均未回退；
10. 未启动 OpenClaw Live、真实模型、Corpus、PB 长跑或远端拆仓。
```

但当前仍不得输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

原因是以下七组正确性阻断仍可复现：

```text
B1. CoverageTemplate 仍可接受同一几何目标的多条不同权重 entry；
B2. KernelEntry 仍可接受任意 kernel_type、重复/乱序 flags，且 CoverageTemplate 可接受负 normalization residual；
B3. Core workspace 的“唯一 mutable owner”只在 AccessRuntime 构造时检查，第二个 CoreRuntime 仍可直接覆盖已成功状态；
B4. 同一个 CoreRuntime 可以绑定两个不同 Access workspace，得到两把不同事务锁；一个失败回滚可撤销另一个已返回成功的写入；
B5. workspace coordinator 以强引用永久保存 Core owner，没有 close/release 生命周期；同进程中旧对象即使不再使用也无法正常关闭后重开；
B6. AccessDecision、CoreRecallRequest、AccessRecallRequest 等活动公共输入仍可接受错误类型并延迟失败；
B7. M1-C3 E2E/报告没有真实覆盖任务书要求的 registry negative matrix、跨 workspace rollback、直接第二 Core owner、close/reopen 和并发读一致性事实。
```

M1-C4 是 M1 的最终正确性闭合，不得进入 M2、M3、真实模型或 OpenClaw Live。

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
8. 本 M1-C4 任务书
9. Core / Access / Snapshot / Trace 模块章程
```

必须更新并遵守根目录 `AGENTS.md`，至少加入：

```text
- Current stage is M1-C4 single-owner, kernel-canonicality, and public-contract final closure.
- Preserve all accepted M1-C3 immutable registry, phase stable-key, Anchor canonicality, ring-1, Evidence, Binding, Snapshot, Trace, boundary, and package results.
- A canonical Core state path has at most one live mutable CoreRuntime owner in one Python process, including bare-Core use outside Access.
- Core workspace ownership is claimed in nollm-core before state read/write or validator binding; Access must not be the only enforcement point.
- Core and Access workspace owner registries must not retain dead runtimes forever; explicit close/context lifecycle and weak cleanup are required.
- One canonical Core workspace may bind to only one canonical Access workspace while active; multiple AccessRuntime objects may share that exact pair only.
- KernelEntry and CoverageTemplate direct constructors must reject duplicate geometric targets, noncanonical flags, unknown kernel_type, invalid weight ranges, and negative residuals.
- Public Core/Access request and decision dataclasses reject wrong direct-constructor types immediately.
- Core Recall is a consistent read of one Core state and cannot interleave with a Core mutation on the same runtime.
- Do not proceed to M2, OpenClaw Live, model calls, corpus execution, PB scale, or remote GitHub work.
```

## Gate 0 PASS

```text
第一性原理和模块所有权不变；
未恢复 relation index、Python semantic placement、graph/vector/embedding；
M1-C3 正确成果全部保留；
任务范围没有扩展到 M2/M3。
```

---

# 2. 保全输入现场

从输入 Bundle 新克隆，不得 reset、clean、改写历史或回退重做。

生成：

```text
docs/project/M1C4_STARTING_STATE.md
```

至少记录：

```text
input bundle filename / SHA-256
input branch / HEAD / status / log
M1-C3 package counts
M0 / architecture / GRF results
boundary report
zstandard 环境情况
本任务下列外部复现值
```

必须逐项保全以下外部复现：

## 2.1 Duplicate geometric target 被接受

基于权威 `eisenstein_exact_v1 / coverage_up` 模板，将同一个：

```text
layer_delta=-1, dq=0, dr=0
```

拆成两条：

```text
weight_q16=30000
weight_q16=35536
```

当前直接构造成功，尽管两条 entry 指向同一几何目标。

## 2.2 非 canonical KernelEntry 被接受

当前可直接构造并进入 CoverageTemplate：

```text
kernel_type="graph_edge"
flags=("eisenstein_exact", "eisenstein_exact")
flags=("z", "a", "a")
```

## 2.3 负 normalization residual 被接受

当前可构造：

```text
entry.weight_q16 = 70000
sum_weight_q16 = 70000
normalization_residual_q16 = 65536 - 70000 = -4464
```

模板仍被接受。

## 2.4 第二个直接 CoreRuntime 可 stale-overwrite

```text
core1 = CoreRuntime(path)
core2 = CoreRuntime(path)  # 在 core1 写入前创建
Access(core1) 成功写 A 并返回 Handle A
core2 直接 put B
reopen：A 消失，B 存在
HandleStore：A binding 仍存在
```

## 2.5 同一个 Core 绑定两个 Access roots

```text
core = CoreRuntime(core_path)
AccessRuntime(core, rootA Evidence/Binding)
AccessRuntime(core, rootB Evidence/Binding)
```

当前被接受，并获得不同 access-root locks。

故障并发复现：

```text
A：Core.put(A) 成功，Binding 写入阻塞后失败
B：Core.put(B) + rootB Binding 成功，并已返回 Handle B
A：按旧 Core snapshot 回滚
最终：B Core atom 被删除，但 rootB Binding 仍存在
```

## 2.6 Coordinator 强引用永久占有

删除 AccessRuntime/CoreRuntime 并执行 GC 后：

```text
weakref(core) 仍非 None
```

同进程新建 CoreRuntime 后再构造 AccessRuntime：

```text
RuntimeError: canonical Core workspace already has a distinct mutable state owner
```

没有 close/release 路径。

## 2.7 AccessDecision 错误类型被接受

当前以下直接构造成功：

```python
AccessDecision(
    decision_id=1,
    statement_id=2,
    action="defer",
    reason_text=3,
    decided_by="host",
)
```

## Gate 1 PASS

```text
输入事实、当前缺陷和环境限制全部保全；
没有用修复后的测试覆盖初始复现；
没有将这些问题降级为文档限制。
```

---

# 3. Gate A：KernelEntry / CoverageTemplate 完整 Canonical 合同

M1-C3 已实现深度不可变方向，但直接构造仍未代表唯一、自洽的 Kernel 合同。

## 3.1 KernelEntry 必须严格验证

`KernelEntry.__post_init__` 至少必须满足：

```text
layer_delta / dq / dr / weight_q16 为 exact int，bool 不得通过；
0 < weight_q16 <= Q16_ONE；
kernel_type 必须是当前活动合同允许的精确值：coverage_template；
flags 必须是 tuple[str, ...]；
flags 必须严格 sorted + unique；
每个 flag 非空；
不得接受重复 flag、乱序 flag 或 graph_edge 等任意类型名。
```

如未来需要其他 kernel_type，应另行定义独立对象/合同，不得在当前 CoverageTemplate 中开放自由字符串。

## 3.2 CoverageTemplate 几何目标必须唯一

模板中 entry 的唯一性不得只用 dataclass 全字段相等判断。

必须按几何目标键拒绝重复：

```text
(layer_delta, dq, dr)
```

同一目标即使：

```text
weight 不同；
flags 不同；
kernel_type 不同；
```

也不得出现两次。

原因：展开后它们是同一个目标 Cell，不能形成两个字节不同但运行时被 merge/max 的伪多边。

## 3.3 Weight / residual 范围

必须保证：

```text
0 < sum_weight_q16 <= Q16_ONE；
normalization_residual_q16 >= 0；
sum_weight_q16 + normalization_residual_q16 == Q16_ONE；
approximation_residual_q16 >= 0；
exact/baseline approximation_residual_q16 == 0；
dream_quasi approximation_residual_q16 > 0 且有明确上界；
单 entry weight 不超过 Q16_ONE；
```

不得仅因代数等式成立而接受负 residual。

## 3.4 Compiler metadata

继续保留 M1-C3 的 frozen `CompilerMetadata`，并补充：

```text
compiler_id 必须为当前 registry 支持的 canonical compiler ID；
method、weight_format、layer_index_direction、flags、fanout 均须与 profile/direction/entries 一致；
compiler flags 必须等于 canonical entry flags union；
任何 public mapping 不得 alias 内部对象。
```

## 3.5 Direct-constructor negative matrix

至少新增：

```text
test_kernel_entry_rejects_unknown_kernel_type
test_kernel_entry_rejects_noncanonical_or_duplicate_flags
test_kernel_entry_rejects_zero_negative_or_over_q16_weight
test_template_rejects_duplicate_geometric_target_with_different_weight
test_template_rejects_duplicate_geometric_target_with_different_flags
test_template_rejects_negative_normalization_residual
test_template_rejects_total_weight_over_q16
test_template_rejects_noncanonical_compiler_id
test_all_nine_registry_templates_still_construct_and_match_oracle
```

## Gate A PASS

```text
所有可公开构造的 KernelEntry/CoverageTemplate 都是 canonical、自洽和有界的；
同一几何模板语义不存在多个 accepted byte representations；
九模板 parity 仍为 9/9。
```

---

# 4. Gate B：Core 层唯一 Mutable Workspace Owner

M1-C3 把 owner 检查放在 `nollm-access`，无法保护 `nollm-bare` 或直接 Core API。

唯一 owner 约束必须由 `nollm-core` 自己执行。

## 4.1 在 Core 构造阶段声明 owner

建立 stdlib-only、进程内的 Core workspace owner registry，例如：

```text
canonical current_state path -> live CoreRuntime owner lease
```

要求：

```text
1. CoreRuntime.__init__ 在 bind semantic validator、read、write 前声明 owner；
2. 同一 canonical state path 已有 live mutable owner时，第二个 CoreRuntime 构造立即拒绝；
3. 拒绝必须发生在第二个 runtime 绑定 store validator 或读取/写入状态之前；
4. 自定义 FileCoreStateStore 以其 canonical store.path 作为 identity；
5. symlink/relative path 归一到同一 identity；
6. Windows-first 使用适合 Windows 的 case normalization；Linux 不得把两个真实不同路径无依据合并；
7. 不引入数据库、daemon、文件锁服务或跨进程协调。
```

## 4.2 生命周期与释放

必须提供明确生命周期：

```text
CoreRuntime.close()
CoreRuntime.__enter__ / __exit__（推荐）
```

要求：

```text
close 幂等；
close 后 runtime 的 read/mutation/recall/snapshot port 操作明确拒绝；
active consistent-read token 存在时不得静默 close；
close 释放 owner lease；
显式 close 后可在同一进程重新打开同一 workspace；
全局 registry 不得以强引用永久保活 CoreRuntime；
可使用 weakref/finalizer 作兜底，但不能只依赖 GC 正确性；
构造中途失败必须释放已声明 lease。
```

## 4.3 Core Recall 必须是单一状态一致读

`CoreRuntime.recall()` 应在整个：

```text
frontier traversal
atoms_at
bridges
result construction
```

期间持有同一 Core RLock，防止同一 runtime 的直接 Core mutation 插入 Recall 中间。

RLock 可重入，内部 `atoms_at()` / `bridges()` 不应死锁。

## Gate B 测试

```text
test_second_core_runtime_same_workspace_rejected_at_core_constructor
test_second_core_runtime_cannot_bind_or_write_before_rejection
test_direct_stale_core_overwrite_is_impossible
test_core_close_releases_owner_and_allows_reopen
test_closed_core_rejects_read_write_recall_and_snapshot
test_failed_core_constructor_releases_owner_lease
test_symlink_and_relative_paths_share_owner_identity
test_core_recall_is_serialized_against_direct_core_mutation
```

## Gate B PASS

```text
同一 Python 进程、同一 canonical Core state path 只有一个 live mutable CoreRuntime；
Bare Core 与 Access Core 均受同一规则保护；
旧 owner 可以显式关闭并安全重开；
不存在强引用永久占有或 stale direct Core overwrite。
```

---

# 5. Gate C：Access Workspace Coordinator 一一绑定与跨 Store 事务

Core owner 由 Core 自己保证后，Access coordinator 仍需保证 Access workspace 组合唯一。

## 5.1 Core workspace 与 Access workspace 必须一一绑定

活动期间必须满足：

```text
一个 canonical Core state path <-> 一个 canonical Access root
```

允许：

```text
多个 AccessRuntime
+ 同一个 CoreRuntime object
+ 同一个 Evidence/Binding root
→ 共享同一 coordinator 和同一 transaction RLock
```

拒绝：

```text
同一个 CoreRuntime + 不同 Access roots；
同一个 Access root + 不同 Core workspaces；
同一个 Core path + 不同 Core objects（应已由 Gate B 更早拒绝）；
Evidence root 与 Binding root 不匹配。
```

不得继续使用：

```text
lock only keyed by access_root
```

从而允许同 Core 获得两把锁。

## 5.2 Coordinator 生命周期

要求：

```text
coordinator 不得永久强引用死 owner；
多个 AccessRuntime 使用同一 pair 时可引用计数或 weak registration；
AccessRuntime.close()/context manager（如引入）必须安全释放自己的 lease；
只要仍有同 pair AccessRuntime，协调器继续有效；
最后一个 Access lease 释放后，可以在 Core 仍存活时重新绑定同一个 Access root；
不得在仍有活动 AccessRuntime 时换绑另一个 Access root。
```

CoreRuntime 的 owner 生命周期与 Access lease 生命周期必须清楚区分。

## 5.3 读写事务串行

以下继续使用同一 coordinator lock：

```text
capture
apply 全部 action
recall
saved_handle
任何 Core + Binding + Evidence 联合读取
rollback
```

必须新增跨 root 防护测试，证明 M1-C3 的外部故障场景在构造阶段即被拒绝，而不是运行时靠运气串行。

## Gate C 测试

```text
test_same_core_same_access_root_shares_one_coordinator
test_same_core_different_access_root_is_rejected
test_same_access_root_different_core_is_rejected
test_cross_access_root_rollback_scenario_cannot_be_constructed
test_one_failed_transaction_cannot_erase_other_success
test_access_close_releases_lease_without_closing_core
test_access_rebind_after_last_lease_release
test_concurrent_recall_and_saved_handle_observe_old_or_new_complete_state
```

继续保留：

```text
all-action failure matrix；
rollback fatal path；
forget without Evidence；
reuse canonical Evidence；
one-current HandleBinding；
```

## Gate C PASS

```text
一个 Core workspace 不会被两个 Access roots 分裂协调；
任何已返回成功的 Access mutation 不会被另一事务回滚撤销；
联合读取不观察中间态；
coordinator 生命周期可关闭、可重开且无永久强引用泄漏。
```

---

# 6. Gate D：活动公共合同严格类型闭合

M2 将依赖 M1 的公共对象。M1 封板前，不得继续接受 Python 类型注解与实际直接构造不一致的对象。

## 6.1 AccessDecision

直接构造必须立即拒绝：

```text
decision_id 非 non-empty exact str；
statement_id 非 non-empty exact str；
action 非 exact str / 不在枚举；
reason_text 非 non-empty exact str；
decided_by 非 exact str / 不在枚举；
target_cell 非 GeometryAddress；
existing_handle 非 AtomHandle；
bridge_spec 非 BridgeSpec；
与 action 无关的多余字段。
```

不得让错误类型延迟到 Evidence path、Core mutation 或文件写入时才失败。

## 6.2 Recall 公共请求

`CoreRecallRequest` 与 `AccessRecallRequest` 至少严格验证：

```text
request_id exact non-empty str；
entry_cells exact tuple[GeometryAddress,...]；
entry_handles exact tuple[AtomHandle,...]；
allowed_kernels exact tuple[str,...]；
budget exact RecallBudget；
entry identity 唯一；
unknown kernel 拒绝；
```

`RecallBudget` 继续 exact int，bool 不得作为 int 通过。

是否要求 allowed_kernels 排序可由当前语义决定；若顺序无语义，应 canonicalize 或拒绝重复，不能保留相同语义多个表现而影响 Trace/报告。

## 6.3 Command 公共对象

对 Put/Remove/Replace/Move/Bridge commands 做最小直接类型验证，确保错误 public dataclass 在进入 `apply_batch` 前或批处理零写阶段明确拒绝。

不得为了类型闭合引入 Pydantic、数据库或外部依赖。

## Gate D 测试

```text
test_access_decision_rejects_non_string_ids_reason_and_source
test_access_decision_rejects_wrong_typed_optional_fields
test_core_recall_request_rejects_list_and_wrong_entry_types
test_access_recall_request_rejects_list_and_wrong_handle_types
test_recall_budget_rejects_bool
test_core_commands_reject_wrong_direct_constructor_types
test_invalid_public_contract_never_writes_core_binding_or_evidence
```

## Gate D PASS

```text
活动公共 Python 合同与类型注解一致；
错误输入在任何状态变更前被拒绝；
M2 可以在稳定 typed contract 上建立 Statement Formation。
```

---

# 7. Gate E：Snapshot / Trace / Boundary / E2E 真值闭合

重新证明：

```text
Snapshot create/restore/clone 与 Core owner lifecycle 一致；
关闭的 Core 不可 Snapshot；
新 workspace target 可 clone；
mixed phase、registry identity、Anchor 和 lateral ring1 保持；
FailingTraceSink 不改变结果；
Core Recall 全程锁不会造成 Trace 或 Snapshot 死锁；
Access coordinator 不引入 CORE -> ACCESS 或循环；
production violations = 0；
production cycles = []；
Bare/Minimal 不引用 Legacy；
旧 GRF 只作 Lab parity oracle。
```

## 7.1 真正升级 M1 E2E

当前脚本仍主要输出 M1-C2 facts，必须重写为 M1-C4 结构化事实，至少包含：

```text
kernel_entry_unknown_type_rejected
kernel_entry_noncanonical_flags_rejected
duplicate_geometric_target_rejected
negative_normalization_residual_rejected
registry_identity_stable
mixed_phase_round_trip
anchor_order_rejected
lateral_ring_one_real_recall
lateral_unregistered_ring_rejected
second_core_owner_rejected_at_constructor
direct_stale_overwrite_prevented
core_close_reopen_succeeds
same_core_different_access_root_rejected
cross_root_rollback_unconstructable
concurrent_recall_consistent
access_decision_wrong_types_rejected
reuse_corrupt_evidence_rejected
snapshot_after_reopen_equal
trace_parity
boundary_zero
```

不得继续只把布尔常量写入结果；每个事实必须由实际操作产生。

修正脚本中的旧文案：

```text
M1C2 E2E fact failed
```

改为当前阶段准确名称。

## 7.2 文档

生成/更新：

```text
docs/validation/M1C4_SINGLE_OWNER_KERNEL_PUBLIC_CONTRACT_REPORT.md
docs/architecture/module-ownership/M1C4_BOUNDARY_CLOSURE.md
docs/architecture/module-ownership/M1C4_BOUNDARY_REPORT.json
docs/project/M1C4_STARTING_STATE.md
```

报告必须区分：

```text
输入 Bundle 事实；
外部 Linux 审计事实；
Windows 实际执行事实；
zstandard 环境限制；
同进程 owner/transaction 保证；
跨进程/崩溃恢复非目标；
Core close/reopen 生命周期；
支持的 lateral ring 合同；
M2 前置条件是否满足。
```

## Gate E PASS

```text
报告、测试和代码保证一致；
没有用 package test pass 掩盖跨 workspace 或直接 Core bypass；
没有把未实现的多进程保证写进结论；
M1 的接受事实可被新克隆重复验证。
```

---

# 8. 独立 Package Gates

## Core

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/packages/nollm-core/src"
python -m pytest -q packages/nollm-core/tests
```

新增或扩展：

```text
test_kernel_entry_canonical_contract.py
test_coverage_template_unique_target_and_weight_bounds.py
test_core_workspace_single_owner_lifecycle.py
test_core_recall_consistent_read.py
test_public_core_contract_strict_types.py
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
close/reopen + Snapshot；
closed owner rejection；
clone to distinct workspace；
```

## Trace

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-trace/src"
) -join ";"
python -m pytest -q packages/nollm-trace/tests
```

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
test_access_workspace_one_to_one_binding.py
test_cross_root_transaction_is_rejected.py
test_access_coordinator_lifecycle.py
test_access_public_contract_strict_types.py
test_concurrent_access_read_complete_state.py
```

新包测试继续不得依赖：

```text
reference/python
OpenClaw
experiments
Legacy GRF private implementation
```

---

# 9. Final Gate

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
python tools/check_module_boundaries.py --report docs/architecture/module-ownership/M1C4_BOUNDARY_REPORT.json

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

python -m compileall -q `
  packages/nollm-core/src `
  packages/nollm-snapshot/src `
  packages/nollm-trace/src `
  packages/nollm-access/src

git diff --check
git status --short
```

如外部环境仅缺 `zstandard`，允许精确排除两项历史压缩测试并单独报告，不得扩大排除范围。

---

# 10. M1-C4 接受条件

只有全部满足，才可输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

条件：

```text
1. M1-C3 的九模板、不可变 Registry、phase stable_key、Anchor、ring1、Evidence、Binding、Snapshot、Trace 和零边界成果全部保留；
2. KernelEntry 只接受 canonical coverage_template entry；
3. KernelEntry flags sorted unique，weight 在合法 Q16 范围；
4. CoverageTemplate 拒绝重复几何目标，即使 weight/flags 不同；
5. normalization residual 不得为负，总权重不超过 Q16_ONE；
6. compiler ID/method/flags/weight format/fanout 与模板一致；
7. 九模板 parity 仍为 9/9；
8. CoreRuntime 在 Core 层声明 canonical workspace owner；
9. 同一进程同一路径第二个 mutable CoreRuntime 构造即拒绝；
10. 第二个 CoreRuntime 不会在拒绝前 bind validator、read 或 write；
11. direct stale Core overwrite 不可发生；
12. CoreRuntime 有明确 close/context 生命周期；
13. close 后可同进程安全 reopen；
14. owner registry 不以强引用永久保活 runtime；
15. Core Recall 对同一 runtime mutation 是一致读；
16. 同一 Core workspace 只绑定一个 canonical Access root；
17. 同 Core + 不同 Access root 构造拒绝；
18. 同 Access root + 不同 Core workspace 构造拒绝；
19. 多个相同 pair AccessRuntime 共享同一 coordinator lock；
20. 跨 root rollback 删除他人成功写入的场景不可构造；
21. Access coordinator 可安全释放并重建，不永久泄漏；
22. recall/saved_handle 不观察事务中间态；
23. reuse 继续验证 canonical Evidence；
24. AccessDecision/CoreRecallRequest/AccessRecallRequest/commands 错误类型在零写前拒绝；
25. accepted state 始终 disk == runtime == snapshot bytes；
26. Core close/reopen、mixed phase、Anchor、lateral、registry identity 全回归；
27. FailingTraceSink 不改变结果；
28. M1-C4 E2E 的结构化事实由实际操作产生并全部为真；
29. production violations = 0；
30. production cycles = []；
31. Bare/Minimal 不引用 Legacy；
32. M0、架构和主要 GRF 回归保持；
33. OpenClaw Live、模型、Corpus、PB 长跑、远端拆仓未启动；
34. AGENTS.md 已更新并遵守；
35. 所有修改已 commit；
36. 工作树干净；
37. 最终只交一个包含完整历史并已验证的 Git bundle。
```

---

# 11. 明确非目标

M1-C4 不做：

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
crash recovery protocol；
远端 GitHub 拆仓；
Graph/Vector/Embedding；
全局 identity/source/topic relation index；
Evidence Capsule/Merkle/供应链安全。
```

---

# 12. 真实停止条件

只有以下情况可停止并返回：

```text
1. Core 层单 owner 必须引入 Access 反向依赖；
2. owner lifecycle 无法在 stdlib-only、同进程条件下实现；
3. CoverageTemplate canonical contract 与保留的 9/9 oracle 真实冲突；
4. Core consistent Recall 必须依赖数据库或跨进程锁；
5. Access one-to-one workspace 组合与当前 public package ownership 真实冲突；
6. 大规模环境故障无法定位。
```

不要因以下问题停止：

```text
需要新增 CoreRuntime.close/context manager；
需要 weakref/lease registry；
需要改变旧 reopen 测试顺序；
需要把 E2E 从 M1-C2 文案升级；
需要增加 strict __post_init__；
需要新增并发测试；
测试数量增加；
文档或目录小调整。
```

---

# 13. 建议内部 Checkpoint

```text
Gate 0-1:
  docs(m1c4): preserve single-owner kernel and public-contract blockers

Gate A:
  fix(m1c4): close canonical kernel entry and template invariants

Gate B:
  fix(m1c4): enforce core workspace owner lifecycle and consistent recall

Gate C:
  fix(m1c4): bind one access workspace and serialize complete transactions

Gate D:
  fix(m1c4): enforce strict active public contracts

Gate E:
  test(m1c4): close snapshot trace boundary and final end-to-end truth
```

通过内部 Gate 后直接继续，不等待外部审查。

---

# 14. 最终交付

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
nollm_m1c4_single_owner_kernel_public_contract_final_closure_20260711_<shorthead>.bundle
```

最终回复必须提供：

```text
branch / HEAD / commits
Gate A-E facts
KernelEntry/CoverageTemplate negative matrix
9/9 parity
Core owner claim/reject/close/reopen facts
same-Core different-Access-root rejection
cross-root rollback prevention
Core Recall consistent-read result
public contract strict-type matrix
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

# 15. 一句话执行目标

> **把 M1-C3 已建立的不可变九模板、phase 全序、Anchor canonicality 和 Access 事务基础，推进为 Core 自己强制的单一 workspace owner、一个 Core 对一个 Access workspace、可关闭重开的无泄漏生命周期、完整 canonical Kernel 直接构造和严格公共输入合同，从而真正封板 M1。**
