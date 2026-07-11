# Nollm M1-C3：不可变 Kernel、Phase 全序 Canonicality 与 Workspace Coordinator 闭合任务书

**日期**：2026-07-11
**阶段编号**：M1-C3 — Immutable Kernel / Phase Canonicality / Workspace Coordinator Closure
**状态**：M1-C2 Bundle 系统审核未通过后的唯一闭合任务
**输入 Bundle**：`nollm_m1c2_complete_kernel_canonical_evidence_serialized_transaction_20260711_6715cdb7.bundle`
**输入 Bundle SHA-256**：`0aeb24737fc6ae031b876b4b74f573d2ac65e1c1e2ea2172db4ff33aafd13cb6`
**输入 HEAD**：`6715cdb7edbac63907805079ef1cbbc973dd2887`
**输入分支**：`codex/m1c2-complete-kernel-canonical-evidence-serialized-transaction`
**建议工作分支**：`codex/m1c3-immutable-kernel-phase-workspace-coordinator`
**主环境**：Windows 10/11 + PowerShell
**执行方式**：大跨度任务 + 内部 Gate + 普通问题就地修复 + 最终单一完整历史 Git bundle

---

# 0. 本任务定位

M1-C2 的工程成果应全部保留：

```text
完整 Bundle / Git 历史 = PASS
HEAD = 6715cdb7edbac63907805079ef1cbbc973dd2887
working tree = clean
production violations = 0
production cycles = []
Manifest = 1394 / 1394
nollm-core = 21 passed
nollm-snapshot = 4 passed
nollm-trace = 1 passed
nollm-access = 27 passed
M0 regression = 18 passed
architecture/no-forbidden/hygiene = 8 passed
geometry parity = 9/9 passed
M1-C2 E2E = passed
GRF external Linux audit = 109 passed, 1 skipped
zstandard-dependent historical tests unavailable = 2
```

已实质完成：

```text
1. 三个 profile 的 up/down/lateral 九模板已进入活动 Core；
2. residual、flags、compiler metadata 和 registry digest 已迁移；
3. 默认 fanout=7，ring=2 默认拒绝；
4. Core state 对顶层 cells/atoms/bridges 顺序、空 Cell 和错误基础类型已有严格校验；
5. MemoryStatement 和 Evidence 不再做数字/布尔值到字符串的强转；
6. Evidence canonical bytes 与同 ID 不可覆盖已成立；
7. forget 在 Evidence 缺失时可按显式 Handle 清理；
8. 同一 CoreRuntime 上的多个 AccessRuntime 已共享 workspace RLock；
9. Bare/Minimal、模块边界和 Addressed Handle 主线保持正确；
10. 未启动 OpenClaw Live、模型、Corpus、PB 长跑或远端拆仓。
```

但当前仍不得输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

原因是以下六组正确性阻断仍可复现：

```text
B1. KernelRegistry / CoverageTemplate 的公开状态可变，registry identity 可在 Core 运行期间被外部改写；
B2. CoverageTemplate 直接构造只检查部分类型，允许 layer-mod、fanout、residual、compiler metadata 与 profile/direction 自相矛盾；
B3. GeometryAddress 的默认 dataclass 排序不是 phase 全序，合法 mixed-phase 状态和 Recall 会 TypeError；
B4. GeometryAnchor.cells 是集合语义却允许任意顺序，形成多个字节不同但运行语义相同的 Core state；
B5. custom fanout 下 max_lateral_ring=2 重复展开 ring=1，而非真实 ring=2 或明确拒绝；
B6. workspace lock 只串行 AccessRuntime，但不同 CoreRuntime 同指向一个工作区时仍会以陈旧内存覆盖成功写入；Access Recall 也可观察 Core/Binding 事务中间态。
```

M1-C3 只闭合上述问题。不得进入 M2、M3、真实模型或 OpenClaw Live。

---

# 1. 开工前最高约束

