# Nollm M1：Core Handle、Access 命令映射、真实包抽取与循环依赖清零任务书

**日期**：2026-07-11
**阶段编号**：M1 — Core Current-State / Addressed Handle / Access Command Boundary Extraction
**状态**：M0-C1 通过系统审核后的唯一下一任务
**基线 Bundle**：`nollm_m0c1_ownership_port_regression_closure_20260711_f62c21a7.bundle`
**基线 Bundle SHA-256**：`14b34b56245bcd862eae99cacedd098fe3d0e03048e50b058516f07122f65023`
**基线 HEAD**：`f62c21a72e416f80b9f4baf6eaa613c91257fc81`
**建议分支**：`codex/m1-core-handle-access-command-extraction`
**主环境**：Windows 10/11 + PowerShell
**执行方式**：大跨度任务 + 内部 Gate + 失败就地修复 + 最终单一 Git bundle
**交付目标**：形成可独立测试的 `nollm-core`、`nollm-access`、`nollm-snapshot`、`nollm-trace` 活动路径；清零当前生产模块违规与循环依赖；旧 GRF 混合实现降为兼容/迁移资产。

---

# 0. M0-C1 接受结论与 M1 定位

M0-C1 已闭合 M0 审核发现的五个硬阻断：

```text
1. relation_field.py 不再被误标 DELETE_LATER；
2. field_engine.py 不再被虚报为纯 Core HIGH；
3. Manifest V2 的 MOVE/HIGH/BLOCKED/DELETE 语义可由机器验证；
4. Snapshot / Trace Port 已绑定真实 GRF 行为；
5. 当前模块化架构回归测试已替代“V2 唯一活动架构”旧断言。
```

M0-C1 最终事实：

```text
Manifest tracked coverage = 1328 / 1328
Manifest generator --check = read-only
M0 tests = 18 passed
real Snapshot/Trace tests = 4 passed
architecture/no-forbidden/hygiene = 8 passed
boundary production findings = 9 reviewed, 0 new
production cycles = 1 reviewed SCC, 0 new
grf tests = 112 passed on recorded Windows environment
external audit = 109 passed, 1 skipped, only 2 zstandard-dependent tests unavailable
working tree = clean
```

因此 M0 可以标记：

```text
NOLLM_M0_MODULE_SEPARATION_ACCEPTED_CANDIDATE
```

但这不表示实际包边界已经完成。当前仍有：

```text
9 条真实 production boundary findings；
1 个 ACCESS / CORE / SNAPSHOT / TRACE 强连通分量；
真实 Core 行为仍主要位于 reference/python/nollm/grf 混合命名空间；
Access package 仍为空骨架；
旧 Facade 仍暴露 deterministic/place 与 ID/source Recall 兼容路径；
旧 GRFFileStore 仍混合 Evidence、Geometry、Trace、Recall 和 Snapshot 责任。
```

M1 的唯一目的：

> **把已经确认的正确几何能力抽取为语义盲、地址化、无全局关系索引的真实 Core；把 Capture、Evidence、LLM/Host PlacementDecision、历史策略和 Recall 格式化放入 Access；用 Addressed Handle 建立唯一受支持的 Core 操作方式；清零生产依赖违规和循环。**

---

# 1. 开工前最高约束

Codex 开始前必须依次读取：

```text
docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
AGENTS.md
本任务书
docs/architecture/module-ownership/M0C1_BOUNDARY_REVIEW.md
docs/architecture/modules/NOLLM_CORE_CHARTER.md
docs/architecture/modules/NOLLM_ACCESS_CHARTER.md
docs/architecture/modules/NOLLM_SNAPSHOT_CHARTER.md
docs/architecture/modules/NOLLM_TRACE_CHARTER.md
```

并在根目录 `AGENTS.md` 更新当前阶段：

```text
- Current stage is M1 Core/Access extraction and cycle removal.
- Do not resume OpenClaw Live, model calls, or corpus execution.
- Core operations require addressed handles; no global atom-id lookup.
- Core Recall accepts explicit geometry entry cells only.
- Access owns semantic decisions and evidence/source mapping.
- Old GRF compatibility code may remain only outside active distributions.
- Do not remove a legacy implementation until a tested replacement exists.
- Production boundary target for M1 is zero violations and zero cycles.
```

若旧实现、旧测试或旧任务书与第一性原理冲突：

```text
回到第一性原理；
不得以兼容性保留错误主路径；
兼容入口只能是薄转换或薄 re-export；
错误实现可保留在 Legacy/Lab，但不得进入活动 Distribution。
```

