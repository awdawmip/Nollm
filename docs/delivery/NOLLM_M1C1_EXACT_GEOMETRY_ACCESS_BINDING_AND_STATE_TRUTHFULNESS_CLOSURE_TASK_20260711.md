# Nollm M1-C1：精确几何、Access 绑定一致性与状态真实性闭合任务书

**日期**：2026-07-11
**阶段编号**：M1-C1 — Exact Geometry / Access Binding / Canonical State Closure
**状态**：M1 Bundle 系统审核未通过后的唯一闭合任务
**输入 Bundle**：`nollm_m1_core_handle_access_command_extraction_20260711_99a3dc84.bundle`
**输入 Bundle SHA-256**：`32ed6ea8d8c8ab20c84962c303b218bd4840027395499a9aabab04fb1f26f438`
**输入 HEAD**：`99a3dc84b5ce6c6afce7808878d27c8be1a19dc3`
**输入分支**：`codex/m1-core-handle-access-command-extraction`
**建议工作分支**：`codex/m1c1-exact-geometry-access-binding-state-closure`
**主环境**：Windows 10/11 + PowerShell
**执行方式**：大跨度任务 + 内部 Gate + 发现问题就地修复 + 最终单一 Git bundle
**阶段目标**：保留 M1 已建立的模块边界和 Addressed Handle，恢复真实 Coverage Template 几何语义，闭合 Access Evidence/Handle 绑定和异常原子性，严格验证 canonical file state，并使零边界报告建立在真实等价替代之上。

---

# 0. 审核结论与本任务定位

M1 Bundle 的 Git、包结构和大部分工程 Gate 完整：

```text
bundle complete history = PASS
working tree = clean
core package tests = 9 passed
snapshot package tests = 3 passed
trace package tests = 1 passed
access package tests = 7 passed
M0 regression = 18 passed
architecture / forbidden / hygiene = 8 passed
GRF regression in external Linux audit = 109 passed, 1 skipped
zstandard-dependent historical tests unavailable = 2
minimal M1 E2E = PASS
reported production violations = 0
reported production cycles = []
```

应保留的 M1 成果：

```text
packages/nollm-core 与 packages/nollm-access 已形成真实代码；
AtomHandle = GeometryAddress + local_atom_id；
Core mutation 不提供 global atom/source/topic lookup；
Core Recall 表面只接受 explicit geometry entry cells；
EvidenceStore 位于 Access；
Snapshot/Trace 已绑定新 Core 一致性锁；
Bare/Minimal manifest 已退出旧 GRF runtime；
OpenClaw Live、模型调用、Corpus、远端拆仓均未启动。
```

但当前不得输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

原因不是文档或测试数量问题，而是五项正确性阻断：

```text
B1. 活动 Core 未迁移既有 Coverage Template/Kernels，反而建立了语义不同的简化几何；
B2. 旧 GRF 被整树降为 Legacy 后才得到 zero-boundary，替代等价性尚未成立；
B3. Core state 解码会强制 int/str 转型并接受重复 cell，文件字节与运行时状态可不一致；
B4. Access 对同一 Handle 的多个 Statement 采用字典序任取，Evidence fallback 可返回错误原文；
B5. Access 在 Core 写成功、HandleStore 写失败时留下半完成状态。
```

M1-C1 只闭合以上问题。不得进入 M2 Corpus、M3 PlacementDecision 模型验证或 OpenClaw Live。

---

# 1. 开工前最高约束