Codex 开始前必须依次读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/project/NOLLM_PROJECT_BOOK_V3_0_MODULAR_GEOMETRY_INFRASTRUCTURE_M1_20260711.md（若仓库路径不同，读取当前 canonical 项目书）
3. 根目录 AGENTS.md
4. M1 主任务书
5. M1-C1 任务书
6. M1-C2 任务书
7. 本 M1-C3 任务书
8. Core / Access / Snapshot / Trace 模块章程
```

必须更新并遵守根目录 `AGENTS.md`，至少加入：

```text
- Current stage is M1-C3 immutable-kernel, phase-canonicality, and workspace-coordinator closure.
- Preserve all accepted M1-C2 nine-template, canonical-Evidence, HandleBinding, boundary, and package results.
- KernelRegistry and all objects contributing to registry/state identity are immutable after construction.
- Geometry ordering must use one explicit stable_key total order; dataclass incidental ordering is forbidden for persistent or Recall semantics.
- GeometryAnchor cells have canonical set semantics and must be strictly sorted and unique.
- Active lateral contract is registry-declared; unregistered rings must be rejected, never approximated by repeating ring 1.
- One process may not host two independent mutable CoreRuntime state owners for the same canonical Core workspace.
- Access reads spanning Core, Binding, and Evidence must not observe an in-progress Access mutation.
- Do not proceed to M2, OpenClaw Live, model calls, corpus execution, or remote GitHub work.
```

## Gate 0 PASS

```text
第一性原理与模块所有权保持；
未恢复外置关系索引、Python semantic placement、graph/vector/embedding；
M1-C2 正确成果全部保留；
任务范围未扩展到 M2/M3。
```

---

# 2. 保全输入现场

从输入 Bundle 新克隆，不得 reset、clean、改写历史或回退重做。

生成：

```text
docs/project/M1C3_STARTING_STATE.md
```

至少记录：

```text
input bundle filename / SHA-256
input branch / HEAD / status / log
M1-C2 package test counts
M0 / architecture / GRF results
boundary report
本任务六组外部复现值
```

外部复现值必须逐项保全：

```text
1. phase sort:
   同一 profile/chart/layer/q/r 下，phase=None 与 phase="p" 分别放入 Atom；
   第二次 put 在 state serialization 中报：
   TypeError: '<' not supported between instances of 'str' and 'NoneType'.

2. registry mutability:
   template = registry.coverage_template(...)
   template.to_mapping()["compiler"]["fanout_limit"] = 999
   会反向修改 registry 内模板，并改变 registry.identity。

3. runtime identity divergence:
   runtime 初始化后修改 registry.fanout_limit；
   store.read_bytes() != runtime.state_bytes()；
   store.read_document() 报 geometry registry mismatch。

4. direct CoverageTemplate semantic contradictions are accepted:
   coverage_up 的 to_layer_mod=99；
   compiler fanout_limit=0；
   exact profile approximation_residual_q16=123；
   wrong layer_index_direction / weight_format；
   均可直接构造成功。

5. two CoreRuntime stale overwrite:
   core1/core2 指向同一个 Core workspace；
   Access A 写入并成功返回 Handle A；
   Access B 使用陈旧 core2 写入并成功返回 Handle B；
   reopen 后 A 消失、B 存在，但 Binding A/B 均存在。

6. unsorted GeometryAnchor:
   GeometryAnchor(cells=(q=1,q=0)) 被接受、持久化并可 reopen；
   但 Recall 对 anchor 使用 membership/sorted target，顺序不具有业务语义。

7. custom lateral fanout:
   KernelRegistry(12) + max_lateral_ring=2；
   _targets 返回 12 项但仅 6 个唯一 cell，ring=1 被重复两次。

8. transient Access Recall:
   revision_current 已写 Core、Binding replace 尚阻塞时并发 recall；
   返回 evidence_payload_mismatch；
   事务随后成功。