## Gate 0 PASS

```text
第一性原理和本任务书已读取；
AGENTS 已更新；
没有恢复 OpenClaw Live / LLM Corpus / 远端拆仓；
没有把 M1 偷换成产品功能阶段。
```

---

# 2. 明确非目标

M1 不做：

```text
真实 OpenClaw Plugin 激活；
真实 llm-task / OpenAI / 外部模型调用；
MemoryStatement Formation Corpus；
Statement Placement Corpus；
模型质量评测；
自动 duplicate / revision / stitch 判断；
History 产品实现；
Audit 产品实现；
用户、租户、权限系统；
Web/API/CLI 产品；
PB/1M 规模长压测；
多 GitHub 仓库拆分；
远端 push / PR；
Graph / Vector / Embedding 主路径；
新的外置关系索引；
Evidence Capsule / Merkle / 供应链安全框架；
重写所有历史 V2 / GRF 测试。
```

M1 可以保留：

```text
旧 GRF tests 作为迁移回归；
旧 Facade 作为 Legacy compatibility adapter；
旧对象格式作为导入 fixture；
旧 deterministic placement 作为明确标记的 Lab baseline；
旧 source/ledger/evidence 文件用于迁移验证。
```

但它们不得进入：

```text
nollm-bare
nollm-minimal
新 nollm-access 活动 API
新 nollm-core 活动 API
```

---

# 3. Gate 1：保全基线与建立 M1 真值记录

从完整 Bundle 克隆后执行：

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git log -12 --oneline --decorate
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py
```

记录到：

```text
docs/project/M1_STARTING_STATE.md
```

必须写明：

```text
baseline HEAD = f62c21a72e416f80b9f4baf6eaa613c91257fc81
production findings = 9
production cycles = 1
migration dependencies = 44
M0C1 branch/status
```

禁止：

```text
git reset --hard
git clean -fd
回退到 76eb10dc 或 6c3a9230
覆盖暂停的 Corpus 结果
修改 remote refs
```

## Gate 1 PASS

```text
M0-C1 四个提交和暂停 checkpoint 完整；
基线数字可复现；
工作树干净或已有修改已单独保全。
```

---

# 4. M1 目标依赖图

最终活动生产依赖必须严格为：

```text
nollm-core        -> Python stdlib only
nollm-snapshot    -> nollm-core public ports
nollm-trace       -> nollm-core Trace contracts
nollm-access      -> nollm-core public API
                    + optional nollm-snapshot public API
nollm-history     -> skeleton only; no M1 production behavior
nollm-audit       -> skeleton only; no M1 production behavior
nollm-openclaw    -> migration asset only; no live activation
nollm-distribution-> composition metadata only
nollm-lab         -> may depend on all public modules and Legacy
```

M1 Final Gate 必须达到：

```text
production_violations = 0
cycles_production = []
new production violations = 0
new production cycles = 0
```

不得通过以下方式伪造清零：

```text
把仍在活动 Distribution 的实现改标 LEGACY；
把有业务逻辑的入口标为 Distribution metadata；
删除依赖检查；
降低 confidence 来隐藏活动依赖；
把旧混合 Facade 继续作为新 Minimal Runtime 入口；
把 relation/index 主路径移到 Access 后继续使用。
```

---

# 5. Gate 2：建立真实 `nollm-core` 公共合同

## 5.1 建议文件结构

```text
packages/nollm-core/src/nollm_core/
  __init__.py
  geometry.py
  atom.py
  handle.py
  bridge.py
  command.py
  state.py
  recall.py
  storage.py
  ports.py
```

具体文件可小幅调整，但职责必须保持。

## 5.2 Core 最小对象

### `GeometryAddress`

字段：

```yaml
profile_id: str
chart_id: str
layer: int
q: int
r: int
phase: str | null
```

要求：

```text
整数坐标；
稳定排序键；
canonical mapping；
可直接计算文件/partition 路径；
不得带 source / user / history / confidence。
```

可从现有 `CellAddress` 抽取或薄 re-export，但活动定义必须位于 `nollm-core`。

### `MemoryAtom`

字段仅允许：

```yaml
atom_id: str
payload_utf8: str
```

禁止字段：

```text
source_ref
created_at
revision_of
truth
trust
confidence
importance
user
session
model
prompt
history
placement_reason
```

`payload_utf8` 是 Core 语义盲 payload，不表示 Core 判断其为事实。

### `AtomHandle`

字段：

```yaml
geometry_address: GeometryAddress
local_atom_id: str
```

要求：

```text
Handle 是 Core 写、改、删、移的唯一定位入口；
调用方必须持有并保存 Handle；
Core 不提供 get_by_global_id；
Core 不维护 atom_id -> address 全局路由；
Core 不从 source/session/topic 解析位置。
```

### Bridge 对象

Core 只接受已经由 Access 提供的明确几何锚点：

```yaml
GeometryAnchor:
  anchor_id: str
  cells: tuple[GeometryAddress, ...]

