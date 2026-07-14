# Nollm 路线书 V3.6：预算约束的自适应多尺度表面导航

**版本**：V3.6  
**日期**：2026-07-14  
**性质**：当前活动路线修订；统一内部聚合 Anchor、动态 Surface Order、LLM 尺度导航和无 Cursor 跨会话恢复  
**代码审视锚点**：

```text
Bundle:
  nollm_caold_real_geometric_cluster_loop_20260714_a515ae77.bundle

Bundle SHA-256:
  b2f4d2f11fb6c916e52826fda1c7feebec9db73096a876798564ecc39dd62c2b

Branch:
  codex/caold-real-geometric-cluster-loop

HEAD:
  a515ae778888ec76ec258ff51e53ee283501dd9b
```

**活动上位依据**：

```text
1. NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md
3. NOLLM_ARCHITECTURE_AMENDMENT_V3_3_SEMANTIC_MEMORY_TOOL_20260712.md
4. NOLLM_PROJECT_BOOK_V3_4_CORE_FUNCTION_PRIORITY_20260713.md
5. 本路线书 V3.6
```

**被本路线书替代的活动路线**：

```text
NOLLM_ARCHITECTURE_AMENDMENT_V3_5_ANCHORLESS_SURFACE_NAVIGATION_20260714.md
NOLLM_ARCHITECTURE_AMENDMENT_V3_5_REV1_INTERNAL_AGGREGATION_SURFACE_20260714.md
NOLLM_CAOLD_ANCHORLESS_SURFACE_TRAVERSAL_TASK_20260714.md
NOLLM_CAOLD_AGGREGATION_SURFACE_TASK_20260714.md
NOLLM_CAOLD_REAL_STITCH_LOOP_TASK_20260714.md
```

这些文件保留为历史推理记录，不再决定活动实现。

---

# 0. 执行摘要

## 0.1 最终路线结论

Nollm 不应固定从某一物理层或“第一层表面”开始导航。

正确路线是：

```text
Core canonical geometry state
→ 多阶内部 Aggregation Anchor
→ 多个可重建 Surface Order
→ 根据几何规模和操作预算选择 Active Surface
→ LLM 分页观察该 Surface
→ LLM 选择一个或多个粗区域
→ CoverageDown 多对多展开
→ LLM 逐层向细处导航
→ 到达有限 Locality
→ Placement 或 Recall
```

动态 Surface Order 的职责仅是：

> **决定以什么几何分辨率向 LLM 展示当前场。**

它不得决定：

```text
用户问题属于什么主题；
应该进入哪个Surface Cell；
哪个记忆相关；
哪个簇应被召回；
哪个Statement应被放置到哪里。
```

这些语义判断继续由真实 LLM 完成。

## 0.2 防止变成索引的核心定义

动态 Surface Order 不是索引，当且仅当：

```text
1. Order选择不读取用户问题和MemoryStatement文本；
2. Surface完全由Core canonical geometry确定性派生；
3. 每次操作重新计算，不持久化入口答案；
4. 分页顺序只按GeometryAddress；
5. 向下展开只使用Coverage；
6. LLM只能选择当前已展示的candidate；
7. 删除全部聚合缓存后，导航和Recall结果不变；
8. 不存在Topic/Source/Entity/Session→Order/Cell映射。
```

## 0.3 Anchor 的最终边界

保留：

```text
Core内部AggregationAnchor
```

删除：

```text
Host/Access/OpenClaw显式Anchor；
cluster root；
持久MemoryCursor；
session/agent/profile Cursor；
语义anchor_id；
Anchor路由；
以Anchor作为跨会话正确性入口。
```

内部AggregationAnchor是：

```text
Coverage几何汇聚结构；
Surface投影骨架；
可重建派生状态；
Bridge/Stitch内部有限端点。
```

它不是：

```text
语义簇；
目录；
主题；
父节点；
跨会话入口答案；
外置关系索引。
```

---

# 1. 为什么现有路线必须调整

## 1.1 当前已验证成果

当前 `a515ae7` 已经真实验证：

```text
真实OpenClaw普通聊天；
真实LLM Formation；
真实LLM从有限candidate_id选择Placement；
Access确定性映射GeometryAddress；
Core写入多个Cell；
两个局部几何区域；
per-entry lateral ring-1 Recall隔离；
Gateway重启；
新Session隐藏Recall；
主代理自然使用；
失败回滚；
OpenClaw→Access→Core依赖。
```

这些成果必须保留。

## 1.2 当前路线的退化风险

当前实际路径依赖：

```text
cluster_anchors；
MemoryCursor；
local_anchor = anchors[-1]；
new_cluster；
固定layer0/q/r候选；
per-anchor Recall。
```

它在小规模测试中能够工作，但长期会退化成：

```text
Host记住簇入口；
最近Anchor代表当前语义现场；
Anchor丢失后旧记忆难以重新进入；
新记忆只比较最近簇；
Surface没有真正的多尺度入口。
```

这会使几何主路径逐渐变成：