```

## Gate 1 PASS

```text
输入事实、当前缺陷和环境限制均已保全；
没有用新测试结果覆盖初始复现记录。
```

---

# 3. Gate A：Kernel / Registry 深度不可变与完整直接构造合同

## 3.1 禁止可变 identity 输入

以下对象一旦进入活动 Core identity，必须深度不可变：

```text
Profile
KernelEntry
CoverageTemplate
compiler metadata
KernelRegistry templates
KernelRegistry fanout contract
KernelRegistry state_identity
```

当前 `CoverageTemplate.compiler` 是普通 `dict`，且 `to_mapping()` 返回同一引用；`KernelRegistry.fanout_limit` 也是可写属性。这会使已持久化 Core state 的 registry identity 在运行期间漂移。

实施要求：

```text
1. compiler metadata 改为 frozen value object，或内部使用不可变 tuple/MappingProxy；
2. to_mapping() 必须返回深拷贝的普通 JSON mapping，不得泄漏内部引用；
3. KernelRegistry 初始化后不可修改 fanout_limit、模板集合或 identity 输入；
4. templates() / coverage_template() 返回的对象不得通过任何公开引用改变 registry；
5. CoreRuntime 对 registry 使用只读引用；不得允许赋值替换后悄然改变 state identity；
6. registry identity 在其生命周期内重复计算必须恒定；
7. Snapshot/create/reopen 前后 identity 必须一致。
```

不得以“Python 私有字段约定”代替机器保证。

## 3.2 CoverageTemplate / KernelEntry 完整语义验证

直接构造和 mapping decode（若提供）必须拒绝：

```text
to_layer_mod != from_layer_mod + direction layer_delta；
entry.layer_delta 与 direction 不一致；
entries 数量 > compiler fanout_limit；
fanout_limit <= 0；
compiler weight_format != profile.weight_format；
layer_index_direction != finer_with_increasing_index；
compiler flags 非 canonical sorted unique tuple[str,...]；
compiler flags 与 entries flags 不一致；
exact/baseline profile approximation_residual != 0；
dream_quasi approximation_residual <= 0；
profile-specific method 不匹配；
source_phase / fields 错误类型；
非 canonical entry 顺序或重复 entry；
normalization / total weight 不一致。
```

如引入 `CompilerMetadata`，必须有严格 `to_mapping/from_mapping` 和测试。

## 3.3 Registry identity 测试

至少新增：

```text
test_registry_is_deeply_immutable
test_template_to_mapping_does_not_alias_internal_state
test_runtime_registry_identity_cannot_drift
test_coverage_template_rejects_wrong_layer_mod
test_coverage_template_rejects_wrong_profile_metadata
test_coverage_template_rejects_noncanonical_flags_and_entries
test_registry_identity_changes_only_by_constructing_a_new_registry
```

## Gate A PASS

```text
registry identity 生命周期内恒定；
不存在公开修改导致 disk/runtime/snapshot identity 分叉；
CoverageTemplate 直接构造代表完整、自洽合同，而非仅类型外壳。
```

---

# 4. Gate B：GeometryAddress 全序、Phase Canonicality 与 Anchor 集合语义

## 4.1 建立唯一几何全序

所有持久状态、Recall、Bridge 和 Access entry 排序必须使用：

```text
GeometryAddress.stable_key()
```

不得使用：

```text
sorted(GeometryAddress values)
sorted(cells.items())
dataclass(order=True) 的偶然 Optional[str] 比较
```

至少修复：

```text
CoreRuntime._document cell ordering；
CellStore.occupied_cells；
Core Recall initial frontier；
Bridge to_anchor target ordering；
AccessRecallRequest entry dedupe/order；
任何测试、Snapshot 或 Trace 中的 GeometryAddress 排序。
```

`stable_key()` 必须定义 `phase=None` 与字符串 phase 的确定性、不冲突全序；不得把合法 phase 静默合并。

## 4.2 mixed-phase 状态必须可用

必须验证：

```text
同一 profile/chart/layer/q/r，phase=None 与 phase="phase:x" 可分别占用；
put/move/replace/remove；
state_bytes；
Snapshot create/restore；
reopen；
Recall entry / Bridge traversal；
Access entry_handles + entry_cells dedupe；
均不报类型错误且字节一致。
```

## 4.3 GeometryAnchor canonical set semantics

当前 Anchor 的 cells 在运行逻辑中用于 membership 和排序后的 bounded traversal，原始 tuple 顺序不具有路径语义。因此必须明确：

```text
GeometryAnchor.cells = canonical sorted unique set represented as tuple
```

选择以下一种并保持一致：

```text
A. 直接构造要求输入已经按 stable_key 排序，否则拒绝；
B. 使用明确 factory 规范化，但持久 decode 必须拒绝非 canonical order。
```

禁止同一 Anchor 语义存在多个合法字节编码。

Top-level cells、atoms、bridges 及 Anchor 内部 cells 均须进入 authoritative semantic order 校验。

## Gate B 测试

```text
test_mixed_none_and_string_phase_state_round_trip
test_mixed_phase_recall_and_access_entry_order
test_bridge_target_order_uses_stable_key
test_unsorted_anchor_cells_rejected
test_anchor_cell_order_is_canonical_in_state_and_snapshot
test_all_geometry_sort_sites_use_total_order
```

## Gate B PASS

```text
合法 phase 不再触发 TypeError；
GeometryAddress 在所有活动路径上只有一个全序；
Anchor 集合语义只有一个 canonical byte representation；
accepted state 继续满足 disk == runtime == snapshot。
```

---

# 5. Gate C：Lateral Ring 合同不得伪造

当前 registry 只注册一个六邻居 `lateral` 模板，语义是 ring=1。Recall 在 `max_lateral_ring > 1` 时循环多次展开同一模板；默认 fanout=7 会在 ring=2 抛错，但 custom fanout=12 会把 ring=1 重复两次。

必须选择并明确实施一个合同：

## 推荐合同（本阶段优先）

```text
活动 KernelRegistry 的 lateral 只代表 ring=1；
RecallBudget.max_lateral_ring 仅允许 0 或 1；
任何 >1 的值在 Recall 开始、任何 frontier 展开前明确拒绝；
fanout_limit 只限制已注册模板 fanout，不自动授权未注册 ring；
未来如需 ring>1，必须注册 ring-specific template 并纳入 registry identity，另行立项。
```

如选择支持 ring>1，则必须：

```text
每个 ring 有独立、预计算、受 fanout 约束的 registry template；
ring 进入 template key 和 registry identity；
不得运行时重复 ring=1 或动态构造无界列表。
```

本阶段不得保留当前“custom fanout 后静默重复 ring=1”的行为。

测试：

```text
test_lateral_ring_one_uses_registered_template_once
test_lateral_ring_two_rejected_even_with_larger_generic_fanout（推荐合同）
test_no_duplicate_targets_from_lateral_budget
test_lateral_contract_is_bound_in_registry_identity
```

## Gate C PASS

```text
lateral 行为与 registry 声明完全一致；
不存在未注册 ring、重复 ring1 或 fanout 参数改变语义而 identity 未充分表达。
```

---

# 6. Gate D：唯一 Workspace State Owner 与真实 Access 串行性

## 6.1 当前问题

共享 `workspace_lock(root)` 只能串行 Access 调用，不能解决两个独立 `CoreRuntime` 对同一 `current_state.json` 各自持有陈旧内存的问题。

必须满足以下之一：

## 推荐方案：一个进程、一个 canonical Core workspace、一个 mutable state owner

建立轻量 `AccessWorkspaceCoordinator` 或等价进程内注册表：

```text
canonical Access workspace identity -> coordinator
coordinator owns:
  shared transaction RLock
  exactly one CoreRuntime identity / state owner
  canonical Binding workspace identity