BridgeSpec:
  bridge_id: str
  from_anchor: GeometryAnchor
  to_anchor: GeometryAnchor
  weight_q16: int
  bridge_class: weak | normal | strong
  max_steps: int
  max_fanout: int
```

Core Bridge 对象不得包含：

```text
evidence_refs
source refs
LLM reason
witness type
accepted_by
accepted_at
truth/trust
```

这些属于 Access 的 StitchDecision/History/Audit。

## 5.3 Core Command

提供明确命令或职责等价 API：

```text
put(atom, target_cell) -> AtomHandle
remove(handle) -> MemoryAtom
replace(handle, new_payload_utf8) -> AtomHandle
move(handle, target_cell) -> AtomHandle
bridge_add(spec)
bridge_remove(bridge_id)
apply_batch(commands) -> tuple[results, ...]
```

要求：

```text
put 不做语义 duplicate 判断；
replace 不表示 revision；
move 不表示语义重分类；
bridge_add 不判断事实关系；
apply_batch 全部成功或全部不生效；
失败不得留下半写状态。
```

## 5.4 禁止 API

活动 Core 不得提供：

```text
get_by_global_id
search_by_source
search_by_topic
search_history
capture
admit
promote
revision
rank_by_importance
semantic_search
embedding_search
find_similar
resolve_entry_by_shard
resolve_entry_by_source
```

## Gate 2 测试

新增：

```text
packages/nollm-core/tests/test_atom_handle_contract.py
packages/nollm-core/tests/test_core_commands.py
packages/nollm-core/tests/test_core_forbidden_surface.py
```

必须验证：

```text
AtomHandle 地址化；
同 atom_id 可在不同独立 Core 实例存在；
没有全局 atom route；
replace/remove/move 必须用 Handle；
MemoryAtom 不出现 Source/History/Audit 字段；
BridgeSpec 无 evidence_refs；
Core package 在仅含自身 PYTHONPATH 时可导入和测试。
```

## Gate 2 PASS

```text
Core public contract 已真实存在；
不是 README-only 或 Protocol-only；
Core API 语义盲；
Handle 是唯一定位方式；
无对象 ID / Source 路由。
```

---

# 6. Gate 3：抽取真实几何当前状态与文件优先状态存储

## 6.1 纯 Core 能力来源

从当前混合实现审查并抽取：

```text
axial.py
eisenstein.py
fixed_point.py
cell_address.py
coverage_template.py
profiles.py
kernel_registry.py
propagation.py
bridge_kernel.py 中纯几何字段
field_engine.py 中 CellStore / density / occupancy
relation_field.py 中 Coverage/Lateral/Bridge 有界传播
recall.py 中有界遍历算法
```

不要整体移动：

```text
PlacementRecord
GeometryMark
EvidenceIsland
LocalPatch 的语义状态
StitchWitness / StitchProposal 的语义接受策略
RecallDigest / source_fallback
GRFFileStore 混合对象存储
GRFLedger
GRFFacade
```

## 6.2 Core CellStore

Core CellStore 只能保存：

```text
GeometryAddress -> local_atom_id -> MemoryAtom
```

允许：

```text
局部 occupancy；
按明确 cell 读取；
按明确 Handle 读取；
按几何邻域读取；
密度状态；
可重建的内存局部 map。
```

禁止：

```text
atom_id -> cell 全局索引；
source -> atom；
patch -> atom；
island -> atom；
identity -> partition route；
object -> related objects；
全局 semantic edge。
```

## 6.3 文件优先状态

实现一个明确的 Core 当前状态事实源，例如：

```text
CoreStateStore
CoreWorkspace
FileCoreStateStore
```

命名可调整，但必须满足：

```text
文件为事实源；
运行时 CellStore 可由文件完整重建；
地址直接决定物理位置或分区；
删除内存缓存后结果不变；
无全局关系索引；
无 Ledger/History/Audit 混入；
原子写入；
apply_batch crash-safe 或至少同卷 staging + replace；
Windows 路径、负坐标、UTF-8 payload 可往返。
```

允许的原型实现：

```text
按 cell/partition 分文件；
或单一 canonical current-state 文件 + 运行时重建。
```

若采用单一状态文件，报告必须明确：

```text
它是 canonical current-state serialization；
不是 object relation index；
M2/PB scale 前需要按几何 partition 拆分；
Recall correctness 不依赖额外 route table。
```

## 6.4 Atomic batch

至少测试：

```text
put + move + replace 同批成功；
中间命令失败时全部回滚；
TraceSink 失败不影响提交；
磁盘写失败模拟时旧 current state 可读取；
重开 Core 后状态一致。
```

## Gate 3 PASS

```text
真实当前状态已进入 nollm-core；
旧 PlacementRecord 不再是 Core occupancy 类型；
Core 可从文件重开；
无全局 identity route；
批处理原子性通过。
```

---

# 7. Gate 4：Core Bounded Recall 只接受几何入口

## 7.1 新 Core Recall 输入

活动 Core 只允许：

```yaml
CoreRecallRequest:
  request_id: str
  entry_cells: tuple[GeometryAddress, ...]
  allowed_kernels: tuple[str, ...]
  budget:
    max_steps: int
    beam: int
    max_layer_delta: int
    max_lateral_ring: int
    max_bridge_steps: int
    max_results: int
