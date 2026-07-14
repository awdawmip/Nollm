# Nollm CAOLD 自适应多尺度 Surface Recall 任务书

**任务文件名**：`NOLLM_CAOLD_ADAPTIVE_SURFACE_RECALL_TASK_20260714.md`  
**日期**：2026-07-14  
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**可验证结果**：

```text
删除全部持久MemoryCursor和显式cluster anchor入口
→ Core从Canonical Cell/Coverage构建Order 0/1/2聚合Surface
→ Access仅依据几何规模和固定预算选择Active Surface
→ 真实LLM分页观察并通过CoverageDown逐层选择入口
→ Gateway重启
→ 新Session重新找到既有Alpha与Office记忆
→ NONE正常
→ 新MemoryStatement至少可通过同一Surface路径完成一次Placement
→ 插件保持启用
→ Statement、Handle、Core和既有用户数据不清空
```

**输入代码Bundle**：`nollm_caold_real_geometric_cluster_loop_20260714_a515ae77.bundle`  
**输入Bundle SHA-256**：`b2f4d2f11fb6c916e52826fda1c7feebec9db73096a876798564ecc39dd62c2b`  
**输入分支**：`codex/caold-real-geometric-cluster-loop`  
**输入HEAD**：`a515ae778888ec76ec258ff51e53ee283501dd9b`  
**输入能力Tag**：`REAL_OPENCLAW_GEOMETRIC_CLUSTER_LOOP_VALIDATED_AT_a515ae778888ec76ec258ff51e53ee283501dd9b`  
**当前路线书**：`NOLLM_ROUTE_BOOK_V3_6_ADAPTIVE_MULTI_SCALE_SURFACE_20260714.md`  
**路线书 SHA-256**：`04093e0b84425f267198f85d59df7fd196243e570381072bf6e82a7623bd7ed1`  
**建议工作分支**：`codex/caold-adaptive-surface-recall`  
**主执行环境**：Windows 10/11、PowerShell、当前真实OpenClaw环境  
**交付要求**：所有真实进展提交；最终工作树干净；仓库外生成并验证单一完整历史Git Bundle  
**插件最终状态**：保持安装和启用  
**数据最终状态**：既有Statement、Handle、Core Cell/Atom、Bridge和历史工作区保留；旧Cursor只备份后删除  
**能力结论边界**：验证有限的动态多尺度Surface导航与无Cursor跨会话Recall；不宣称大规模性能、完整多物理层Placement、Stitch、发布、封板或完整安全。

---

# 0. 任务推进向量

```text
任务推进向量：
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
保留Core确定性几何、Coverage、有限Recall和真实OpenClaw链路；
删除Host持久入口、MemoryCursor、cluster_anchor和new_cluster身份路径；
建立多阶内部Aggregation、预算约束Active Surface和真实LLM Scale Scan；
证明删除Cursor后跨Session仍可重新发现和使用旧记忆。

范围变化：
V3.6成为当前活动路线；
V3.5、V3.5 Rev.1、Anchorless任务、Aggregation Surface旧任务和旧Stitch任务降为历史；
Physical Memory Layer、Aggregation Order、Active Surface和Locality正式分离；
本任务不扩展Bridge/Stitch，不以公开GeometryAnchor作为Surface入口。
```

## 0.1 各内部Gate的向量复述要求

每个Gate开始时在任务报告记录：

```text
当前预计向量：
C +10 | S 0 | T 0 | A +10 | H 0 | U 0 | O +10 | L +5 | D +5
当前主方向：
多阶聚合 → 动态表面 → LLM尺度导航 → 无Cursor跨Session Recall。
```

每个Gate结束时记录：

```text
当前实际偏差；
是否新增受影响模块；
是否出现超过5%的模块偏差；
是否需要更新任务范围和向量。
```

不得静默把Snapshot、Trace、History、Audit或Stitch加入实现范围。

---

# 1. 活动依据与优先级

开始执行前必须按以下顺序读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/project/NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md
3. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_3_SEMANTIC_MEMORY_TOOL_20260712.md
4. docs/project/NOLLM_PROJECT_BOOK_V3_4_CORE_FUNCTION_PRIORITY_20260713.md
5. 新加入仓库的 NOLLM_ROUTE_BOOK_V3_6_ADAPTIVE_MULTI_SCALE_SURFACE_20260714.md
6. docs/project/NOLLM_CURRENT_STATUS.md
7. docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
8. 本任务书
9. 受影响模块章程
10. 根目录 AGENTS.md
```

冲突处理：

```text
最高原则 > V3.1稳定模块边界 > V3.3语义记忆修订
> V3.4核心功能优先 > V3.6动态Surface路线
> 当前状态 > 本任务变化量 > 历史任务和报告。
```

以下文件不得覆盖V3.6：

```text
NOLLM_ARCHITECTURE_AMENDMENT_V3_5_ANCHORLESS_SURFACE_NAVIGATION_20260714.md
NOLLM_ARCHITECTURE_AMENDMENT_V3_5_REV1_INTERNAL_AGGREGATION_SURFACE_20260714.md
NOLLM_CAOLD_ANCHORLESS_SURFACE_TRAVERSAL_TASK_20260714.md
NOLLM_CAOLD_AGGREGATION_SURFACE_TASK_20260714.md
NOLLM_CAOLD_REAL_STITCH_LOOP_TASK_20260714.md
```

它们仅作历史推理参考。

---

# 2. 输入代码锚点与已验证基线

## 2.1 Git基线

```text
Branch:
  codex/caold-real-geometric-cluster-loop

HEAD:
  a515ae778888ec76ec258ff51e53ee283501dd9b

Tag:
  REAL_OPENCLAW_GEOMETRIC_CLUSTER_LOOP_VALIDATED_AT_a515ae778888ec76ec258ff51e53ee283501dd9b