```text
Host入口路由
→ 找到局部
→ 几何做有限传播
```

而不是：

```text
几何多尺度投影
→ LLM自主选择入口
→ 几何局部传播。
```

## 1.3 固定第一层表面也不成立

若固定从最细表面开始：

```text
Surface Cell数随数据量增长；
分页次数线性增长；
LLM每次Placement/Recall重复浏览大量表面；
最终退化为LLM线性浏览几何摘要库。
```

若固定从最粗表面开始：

```text
细节长期被过度压缩；
孤立或低密度记忆容易被淹没；
每次都需要多次下钻；
小数据阶段浪费模型调用。
```

因此必须动态选择：

```text
当前预算内最细、信息损失最小的Surface Order。
```

---

# 2. 五个必须分开的概念

## 2.1 Physical Memory Layer

实际 `MemoryAtom` 和 `Cell occupancy` 所在的几何层。

```text
Layer 0
Layer 1
Layer 2
...
```

规则：

```text
每层都可以拥有原生MemoryAtom；
上层不是纯索引；
下层不是唯一内容层；
Layer编号方向由Profile明确；
不把Layer等同于Aggregation Order。
```

## 2.2 Aggregation Order

内部聚合次数，不等同于物理Memory Layer。

```text
Order 0：
  当前选定物理层的直接观察投影。

Order 1：
  对Order 0进行一次Coverage聚合。

Order 2：
  对Order 1再次聚合。

Order k：
  重复应用确定性Aggregation/Coverage得到的更粗观察层。
```

Aggregation Order可以超过实际物理Memory Layer数量。

## 2.3 Internal Aggregation Anchor

Core内部的几何聚合支点。

建议内部形态：

```text
_AggregationAnchor
```

它由以下内容确定：

```text
profile_id；
aggregate GeometryAddress；
physical layer / aggregation order；
CoverageTemplate identity；
canonical member-cell projection；
materialization version。
```

不包含：

```text
语义名称；
Topic；
Source；
Entity；
Session；
用户；
最近访问；
LLM生成的anchor_id。
```

## 2.4 Surface Projection

某个Aggregation Order的可分页观察投影。

```text
Surface(Order k)
```

包含有限、可公开的几何统计和Access投影后的Statement预览。

## 2.5 Active Surface

一次具体Placement或Recall操作选定的初始观察Surface：

```text
Active Surface = Surface(Order k*)
```

`k*`由几何规模和预算确定，不由语义查询确定。

---

# 3. 动态 Surface Order 的正式算法

## 3.1 输入

Order选择器只允许读取：

```text
Geometry Profile；
各Order的occupied aggregate cell数量；
每页Cell数；
每Cell固定预览预算；
最大页数；
总Token预算；
操作预算Profile；
最大允许Aggregation Order；
Coverage fanout和展开成本统计。
```

禁止读取：

```text
用户问题；
MemoryStatement文本；
Topic；
Source；
Entity；
Session；
模型输出；
历史命中；
最近使用Cell；
Cursor；
语义评分。
```

## 3.2 成本模型

设：

```text
N_k：
  Surface Order k 的occupied aggregate cell数量。

B_cell：
  每个SurfaceCellView的固定预算估计。

B_page：
  每页固定协议开销。

P_k：
  ceil(N_k / page_size)。

T_k：
  P_k * B_page + N_k * B_cell。
```

可加入几何展开成本：

```text
D_k：
  从Order k下降到目标Locality的最大层数或预计展开成本。
```

综合成本：

```text
Cost_k = T_k + λ * D_k
```

第一版可以令：

```text
λ = 0
```

只按Surface展示预算选择，避免过早引入复杂优化。

## 3.3 选择规则

选择满足预算的最细Order：

```text
k* = min {
  k |
  P_k <= max_pages
  and T_k <= token_budget
  and N_k <= max_surface_cells
}
```

如果多个Order满足：

```text
选择k最小者，即最细者。
```

如果没有任何预建Order满足：

```text
继续确定性生成更高Aggregation Order；
直到满足预算；
或达到hard_max_order。
```

达到hard_max_order仍不满足时：

```text
仍从最粗可用Order分页；
不允许转向语义索引；
报告surface_budget_overflow；
允许LLM继续多页遍历或defer。
```

## 3.4 Placement与Recall预算Profile

允许两个固定操作预算：

```text
placement_surface_budget
recall_surface_budget
```

它们只能包含：

```text
page_size；
max_pages；
max_surface_cells；
preview_chars；
max_descent_depth；
selected_entries_limit。
```

不能包含语义规则。

推荐初始值：

```text
Placement：
  page_size = 8
  max_pages = 6
  max_surface_cells = 48
  selected_entries_limit = 1
  max_descent_depth = 4

Recall：
  page_size = 8
  max_pages = 4
  max_surface_cells = 32
  selected_entries_limit = 3
  max_descent_depth = 4
```

具体参数必须由真实运行调整，不写死为永久标准。

---

# 4. 为什么动态Order不是索引

## 4.1 它不回答“去哪里”