```

要求：

```text
1. 第二个 AccessRuntime 使用同一个 CoreRuntime 对象：允许并共享 coordinator；
2. 第二个独立 CoreRuntime 指向同一 Core state path：构造 AccessRuntime 时立即拒绝；
3. 不得等到首次 mutation 后才发现；
4. Core workspace、HandleStore workspace 必须形成明确、可验证的组合关系；
5. 不引入数据库、daemon、文件锁服务或跨进程协调；
6. 报告准确声明只保证同一 Python 进程。
```

如果选择共享 Core state owner 而非拒绝，必须真正共享同一内存状态和 Core lock，不得只共享路径字符串。

## 6.2 Access read consistency

以下读取跨越 Core、Binding、Evidence，必须使用同一 coordinator read/transaction lock：

```text
AccessRuntime.recall
saved_handle
任何 binding + evidence + core 联合读取
```

并发 mutation 时，读取只能看到：

```text
完整旧状态
或
完整新状态
```

不得看到：

```text
Core 新 payload + Binding 旧 current statement
→ transient evidence_payload_mismatch
```

真正的长期文件损坏仍应返回明确 fallback；事务中间态不应泄漏为业务错误。

## 6.3 reuse Evidence 验证

`reuse` 在写入 supporting binding 前，应通过 `get_original()` 验证 Evidence 文件真实存在且 canonical；仅调用 `exists()` 不足以阻止把损坏 Evidence ID 绑定到 Handle。

`forget` 继续不要求 Evidence 存在。

## Gate D 测试

```text
test_two_access_runtimes_same_core_share_coordinator
test_second_distinct_core_runtime_same_workspace_is_rejected
test_stale_core_runtime_cannot_overwrite_prior_success
test_concurrent_recall_never_observes_transaction_midstate
test_saved_handle_is_serialized_with_mutation
test_reuse_rejects_corrupt_or_noncanonical_evidence_before_binding
test_workspace_identity_mismatch_rejected
```

必须保留 M1-C2 的：

```text
一失败一成功 rollback serialization；
all-action Binding failure matrix；
AccessConsistencyError；
forget without Evidence；
Evidence immutable capture。
```

## Gate D PASS

```text
同一进程、同一 workspace 不存在两个独立陈旧 Core owner；
任何已成功返回的 Access mutation 不会被之后的陈旧 Runtime 覆盖；
Recall/Binding/Evidence 联合读取不观察事务中间态；
保证范围与代码约束一致。
```

---

# 7. Gate E：Snapshot / Trace / Boundary 与 E2E 真值闭合

重新证明：

```text
Snapshot 绑定稳定、不可变的 registry identity；
mixed-phase state 可 Snapshot/restore/reopen；
FailingTraceSink 不改变结果；
Trace 对 mixed-phase 和 lateral ring1 使用 canonical stable keys；
Access coordinator 不引入 CORE -> ACCESS、Snapshot -> Access 或任何循环；
production violations = 0；
production cycles = []；
Bare/Minimal 不引用 Legacy；
旧 GRF 仅作为 Lab parity oracle。
```

升级 `lab/nollm-lab/m1/run_m1_minimal_e2e.py`，新增结构化布尔事实：

```text
registry_deeply_immutable
registry_identity_stable
coverage_direct_constructor_negative_matrix
mixed_phase_round_trip
mixed_phase_recall
anchor_order_rejected
lateral_ring_one_real_recall
lateral_unregistered_ring_rejected
same_workspace_distinct_core_rejected
stale_overwrite_prevented
concurrent_recall_consistent
reuse_corrupt_evidence_rejected
```

并补回 M1-C2 E2E 未真实覆盖的：

```text
实际 lateral ring=1 Recall（不是只检查 registry 长度）；
reversed cells；
bad direct Bridge/Anchor types；
numeric/bool MemoryStatement；
forget with missing Evidence；
rollback failure details；
reopen after all fault paths。
```

更新：

```text
docs/validation/M1C3_IMMUTABLE_KERNEL_PHASE_WORKSPACE_REPORT.md
docs/architecture/module-ownership/M1C3_BOUNDARY_CLOSURE.md
docs/architecture/module-ownership/M1C3_BOUNDARY_REPORT.json
```

报告必须区分：

```text
外部复现事实；
Windows 实际结果；
当前 Linux 外审结果；
zstandard 环境依赖；
同进程保证；
多进程/崩溃恢复非目标；
支持的 lateral ring 合同；
M2 前置条件。
```

## Gate E PASS

```text
报告、测试和实际代码保证完全一致；
不存在以默认 fixture 通过掩盖公开参数组合错误；
不存在以“共享 lock”描述掩盖多个陈旧 state owner。
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
test_registry_deep_immutability.py
test_coverage_template_semantic_validation.py
test_phase_total_order.py
test_anchor_canonical_order.py
test_lateral_registered_ring_contract.py
```

## Snapshot

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src"
) -join ";"
python -m pytest -q packages/nollm-snapshot/tests
```