Bundle:
  nollm_caold_real_geometric_cluster_loop_20260714_a515ae77.bundle

Bundle SHA-256:
  b2f4d2f11fb6c916e52826fda1c7feebec9db73096a876798564ecc39dd62c2b
```

开工时必须核验：

```text
git bundle verify；
git fsck --full；
HEAD准确；
工作树状态；
最近提交；
Tag指向；
输入Bundle SHA-256。
```

## 2.2 已验证自动回归

`a515ae7`外部审核已复现：

```text
Core                               39 passed
Snapshot                            7 passed
Trace                               3 passed
Access                             66 passed
OpenClaw Python                    36 passed
OpenClaw Node                      15 passed
M0                                 45 passed
Architecture / hygiene              8 passed
Geometry parity                    9 / 9
Core capability                   25 / 25
Minimal E2E                       passed
Manifest                         1769 / 1769
Unclassified                       0
Production violations              0
Production cycles                 []
```

## 2.3 已验证真实能力

必须保留：

```text
真实OpenClaw普通聊天；
真实LLM Formation；
真实LLM从有限candidate_id选择Placement；
Access确定性映射GeometryAddress；
多个Cell写入；
真实revision_current；
失败原子回滚；
duplicate reuse；
similar-distinct new；
两个局部几何区域；
per-entry lateral ring-1 Core Recall隔离；
Gateway重启；
新Session隐藏Recall；
主代理自然使用；
NONE/无注入；
OpenClaw只依赖Access；
插件保持启用；
旧工作区和用户数据保留。
```

## 2.4 当前错误或临时路径

必须在本任务退出生产主路径：

```text
MemoryCursor；
memory_cursor.json；
session cursor；
agent/profile cursor；
cluster_anchors；
entry_cells持久入口提示；
cursor_source；
local_anchor = anchors[-1]；
new_cluster；
_allocate_cluster_anchor；
以最近anchor代表当前语义现场；
per_anchor_context作为跨Session正确性入口。
```

## 2.5 本任务冻结但不扩展的资产

以下资产不在本任务中全面重构：

```text
公开GeometryAnchor；
BridgeSpec的from_anchor/to_anchor；
真实Stitch；
Unstitch；
跨簇Bridge导航。
```

规则：

```text
不得把GeometryAnchor用于Surface导航；
不得新增Host可见anchor_id；
不得新增Anchor registry；
不得删除现有Bridge能力；
若相关测试因其他改动受影响，只做最小保持；
R6前另行生成CSTAOLD或相应范围任务进行纯化。
```

---

# 3. 现有资产审视与本任务分类

## 3.1 KEEP：直接保留

### Core

```text
packages/nollm-core/src/nollm_core/geometry.py
packages/nollm-core/src/nollm_core/coverage_template.py
packages/nollm-core/src/nollm_core/kernel_registry.py
packages/nollm-core/src/nollm_core/recall.py
packages/nollm-core/src/nollm_core/state.py
packages/nollm-core/src/nollm_core/storage.py
packages/nollm-core/src/nollm_core/atom.py
packages/nollm-core/src/nollm_core/handle.py
packages/nollm-core/src/nollm_core/command.py
```

保留能力：

```text
GeometryAddress；
canonical stable order；
CoverageUp/Down；
Lateral；
compiled kernel registry；
explicit-entry bounded Recall；
atomic state；
Cell/Atom canonical persistence。
```

### Access

```text
StatementStore；
MemoryStatement；
HandleStore；
AccessRuntime；
new/reuse/revision/move/defer原子映射；
失败回滚；
当前Handle绑定；
有限candidate_id验证思想。
```

### OpenClaw

```text
Hook快速返回；
Dream Agent；
真实Host模型与认证继承；
deliver=false；
ConversationMaterial边界；
Formation JSON韧性；
Placement JSON有限修复；
隐藏Recall注入；
主聊天失败开放；
插件安装、启用和诊断。
```

### Lab

```text
Coverage编译；
compiled template生成；
9/9 Geometry parity；
25维Core capability；
Minimal E2E；
当前真实OpenClaw报告作为历史能力基线。
```

## 3.2 PUREFY：本任务纯化

### Core公共Surface读取面

新增纯几何、只读、语义盲的Surface公共合同。

### Access入口选择

把：

```text
Access owns entry selection
```

纯化为：

```text
Access owns fixed budget policy、Surface投影、LLM选择验证和结果格式；
LLM负责语义入口选择；
Core负责确定性Surface和Coverage展开。
```

### OpenClaw Host状态

只保留：

```text
本次subagent运行内的临时Traversal Stack和correlation。
```

删除跨操作入口状态。

## 3.3 REBUILD：本任务重建

```text
packages/nollm-core/src/nollm_core/aggregation.py
packages/nollm-core/src/nollm_core/surface.py
packages/nollm-access/src/nollm_access/surface.py
packages/nollm-access/src/nollm_access/memory_loop.py
integrations/openclaw/formation-loop/python/nollm_openclaw_formation/memory_loop.py
integrations/openclaw/formation-loop/src/index.ts
OpenClaw Surface Traversal Prompt和Wire合同
```

文件名可按现有风格微调，但职责不得漂移。

## 3.4 DELETE_ACTIVE：从生产活动路径删除

```text
MemoryCursor数据模型；
FileMemoryCursorStore或等价函数；
CURSOR_SCHEMA_VERSION；
_load_cursor；
_load_agent_cursor；
_recall_cursor；
_store_cursor；
_cursor_state；
_cursor_path；
_agent_cursor_key；
cluster_anchors字段；
entry_cells持久字段；
new_cluster动作；
cluster_anchor结果字段；
Cursor配置、诊断和报告字段；
旧Cursor专属测试。
```

历史报告不删除。

## 3.5 MIGRATE_ONCE：一次性处理

```text
备份真实memory_cursor.json；
记录SHA-256和大小；
确认Statement/Handle/Core状态；
删除Cursor文件；
新版本启动后不再生成Cursor；
旧OpenClaw配置删除Cursor相关字段；
不生成新的持久入口表。
```

## 3.6 PAUSE：本任务暂停

```text
History产品；
Audit产品；
新的安全门禁；
发布系统；
大规模Token优化；
语义摘要Anchor；
多物理层写入尺度选择；
真实Stitch/Unstitch；
跨Provider质量矩阵；
长期运行压力。
```

## 3.7 FREEZE_HISTORY：历史保留

```text
旧GRF/OCP路线；
旧Evidence-first流程；
旧Anchor field协议；
旧Cursor真实报告；
V3.5两版纠偏文档；
旧Anchorless/Aggregation/Stitch任务。
```

不得重新激活为生产合同。

---

# 4. 任务开始前模块完成度

V3.6对目标范围重算后的活动基线：

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务是否影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 90% | 高 | Core 39、Geometry 9/9、Capability 25/25；真实多Cell与Recall | 多阶Aggregation、Surface API、缓存重建 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 7 package tests；状态字节合同 | 版本迁移、增量Snapshot | 否，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 3 package tests；Trace不改变状态 | Surface观察事件未定义 | 否，本任务不扩展 |
| ACCESS | `CAPABILITY_VALIDATED` | 85% | 高 | 66 tests；原子revision；候选映射；失败回滚 | 当前入口依赖Cursor/cluster anchor；无Scale Scan | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 未实现，当前暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 未实现，当前暂停 | 否 |
| OPENCLAW | `CAPABILITY_VALIDATED` | 75% | 中高 | 36 Python、15 Node；真实Formation/Placement/Recall | 跨Session正确性依赖Cursor；无动态Surface | 是 |
| LAB | `IMPLEMENTED` | 85% | 高 | Coverage、Parity、Core能力、真实报告 | 缺Order 0/1/2和动态选择验证 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 65% | 中高 | 插件0.5.0启用；Access-only依赖 | 旧Cursor配置和Placement v2合同 | 是 |

说明：

```text
完成度降低不是代码突然退步；
而是V3.6判定Cursor/cluster anchor不能继续计入目标架构能力。
```

---

# 5. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 90% | 100% | +10% | Order 0/1/2聚合、Surface分页、CoverageDown投影、运行时重建 | 单元、Parity、重开、真实Recall | Bridge纯化、多物理层、规模 |
| SNAPSHOT | 50% | 50% | 0% | 无合同变化 | 7 tests和状态字节回归 | 版本迁移 |
| TRACE | 40% | 40% | 0% | 不新增产品Trace合同 | 3 tests和状态隔离 | Surface性能观察后续 |
| ACCESS | 85% | 95% | +10% | 固定预算选择器、SurfaceNavigator、无Cursor Recall、最小Placement连续性 | 单元、跨模块、真实OpenClaw | 完整Surface Placement质量、Stitch |
| HISTORY | 10% | 10% | 0% | 无变化 | 章程回归 | 未实现 |
| AUDIT | 10% | 10% | 0% | 无变化 | 章程回归 | 未实现 |
| OPENCLAW | 75% | 85% | +10% | 真实LLM Scale Scan、无Cursor跨Session、隐藏注入、最小新写入 | Windows Live R1/R2/R3/P1 | 长期成本、其他模型 |
| LAB | 85% | 90% | +5% | Order选择、Coverage下降、重建一致性和Live报告 | 新验证工具和单一报告 | 大规模性能 |
| DISTRIBUTIONS | 65% | 70% | +5% | 新Surface配置、Placement/Recall Wire、插件保持启用 | install/diagnose/restart | 正式版本协商 |

目标值只是预测。即使CORE达到100%，也只表示当前Core章程和本轮V3.6能力，不表示封板。

---

# 6. 所有权与公共合同变化

## 6.1 Core所有权

Core新增并独占：

```text
多阶Aggregation投影；
内部AggregationAnchor；
Surface Order统计；
Surface分页；
CoverageDown projection；
运行时聚合重建；
Surface结构合法性；
canonical几何顺序。
```

Core不得读取：

```text
用户问题；
Statement文本；
Topic；
Source；
Session；
LLM输出；
Token内容；
历史命中。
```

## 6.2 Access所有权

Access新增并独占：

```text
SurfaceBudgetProfile；
根据Core结构统计选择Active Surface；
SurfaceCellView的Statement有限投影；
临时Traversal状态Schema；
LLM选择合法性验证；
多入口Recall结果格式；
前沿扩展编排；
Statement/Handle/Core原子协调。
```

Access不得：

```text
用Python关键词选择Surface Cell；
按查询语义选择Order；
持久化入口；
建立Topic/Source/Entity映射；
引入vector/graph/embedding。
```

## 6.3 OpenClaw所有权

OpenClaw负责：

```text
真实LLM Surface Traversal；
分页模型调用；
CoverageDown逐层选择；
临时operation correlation；
Recall Agent；
隐藏注入；
正常聊天和后台Dream组合。
```

OpenClaw不得：

```text
持久化Surface入口；
保存上次Order；
直接import Core；
直接Provider HTTP；
Python语义选择；
暴露Surface工具给主代理。
```

## 6.4 Lab所有权

Lab负责：

```text
Aggregation数学验证；
Order 0/1/2构造；
Coverage组合；
预算边界；
重建一致性；
fixtures；
真实结果报告。
```

生产模块不得依赖Lab。

## 6.5 Distributions所有权

Distributions只描述：

```text
Surface预算配置；
插件版本；
Wire版本；
组合依赖；
默认模型继承。
```

不得实现选择器或导航逻辑。

---

# 7. Core多阶Aggregation合同

## 7.1 本任务支持范围

本任务至少实现：

```text
Order 0
Order 1
Order 2
```

定义：

```text
Order 0：
  明确SurfacePlane内的当前Canonical occupied Cell投影。