Codex 开始前必须依次读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. 根目录 AGENTS.md
3. docs/delivery/NOLLM_M1_CORE_HANDLE_ACCESS_COMMAND_EXTRACTION_AND_CYCLE_BREAK_TASK_20260711.md
4. 本 M1-C1 任务书
5. docs/architecture/modules/NOLLM_CORE_CHARTER.md
6. docs/architecture/modules/NOLLM_ACCESS_CHARTER.md
7. docs/architecture/modules/NOLLM_SNAPSHOT_CHARTER.md
8. docs/architecture/modules/NOLLM_TRACE_CHARTER.md
```

更新根目录 `AGENTS.md`，至少加入：

```text
- Current stage is M1-C1 exact geometry, binding consistency, and canonical-state closure.
- Preserve the M1 package boundary and Addressed Handle design.
- Do not proceed to M2, OpenClaw Live, real model calls, or corpora.
- Active Core coverage must use authoritative Coverage Templates/Kernels; do not substitute q//2 or q*2 heuristics.
- Access Recall must use an unambiguous canonical Evidence binding; never choose a statement by lexical order.
- Access mutations spanning Core and binding state must be exception-atomic.
- Canonical file state must reject coercion, duplicate cells, unknown profiles, and non-canonical bytes.
- Boundary zero is valid only after functional replacement is proven; owner/lifecycle relabeling alone is forbidden.
```

## Gate 0 PASS

```text
第一性原理、M1 和 M1-C1 均已读取；
AGENTS.md 已更新；
未恢复 graph/vector/embedding、Python semantic placement、OpenClaw Live 或旧 Corpus；
未把本任务扩成 M2/M3。
```

---

# 2. 保全输入现场

从完整 Bundle 克隆，不得 reset、clean 或改 remote refs。

记录：

```text
docs/project/M1C1_STARTING_STATE.md
```

必须写明：

```text
input HEAD = 99a3dc84b5ce6c6afce7808878d27c8be1a19dc3
input bundle SHA-256 = 32ed6ea8d8c8ab20c84962c303b218bd4840027395499a9aabab04fb1f26f438
branch/status/log
package test counts
M0/architecture/GRF counts
production boundary report
five audit blockers
```

## Gate 1 PASS

```text
M0-C1 与 M1 两个提交链完整；
暂停的 OpenClaw/Corpus 历史仍在；
工作树初始状态已保全；
没有回退到 f62c21a7 重新实现 M1。
```

---

# 3. Gate A：恢复权威 Coverage Template / Kernel 几何

## 3.1 当前错误必须删除

当前活动实现中的以下规则不得继续作为 Core 主路径：

```python
coverage_up:
  layer + 1
  q // 2
  r // 2

coverage_down:
  layer - 1
  q * 2
  r * 2
  + lateral ring
```

它与已接受 GRF 几何语义相反且不等价。

外部审核复现：

```text
input cell:
  profile=eisenstein_exact_v1
  layer=3
  q=4
  r=-2

accepted coverage_up:
  layer=2
  offsets=(0,0),(1,0),(0,1)
  normalized Q16 weights=(21846,21845,21845)

current M1 coverage_up:
  one cell only
  layer=4
  q=2
  r=-1

accepted coverage_down:
  layer=4
  offsets=(0,0),(-1,0),(0,-1)

current M1 coverage_down:
  seven cells
  layer=2
  centered near q=8,r=-4