新增 mixed-phase + registry identity Snapshot 测试。

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
test_workspace_coordinator_single_state_owner.py
test_access_read_transaction_consistency.py
test_reuse_validates_canonical_evidence.py
test_mixed_phase_access_recall.py
```

新包测试继续不得依赖 `reference/python`、OpenClaw 或 experiments。

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
python tools/check_module_boundaries.py --report docs/architecture/module-ownership/M1C3_BOUNDARY_REPORT.json

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

python -m compileall -q packages/nollm-core/src packages/nollm-snapshot/src packages/nollm-trace/src packages/nollm-access/src

git diff --check
git status --short
```

若外部环境仅缺 `zstandard`，允许精确排除两项历史压缩测试，并单独报告。

---

# 10. M1-C3 接受条件

只有全部满足，才可输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

条件：

```text
1. M1-C2 的九模板、Canonical Evidence、one-current Binding 和零边界成果全部保留；
2. KernelRegistry 及 identity 输入深度不可变；
3. template.to_mapping 不泄漏内部可变引用；
4. 运行期间不能通过 fanout/template 修改造成 registry identity 漂移；
5. CoverageTemplate 直接构造完整验证 layer-mod、fanout、residual、method、flags、weight format 和 entry 顺序；
6. mixed None/string phase 在 state、Snapshot、Recall、Bridge、Access 中均可用；
7. 所有 GeometryAddress 排序使用唯一 stable_key 全序；
8. GeometryAnchor cells 具有唯一 canonical set 表示；
9. 不存在相同语义、不同 Anchor bytes 的 accepted state；
10. lateral ring 合同明确；未注册 ring 不会重复 ring1；
11. custom fanout 不会静默改变未注册 lateral 语义；
12. 同一进程同一 workspace 只有一个 mutable Core state owner，或多个 AccessRuntime 真正共享同一 owner；
13. 第二个陈旧 CoreRuntime 无法覆盖先前成功写入；
14. Access recall/saved_handle 不观察事务中间态；
15. reuse 写 Binding 前验证 canonical Evidence；
16. 一失败一成功事务测试继续通过；
17. all-action 异常原子性和 rollback fatal path 继续通过；
18. accepted state 始终 disk == runtime == snapshot bytes；
19. registry mutation negative、mixed phase、anchor order、stale runtime、concurrent recall 等新 E2E facts 全部为真；
20. Snapshot/Trace 回归通过；
21. production violations = 0；
22. production cycles = []；
23. Bare/Minimal 不引用 Legacy；
24. M0、架构和主要 GRF 回归保持；
25. OpenClaw Live、模型、Corpus、远端拆仓未启动；
26. 所有修改已 commit；
27. 工作树干净；
28. 最终仅交一个包含完整历史并已验证的 Git bundle。
```