Order选择器只回答：

```text
“当前最多应该以多粗的分辨率展示几何？”
```

它不回答：

```text
“Alpha项目在哪？”
“用户偏好在哪？”
“本问题应该进入哪个Cell？”
```

## 4.2 它不读取语义

给定同一个Core状态和同一个预算：

```text
任何用户问题都得到相同初始Surface Order。
```

## 4.3 它不保存入口答案

每次操作：

```text
从Core状态重新计算Order统计；
重新选择Active Surface；
重新从第一页开始。
```

不保存：

```text
query→Order；
query→Surface Cell；
session→Surface Cell；
topic→Surface Cell。
```

## 4.4 它可完全重建

删除：

```text
Aggregation materialization；
Surface page cache；
Order统计缓存。
```

系统仍可从：

```text
Cell occupancy；
Coverage templates；
Bridge state；
current Handle bindings。
```

重建相同Surface和分页结果。

## 4.5 LLM仍然承担入口语义

系统选择尺度后：

```text
LLM必须自己浏览Surface；
自己选择粗区域；
自己决定继续、下钻、返回、NONE或defer。
```

---

# 5. 内部 Aggregation Anchor 设计

## 5.1 内部对象

建议：

```text
_AggregationAnchor
```

字段：

```text
aggregate_address；
aggregation_order；
source_layer；
target_projection_layer；
coverage_template_id；
member_projection_digest；
member_cell_count；
occupied_member_count；
native_occupancy_count；
aggregate_occupancy_count；
density_q16；
dispersion_q16；
boundary_mass_q16；
bridge_endpoint_count；
materialization_version。
```

## 5.2 不持久化完整children目录

不得把：

```text
member_cells
```

当作唯一Canonical目录长期持久化。

允许：

```text
运行时通过Coverage展开；
或物化canonical member projection作为可重建缓存。
```

同一个下层Cell可以参与多个AggregationAnchor。

## 5.3 native与aggregate内容分离

粗Surface Cell可能同时包含：

```text
native_occupancy：
  直接写在该物理层的MemoryAtom。

aggregate_occupancy：
  从更细局部向上汇聚的占用信号。
```

Surface View必须区分二者。

## 5.4 几何统计

允许公开给LLM：

```text
occupied_member_count；
native_statement_count；
aggregate_statement_count；
density；
dispersion；
boundary_mass；
truncated；
has_deeper_locality；
has_bridge_endpoint。
```

这些是几何/数量统计，不是Python语义摘要。

## 5.5 缓存规则

内部聚合缓存可以持久化，但必须：

```text
derived=true；
有Profile/Template/Schema版本；
可以删除；
可以重建；
删除后Recall正确性不变；
写入失败不污染Canonical Core state。
```

---

# 6. Surface View 的有界投影

## 6.1 Core输出

Core只输出：

```text
surface_cell_id；
aggregate GeometryAddress；
aggregation_order；
native_occupancy_count；
aggregate_occupancy_count；
occupied_member_count；
density_q16；
dispersion_q16；
boundary_mass_q16；
has_deeper_locality；
has_bridge_endpoint；
next token。
```

Core不输出Statement文本。

## 6.2 Access投影

Access通过当前Handle绑定提供有限预览：

```text
最多N条当前MemoryStatement；
每条最多M字符；
按确定性Handle顺序；
标记truncated；
标记remaining_count。
```

初始建议：

```text
statements_per_surface_cell <= 3
chars_per_statement <= 256
```

## 6.3 高分散区域

若粗Surface Cell：

```text
dispersion高；
boundary_mass高；
aggregate_occupancy分散；
```

Access可以显示几何标记：

```text
spread = low | medium | high
```

该标记由固定阈值计算，不使用Statement语义。

它只提示LLM：

```text
该区域可能需要继续下钻。
```

---

# 7. LLM 多尺度导航协议

## 7.1 通用动作

```text
continue_page
open_surface_cell
select_entry
request_coarser_surface
return_to_parent
none
defer
```

## 7.2 open_surface_cell

LLM只能选择当前页中已展示的：

```text
surface_cell_id
```

Core通过CoverageDown返回下一Order的候选投影。

## 7.3 CoverageDown不是children

返回：

```text
coverage candidate IDs；
GeometryAddress；
Coverage weight；
core / halo / boundary flags；
occupancy统计。
```

不返回：

```text
唯一parent；
唯一children；
目录路径。
```

## 7.4 request_coarser_surface

LLM可以请求更粗Surface，但只能表达：

```text
“当前层仍过碎。”
```

系统提供更高Order完整投影。

LLM不能同时指定：

```text
“跳到更粗层中的Alpha区域。”
```

## 7.5 return_to_parent

单次操作可以保留临时Traversal Stack：

```text
Surface Order；
selected cell；
page token。
```

运行结束删除，不持久化。

---

# 8. Placement 路线