Order 1：
  对Order 0逐Cell应用coverage_up一次后形成的聚合投影。

Order 2：
  对Order 1再次应用coverage_up形成的更粗投影。
```

## 7.2 SurfacePlane

第一版必须显式指定结构Plane：

```text
profile_id
chart_id
phase
base_layer
```

默认Live Plane：

```text
profile_id = eisenstein_exact_v1
chart_id = default
phase = null
base_layer = 0
```

该Plane来自插件/工作区几何配置，不来自查询语义。

本任务不自动在多个物理Memory Layer之间做语义选择。

## 7.3 内部AggregationAnchor

建议私有类型：

```text
_AggregationAnchor
```

字段最低包括：

```text
order；
aggregate_address；
source_plane；
coverage_template_identity；
occupied_member_count；
native_occupancy_count；
aggregate_occupancy_count；
density_q16；
dispersion_q16；
boundary_mass_q16。
```

禁止字段：

```text
topic；
source；
entity；
session；
user；
semantic_name；
cluster_id；
任意Host anchor_id。
```

## 7.4 聚合算法

每个Order的聚合必须：

```text
按source GeometryAddress stable_key处理；
应用KernelRegistry的coverage_up；
使用Q16权重；
对相同target address确定性累积；
对member投影去重；
输出按target stable_key排序；
不读取Atom payload；
不使用Statement hash；
不建立唯一parent。
```

同一源Cell可以贡献给多个粗Cell。

## 7.5 native与aggregate occupancy

Surface Cell必须分别记录：

```text
native_occupancy_count：
  在该实际GeometryAddress直接持有的Atom数量。