```

禁止 Core entry modes：

```text
shard_id
atom_id
placement_id
admission_id
island_id
patch_id
source_window
session_id
topic
text query
```

## 7.2 新 Core Recall 输出

稳定输出只应包含 Core 当前状态事实，例如：

```yaml
CoreRecallItem:
  handle: AtomHandle
  atom: MemoryAtom
  score_q16: int

CoreRecallResult:
  request_id: str
  items: tuple[CoreRecallItem, ...]
  budget_exhausted: bool
```

下列信息不得进入稳定 Core Recall 结果：

```text
source_fallback_ref
EvidenceShard ID
CoverageReport 产品说明
truth/confidence
用户/会话
LLM reason
全局 rejected atom 列表
```

Traversal path、frontier、drift、bridge count 可以通过 Trace 事件输出，不作为稳定业务对象。

## 7.3 传播实现

必须继续满足：

```text
Coverage template lookup；
Cell occupancy；
局部 lateral；
显式 BridgeSpec；
有界 beam / steps / fanout；
确定性排序；
exact profile runtime 无 float / polygon / sin / cos；
无 graph/vector/embedding；
无 object-level relation edge。
```

## 7.4 删除错误主入口

旧 `QueryProbe` 的 ID/source entry modes：

```text
可保留在 Legacy compatibility adapter；
不得被新 Core、Access Minimal Runtime 或 Distribution 调用；
不得在新 package 中复制。
```

## Gate 4 测试

至少包含：

```text
explicit cell direct hit；
coverage up/down；
lateral bounded；
bridge bounded；
beam deterministic；
budget exhausted；
empty cell；
negative coordinates；
删除/禁用任意 cache 后输出一致；
不存在 ID/source entry resolver；
Trace 开关不改变 Recall 结果。
```

## Gate 4 PASS

```text
Core Recall 从 GeometryAddress 进入；
不再从对象 ID/source 进入；
关系由 Cell/Coverage/Bridge 产生；
Core 输出不带 Source fallback。
```

---

# 8. Gate 5：建立真实 `nollm-access` 与 Core 命令映射

## 8.1 Access 最小文件结构

建议：

```text
packages/nollm-access/src/nollm_access/
  __init__.py
  statement.py
  evidence_store.py
  handle_store.py
  placement_contract.py
  commands.py
  runtime.py
  recall.py
  policies.py
```

## 8.2 `MemoryStatement`

Access 对象允许：

```yaml
statement_id: str
content_utf8: str
source_handle: str | null
context_refs: tuple[str, ...]
```

可以有：

```text
source / context / host 物理引用；
但不得用这些引用建立几何关系索引。
```

Access 不得自动判断该 statement 是否真实。

## 8.3 Evidence 保全

实现：

```text
EvidenceStore Protocol
FileEvidenceStore（M1 默认实现）
```

至少支持：

```text
put_original(statement)
get_original(statement_id)
exists(statement_id)
```

要求：

```text
原始 UTF-8 内容可回读；
Evidence 文件与 Core 当前状态分离；
EvidenceStore 不被 Core import；
Access Recall 可从 Core Handle 解析回原始 Evidence；
EvidenceStore 不是语义搜索库；
不建立 topic/entity/vector/graph 索引。
```

## 8.4 Handle Store

Access 可以保存：

```text
statement_id -> AtomHandle
```

但必须明确：

```text
这是调用方持有 Handle 的物理注册表；
只用于明确 mutation/reuse/forget；
不得作为 Recall 主入口；
不得维护相关对象边；
不得由 Core 读取。
```

## 8.5 Placement / Action 合同

定义 Access 决策：

```text
reuse
new
revision_current
revision_keep_history
stitch
unstitch
defer
forget
```

决策必须由外部 Host/LLM/人工显式提供。

禁止：

```text
Python 关键词决定动作；
hash 决定 cell；
固定评分决定 new/reuse/revision；
伪向量判断相似；
AccessRuntime 内自动生成语义决定。
```

建议对象：

```yaml
AccessDecision:
  decision_id: str
  statement_id: str
  action: enum
  target_cell: GeometryAddress | null
  existing_handle: AtomHandle | null
  bridge_spec: AccessBridgeDecision | null
  reason_text: str
  decided_by: host | llm | human | fixture