```text
ConversationMaterial
→ Dream Formation
→ MemoryStatement
→ 计算Active Surface
→ LLM遍历Surface
→ LLM选择open/select/expand/defer
→ CoverageDown逐层导航
→ LocalityView
→ LLM选择new_local/reuse/revision/move/defer
→ Access原子编排
→ Core写入
```

## 8.1 expand_surface

当完整表面无合适局部时：

```text
LLM选择expand_surface。
```

Core/Access提供内容无关frontier candidate。

frontier分配只使用：

```text
GeometryAddress；
occupied aggregate cells；
canonical spiral/frontier规则；
固定最小间距；
Coverage合法性。
```

不得使用：

```text
Statement hash；
关键词；
Topic；
Source；
Embedding。
```

## 8.2 第一阶段写入尺度

本路线第一阶段：

```text
MemoryStatement仍写入当前已验证工作层；
动态Order只用于观察和入口导航。
```

暂不同时让LLM决定写入物理层。

这样可以隔离：

```text
导航尺度问题；
语义存储尺度问题。
```

后续再单独验证跨物理层Placement。

---

# 9. Recall 路线

```text
用户问题
→ 计算Recall Active Surface
→ Surface Recall Agent分页观察
→ 逐层CoverageDown
→ 选择有限entry cells
→ Core per-entry bounded Recall
→ 合并Handle唯一结果
→ Recall Agent选择有用Statement或NONE
→ 隐藏注入主代理
```

## 9.1 多入口

LLM可以选择：

```text
最多2或3个入口。
```

系统保留每个入口的独立Core结果，避免隐藏几何路径。

合并只进行：

```text
Handle唯一化；
固定入口顺序；
Core稳定顺序；
总结果预算截断。
```

Python不做语义排序。

## 9.2 无Cursor跨会话

删除全部：

```text
MemoryCursor；
session cursor；
agent/profile cursor；
recent anchors；
persistent entry hints。
```

每个新Session都从动态Active Surface重新导航。

---

# 10. Scale Selection 的风险与约束

## 10.1 过粗导致细节被淹没

缓解：

```text
选择预算内最细Order；
提供dispersion和boundary_mass；
允许LLM下钻；
允许request finer/open；
限制单Cell预览；
保留native occupancy。
```

## 10.2 重叠Coverage导致重复候选

缓解：

```text
Surface Cell按aggregate GeometryAddress唯一；
CoverageDown结果按candidate ID唯一；
同一Handle在最终Recall时确定性去重；
不强制唯一parent。
```

## 10.3 Order抖动

Core状态微小变化可能导致：

```text
Order 1 ↔ Order 2频繁切换。
```

第一版允许确定性抖动，不持久化滞回状态。

可以使用不含历史状态的固定安全边际：

```text
选择Order时要求预算使用率 <= 80%
```

但不得保存上次Order作为跨操作状态。

## 10.4 聚合缓存不一致

规则：

```text
Template/Profile版本变化时缓存失效；
Core打开时验证物化摘要；
失败则重建；
不允许使用旧缓存继续导航。
```

## 10.5 最粗Order仍过大

处理：

```text
继续生成更高Order；
达到hard_max_order后分页；
允许LLM继续多页；
允许defer；
不启用语义索引。
```

---

# 11. Bridge / Stitch 的位置

Stitch暂不作为下一任务。

正确顺序：

```text
1. 多阶内部AggregationAnchor；
2. 动态Active Surface；
3. LLM逐层导航；
4. 无Cursor跨Session恢复；
5. 再实现真实Stitch。
```

未来Stitch：

```text
LLM分别导航到Locality A和Locality B；
Access提供有限Cell endpoint candidates；
LLM选择endpoint candidate IDs；
Core内部构造AggregationAnchor endpoint；
Core写入Bridge。
```

LLM不选择内部anchor_id。

---

# 12. 现有资产总览

当前仓库Manifest大致包含：

```text
CORE           20项
ACCESS        110项
OPENCLAW      115项
LAB           778项
LEGACY        676项
DISTRIBUTION   54项
SNAPSHOT        6项
TRACE           4项
HISTORY         3项
AUDIT           3项
```

生命周期大致为：

```text
ACTIVE          184
GENERATED        30
MIGRATION_ASSET 539
HISTORICAL     1016
```

现有资产非常庞大，不能把全部历史资产重新纳入活动路线。

本路线采用以下分类：

```text
KEEP_AUTHORITY
KEEP_ACTIVE
PUREFY
REBUILD
MIGRATE_ONCE
DELETE_ACTIVE
PAUSE
FREEZE_HISTORY
RETAIN_BASELINE
```

---

# 13. 现有权威文档分类

## 13.1 KEEP_AUTHORITY

### `docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md`

保留最高原则：

```text
Architecture is the Index；
真实LLM负责语义；
Core负责确定性几何；
无graph/vector/embedding主路径；
错误关系索引必须删除；
核心功能优先。
```

需要修订：

```text
“是否形成新簇”改为“是否进入现有局部或扩展表面”；
目标架构中的固定入口改为动态多尺度Surface；
Evidence fallback旧措辞继续按V3.3解释。
```

### `docs/project/NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md`