aggregate_occupancy_count：
  下层投影形成的加权或计数汇聚。

occupied_member_count：
  参与聚合的下层occupied Cell数量。
```

不得把上层降格为纯索引。

## 7.6 运行时重建

本任务默认使用：

```text
运行时派生或进程内memoization；
不新增持久聚合事实文件。
```

Core mutation、state import和workspace reopen后：

```text
聚合状态必须失效并重建。
```

验收：

```text
关闭Core；
重开；
Order统计、Surface页面和Recall路径一致。
```

若执行中确有性能需要引入物化缓存，必须先更新任务范围；当前任务不得静默增加持久聚合数据库。

---

# 8. Core Surface公共只读合同

建议新增公共不可变类型：

```text
SurfacePlane
SurfaceOrderInfo
SurfaceCellProjection
SurfacePage
CoverageDescentCell
CoverageDescentPage
```

建议新增CoreRuntime方法：

```text
surface_orders(plane, max_order)
surface_page(plane, order, after, limit)
surface_descend(plane, parent_order, parent_address, after, limit)
```

名称可按代码风格调整，但语义必须一致。

## 8.1 SurfaceOrderInfo

最低字段：

```text
plane；
order；
occupied_cell_count；
page_count_hint；
native_atom_count；
aggregate_mass_q16；
max_descent_depth；
overflow。
```

不包含Statement文本。

## 8.2 SurfacePage

最低字段：

```text
plane；
order；
cells；
has_more；
next_after；
```

分页：

```text
严格按GeometryAddress stable_key；
无重复；
无遗漏；
after token只包含几何位置；
token不持久化。
```

## 8.3 surface_descend

从一个已展示的粗Cell向下一Order展开：

```text
Order 2 → Order 1
Order 1 → Order 0
```

结果来自：

```text
CoverageDown或与CoverageUp一致的确定性逆投影；
当前实际occupied投影；
多对多候选；
Coverage weight；
core/halo/boundary flags。
```

不得返回唯一children目录。

## 8.4 Surface不替代Recall

Surface API只用于选择入口。

最终记忆候选仍由：

```text
CoreRecallRequest(entry_cells, allowed_kernels, finite budget)
```

产生。

---

# 9. 动态Active Surface选择器

## 9.1 所有权

选择器属于Access，因为：

```text
Core只提供结构统计；
Access拥有操作预算和Host投影；
OpenClaw不得自行选择初始Order。
```

## 9.2 输入

只允许：

```text
SurfaceOrderInfo；
固定SurfaceBudgetProfile；
每Cell固定预览上限；
每页固定协议成本；
最大Order。
```

禁止：

```text
query文本；
Statement文本；
topic/source/entity；
session；
历史结果；
上次Order；
LLM评分。
```

## 9.3 选择算法

设：

```text
N_k = Order k occupied_cell_count
P_k = ceil(N_k / page_size)
T_k = P_k * page_overhead_units + N_k * cell_preview_units
```

选择：

```text
满足以下条件的最小k：

P_k <= max_pages
N_k <= max_surface_cells
T_k <= max_projection_units
```

最小k表示预算内最细Order。

若无Order满足：

```text
选择hard_max_order；
标记overflow=true；
继续分页；
不得调用语义索引。
```

## 9.4 初始预算Profile

建议：

```text
Recall:
  page_size = 8
  max_pages = 4
  max_surface_cells = 32
  max_projection_units = 固定整数
  selected_entries_limit = 3
  max_descent_depth = 2

Placement:
  page_size = 8
  max_pages = 6
  max_surface_cells = 48
  max_projection_units = 固定整数
  selected_entries_limit = 1
  max_descent_depth = 2
