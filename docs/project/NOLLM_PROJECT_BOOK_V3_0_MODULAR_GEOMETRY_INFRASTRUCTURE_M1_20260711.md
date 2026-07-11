# Nollm 项目书 V3.0：模块化几何记忆基础设施与 M1 活动架构

**版本**：V3.0
**日期**：2026-07-11
**状态**：当前项目级活动架构
**当前阶段**：M1 — Core Handle / Access Command Boundary Extraction
**当前基线**：M0-C1 Accepted Candidate，HEAD `f62c21a72e416f80b9f4baf6eaa613c91257fc81`

---

## 0. 规范层级

Nollm 后续设计、任务、审核和交付，按以下层级解释：

```text
1. NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
   约束项目目标、禁止路线和防漂移不变量。

2. 本项目书
   解释当前模块所有权、活动架构、阶段状态和演进顺序。

3. 当前阶段任务书
   当前为 NOLLM_M1_CORE_HANDLE_ACCESS_COMMAND_EXTRACTION_AND_CYCLE_BREAK_TASK_20260711.md。

4. 仓库根目录 AGENTS.md、模块章程、依赖防火墙和测试 Gate。

5. 旧 V2、GRF、OpenClaw、任务书和交付记录
   仅作历史、研究或迁移参考，不得反向覆盖活动架构。
```

第一性原理中的架构不变量保持最高优先级；其中与当时阶段绑定的执行顺序，由本项目书和当前任务书更新，但不得违反第一性原理的方向。

---

## 1. 一句话定义

> **Nollm 是一组面向 LLM 长期记忆的可组合几何基础设施：Access/Host 负责理解、证据保全、语义决策和使用策略；Core 只维护语义盲的记忆原子、几何当前状态和有界传播；Snapshot、Trace、History、Audit、Adapter 和 Lab 分别承担自己的状态与工具职责。**

Nollm 不是：

```text
传统数据库；
向量数据库；
知识图谱；
GraphRAG 包装层；
embedding + 几何可视化；
OpenClaw 插件本身；
规定所有用户必须采用同一记忆策略的完整产品。
```

---

## 2. 第一性原理在模块化架构中的准确表达

### 2.1 Evidence first

Nollm **系统整体**必须保全可回到原文的 Evidence，但 Evidence 不再由最小 Core 拥有。

```text
原始 Evidence：Access / Adapter / external EvidenceStore
几何当前状态：Core
语义历史：Access / History
执行轨迹：Trace
操作审计：Audit
```

必须始终成立：

```text
Evidence ≠ Interpretation
Interpretation ≠ PlacementDecision
PlacementDecision ≠ Core geometry state
Geometry position ≠ fact confirmation
Recall path ≠ proof
```

### 2.2 File first

File-first 不是“所有文件都归 Core”，而是：

```text
每个持久模块对自己拥有的状态采用明确、可重建、可验证的文件事实源；
运行时缓存、Lookup、Snapshot 和 Trace 不得冒充其他模块的事实源。
```

### 2.3 Architecture is the Index

关系正确性必须主要来自：

```text
GeometryAddress
Cell occupancy
Coverage template/kernel
局部邻接
显式、可逆的 Bridge/Stitch
有界传播
```

禁止正确性主路径：

```text
object/source/entity -> 倒排索引或 route table -> object -> geometry
```

允许：

```text
地址直接计算 partition；
Cell 自身局部 occupancy；
调用方保存 Addressed Handle；
删除后不影响结果的缓存；
Evidence 文件的最小物理定位器。
```

### 2.4 LLM/Host 决定语义

下列决定由真实 LLM、Host 或人工显式提供：

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

Python/Core/Access Runtime 不得通过关键词、hash、固定评分、伪向量或硬编码答案模拟这些语义决定。

### 2.5 Geometry 不是语义真相

```text
Coverage 不是 parent；
Cell 不是 folder；
Bridge/Stitch 不是事实合并；
距离不是事实关系证明；
位置不是可信度；
Recall 分数不是事实真实性。
```

---

## 3. 模块体系

```text
nollm-core
nollm-snapshot
nollm-trace
nollm-access
nollm-history（可选）
nollm-audit（可选）
nollm-openclaw
nollm-lab
nollm-distributions
```

### 3.1 nollm-core

唯一职责：

```text
维护几何当前状态；
执行确定性、原子的当前状态操作；
按显式几何入口执行有界 Recall。
```

Core 拥有：

```text
GeometryAddress
MemoryAtom(atom_id, payload_utf8)
AtomHandle(geometry_address, local_atom_id)
CellStore / local occupancy
Coverage templates/kernels
Bridge runtime
Bounded Recall
Atomic batch
Current-state file storage
Snapshot Port
Trace/Observability Port
```