```

因此不得把当前 `geometry.py` 的简化方法仅改名为 template。

## 3.2 权威层方向

保持：

```text
LAYER_INDEX_DIRECTION = finer_with_increasing_index
coverage_up   -> layer_delta = -1
coverage_down -> layer_delta = +1
lateral       -> layer_delta = 0
```

## 3.3 Core 内建立真实纯几何模块

在 `packages/nollm-core/src/nollm_core/` 内建立或迁移：

```text
axial.py
fixed_point.py
profiles.py
coverage_template.py
kernel_registry.py
```

可按代码结构合并，但公共职责必须存在：

```text
Profile registry
CoverageTemplate
KernelEntry
CoverageTemplateCompiler 或等价确定性编译器
KernelRegistry
Q16 normalization/residual
runtime template expansion
bounded lateral expansion
```

必须支持当前已接受 profile：

```text
eisenstein_exact_v1
aligned_baseline_v1
dream_quasi_v1
```

要求：

```text
unknown profile 不得进入活动 Core state 或 Recall；
exact profiles runtime 不得使用 float、polygon、shapely、sin、cos；
template fanout 有硬上限；
权重使用整数 Q16；
同一输入确定性输出；
phase/chart/profile 在地址传播中保持合同语义；
Coverage 不是 parent/fact/truth。
```

## 3.4 Runtime 必须使用 Registry/Template

`CoreRuntime.recall()` 的跨层目标必须来自：

```text
KernelRegistry lookup
→ CoverageTemplate expansion
→ Q16 weighted sparse frontier
```

不得来自：

```text
q // 2
q * 2
硬编码 3/4 权重
按 profile 名称但忽略 profile 规则
```

`allowed_kernels` 仍可保持字符串表面，但必须映射到已注册 kernel。

## 3.5 旧 GRF 处理

活动新包不得 import `reference/python/nollm/grf/**`。

旧纯几何文件可采取：

```text
A. 薄 re-export/adapter；或
B. Legacy 实现保留，但必须有新旧 parity gate，且明确新 Core 是 authoritative。
```

禁止：

```text
两套实现都宣称 active；
只让旧 GRF 测试通过，却不测试新 Core；
把整个旧 GRF 标 Legacy 后宣称几何已迁移。
```

## Gate A 测试

新 Core 独立测试至少覆盖：

```text
三个 profile 的 up/down/lateral；
layer direction；
Q16 normalization；
fanout bound；
negative coordinates；
phase preservation；
unknown profile rejection；
exact runtime source scan：无 float/math/shapely/polygon/sin/cos；
同一输入重复输出一致；
Recall 使用 template 权重，不使用硬编码缩放。
```

在 Lab/compatibility gate 增加：

```text
accepted legacy fixture vs new Core parity
```

至少比较：

```text
profile
source cell
expanded target cells
layer_delta
dq/dr
weight_q16
ordering
```

## Gate A PASS

```text
活动 Core 的 Coverage 语义与已接受模板一致；
up/down 层方向正确；
unknown profile 被拒绝；
新 Core 不依赖 Legacy；
旧 GRF regression 不能替代新 Core parity。
```

---

# 4. Gate B：严格 canonical state 与反强制转型

## 4.1 当前问题

当前 `from_mapping()` 使用：

```python
str(value)
int(value)
```

会导致：

```text
1.5 -> 1
2.25 -> 2
-3.75 -> -3
True -> 1
非字符串对象 -> 字符串
```

当前 `_decode()` 还会接受重复 GeometryAddress，并以最后一个 cell 静默覆盖前一个。

审核已复现：

```text
malformed float-coordinate snapshot accepted
runtime coordinates differ from file coordinates
store.read_bytes() != runtime.state_bytes()

duplicate-cell snapshot accepted
first cell silently discarded
store.read_bytes() != runtime.state_bytes()
```

这违反 File-first、canonical state 和 deterministic replay。

## 4.2 严格类型规则

对所有持久对象实行 exact type validation：

```text
str 字段必须 type(value) is str 且非空；
int 字段必须 type(value) is int；
bool 不得作为 int；
list/tuple 结构必须明确；
未知字段按 schema policy 拒绝或明确忽略，不得无意吞入；
不得用 str()/int() 修复非法输入。
```

至少覆盖：

```text
GeometryAddress
MemoryAtom
AtomHandle
GeometryAnchor
BridgeSpec
Recall budget/request（若可持久）
Core state document
Access Evidence document
Access binding document
```

## 4.3 Core state 结构不变量

导入、重开和 Snapshot restore 前必须完整验证：

```text
schema_version 正确；
state bytes canonical；
profile/registry identity 正确；
GeometryAddress 唯一；
每个 cell 的 local_atom_id 唯一；
bridge_id 唯一；
所有 profile 已注册；
所有整数严格为 int；
没有 duplicate cell last-write-wins；
没有 silent coordinate coercion。
```

如果引入：

```text
kernel_registry_id / profile_registry_version
```

必须进入 canonical state，restore 时验证，防止同一坐标在不同 kernel 语义下被静默解释。

## 4.4 文件与运行时同一性

对任何被接受的状态必须始终满足：

```text
FileCoreStateStore.read_bytes() == CoreRuntime.state_bytes()
```

时点：

```text
初始化后；
每次 batch 后；
import_state 后；
Snapshot restore 后；
reopen 后。
```

`read_document()` 也必须验证 canonical bytes，而不只是 schema_version。

## Gate B 测试

必须加入负例：

```text
float layer/q/r；
bool layer/q/r；
重复 cell；
重复 atom；
重复 bridge；
unknown profile；
非 canonical JSON（空格、键序或缺少结尾规则，按项目 canonical contract）；
非法 UTF-8；
非法字段类型；
restore 失败后旧文件与内存完全不变。
```

## Gate B PASS

```text
非法状态全部 pre-write reject；
接受状态的磁盘、内存、Snapshot 字节一致；
不存在静默转型或 last-write-wins；
File-first 事实源可验证。
```

---

# 5. Gate C：Access Canonical Binding 模型

## 5.1 当前问题

当前 HandleStore 只保存：

```text
statement_id -> AtomHandle
```

反向解析时：

```python
matches = sorted(...)
return matches[0]
```

这会让同一 Handle 的多个 Statement 由字典序决定 Evidence。

审核复现：

```text
Core payload = original evidence
reuse statement = different reuse evidence
Access Recall 返回字典序更小的 reuse statement
```

该结果不是显式策略，而是偶然排序。

`revision_current` 后如果 HandleStore 丢失，当前代码还会回退到：

```python
item.atom.atom_id
```

审核复现：

```text
Core payload = new evidence
fallback statement = original
fallback Evidence = old evidence
fallback_error = None
```

这会把旧原文当成当前 Core payload 的 Evidence，违反 Evidence-first。

## 5.2 建立明确 Binding 对象

将 `FileHandleStore` 升级为职责明确的 BindingStore，或在现有名称下实现等价合同。

建议逻辑对象：

```yaml
HandleBinding:
  handle: AtomHandle
  current_statement_id: str
  supporting_statement_ids: tuple[str, ...]
```

必须维持：

```text
一个 Handle 只有一个 current_statement_id；
一个 statement_id 最多绑定一个 Handle；
reuse 可增加 supporting statement，但不得用字典序替换 current；
revision_current 显式切换 current_statement_id；
revision_keep_history 为新 Handle 建立新 current；
forget 删除该 Handle 的全部 binding；
反向解析不扫描后任取第一个；
binding 文件可 canonical 重建和严格验证。
```

如采用不同对象设计，也必须消除歧义并满足上述语义。

## 5.3 Action 绑定语义固定

### `new`

```text
Core.put
current_statement_id = decision.statement_id
supporting = empty
```

### `reuse`

```text
Core 不写；
验证 explicit Handle；
原 current_statement_id 保持不变；
新 statement 可加入 supporting_statement_ids；
不得改变 Recall 当前 Evidence，除非未来独立显式策略授权。
```

### `revision_current`

```text
Core.replace；
current_statement_id 切换为新 statement；
旧 current 不再作为 current；
是否保留为 supporting 必须由当前 M1-C1 固定策略明确，不得偶然处理。
```

推荐 M1-C1 简化策略：

```text
旧 Evidence 文件保留；
旧 statement 从该 Handle 的 active binding 中移除；
History 产品语义仍延后。
```

### `revision_keep_history`

```text
旧 Handle/binding 不变；
新 Core.put；
新 Handle/current binding。
```

### `forget`

```text
Core.remove；
删除 Handle 的 current/supporting bindings；
Evidence 原文是否物理删除不由 Core 决定，M1-C1 默认保留。
```

## 5.4 Recall Evidence 规则

Access Recall 必须：

```text
以 HandleBinding.current_statement_id 解析当前 Evidence；
不得按 statement 字典序选择；
不得在 binding 缺失时直接用 atom_id 猜 Evidence；
current binding 缺失 -> binding_missing；
Evidence 文件缺失 -> evidence_missing；
Core payload 与 current Evidence 不一致 -> evidence_payload_mismatch；
不得返回不匹配的原文且 fallback_error=None。
```

可选输出 supporting ids，但不得冒充当前 Evidence。

## 5.5 Decision 合同去歧义

每个 action 必须拒绝与其无关或冲突的字段，例如：

```text
new + existing_handle
reuse + target_cell
revision_current + target_cell（除非明确采用 remove+put move policy）
defer + target_cell/handle/bridge
forget + bridge_spec
stitch + target_cell/existing_handle
```

不得默默忽略冲突字段。

## Gate C 测试

至少覆盖：

```text
一个 Handle 多个 reuse supporting Evidence；
current Evidence 不受 statement_id 排序影响；
revision_current 后 binding 丢失 -> binding_missing，不返回旧 Evidence；
current Evidence 缺失 -> evidence_missing；
payload/Evidence 不一致 -> evidence_payload_mismatch；
forget 清理全部 Handle bindings；
Handle binding 文件 duplicate/current 冲突拒绝；
所有 action 冲突字段拒绝。
```

## Gate C PASS

```text
Access Recall 的 Evidence 选择由显式 binding 决定；
不存在字典序选择；
不存在 atom_id 猜测导致旧 Evidence 冒充当前 Evidence；
reuse/revision/forget 的绑定语义确定。
```

---

# 6. Gate D：Access 跨 Core/Binding 写入异常原子性

## 6.1 当前问题

当前顺序：

```text
Core.put/replace/remove 成功
→ HandleStore.put/remove 失败
→ Access.apply 抛错
→ Core 已改变
```

审核复现：

```text
new action
HandleStore.put raises OSError
Access.apply raises
Core placement_count = 1
```

这会形成无 Binding 的孤立 Core atom，且调用方收到失败。

## 6.2 M1-C1 原子性范围

在可信本地开发环境，至少实现**异常原子性**：

```text
Access.apply 返回成功：Core 与 Binding 同时为新状态；
Access.apply 抛出异常：Core 与 Binding 同时恢复旧状态。
```

本任务不要求：

```text
分布式事务；
数据库；
Event Sourcing；
审计链；
Merkle；
跨机器 crash recovery。
```

可采用：

```text
A. Core pre-state bytes + Binding pre-state bytes，失败时恢复；
B. 同工作区 staged transaction + deterministic rollback；
C. 等价的轻量本地事务协议。
```

不得引入新的关系索引或 Audit 系统。

## 6.3 必须原子的 action

```text
new
revision_current
revision_keep_history
forget
```

`reuse` 仅写 BindingStore，也必须保持文件原子写。

`stitch/unstitch` 只写 Core，沿用 Core atomic command。

`defer` 不写。

## 6.4 失败补偿要求

对故障注入：

```text
BindingStore write fail；
Core write fail；
Core rollback fail（必须显式暴露 fatal consistency error，不能伪称普通失败）；
Binding restore fail；
```

至少保证普通单点异常下：

```text
Core state bytes unchanged；
Binding state bytes unchanged；
Evidence files unchanged；
reopen 后一致。
```

若 crash-atomic 尚未实现，报告必须明确：

```text
M1-C1 proves exception atomicity, not process-crash atomicity across Access/Core files.
```

## Gate D 测试

至少为每个 action 注入：

```text
Core failure before commit；
Binding write failure after Core command；
Binding validation failure；
rollback/restore path；
```

比较：

```text
Core state bytes
Binding bytes
saved handles
Recall Evidence
reopen result
```

## Gate D PASS

```text
普通异常不会留下 orphan atom、stale binding 或 false success；
失败前后 Core/Binding/Evidence 可验证一致；
没有引入重型安全/审计基础设施。
```

---

# 7. Gate E：边界报告真实性与 Legacy 分类收口

## 7.1 当前问题

M1 将：

```text
reference/python/nollm/grf/**
```

整树统一分类为：

```text
LEGACY / MIGRATION_ASSET / QUARANTINE / LOW
```

并修改 checker，使非 `ACTIVE` 的 production-owner 文件退出 production graph。

该机制本身可以支持暂停资产，但当前新 Core 尚未等价替代 Coverage，因此 zero-boundary 结论过早。

此外，generator 中存在两个连续的：

```python
if p.startswith("reference/python/nollm/grf/"):
```

第二个分支不可达，旧的逐文件审查逻辑被整树规则覆盖。

## 7.2 正确闭合方式

M1-C1 必须：

```text
先完成 Gate A-D；
再重新判断旧 GRF 的生命周期；
删除不可达分类分支；
不得仅按目录名证明“已有正确替代”；
每个仍有唯一正确实现价值的纯几何资产必须有迁移/Parity 证据；
错误关系索引和 semantic placement 可继续 Legacy/Lab；
Bare/Minimal 仍不得引用旧 GRF。
```

允许最终 production：

```text
CORE -> stdlib
SNAPSHOT -> CORE
TRACE -> CORE
ACCESS -> CORE (+ optional SNAPSHOT if actual import exists)
```

要求：

```text
production_violations = 0
cycles_production = []
```

但必须增加机器或人工 Gate 证明：

```text
zero is not produced only by lifecycle relabeling；
new active geometry parity passed；
distributions point to new packages；
Legacy files are not imported by active packages；
package tests use minimal PYTHONPATH。
```

生成：

```text
docs/architecture/module-ownership/M1C1_BOUNDARY_CLOSURE.md
```

逐项说明：

```text
哪些旧纯几何能力已迁移；
哪些只保留 compatibility；
哪些旧错误主路径仍为 Lab/Legacy；
为何当前 zero-boundary 是真实替代而非 owner suppression。
```

## Gate E PASS

```text
边界零债务建立在功能替代和 parity 上；
Manifest 无不可达分类逻辑；
旧 GRF 不进入活动发行版；
新 Core 不 import Legacy。
```

---

# 8. Gate F：Snapshot / Trace 回归

Gate A-D 修改后，重新证明：

```text
Snapshot freeze 与 Core mutation 使用同一锁；
Snapshot bytes 包含并验证 geometry/kernel registry identity；
restore 失败不修改旧状态；
Trace failure 不影响 Core、Binding、Snapshot、Recall；
Trace frontier 可反映 template expansion，但不进入稳定业务结果；
删除 Trace 文件不改变 File-first state。
```

比较：

```text
NullTraceSink
MemoryTraceSink
FailingTraceSink
CompositeTraceSink
```

输出必须一致：

```text
Core state bytes
Binding bytes
AtomHandles
Recall result
Bridge state
Snapshot bytes
reopen result
```

## Gate F PASS

```text
精确 Coverage 和 Access transaction 未破坏 Snapshot/Trace 可组合性。
```

---

# 9. Gate G：最小端到端验证升级

更新：

```text
lab/nollm-lab/m1/run_m1_minimal_e2e.py
```

不得创建 M2 Corpus。

最小链必须包含：

```text
1. capture Evidence；
2. explicit new + eisenstein_exact_v1 target；
3. Access -> Core.put；
4. exact template coverage recall；
5. Evidence fallback；
6. explicit reuse，验证 current Evidence 不被 alias 替换；
7. revision_current，验证 canonical binding 切换；
8. revision_keep_history；
9. Snapshot create；
10. move/bridge；
11. restore；
12. Recall 与 Evidence 回到快照状态；
13. FailingTraceSink 结果一致；
14. HandleStore 故障注入，验证无 partial commit；
15. malformed snapshot 拒绝；
16. unknown profile 拒绝；
17. defer 不写。
```

负例必须包含：

```text
ID/source Core entry 不存在；
q//2/q*2 heuristic source scan 不得出现；
unknown profile；
float coordinate；
duplicate cell；
reuse lexical ambiguity；
revision stale Evidence fallback；
BindingStore failure after Core write；
conflicting AccessDecision fields；
bridge/budget bound。
```

报告：

```text
docs/validation/M1C1_EXACT_GEOMETRY_ACCESS_BINDING_STATE_REPORT.md
```

必须分开：

```text
已验证事实；
环境依赖；
Legacy compatibility；
已知限制；
M2 前置条件。
```

---

# 10. 独立测试 Gate

## Core

最小 `PYTHONPATH` 仅包含：

```text
packages/nollm-core/src
```

执行：

```powershell
python -m pytest -q packages/nollm-core/tests
```

必须新增：

```text
test_coverage_template_contract.py
test_profile_registry.py
test_core_recall_exact_geometry.py
test_core_state_strict_validation.py
```

## Snapshot

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src"
) -join ";"
python -m pytest -q packages/nollm-snapshot/tests
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

必须新增：

```text
test_binding_store_invariants.py
test_access_evidence_resolution.py
test_access_exception_atomicity.py
test_access_decision_field_exclusivity.py
```

新 package tests 不得加入：

```text
reference/python
integrations/openclaw
experiments/grf
```

Parity 测试单独放入 Lab/compatibility gate。

---

# 11. Final Gate

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
python tools/check_module_boundaries.py --report docs/architecture/module-ownership/M1C1_BOUNDARY_REPORT.json

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
python lab/nollm-lab/m1/run_m1_minimal_e2e.py
python lab/nollm-lab/m1/run_geometry_parity.py

git diff --check
git status --short
```

若外部环境仅缺 `zstandard`，允许精确排除：

```powershell
python -m pytest -q reference/python/tests/grf `
  --ignore=reference/python/tests/grf/test_grf7r2_evidence_pack.py `
  --ignore=reference/python/tests/grf/test_grf7r3_compact_evidence.py
```

必须记录完整 Windows 结果或明确说明环境未验证项。

---

# 12. M1-C1 接受条件

只有全部满足，才可输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

条件：

```text
1. M1 Addressed Handle 与 package boundary 保留；
2. Core 使用 authoritative Coverage Template/Kernel；
3. coverage_up=-1，coverage_down=+1；
4. 三个已接受 profile 均有独立测试；
5. unknown profile 被拒绝；
6. exact runtime 无 float/polygon/sin/cos；
7. 新旧 accepted geometry parity 通过；
8. Core state 不做 int/str 强制转型；
9. duplicate cell/atom/bridge 被拒绝；
10. 接受状态始终 disk bytes == runtime state bytes；
11. Snapshot restore 严格验证 canonical state；
12. Handle binding 有唯一 current Evidence；
13. reuse 不通过字典序改变 current Evidence；
14. revision_current 不会 fallback 到旧 Evidence；
15. binding_missing/evidence_missing/payload_mismatch 明确区分；
16. Access mutating actions 具备异常原子性；
17. 故障注入后无 orphan atom/stale binding；
18. AccessDecision 冲突字段被拒绝；
19. production_violations = 0；
20. cycles_production = []；
21. zero-boundary 不依赖纯 owner/lifecycle suppression；
22. Bare/Minimal 不引用旧 GRF；
23. 新 packages 不 import Legacy；
24. Snapshot/Trace 组合回归通过；
25. M0、架构和主要 GRF 回归保持；
26. OpenClaw Live、模型、Corpus、远端拆仓未启动；
27. 工作树干净；
28. 最终只交一个完整历史 Git bundle。
```

---

# 13. 明确非目标

M1-C1 不做：

```text
MemoryStatement Formation Corpus；
PlacementDecision Corpus；
真实 LLM；
OpenClaw Live；
语义质量评测；
History/Audit 产品化；
PB/1M 压测；
远端 GitHub 拆仓；
Graph/Vector/Embedding；
全局 relation index；
Evidence Capsule/Merkle/供应链安全；
跨机器分布式事务。
```

---

# 14. 真实停止条件

只有以下情况可停止并回到外部审查：

```text
1. accepted Coverage Template 无法在 nollm-core 独立实现；
2. exact geometry parity 暴露旧已接受语义本身矛盾；
3. Access binding 无法在不建立关系索引的前提下消除歧义；
4. 异常原子性必须引入重型 Event Sourcing/Audit；
5. canonical state 无法在 Windows 文件语义下实现；
6. production boundary 必须依赖旧混合 GRF 才能保持功能；
7. 需要真实 LLM/OpenClaw 才能验证本任务基础合同；
8. 大规模环境故障无法定位。
```

不要因以下问题停止：

```text
文件名；
目录小调整；
测试数量；
文档措辞；
兼容 warning；
旧 GRF 个别测试需要薄 adapter；
非关键性能不漂亮；
当前状态仍为单一 canonical file。
```

---

# 15. 建议内部 Checkpoint

```text
Gate 0-2:
  docs(m1c1): record audit blockers and bind closure rules

Gate A-B:
  fix(m1c1): restore exact coverage kernels and strict canonical state

Gate C-D:
  fix(m1c1): establish canonical access bindings and exception atomicity

Gate E-F:
  refactor(m1c1): make boundary zero truthful and rebind snapshot trace

Gate G-Final:
  test(m1c1): close parity, failures, and end-to-end validation
```

通过内部 Gate 后直接继续，不等待外部审查。

---

# 16. 最终交付

必须：

```text
所有改动 commit；
工作树干净；
Bundle 在仓库外生成；
Bundle 包含完整历史；
验证 Bundle；
文件名包含阶段和 HEAD 短哈希；
只交一个 Git bundle。
```

建议文件名：

```text
nollm_m1c1_exact_geometry_access_binding_state_closure_20260711_<shorthead>.bundle
```

最终回复提供：

```text
branch
HEAD
commit list
Gate A-G summary
exact geometry parity count
package test counts
M0/architecture/GRF regression
production boundary count
production cycle count
known limitations
bundle filename
bundle SHA-256
```

不得声称：

```text
M2 已开始；
LLM Placement 已验证；
OpenClaw 已接入；
Memory Quality 已证明；
PB 级已完成；
History/Audit 已产品化；
GitHub 已拆仓。
```

---

# 17. 一句话执行目标

> **保留 M1 正确的 Addressed Handle 和模块边界，但把“简化几何替代、Evidence 绑定偶然性、文件状态静默转型和 Access 半写”全部闭合，使 zero-boundary 对应真实、可回放、证据一致的几何 Core/Access 基线。**