保留：

```text
模块所有权；
依赖方向；
Core纯净性；
Access/Host边界；
可演进基线。
```

需要修订：

```text
Access owns entry selection
→ Access owns geometry projection and validates LLM surface choices。

Core explicit-entry Recall
→ Core accepts explicit cells selected through Surface navigation；
Core本身不保存Host entry hints。
```

### `docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_3_SEMANTIC_MEMORY_TOOL_20260712.md`

保留：

```text
MemoryStatement是持久语义单元；
OpenClaw后台Dream Agent；
Nollm是工具而不是语义保证。
```

无需因Surface路线重写核心内容。

### `docs/project/NOLLM_PROJECT_BOOK_V3_4_CORE_FUNCTION_PRIORITY_20260713.md`

保留：

```text
核心功能优先；
真实OpenClaw链路；
暂停外围治理；
成功接入后保持启用和数据。
```

需要替换：

```text
bounded cluster anchors
→ adaptive multi-scale surface navigation。
```

## 13.2 NEW_AUTHORITY

新增本路线书：

```text
NOLLM_ROUTE_BOOK_V3_6_ADAPTIVE_MULTI_SCALE_SURFACE_20260714.md
```

成为当前几何导航与下一阶段调度权威。

---

# 14. Core 资产分类

## 14.1 KEEP_ACTIVE

### `geometry.py`

保留：

```text
GeometryAddress；
canonical order；
lateral；
partition math。
```

需增加：

```text
Aggregation Order和Surface投影使用的稳定排序辅助；
不把Order写入GeometryAddress语义层。
```

### `coverage_template.py`

保留核心：

```text
CoverageTemplate；
KernelEntry；
coverage_up；
coverage_down；
lateral；
固定点权重；
fanout限制。
```

它是多尺度Surface的主要数学基础。

### `kernel_registry.py`

保留：

```text
编译模板加载；
模板身份；
运行时lookup；
摘要校验。
```

需要扩展：

```text
Aggregation Order连续应用；
可用Order统计；
Surface构建所需模板解析。
```

### `recall.py`

保留：

```text
explicit entry cells；
Coverage/Lateral/Bridge有界传播；
确定性结果。
```

不负责：

```text
Surface Order选择；
LLM导航；
语义相关性。
```

### `state.py / storage.py`

保留：

```text
Cell/Atom/Bridge canonical state；
原子写入；
重开；
occupancy；
occupied_cells。
```

需要增加：

```text
surface_info；
surface_page；
surface_children/coverage_down_projection；
aggregation cache rebuild；
cache失效。
```

## 14.2 PUREFY

### `bridge.py`

当前：

```text
GeometryAnchor(anchor_id, cells)
BridgeSpec(from_anchor, to_anchor)
```

处理：

```text
任意字符串anchor_id退出公共合同；
GeometryAnchor从Core __all__移除；
重构为内部_AggregationAnchor或canonical endpoint aggregation；
Bridge持久端点由有限Cell集合/确定性AggregationKey表达；
保留Bridge传播能力。
```

不是完全删除内部Anchor。

### `__init__.py`

移除公开：

```text
GeometryAnchor
```

增加公开：

```text
SurfaceInfo；
SurfacePage；
SurfaceProjectionCell；
LocalityProjection；
或同等最小只读对象。
```

## 14.3 REBUILD

当前Core没有：

```text
多阶AggregationAnchor；
Surface Order统计；
动态Surface projection；
聚合缓存重建。
```

需要新增私有模块，建议：

```text
aggregation.py
surface.py
```

职责：

```text
几何聚合；
Order构建；
Surface分页；
CoverageDown projection；
缓存重建。
```

## 14.4 RETAIN_BASELINE

### `compiled_templates.py`

保留生成结果和9/9 parity。

### Core测试

保留：

```text
几何地址；
Coverage模板；
Recall；
状态；
Bridge；
Core能力验证。
```

重写或删除：

```text
任意字符串GeometryAnchor公共对象测试；
Anchor canonical order公共合同测试。
```

新增：

```text
Order 0/1/2；
动态选择；
缓存删除重建；
CoverageDown多对多；
native/aggregate occupancy；
Bridge内部端点。
```

---

# 15. Access 资产分类

## 15.1 KEEP_ACTIVE

### `statement.py / statement_store.py`

完整保留。

### `handle_store.py`

保留当前绑定合同。

### `runtime.py`

保留：

```text
new/reuse/revision/move/stitch/defer/forget映射；
原子Core/Binding回滚。
```

### `placement_contract.py`

保留有限Wire Schema思想，但需要从：

```text
new_cluster / cluster anchor candidate
```

改为：

```text
surface traversal decision；
local placement decision；
frontier expansion decision。
```

## 15.2 REBUILD

### `memory_loop.py`

当前可复用：

```text
Access-owned Core生命周期；
Statement/Handle/Core组合；
候选ID映射；
失败回滚；
local context投影；
Recall结果映射。
```

必须删除：