Core 不拥有：

```text
原始 Source/Evidence 元数据；
事实真实性；
当前事实或历史事实；
revision 语义；
用户、会话、权限；
LLM、Prompt、模型理由；
Source fallback；
Trace 持久化；
Audit；
全局 ID/source/topic relation lookup。
```

### 3.2 nollm-snapshot

```text
create
restore
clone
verify
structural diff
optional incremental snapshot
```

Snapshot 是几何当前状态的切片，不是语义历史、Trace、Audit 或 Event Sourcing。

### 3.3 nollm-trace

实现可选 Sink 和调试工具：

```text
NullTraceSink
MemoryTraceSink
JsonlTraceSink
MetricsTraceSink
CompositeTraceSink
frontier/cell inspectors
performance summaries
```

Trace 失败不得影响 Core correctness；Trace 数据不得进入 Core 持久状态。

### 3.4 nollm-access

负责“如何使用 Nollm”：

```text
MemoryStatement
EvidenceStore
HandleStore
外部 Placement/Action contract
Access -> Core command mapping
current/history policy
Recall entry selection
Recall result formatting
Evidence fallback
Host/user/session/source policy
```

Access 可以保存 `statement_id -> AtomHandle`，但该注册表只用于明确 mutation、reuse、forget 和 Evidence 回落，不得成为关系召回主入口。

### 3.5 nollm-history

可选模块，负责语义版本链、时间线和产品历史策略。Core 不理解 revision、superseded、latest 或 current truth。

### 3.6 nollm-audit

可选模块，记录 Host、用户、模型、Prompt、外部 Source Handle、Access 决策和 Core 命令结果。Core 不依赖 Audit。

### 3.7 nollm-openclaw

未来语义 Host / Adapter：

```text
typed hooks
session mapping
llm-task
statement formation
placement decision
recall injection
plugin install/update/doctor/logging
```

当前 M1 不激活 OpenClaw Live，不调用真实模型。

### 3.8 nollm-lab

保存：

```text
语料、Gold labels、数学验证、benchmark、stress、迁移工具、故障注入、可视化、兼容性测试和对照 baseline。
```

Lab 可以依赖所有模块；任何活动模块不得反向依赖 Lab。

### 3.9 nollm-distributions

只组装，不实现业务逻辑：

```text
nollm-bare
nollm-minimal
nollm-openclaw
nollm-debug
nollm-audited
```

---

## 4. 依赖方向

活动生产依赖目标：

```text
nollm-core        -> Python stdlib only
nollm-snapshot    -> nollm-core public ports
nollm-trace       -> nollm-core trace contracts
nollm-access      -> nollm-core public API
                    + optional nollm-snapshot public API
nollm-history     -> nollm-access
                    + optional nollm-snapshot
nollm-audit       -> nollm-access
                    + optional nollm-trace / external source store
nollm-openclaw    -> nollm-access
                    + selected public sibling APIs
nollm-distributions -> composition metadata only
nollm-lab         -> may depend on all public modules and Legacy
```

禁止：

```text
Core -> Access/Snapshot/Trace/OpenClaw/Lab
Snapshot -> Access/Trace implementation
Trace -> Access/OpenClaw
Access -> Legacy GRF private implementation
OpenClaw -> Core private objects
Distribution -> business logic
任何生产循环依赖
```

---

## 5. 活动公共合同

### 5.1 Core Handle

```yaml
AtomHandle:
  geometry_address:
    profile_id: str
    chart_id: str
    layer: int
    q: int
    r: int
    phase: str | null
  local_atom_id: str
```

调用方必须保存 Handle。Core 不保证仅凭全局 `atom_id` 找回位置。

### 5.2 Core current-state API

```text
put(atom, target_cell) -> AtomHandle
remove(handle) -> MemoryAtom
replace(handle, new_payload_utf8) -> AtomHandle
move(handle, target_cell) -> AtomHandle
bridge_add(spec)
bridge_remove(bridge_id)
recall(entry_cells, budget, options) -> CoreRecallResult
apply_batch(commands)
```

### 5.3 禁止的 Core API

```text
get_by_global_id
search_by_source
search_by_topic
semantic_search
embedding_search
find_similar
search_history
capture
admit
promote
revision
resolve_entry_by_shard/source/session
```

### 5.4 Access Decision 映射

| Access action | Core operation |
|---|---|
| `reuse` | 不写；验证显式 Handle |
| `new` | `put` |
| `revision_current` | `replace` 或原子 `remove + put` |
| `revision_keep_history` | 保留旧 Handle，再 `put` |
| `stitch` | `bridge_add` |
| `unstitch` | `bridge_remove` |
| `defer` | 不修改 Core |
| `forget` | `remove` |