```

数值可根据真实运行小幅调整，但不得加入语义条件。

## 9.5 防索引测试

必须证明：

```text
同一Core状态和同一预算；
不同query文本；
初始Active Surface Order完全相同。
```

还必须证明：

```text
删除运行时聚合对象；
重开；
Order选择完全相同。
```

---

# 10. Access SurfaceNavigator合同

建议新增：

```text
AccessSurfaceNavigator
SurfaceBudgetProfile
SurfaceCellView
SurfaceTraversalState
SurfaceTraversalDecision
LocalityView
SurfaceRecallRequest
SurfaceRecallResult
```

## 10.1 SurfaceCellView

Access把Core几何投影为：

```text
candidate_id；
order；
GeometryAddress；
native_occupancy_count；
aggregate_occupancy_count；
occupied_member_count；
density；
dispersion；
boundary_mass；
has_deeper_locality；
最多固定数量的当前Statement预览；
truncated；
remaining_count。
```

## 10.2 Statement预览硬上限

第一版：

```text
statements_per_surface_cell <= 3
chars_per_statement <= 256
surface_cells_per_page <= 8
```

预览选择：

```text
只取当前Handle绑定；
按Handle canonical order；
不做语义排序；
不读取旧revision；
不读取pending Statement。
```

## 10.3 candidate_id

给LLM的candidate_id只在当前页面/当前operation有效。

不得：

```text
持久化；
跨Session复用；
包含Topic；
作为长期对象ID。
```

## 10.4 临时Traversal State

可以保存：

```text
当前Order；
当前页after token；
已打开Surface Cell；
Coverage下降路径；
返回栈；
本次已选择entry。
```

必须：

```text
仅存在于单次后台subagent operation；
运行结束删除；
不写入工作区；
不跨Session。
```

---

# 11. OpenClaw Surface Traversal Wire

## 11.1 新Wire版本

建议：

```text
nollm_openclaw_surface_traversal_v1
nollm_openclaw_surface_placement_v1
nollm_openclaw_surface_recall_v1
```

旧：

```text
nollm_openclaw_placement_v2
nollm_openclaw_memory_cursor_v2
```

退出活动默认。

## 11.2 导航动作

允许：

```text
continue_page
open_surface_cell
select_entry
request_coarser_surface
return_to_parent
none
defer
```

Placement局部动作：

```text
new_local
reuse
revision_current
move
expand_surface
defer
```

删除：

```text
new_cluster
cluster_anchor
anchor_id
cursor_source
```

## 11.3 LLM约束

LLM只能选择：

```text
当前Prompt已展示的candidate_id；
当前Traversal可达的动作；
当前已有Handle。
```

LLM不得：

```text
生成任意GeometryAddress；
生成内部AggregationAnchor；
跳到未展示Cell；
返回Topic路由；
调用工具；
暴露隐藏推理。
```

## 11.4 模型调用上限

为了防止无限Scale Scan：

```text
Recall总Traversal调用 <= 12
Placement总Traversal调用 <= 16
每层分页不超过预算Profile max_pages
下降深度 <= 2
JSON格式修复和重试继续有限
```

达到上限：

```text
Recall返回NONE/available=false；
Placement defer；
主聊天继续；
不写入污染。
```

---

# 12. 删除MemoryCursor与显式Anchor入口

## 12.1 必须删除的代码

从OpenClaw形成链路删除：

```text
CURSOR_SCHEMA_VERSION
_cursor_path
_agent_cursor_key
_empty_cursor
_validated_cursor
_cursor_state
_load_cursor
_load_agent_cursor
_recall_cursor
_store_cursor
_append_recent
memory_cursor.json读写
```

从Access删除：

```text
cluster_anchors参数
cursor_cells
per_anchor_context
local_anchor = anchors[-1]
cluster_anchor结果
new_cluster候选
_allocate_cluster_anchor
```

## 12.2 数据处理

对真实工作区：

```text
1. 备份memory_cursor.json；
2. 记录SHA-256、大小、session数、agent数；
3. 记录Statement/Handle/Core状态摘要；
4. 删除Cursor文件；
5. 启动新插件；
6. 确认Cursor文件不再生成。
```

不得把Cursor迁移为：

```text
surface hints；
recent cells；
entry seed；
cluster registry；
query cache。
```

## 12.3 跨会话正确性

删除Cursor后：

```text
新Session必须从Active Surface第一页开始；
不能读取上一Session的入口；
不能读取agent最近地址；
不能使用Host语义路由。
```

---

# 13. 最小Surface Placement连续性

虽然主验收是Recall，但删除Cursor后不能让现有Formation→Placement链路失效。

本任务必须完成最小切换：

```text
新MemoryStatement
→ Placement Active Surface
→ 真实LLM Scale Scan
→ 选择已有Locality或expand_surface
→ 原有Access原子Placement
→ Core写入
```

最低Live：

```text
P1：
  一条与Alpha局部相关的新MemoryStatement；
  选择Alpha所在Surface路径；
  最终new_local；
  Core写入；
  无Cursor。

P2：
  一条与现有局部无关的新MemoryStatement；
  完整观察当前Surface；
  选择expand_surface或defer；
  若expand，使用内容无关frontier；
  不创建Cluster对象。
```

P2模型若合理defer：

```text
记录真实结果；
不因模型未扩展而拒绝Bundle；
但不得用Python强制expand。
```

本任务不据此宣称完整Surface Placement质量，下一任务另行强化。

---

# 14. expand_surface合同

## 14.1 含义

```text
现有Surface中没有适合的局部；
从几何前沿开始新的局部生长。
```

它不创建：

```text
Cluster ID；
Root；
Anchor identity；
语义目录。
```

## 14.2 Frontier生成

只允许使用：

```text
当前Surface occupied geometry；
canonical spiral/frontier顺序；
固定最小几何间距；
Coverage合法性；
Cell occupancy。
```

不得使用：

```text
Statement hash；
关键词；
Topic；
Source；
Embedding；
模型语义分数。
```

## 14.3 当前性能限制

允许第一版扫描当前Plane的occupied Cell避免冲突。

报告必须准确写：

```text
存在全Plane几何occupancy扫描；
不存在全局语义或Statement扫描；
该性能问题留到“工作得久”阶段。
```

---

# 15. 真实Windows/OpenClaw验收环境

## 15.1 工作区策略

不得清空旧工作区。

建议：

```text
保留：
  nollm-caold-geometric-v1
  nollm-caold-revision-v5
  其他已有Nollm目录