---

# 11. 明确非目标

M1-C3 不做：

```text
MemoryStatement Formation Corpus；
PlacementDecision Corpus；
真实 LLM；
OpenClaw Live；
语义质量评测；
History/Audit 产品化；
PB/1M 压测；
跨进程文件锁或分布式事务；
数据库/Event Sourcing；
远端 GitHub 拆仓；
Graph/Vector/Embedding；
全局 identity/source/topic relation index；
Evidence Capsule/Merkle/供应链安全。
```

---

# 12. 真实停止条件

只有以下情况可停止：

```text
1. Phase 被证明在活动 GeometryAddress 中不应存在，且需要项目级合同变更；
2. KernelRegistry 深度不可变必须破坏当前 public package ownership；
3. 一个 workspace 一个 state owner 无法在不引入反向依赖的条件下实现；
4. Access read consistency 必须依赖数据库或多进程事务；
5. retained 9-template oracle 与 phase/lateral 合同出现真实自相矛盾；
6. 大规模环境故障无法定位。
```

不要因以下问题停止：

```text
需要移除 dataclass(order=True)；
需要新增 stable-key helper；
需要 frozen compiler metadata；
需要 workspace coordinator registry；
需要限制第二个 CoreRuntime；
需要重写 M1 E2E；
测试数量增加；
文档或目录小调整。
```

---

# 13. 建议内部 Checkpoint

```text
Gate 0-1:
  docs(m1c3): preserve immutable-kernel phase and coordinator blockers

Gate A:
  fix(m1c3): freeze kernel identity and complete template invariants

Gate B-C:
  fix(m1c3): establish phase total order anchor canonicality and lateral contract

Gate D:
  fix(m1c3): enforce one workspace state owner and serialized Access reads

Gate E:
  test(m1c3): close snapshot trace boundary and full end-to-end truth
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
nollm_m1c3_immutable_kernel_phase_workspace_coordinator_20260711_<shorthead>.bundle
```

最终回复必须提供：

```text
branch / HEAD / commits
Gate A-E facts
registry immutability negative matrix
CoverageTemplate direct-constructor negative matrix
mixed-phase state/Recall/Snapshot facts
Anchor canonical order facts
lateral registered-ring facts
workspace state-owner / stale-runtime result
concurrent read consistency result
package test counts
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
多进程 crash transaction 已实现；
远端仓库已拆分。
```

---

# 15. 一句话执行目标

> **把 M1-C2 已建立的九模板、Canonical Evidence 和同进程事务基础，从“默认 fixture 下成立”推进为不可被公开引用改写、对 phase 具有真正全序、对一个 workspace 只有一个状态所有者、且 Access 读取永远不暴露事务中间态的可封板 M1 合同。**