---

## 6. 当前工程状态

### 6.1 已接受基线

M0-C1 已作为：

```text
NOLLM_M0_MODULE_SEPARATION_ACCEPTED_CANDIDATE
```

已验证：

```text
Manifest tracked coverage = 1328 / 1328
Manifest --check 为只读
M0 tests = 18 passed
real Snapshot/Trace tests = 4 passed
architecture/no-forbidden/hygiene = 8 passed
production boundary findings = 9 reviewed, 0 new
production cycles = 1 reviewed SCC, 0 new
GRF external audit = 109 passed, 1 skipped；2 个 zstandard 环境依赖未运行
working tree = clean
```

基线 Bundle：

```text
nollm_m0c1_ownership_port_regression_closure_20260711_f62c21a7.bundle
SHA-256: 14b34b56245bcd862eae99cacedd098fe3d0e03048e50b058516f07122f65023
HEAD: f62c21a72e416f80b9f4baf6eaa613c91257fc81
```

### 6.2 当前唯一工程任务

```text
NOLLM_M1_CORE_HANDLE_ACCESS_COMMAND_EXTRACTION_AND_CYCLE_BREAK_TASK_20260711.md
```

M1 要完成：

```text
真实 nollm-core / nollm-access 包抽取；
Addressed Handle；
文件优先 Core current state；
显式几何入口 Recall；
EvidenceStore 与 Access 命令映射；
Snapshot/Trace 绑定新 Core；
旧 GRF 混合路径退出活动 Distribution；
production violations = 0；
production cycles = []。
```

### 6.3 M1 明确不做

```text
OpenClaw Live；
真实模型调用；
MemoryStatement/Placement Corpus 长跑；
模型质量评测；
自动语义判断；
History/Audit 产品化；
PB/1M 长压测；
远端 GitHub 拆仓；
Graph/Vector/Embedding 主路径；
Evidence Capsule/Merkle/重复安全框架。
```

---

## 7. 旧实现处理纪律

每项旧资产只能选择：

```text
迁移为活动实现；
薄 re-export；
Legacy compatibility adapter；
Lab baseline；
Quarantine；
在已有正确替代且确认无价值后删除。
```

不得：

```text
复制两套活动 Core；
通过修改 owner 标签伪造边界清零；
旧 GRF Facade 继续作为 Minimal/Bare 入口；
把关系索引移到 Access 后继续作为召回主路；
把 Python semantic placement 改名后保留；
因“不属于 Core”直接删除 Snapshot、Trace、History、Audit、OpenClaw 或 Lab 资产。
```

---

## 8. 发行组合

### nollm-bare

```text
nollm-core
```

### nollm-minimal

```text
nollm-core
nollm-snapshot
nollm-access
NullTraceSink
FileEvidenceStore
```

### nollm-debug

```text
nollm-minimal
nollm-trace
selected Lab inspectors
```

### nollm-audited

```text
nollm-minimal
nollm-trace
nollm-audit skeleton/current implementation
```

### nollm-openclaw

```text
adapter migration asset
live activation paused
requires future real OpenClaw E2E
```

---

## 9. 后续路线（条件式，不提前实施）

```text
M1  Core/Access 抽取、Handle、循环清零
  ↓
M2  MemoryStatement Formation 合同与新 Corpus
  ↓
M3  Statement PlacementDecision 合同、局部上下文和模型验证
  ↓
M4  OpenClaw real LLM Placement E2E
  ↓
M5  无外置关系索引的 Geometry Recall 质量与性能验证
  ↓
M6  接口稳定后再评估物理 GitHub 拆仓
```

每阶段是否启动，以前一阶段接受审核和新的任务书为准。

---

## 10. 协作与交付

```text
主环境：Windows 10/11 + PowerShell
任务规模：大跨度 + 内部 Gate
执行：失败就地修复，除真实架构阻断外不中断主流程
文档：区分已验证事实、合理假设、待确认事项、建议动作
根规则：每阶段更新并遵守 AGENTS.md
交付：完整历史、工作树干净、仓库外单一 Git bundle
不要求：receipt、evidence capsule、Merkle、安全供应链材料
```

---

## 11. 最终表述

> **Nollm 不用外置索引先找到对象再展示几何。Access/LLM 把可回到 Evidence 的记忆内容放到明确几何地址；Core 只用 Cell occupancy、Coverage、局部邻接和显式 Bridge 维护当前关系场并执行有界召回；Snapshot、Trace、History、Audit 和具体 Host 作为独立可组合模块存在。**