新建：
  nollm-caold-adaptive-surface-v1
```

新工作区通过：

```text
复制StatementStore、HandleStore和Core canonical state；
不复制Cursor；
不复制持久入口提示。
```

确认复制前后：

```text
Statement数量；
Handle数量；
Core placement_count；
Core state SHA；
Bridge数量。
```

## 15.2 插件最终状态

最终插件：

```text
安装；
enabled=true；
write_mode=statement-store；
模型继承策略保持；
persist_subagent_transcripts=false；
指向adaptive-surface工作区；
Gateway健康。
```

旧数据保留。

---

# 16. 真实Recall主验收

## 16.1 预算验证模式

为了在当前少量数据上真实触发粗Order，可使用一个仅含结构预算的验证Profile：

```text
max_surface_cells设置得足以迫使Order 0不满足；
Order 1或Order 2满足。
```

该Profile：

```text
不读取query；
不包含Topic；
只用于验证动态Order和CoverageDown；
Live结束后可保留为debug validation profile；
生产默认恢复正常预算。
```

## 16.2 R1：Alpha

新独立Session自然提问：

```text
Alpha项目发布前，我还需要关注哪些安排和负责人？
```

必须记录：

```text
初始Active Surface Order；
Order选择输入统计；
Surface页；
真实LLM选择；
CoverageDown路径；
最终entry cells；
per-entry Core Recall；
Recall Agent选择；
隐藏注入；
主代理可见回答。
```

要求：

```text
找到既有Alpha发布窗口、风险评审、负责人等当前记忆；
不依赖Cursor；
不提Nollm；
Office内容不进入最终回答。
```

## 16.3 R2：Office

另一个新Session：

```text
访客到办公室后在哪里登记，咖啡厅几点关闭？
```

要求：

```text
相同Core状态和预算下初始Order与R1一致；
LLM选择不同Surface区域；
找到Office记忆；
Alpha不进入最终回答；
不依赖此前R1入口。
```

## 16.4 R3：NONE

另一个新Session：

```text
太阳系最大的行星是什么？
```

要求：

```text
从Active Surface开始；
LLM选择NONE或Recall Agent最终NONE；
无Nollm记忆注入；
主代理正常回答。
```

## 16.5 重启验证

至少：

```text
写入/复制完成后Gateway重启一次；
R1/R2完成后再重启一次；
重启后重复一个相关查询；
结果仍来自Surface导航；
Cursor文件仍不存在。
```

---

# 17. Query无关Order硬验证

自动和Live报告都必须证明：

```text
R1 query != R2 query != R3 query
Core canonical state相同
Recall budget profile相同
初始Active Surface Order相同
```

若不同：

```text
必须证明差异只来自Core状态或固定budget变化；
任何query文本参与Order选择视为任务失败。
```

---

# 18. 失败与回滚

至少覆盖：

```text
无效Surface candidate_id；
过期page token；
选择未展示Cell；
CoverageDown空结果；
请求超过max descent；
Surface budget overflow；
聚合构建异常；
Core写失败；
Handle写失败；
OpenClaw subagent超时；
JSON无效。
```

要求：

```text
Recall失败开放；
Placement defer或零写入；
新Statement不成为孤立数据；
Core/Handle旧状态不损坏；
不生成Cursor；
下一正常聊天继续；
插件保持启用；
用户数据不清空。
```

---

# 19. 内部Gate与实施工作流

## Gate 0：活动依据切换与保护性Checkpoint

### 开始向量

```text
C +10 | S 0 | T 0 | A +10 | H 0 | U 0 | O +10 | L +5 | D +5
```

### 工作

```text
核验Bundle、HEAD、Tag、clean tree；
读取活动依据与AGENTS；
把V3.6路线书加入docs/project；
把本任务书加入docs/project/tasks；
更新ACTIVE_PROJECT为V3.6 + 本任务IN_PROGRESS；
更新CURRENT_STATUS和Ledger为V3.6重算基线；
把V3.5两版、旧Anchorless、旧Aggregation、旧Stitch标为历史；
备份真实Nollm工作区和Cursor；
形成第一个Checkpoint commit。
```

建议提交：

```text
checkpoint(caold): activate adaptive multi-scale surface route
```

### Gate结束

必须确认：

```text
活动指针唯一；
没有把历史任务写为当前；
真实数据备份可验证；
工作树状态已提交；
向量无新增模块。
```

---

## Gate 1：Core多阶聚合Surface

### 开始向量

```text
C +10主推进；A/O/L/D仍按原方向等待。
```

### 工作

```text
实现Order 0/1/2；
实现内部AggregationAnchor；
实现native/aggregate occupancy；
实现SurfaceOrderInfo；
实现SurfacePage；
实现CoverageDown projection；
实现reopen重建；
不新增持久聚合事实。
```

### 内部Gate

```text
G1.1 Order 0 canonical projection
G1.2 Order 1 single coverage aggregation
G1.3 Order 2 repeated aggregation
G1.4 overlapping coverage and no unique parent
G1.5 surface pagination
G1.6 restart/rebuild identity
```

建议提交：

```text
feat(core): add rebuildable multi-order surface projections
```

### Gate结束

确认：

```text
Core不读取文本；
Order 0/1/2可复现；
缓存/进程重建一致；
Core旧Recall和Bridge回归；
实际C偏差不超过5%。
```

---

## Gate 2：预算约束Active Surface

### 开始向量

```text
C +10 | A +10为当前主推进。
```

### 工作

```text
实现SurfaceBudgetProfile；
实现最细可承受Order算法；
实现overflow；
Placement/Recall固定预算；
证明query无关；
不持久化上次Order。
```

建议提交：

```text
feat(access): select active surface from structural budgets
```

### Gate结束

确认：

```text
相同Core+budget得到相同Order；
query文本未进入函数签名或调用；
无Session/Topic映射；
向量仍为CAOLD。
```

---

## Gate 3：Access SurfaceNavigator与LLM Scale Scan合同

### 开始向量

```text
A +10 | O +10成为当前主推进。
```

### 工作

```text
实现SurfaceCellView；
限制Statement预览；
实现临时Traversal；
实现continue/open/coarsen/return/select/none；
实现CoverageDown逐层导航；
实现多入口Recall；
实现candidate验证。
```

建议提交：

```text
feat(access): expose bounded multi-scale surface navigation
```

### Gate结束

确认：

```text
LLM只能选展示candidate；
无持久Traversal；
Prompt总量有界；
CoverageDown非树；
无Python语义选择。
```

---

## Gate 4：OpenClaw无Cursor切换与Placement连续性

### 开始向量

```text
O +10主推进；A和D同步。
```

### 工作

```text
删除Cursor代码和配置；
新增Surface Traversal Prompt/Wire；
Recall改用Scale Scan；
Placement改用Surface入口；
删除new_cluster；
加入expand_surface；
更新插件版本；
保持真实Dream Agent和隐藏注入。
```

建议提交：

```text
feat(openclaw): replace cursor routing with surface scale scan
```

### Gate结束

确认：

```text
生产代码MemoryCursor=0；
cluster_anchors=0；
new_cluster=0；
memory_cursor.json不会生成；
插件仍能形成、放置和召回；
OpenClaw无Core import。
```

---

## Gate 5：Lab结构验证与Windows真实闭环

### 开始向量

```text
L +5验证C/A/O成果；D +5准备运行组合。
```

### 工作

```text
Order 0/1/2 fixtures；
预算切换fixtures；
query无关验证；
重建一致性；
真实工作区复制；
Cursor删除；
Gateway重启；
R1/R2/R3；
P1和可选P2；
失败继续；
插件和数据保留。
```

建议提交：

```text
test(caold): validate cursor-free adaptive surface recall
```

### Gate结束

确认：

```text
真实LLM从粗Surface下钻；
R1/R2相同初始Order、不同语义入口；
R3 NONE；
Cursor不存在；
至少一次新Placement继续可用；
未补造Live证据。
```

---

## Gate 6：项目回归、状态回填与Bundle

### 开始向量

```text
按实际结果复算全部模块。
```

### 工作

```text
运行完整测试；
更新Manifest；
运行边界检查；
生成单一报告；
更新ACTIVE_PROJECT、CURRENT_STATUS、Ledger；
记录实际向量和偏差；
所有修改commit；
确认clean tree；
生成并验证完整历史Bundle。
```

若完成，允许Tag：

```text
REAL_OPENCLAW_ADAPTIVE_SURFACE_RECALL_VALIDATED_AT_<HEAD>
```

若未完成：

```text
CAOLD_ADAPTIVE_SURFACE_RECALL_IN_PROGRESS_AT_<HEAD>
```

无论哪种均必须交付Bundle。

建议最终提交：

```text
docs(caold): record adaptive surface recall checkpoint
```

---

# 20. 自动测试矩阵

## 20.1 Core独立测试

至少新增：

```text
Order 0只包含Plane内canonical occupied cells；
Order 1通过coverage_up聚合；
Order 2重复聚合；
Q16质量确定性；
同一source参与多个aggregate cell；
无唯一parent；
native/aggregate occupancy分离；
Surface分页无重复遗漏；
after token稳定；
CoverageDown多对多；
Core重开后Surface一致；
mutation后聚合失效；
import state后聚合失效；
Core不读取Atom payload生成Order；
Bridge旧回归通过。
```

## 20.2 Access独立测试

```text
最细可承受Order；
Order 0/1/2边界切换；
overflow；
不同query不影响Order；
不同固定budget可以影响Order；
Surface preview硬上限；
只投影当前Handle绑定；
candidate_id只在operation有效；
LLM不能选未展示candidate；
Traversal深度上限；
Traversal调用上限；
多入口结果稳定去重；
无持久状态；
expand_surface不使用Statement hash。
```

## 20.3 OpenClaw Python测试

```text
无CURSOR_SCHEMA_VERSION；
无memory_cursor读写；
无cluster_anchors；
无new_cluster；
Surface Prompt字段完整；
导航JSON有限修复；
错误candidate不执行；
Recall NONE；
Placement defer；
超时失败开放；
隐藏注入；
OpenClaw不import nollm_core。
```

## 20.4 OpenClaw Node测试

```text
插件Schema含Surface预算；
插件Schema无Cursor配置；
Hook仍快速返回；
Surface subagent deliver=false；
Traversal调用有界；
Recall注入保持隐藏；
Formation/Placement/Recall链路正常；
plugin import check。
```

## 20.5 Lab验证

```text
Geometry parity 9/9保持；
Core capability至少25维保持并增加Surface能力；
Minimal E2E保持；
Order选择结构性；
CoverageDown路径；
重建一致；
Live报告格式。
```

## 20.6 项目级回归

建议命令：

```powershell
python -m pytest packages/nollm-core/tests -q
python -m pytest packages/nollm-snapshot/tests -q
python -m pytest packages/nollm-trace/tests -q
python -m pytest packages/nollm-access/tests -q
python -m pytest integrations/openclaw/formation-loop/tests -q
python -m pytest reference/python/tests/m0 -q