```text
cursor_cells；
cluster_anchors；
local_anchor = anchors[-1]；
new_cluster；
_allocate_cluster_anchor；
per_anchor_context；
cluster_anchor返回字段。
```

重建为：

```text
AccessSurfaceNavigator；
surface_info/page；
surface traversal；
coverage descent；
locality context；
frontier expansion；
per-entry Recall；
bounded result merge。
```

## 15.3 DELETE_ACTIVE

### MemoryCursor相关实现

当前主要位于OpenClaw bridge，但Access中的Cursor参数和cluster anchor合同全部删除。

不保留兼容双路径。

## 15.4 RETAIN_BASELINE

现有真实能力测试保留其核心行为：

```text
revision原子性；
duplicate reuse；
similar-distinct new；
Placement失败清理Statement；
多Cell局部隔离。
```

但重写入口：

```text
从Surface导航得到Locality；
不再从Cursor/cluster anchor进入。
```

---

# 16. OpenClaw 资产分类

## 16.1 KEEP_ACTIVE

### Hook与Dream Agent

保留：

```text
message_sent / agent_end阶段区分；
Hook快速返回；
bounded ConversationMaterial；
真实subagent；
deliver=false；
Prompt/Schema；
JSON韧性；
同模型重试；
失败不阻塞主聊天。
```

### Formation流程

保留：

```text
DreamFormation；
StatementStore；
Placement继续链路。
```

### Hidden Recall injection

保留：

```text
回复前Recall Agent；
隐藏上下文；
主代理自然使用；
NONE失败开放。
```

## 16.2 DELETE_ACTIVE

### `memory_loop.py`中的Cursor路径

删除：

```text
_load_cursor；
_store_cursor；
_recall_cursor；
session cursor；
agent cursor；
cluster_anchors；
entry_cells持久化；
cursor_source；
memory_cursor.json。
```

### Placement Prompt中的旧动作

删除：

```text
new_cluster；
cluster_anchor；
anchor/entry cursor。
```

## 16.3 REBUILD

新增：

```text
Surface Traversal Prompt；
Surface Page循环；
open/continue/coarsen/select/none协议；
CoverageDown逐层导航；
多入口Recall；
单次Traversal Stack。
```

单次Traversal状态只在subagent运行中存在。

## 16.4 KEEP_CONFIGURATION

保留：

```text
OpenClaw当前Provider/auth；
inherit/dedicated模型；
P1 JSON Prompt基础；
插件安装/启用/禁用/诊断；
成功后保持启用。
```

新增配置只允许几何预算：

```text
placement_surface_budget；
recall_surface_budget；
hard_max_order；
page_size；
preview limits。
```

不得新增语义路由配置。

---

# 17. Lab 资产分类

## 17.1 KEEP_ACTIVE

### `lab/nollm-lab/geometry/**`

保留：

```text
Coverage编译；
Research profiles；
模板生成；
编译支持。
```

需扩展：

```text
多阶Aggregation Order实验；
Surface规模模拟；
Order选择预算实验；
CoverageDown路径完整性；
缓存重建一致性。
```

### `lab/nollm-lab/m1/run_geometry_parity.py`

保留9/9 parity。

### `run_core_capability_validation.py`

保留，但增加Surface/Aggregation维度时需更新。

## 17.2 RETAIN_BASELINE

真实OpenClaw Formation、Runtime Truth、Revision、Cluster运行记录：

```text
保留为HISTORICAL_RESULT或能力checkpoint；
不作为V3.6入口合同。
```

## 17.3 FREEZE_HISTORY

大量旧：

```text
GRF7/GRF8；
OCP；
V1/V2；
旧OpenClaw provider；
旧Evidence；
旧Anchor field；
旧Corpus；
旧审计receipt。
```

继续保留Git历史，不重新激活。

## 17.4 PAUSE

暂停：

```text
新的大规模语义质量矩阵；
新的安全/攻击实验；
新的发布Gate；
完整长期性能验证。
```

当前Lab只服务：

```text
Aggregation数学；
Surface导航；
真实OpenClaw最小Live；
缓存可重建；
无Cursor跨会话。
```

---

# 18. Distribution 资产分类

## 18.1 KEEP_ACTIVE

保留：

```text
nollm-bare；
nollm-minimal；
nollm-openclaw；
debug组合；
插件安装/诊断；
模型继承配置。
```

## 18.2 REBUILD

OpenClaw配置删除：

```text
cursor path；
cluster anchor limits；
recent entry limits；
new_cluster配置。
```

新增：

```text
placement surface budget；
recall surface budget；
max aggregation order；
Surface preview limits；
aggregation cache mode：
  runtime
  rebuildable-materialized。
```

## 18.3 PAUSE

暂停：

```text
release-ready；
版本协商扩展；
自动更新；
跨平台发布；
新的audited distribution。
```

---

# 19. 历史协议和哲学资产分类

## 19.1 RETAIN_CONCEPT

### `docs/philosophy/architecture-is-the-index.md`

保留概念，更新“files/cards/anchor fields”旧措辞。