```

`reason_text` 仅在 Access/Audit；不得传入 Core state。

## 8.6 Access → Core 映射

必须严格实现：

| Access action | Core operation |
|---|---|
| `reuse` | 无写操作；验证显式 Handle 仍存在 |
| `new` | `put` |
| `revision_current` | `replace`，或显式 `remove + put` batch |
| `revision_keep_history` | 旧 Handle 不变；新 statement `put` |
| `stitch` | `bridge_add` |
| `unstitch` | `bridge_remove` |
| `defer` | 无 Core 写操作 |
| `forget` | `remove` |

Core 不知道：

```text
reuse
revision
history
defer
forget
```

## 8.7 Access Recall

Access 接收：

```text
Host/LLM 已选择的 explicit entry_cells；
或调用方保存的 AtomHandle 并显式取其 geometry_address。
```

Access 不得：

```text
按 statement_id 全局搜索相关位置；
按 source_window 选择关系入口；
按关键词/embedding 自动选择入口；
扫描全部 Evidence 进行相似检索。
```

Access 调用 Core Recall 后：

```text
用返回的 AtomHandle / atom_id 找到明确 statement/evidence；
格式化 AccessRecallResult；
提供原始 Evidence fallback；
明确 path/distance 不是真相证明。
```

## Gate 5 测试

至少覆盖：

```text
capture only：Evidence 保存但 Core 不变；
new：put + Handle 保存；
reuse：Core 不写；
revision_current：旧 payload 被替换，语义记录只在 Access；
revision_keep_history：两个 atom 共存；
defer：Core 不变；
forget：用 Handle 删除；
stitch/unstitch：显式几何锚点；
Access Recall：explicit cell -> Core -> Evidence fallback；
不存在 Python semantic decision function。
```

## Gate 5 PASS

```text
Access package 不再是空骨架；
语义决策与 Core 操作已分离；
Evidence 可回到原文；
Core 不 import Access；
Access 不使用 relation index 召回。
```

---

# 9. Gate 6：Snapshot / Trace 绑定新 Core，而不是旧混合 Workspace

## 9.1 Snapshot

保留 M0-C1 公共合同：

```text
ConsistentStatePort
SnapshotService
```

但新增真实新 Core 绑定：

```text
CoreRuntime / CoreStateStore 实现 ConsistentStatePort；
SnapshotService.create/restore/clone/verify/diff 对新 Core 工作；
读冻结必须与 Core mutation 使用同一一致性边界；
不得仅依赖 adapter 实例私有锁而忽略 Core 写锁；
restore 失败不破坏旧 current state。
```

旧：

```text
GRFWorkspaceConsistentStateAdapter
```

可以保留为：

```text
Legacy compatibility adapter
```

但新 `nollm-minimal` 不得依赖它。

## 9.2 Trace

新 Core 实际操作至少发出：

```text
core.put
core.remove
core.replace
core.move
core.batch.begin
core.batch.commit / rollback
core.bridge.add / remove
core.recall.begin / end
core.recall.frontier（internal/experimental）
core.snapshot.freeze / release
```

要求：

```text
stable/internal/experimental 分级；
NullTraceSink 为默认；
普通失败 Sink 不影响结果；
Trace 不进入 Core 文件状态；
删除 Trace 文件不改变 Snapshot / Recall；
Metrics/Jsonl/Memory/Composite 位于 nollm-trace。
```

## Gate 6 测试

在新 Core 路径下比较：

```text
NullTraceSink
MemoryTraceSink
FailingTraceSink
CompositeTraceSink
```

比较：

```text
Core state bytes
AtomHandle
Recall result
Bridge state
Snapshot bytes
重开结果
```

必须一致。

## Gate 6 PASS

```text
Snapshot/Trace 已绑定新 package Core；
旧 GRF adapter 不再是唯一真实绑定；
一致性锁覆盖真实 mutation；
Trace failure 不影响 correctness。
```

---

# 10. Gate 7：处理旧 GRF 混合实现与兼容边界

## 10.1 正确处理方式

对 `reference/python/nollm/grf/**` 逐项选择：

```text
A. 纯实现已移动：旧文件变为薄 re-export；
B. 旧 API 需要迁移：变为 Legacy compatibility adapter；
C. 仅实验/历史：移动或标记为 Lab/Legacy；
D. 已有正确替代且无价值：删除；
E. 尚未迁移：保持 Legacy/Quarantine，不进入活动 Distribution。
```

不得：

```text
复制两套活动 Core；
旧路径继续承担正确性主路径；
兼容入口包含业务逻辑；
新 package 反向 import reference/python/nollm/grf；
为通过边界检查只改 Manifest owner。
```

## 10.2 必须退出活动路径的旧行为

```text
GRFFacade.place 的任何 Python semantic/deterministic 默认策略；
QueryProbe 的 shard/source/island/patch/admission ID Core entry；
GRFFileStore 对 Core/Evidence/Trace/Recall 的混合所有权；
GRFLedger 被 Access/Core 直接依赖；
OpenClaw adapter 直接构造 Core private 几何对象；
source_window -> placement 关系入口；
任何 identity -> partition relation route。
```

可以保留为 Lab baseline，但必须满足：

```text
目录或 Manifest 明确 LEGACY/LAB；
新 distributions 不引用；
文档明确不是 accepted runtime；
测试名称明确 compatibility/baseline。
```

## 10.3 Compatibility re-export

凡旧 import 继续支持：

```text
登记 packages/COMPATIBILITY_REEXPORTS.md；
文件只允许 imports、aliases、__all__、deprecation note；
不得含状态、I/O、算法、判断或持久化；
新增机器测试检查无业务逻辑。
```

## Gate 7 PASS

```text
活动 Core/Access 全部来自 packages；
旧 GRF 路径不进入 Minimal/Bare；
兼容层为薄层；
错误主路径仅可作为 Legacy/Lab。
```

---

# 11. Gate 8：清零九条生产违规和生产循环

M0-C1 冻结的九条真实债务：

```text
1. relation_field.py CORE -> ACCESS placement
2. field_engine.py CORE -> ACCESS placement
3. replay.py SNAPSHOT -> ACCESS storage
4. replay.py SNAPSHOT -> TRACE ledger
5. storage.py ACCESS -> TRACE ledger
6. facade.py ACCESS -> TRACE ledger
7. openclaw_bridge.py OPENCLAW -> CORE cell/recall
8. integrations/adapters/grf7r_facade_runtime.py OPENCLAW -> CORE canonical bytes
9. 上述边构成 ACCESS / CORE / SNAPSHOT / TRACE SCC
```

M1 必须通过真实抽取解决，而不是只更新 Baseline。

执行流程：

```powershell
python tools/check_module_boundaries.py --report docs/architecture/module-ownership/M1_BOUNDARY_REPORT.json
```

人工核对：

```text
production_violations = 0
cycles_production = []
```

仅在确认新活动 Distribution 和 package imports 正确后，才允许：

```powershell
python tools/check_module_boundaries.py --write-baseline
```

并生成：

```text
docs/architecture/module-ownership/M1_BOUNDARY_CLOSURE.md
```

说明每条旧债务如何解决、替代路径是什么、旧文件当前状态是什么。

## Gate 8 PASS

```text
生产违规为 0；
生产循环为 0；
不是通过 owner 降级伪造；
活动包可独立测试。
```

---

# 12. Gate 9：发行组合切换到新活动包

更新：

```text
distributions/nollm-bare/manifest.json
distributions/nollm-minimal/manifest.json
distributions/nollm-debug/manifest.json
distributions/nollm-audited/manifest.json
distributions/nollm-openclaw/manifest.json
```

M1 要求：

### `nollm-bare`

```text
只依赖 nollm-core；
可执行 put/remove/replace/move/bridge/recall；
无 EvidenceStore、Snapshot implementation、Trace implementation、Access。
```

### `nollm-minimal`

```text
nollm-core
nollm-snapshot
nollm-access
默认 NullTraceSink
FileEvidenceStore
```

### `nollm-debug`

```text
nollm-minimal
nollm-trace
selected Lab inspectors（不进入生产依赖）
```

### `nollm-audited`

M1 只更新组合声明：

```text
nollm-minimal
nollm-trace
nollm-audit skeleton
```

不得在 M1 实现完整 Audit。

### `nollm-openclaw`

继续标记：

```text
adapter migration asset
live activation paused
requires future OpenClaw E2E
```

不得引用旧 GRFFacade 作为正式 runtime。

## Gate 9 PASS

```text
Bare/Minimal 指向新包；
旧混合 GRF 不在活动组合；
OpenClaw 仍暂停；
Distributions 无业务逻辑。
```

---

# 13. Gate 10：端到端最小验证

在 `lab/nollm-lab/m1/` 或等价 Lab 路径建立一个不调用模型的显式决策验证：

```text
1. Access capture 原始 statement；
2. 人工 fixture 提供 action=new + explicit target_cell；
3. Access 映射 Core.put；
4. 保存 AtomHandle；
5. Core explicit-cell Recall；
6. Access 回到原始 Evidence；
7. action=revision_current；
8. Core.replace；
9. Snapshot create；
10. 继续 move / bridge；
11. Snapshot restore；
12. Recall 回到快照时状态；
13. FailingTraceSink 下重复，结果一致；
14. action=defer 不修改 Core；
15. action=revision_keep_history 保留两个 atom。
```

另建负例：

```text
按 atom_id 请求 Core 全局查找 -> API 不存在或明确拒绝；
按 source_window 请求 Core Recall -> 明确拒绝；
Access decision selected_cell 未提供 -> 拒绝；
Access 尝试自动 hash placement -> 测试扫描失败；
Bridge 超预算 -> 拒绝；
Batch 中间失败 -> 状态不变；
Source/Evidence 缺失 -> Access 返回明确 fallback error，不伪称 Core 无记忆。
```

报告：

```text
docs/validation/M1_CORE_ACCESS_EXTRACTION_REPORT.md
```

必须区分：

```text
已验证事实；
兼容层；
保留的 Legacy；
未实现能力；
M2/OpenClaw 前置条件。
```

## Gate 10 PASS

```text
最小 Capture -> Explicit Decision -> Core -> Recall -> Evidence 链可运行；
全程无模型、无语义模拟、无关系索引；
Snapshot/Trace 可组合；
历史策略只在 Access。
```

---

# 14. Manifest 与文档同步

更新：

```text
MODULE_OWNERSHIP_MANIFEST.json/.csv
M0_BOUNDARY_BASELINE.json -> M1 zero-debt baseline
README.md
ARCHITECTURE.md
ROADMAP.md
AGENTS.md
docs/project/NOLLM_CURRENT_STATUS.md
packages/COMPATIBILITY_REEXPORTS.md
```

Manifest 必须如实表达：

```text
新 package 文件为 ACTIVE/HIGH，依赖闭合；
旧薄 re-export 有明确 compatibility 证据；
旧混合实现为 LEGACY/LAB/MIGRATION_ASSET；
DELETE 仅在已有正确替代且代码证据完整时使用；
没有 HIGH + MOVE + PENDING；
UNCLASSIFIED = 0。
```

当前状态文档必须写明：

```text
M1 establishes package-level Core/Access behavior.
OpenClaw Live and LLM corpora remain paused.
M1 does not prove LLM placement quality.
Physical GitHub split remains deferred.
```

---

# 15. 独立测试 Gate

至少建立：

```text
packages/nollm-core/tests/**
packages/nollm-snapshot/tests/**
packages/nollm-trace/tests/**
packages/nollm-access/tests/**
```

每个 package 必须可在最小 PYTHONPATH 下独立运行。

PowerShell 示例：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

$env:PYTHONPATH = "$PWD/packages/nollm-core/src"
python -m pytest -q packages/nollm-core/tests

$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src"
) -join ";"
python -m pytest -q packages/nollm-snapshot/tests

$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-trace/src"
) -join ";"
python -m pytest -q packages/nollm-trace/tests

$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-access/src"
) -join ";"
python -m pytest -q packages/nollm-access/tests
```

禁止独立测试偷偷加入：

```text
reference/python
legacy
integrations/openclaw
experiments/grf
```

除专门 compatibility gate 外，新 package tests 不得 import 旧 GRF。

---

# 16. Final Gate

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
python tools/check_module_boundaries.py

python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests
python -m pytest -q packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests

python -m pytest -q reference/python/tests/m0
python -m pytest -q reference/python/tests/test_no_forbidden_features.py reference/python/tests/test_architecture_language.py reference/python/tests/test_repository_hygiene.py
python -m pytest -q reference/python/tests/grf

python lab/nollm-lab/m1/run_m1_minimal_e2e.py

git diff --check
git status --short
```

若当前环境仅缺少 `zstandard`：

```powershell
python -m pytest -q reference/python/tests/grf `
  --ignore=reference/python/tests/grf/test_grf7r2_evidence_pack.py `
  --ignore=reference/python/tests/grf/test_grf7r3_compact_evidence.py
```

报告必须同时记录完整 Windows 环境结果或明确说明未验证原因。

---

# 17. Final Gate 必须满足的事实

只有全部满足，才能输出：

```text
NOLLM_M1_CORE_ACCESS_BOUNDARY_ACCEPTED_CANDIDATE
```

条件：

```text
1. Core public API 位于 packages/nollm-core；
2. Access public API 位于 packages/nollm-access；
3. AtomHandle 使用 GeometryAddress + local_atom_id；
4. Core 无 global atom/source/topic lookup；
5. Core Recall 只接受 explicit geometry entry_cells；
6. MemoryAtom 无 source/history/audit/semantic 字段；
7. EvidenceStore 位于 Access，原始 Evidence 可回读；
8. Access 决策由外部显式提供，不由 Python 推断；
9. Access action 到 Core command 映射完整；
10. CellStore 不依赖 PlacementRecord；
11. RelationField 不依赖 Access 对象；
12. Core Recall 输出不含 source_fallback；
13. Snapshot 绑定新 Core 一致性锁；
14. Trace failure 不影响新 Core；
15. apply_batch 原子；
16. 文件事实源可重开；
17. production_violations = 0；
18. cycles_production = []；
19. Bare/Minimal distributions 不引用旧 GRF runtime；
20. 旧错误主路径仅为 Legacy/Lab/compat；
21. 新 package tests 可独立运行；
22. GRF 主要回归保持；
23. OpenClaw Live / 模型调用 / Corpus 未启动；
24. 远端 GitHub 未拆分；
25. 工作树干净；
26. 最终只交一个完整历史 Git bundle。
```

---

# 18. 真实停止条件

只有以下情况可以停止并回到外部审查：

```text
1. Core 无法在不使用 global identity/source route 的情况下正确 Recall；
2. CellStore 必须依赖 PlacementRecord / Evidence / Source 才能工作；
3. Access/Core 解耦必须引入 graph/vector/embedding；
4. 文件当前状态无法实现原子 batch；
5. Snapshot 一致性必须把 History/Audit 写入 Core；
6. 旧兼容行为无法从活动 Distribution 移除；
7. 生产循环无法在不重新设计模块架构时清零；
8. 需要真实 OpenClaw/LLM 才能验证基础命令映射；
9. 大规模环境失败无法定位；
10. 第一性原理与模块化修正书发生无法协调的直接冲突。
```

不要因以下问题停止：

```text
文件名；
目录小调整；
测试数量；
文档措辞；
兼容 warning；
非关键性能不漂亮；
Prototype 状态文件尚未 PB 分片；
旧 GRF 某个 Lab 测试需要薄适配；
日志事件命名小差异。
```

这些应在任务内修复或记录 limitation。

---

# 19. 建议内部 Checkpoint

允许但不强制：

```text
Gate 0-2:
  docs(m1): establish core/access extraction contracts

Gate 3-4:
  refactor(m1): extract addressed core state and geometry recall

Gate 5-6:
  feat(m1): implement access command mapping and real port binding

Gate 7-9:
  refactor(m1): retire mixed runtime from active distributions

Gate 10-Final:
  test(m1): close cycles and validate minimal end to end
```

每个 checkpoint 后：

```text
记录 Gate facts；
内部自检；
通过后直接继续；
不等待外部审查。
```

---

# 20. 最终交付

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
nollm_m1_core_handle_access_command_extraction_20260711_<shorthead>.bundle
```

最终回复只需提供：

```text
branch
HEAD
commit list
Gate summary
production boundary count
production cycle count
package test counts
GRF regression result
known limitations
bundle filename
bundle SHA-256
```

不得声称：

```text
OpenClaw 已接入；
LLM Placement 已验证；
Memory Quality 已证明；
PB 级已完成；
GitHub 已拆仓；
History/Audit 已产品化。
```

---

# 21. 一句话执行目标

> **把 Nollm 从“已画出模块目录、但正确行为仍混在旧 GRF 命名空间”推进到“Core 通过地址化 Handle 维护文件优先几何当前状态，Access 显式映射外部语义决定，Snapshot/Trace 真实组合，生产依赖和循环全部清零”的可运行模块化基线。**