python lab/nollm-lab/m1/run_geometry_parity.py --check
python lab/nollm-lab/m1/run_core_capability_validation.py --check
python lab/nollm-lab/m1/run_m1_minimal_e2e.py --check

python tools/generate_module_ownership_manifest.py
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py

Push-Location integrations/openclaw/formation-loop
npm test
npm run plugin:check
Pop-Location
```

若实际脚本不支持某个`--check`，按脚本帮助调整，并在报告中记录真实命令。

---

# 21. 机器边界Gate

最终必须：

```text
Manifest tracked = Git tracked；
unclassified = 0；
production violations = 0；
production cycles = []；
OpenClaw direct nollm_core imports = 0；
生产代码MemoryCursor = 0；
生产代码cluster_anchors = 0；
生产代码new_cluster = 0。
```

历史文档中的这些字符串允许存在，但必须被分类为历史。

---

# 22. 单一任务报告

只新增：

```text
docs/project/CAOLD_ADAPTIVE_SURFACE_RECALL_REPORT.md
```

最低记录：

```text
输入Bundle/HEAD；
分支和最终HEAD；
预计/实际向量；
全部模块实际完成度；
资产分类执行结果；
删除的Cursor/cluster路径；
备份和数据保留；
SurfacePlane；
Order 0/1/2统计；
预算Profile；
R1/R2/R3初始Order；
LLM逐层路径；
per-entry Core Recall；
隐藏注入；
P1/P2 Placement连续性；
失败回滚；
测试命令和结果；
Manifest和边界；
插件最终状态；
旧工作区保留；
known limitations；
Bundle文件名和SHA-256。
```

不要求：

```text
完整聊天；
隐藏推理；
完整raw trace；
历史Prompt哈希补造；
外围审计包。
```

---

# 23. 状态与进度账回填

完成时更新：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
```