### `docs/philosophy/scale-scan-not-tree-descent.md`

高度相关，应升级其核心思想：

```text
Recall是Scale Scan；
不是Tree Descent。
```

但需删除：

```text
active anchor fields
```

改为：

```text
Surface projection + Coverage descent。
```

### `docs/philosophy/layered-honeycomb-memory-field.md`

保留每层皆有信息的原则，更新“当前runtime未实现geometry”过期说明。

## 19.2 FREEZE_HISTORY

### `docs/philosophy/anchor-is-field-not-folder.md`

保留为早期思想来源，但不再作为当前Anchor合同。

其中“不是Folder”的提醒有价值；“Anchor field crossing layers”不再直接决定实现。

### `protocol/ANCHOR.md / ANCHOR_FIELD.md`

冻结历史，不进入当前生产合同。

### `cortex/ANCHOR_COMPOSER.md`

冻结历史。

## 19.3 RETAIN_MATH_REFERENCE

### `NOLLM_GEOMETRY_ARCHITECTURE_AMENDMENT_V2_ATLAS_COVERAGE_KERNELS`

保留：

```text
局部Chart；
双向Coverage；
多对多；
反树；
Anchor外部不可见；
CoverageUp/Down；
Atlas/Gluing。
```

其中与“原始Evidence永久保全”冲突的段落按V3.3解释。

### GRF Coverage与Kernel资产

保留：

```text
Coverage direction semantics；
Kernel normalization；
fixed-point；
fanout bounds；
multi-step coverage；
residual semantics。
```

PlacementIndex、route table等旧关系路径继续冻结。

---

# 20. 数据资产分类与迁移

## 20.1 必须保留

用户真实：

```text
StatementStore；
HandleStore；
Core Atom；
Cell occupancy；
revision当前绑定；
已有Bridge；
OpenClaw插件配置；
当前模型配置。
```

## 20.2 一次性迁移

### Cursor

```text
备份；
删除MemoryCursor文件；
删除session/agent Cursor；
不迁移为其他持久入口表。
```

### Cluster Anchor

当前没有独立Cluster对象文件时：

```text
只删除配置和Wire字段。
```

若持久状态存在：

```text
只保留实际Cell/Handle/Core数据；
不保留cluster identity。
```

### GeometryAnchor / Bridge

若现有Bridge使用任意字符串Anchor：

```text
迁移为内部canonical aggregation endpoint；
保留实际Cell集合和Bridge传播；
移除语义anchor_id。
```

## 20.3 可删除

```text
旧Cursor测试文件；
旧Cursor诊断；
旧cluster anchor Prompt；
旧new_cluster live记录中的活动配置；
过时任务状态文件。
```

历史报告本身保留。

---

# 21. 新目标架构

```text
OpenClaw normal chat
    ↓
Dream Agent
    ↓
MemoryStatement
    ↓
Core computes available Surface Orders
    ↓
Budgeted Adaptive Surface Selector
    ↓
Active Surface(Order k*)
    ↓
Surface Traversal LLM
    ↓
CoverageDown / request_coarser / continue page
    ↓
Finite LocalityView
    ↓
Placement LLM
    ↓
Access atomic orchestration
    ↓
Core Cell write
```

Recall：

```text
User query
    ↓
Core computes available Surface Orders
    ↓
Recall budget selects Active Surface
    ↓
Surface Recall LLM traverses scales
    ↓
Select finite entry cells
    ↓
Core bounded Recall
    ↓
Recall Agent
    ↓
Hidden context injection
    ↓
Main agent natural reply
```

---

# 22. 路线阶段

## 阶段 R0：活动路线切换与资产清理

目标：

```text
V3.6进入ACTIVE_PROJECT；
V3.5/V3.5 Rev.1和旧Stitch任务降级历史；
修正第一性原理、V3.1、V3.4中的入口措辞；
保留a515ae7为局部几何checkpoint。
```

不单独生成外围治理项目；作为下一实现任务的开头完成。

## 阶段 R1：Core多阶聚合骨架

实现：

```text
_AggregationAnchor；
Order 0/1/2；
CoverageUp重复应用；
native/aggregate occupancy；
SurfaceInfo；
SurfacePage；
聚合缓存重建。
```

验收：

```text
缓存删除后Surface一致；
分页稳定；
无语义字段；
Bridge现有能力不回退。
```

## 阶段 R2：动态Active Surface选择

实现：

```text
BudgetProfile；
Order统计；
最细可承受Order算法；
hard max和overflow；
Placement/Recall不同固定预算。
```

验收：

```text
不同问题在相同Core状态/预算下选择相同Order；
不读取文本；
Order 0/1/2切换可复现；
不持久化上次Order。
```

## 阶段 R3：LLM逐层Scale Scan

实现：

```text
Surface Traversal Wire；
continue/open/coarsen/select/none；
CoverageDown多对多；
临时Traversal Stack；
SurfaceCellView有界预览。
```

验收：

```text
LLM从粗层找到目标局部；
无唯一parent；
覆盖重叠可处理；
Prompt有界。
```