必须记录：

```text
V3.6为活动路线；
当前任务状态；
最终HEAD；
能力Tag或IN_PROGRESS Tag；
实际推进向量；
全部模块实际完成度；
预计与实际偏差；
Cursor/cluster路径已删除或仍残留的位置；
下一候选能力。
```

不得继续写：

```text
Access 100%基于cluster anchor；
跨Session Recall依赖agent Cursor；
下一任务是旧Stitch。
```

---

# 24. Git与Bundle交付

## 24.1 Checkpoint Policy

每个大Gate至少一个提交。

普通代码、测试、文档问题就地修复，不因非架构问题停止。

## 24.2 最终工作树

必须：

```text
git status --short
```

无输出。

## 24.3 Bundle

建议文件：

```text
nollm_caold_adaptive_surface_recall_20260714_<shorthead>.bundle
```

必须在仓库外生成：

```powershell
git bundle create ..\nollm_caold_adaptive_surface_recall_20260714_<shorthead>.bundle --all
git bundle verify ..\nollm_caold_adaptive_surface_recall_20260714_<shorthead>.bundle
Get-FileHash ..\nollm_caold_adaptive_surface_recall_20260714_<shorthead>.bundle -Algorithm SHA256
```

Bundle必须包含完整历史，而非仅当前分支增量。

---

# 25. 完整验收条件

全部同时满足才允许：

```text
REAL_OPENCLAW_ADAPTIVE_SURFACE_RECALL_VALIDATED_AT_<HEAD>
```

条件：

```text
V3.6进入活动依据；
Order 0/1/2存在；
内部Aggregation不读取语义；
Active Surface只按结构预算选择；
相同Core+budget下不同query选择相同初始Order；
Surface分页稳定；
CoverageDown多对多；
真实LLM逐层选择入口；
持久MemoryCursor=0；
显式cluster anchor入口=0；
new_cluster=0；
删除Cursor后Gateway重启；
新Session R1找到Alpha；
新Session R2找到Office；
R1/R2不依赖访问顺序；
R3 NONE；
至少一个新MemoryStatement通过Surface路径成功Placement；
隐藏注入；
主代理自然使用；
无Python语义选择；
无graph/vector/embedding或外置关系索引；
OpenClaw只依赖Access；
插件保持启用；
旧用户数据和旧工作区保留；
所有测试通过或环境限制如实记录；
Manifest和边界通过；
工作树干净；
完整历史Bundle验证通过。
```

---

# 26. 未完成时的合法交付

即使真实LLM没有完成全部Scale Scan，也必须：

```text
提交所有真实代码和测试进展；
工作树clean；
生成并验证Bundle；
报告IN_PROGRESS；
明确已完成和未完成；
插件不清空；
数据不清空；
不补造证据。
```

合法状态：

```text
CAOLD_ADAPTIVE_SURFACE_RECALL_IN_PROGRESS_AT_<HEAD>
```

不允许因为以下原因拒绝交付：

```text
模型选择不理想；
Live窗口不足；
缺少完整聊天；
缺少历史Prompt哈希；
部分真实场景未完成。
```

---

# 27. 明确非目标

本任务不做：

```text
真实Stitch/Unstitch；
GeometryAnchor/Bridge最终公共合同纯化；
History产品；
Audit产品；
安全和攻击门禁；
正式发布；
跨平台发行；
多Provider评测；
PB级性能；
向量、图、embedding；
Topic/Source/Entity索引；
持久Surface cache；
持久Traversal；
语义自动选择Physical Memory Layer；
LLM生成内部Anchor；
删除旧Statement或用户数据。
```

---

# 28. 下一候选能力

本任务通过后，再重新评估：

```text
Surface Placement完整闭环
```

或在Placement连续性已充分验证时进入：

```text
基于多尺度Locality endpoint的真实Stitch
```

下一任务必须重新生成：

```text
任务名称；
推进向量；
全部模块完成度矩阵；
代码锚点；
实际V3.6结果。
```

不得沿用旧Anchor pair Stitch任务。