## 阶段 R4：删除Cursor的Recall闭环

实现：

```text
删除MemoryCursor；
每个新Session重新Surface导航；
Alpha/Office跨Session恢复；
NONE。
```

验收：

```text
删除Cursor文件；
重启；
新Session仍找到旧记忆；
访问顺序不影响正确性。
```

## 阶段 R5：Surface Placement闭环

实现：

```text
MemoryStatement从动态Surface选择局部；
相关进入已有Locality；
无关expand_surface；
不使用new_cluster。
```

验收：

```text
真实OpenClaw；
真实LLM；
Core写入；
重启；
新SessionRecall。
```

## 阶段 R6：内部端点Stitch

在R1-R5通过后：

```text
两个Locality通过Surface导航分别定位；
LLM选择有限endpoint candidates；
Core内部构造AggregationAnchor endpoint；
Bridge；
Unstitch。
```

## 阶段 R7：工作得久

再处理：

```text
高Order增量维护；
并行分页；
缓存；
全Cell扫描优化；
Surface压缩性能；
大规模Token成本；
长期运行。
```

不得提前使用语义索引优化。

---

# 23. 路线推进方向

这是多任务路线，不是单一任务推进向量。

预计完成整条R1-R5后：

```text
CORE +10~15%
ACCESS +10~15%
OPENCLAW +10~15%
LAB +10%
DISTRIBUTIONS +5%
SNAPSHOT 0%
TRACE 0%
HISTORY 0%
AUDIT 0%
```

完成度基线建议按目标纠偏重算：

| 模块 | 当前记录 | V3.6路线基线 | 原因 |
|---|---:|---:|---|
| CORE | 95% | 90% | Coverage/Core能力强，但缺多阶Aggregation与Surface API，GeometryAnchor公共面需纯化 |
| SNAPSHOT | 50% | 50% | 范围不变 |
| TRACE | 40% | 40% | 范围不变 |
| ACCESS | 95% | 85% | 当前Placement/Recall依赖Anchor/Cursor，需重建Surface Navigator |
| HISTORY | 10% | 10% | 暂停 |
| AUDIT | 10% | 10% | 暂停 |
| OPENCLAW | 90% | 75% | 当前跨Session正确性依赖Cursor，需重建Scale Scan |
| LAB | 90% | 85% | 真实成果保留，但需新Aggregation/Surface验证 |
| DISTRIBUTIONS | 70% | 65% | 配置和数据迁移需更新 |

这属于目标架构纠偏后的基线重算，不是已有代码突然失效。

---

# 24. 下一任务建议

下一任务应覆盖一个大跨度真实结果：

```text
Core多阶Aggregation
+
动态Active Surface
+
真实LLM Scale Scan
+
删除Cursor后的跨Session Recall
```

建议任务名：

```text
NOLLM_CAOLD_ADAPTIVE_SURFACE_RECALL_TASK_20260714.md
```

受影响模块：

```text
C A O L D
```

预计任务推进向量：

```text
CORE +10% | ACCESS +10% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5% |
其余模块 0%
```

任务不应先单独实现文档或聚合缓存，而应以如下真实能力为验收：

```text
删除全部Cursor
→ Core形成Order 0/1/2 Surface
→ 根据预算自动选择Order
→ 真实LLM逐层下钻
→ 新Session找到已有Alpha和Office记忆
→ NONE正常
→ 插件保持启用
→ 数据不清空。
```

---

# 25. 长期防漂移规则

以后任何Surface优化都必须回答：

```text
1. 是否读取了查询语义来选Order？
2. 是否保存了query/session/topic到Cell的映射？
3. 删除缓存后能否从Core重建同样Surface？
4. 分页是否只按GeometryAddress？
5. 向下是否只通过Coverage？
6. LLM是否只选择已展示candidate？
7. 是否引入了唯一parent/children树？
8. 是否把内部Anchor暴露为Host入口？
9. 是否把Cluster实体化？
10. 是否用vector/graph/embedding替代几何导航？
```

任何一项违反：

```text
停止扩展；
删除错误路径；
回到V3.6。
```

---

# 26. 最终路线概括

```text
Memory Layer：
  实际记忆场，每层可以有原生内容。

Aggregation Order：
  Core内部重复Coverage形成的观察尺度。

Internal Aggregation Anchor：
  几何汇聚骨架，可重建，不对外，不承载语义身份。

Active Surface：
  根据几何规模和操作预算动态选择的初始观察投影。

LLM Scale Scan：
  LLM在Surface中分页、下钻、返回和选择入口。

Locality：
  在明确入口和预算下由Coverage/Lateral/Bridge形成的有限现场。

Cluster：
  运行时观察，不是对象、Root或目录。

Cursor：
  从活动架构删除。

Index：
  不另建；多尺度Geometry本身就是导航和关系结构。
```

> **系统只决定“给 LLM 看多粗”；LLM 决定“从哪里进入”；Coverage 决定“如何逐层展开”；Core 决定“几何操作是否合法”。**
