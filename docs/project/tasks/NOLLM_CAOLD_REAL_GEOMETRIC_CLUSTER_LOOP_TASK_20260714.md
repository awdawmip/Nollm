# Nollm CAOLD 真实几何簇闭环任务书

**模块缩写**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`
**日期**：2026-07-14
**任务文件名**：`NOLLM_CAOLD_REAL_GEOMETRIC_CLUSTER_LOOP_TASK_20260714.md`
**性质**：“工作得对”阶段的真实几何关系能力
**输入Bundle**：`nollm_caold_real_revision_loop_20260713_a1a368d1.bundle`
**输入Bundle SHA-256**：`979eb3212f94f6a4053d41cbb127cb61d8f93ca9a944e7b3d375a21394e1f20a`
**输入分支**：`codex/caold-real-revision-loop`
**输入HEAD**：`a1a368d115f133b973011e5275fa15fb8f66b990`
**已验证能力**：`REAL_OPENCLAW_REVISION_LOOP_VALIDATED_AT_a1a368d115f133b973011e5275fa15fb8f66b990`
**建议分支**：`codex/caold-real-geometric-cluster-loop`
**主环境**：真实Windows 10/11 + 当前OpenClaw
**交付形式**：所有真实进展提交、工作树干净、仓库外单一完整历史Git Bundle
**成功后环境**：插件保持安装和启用，现有Nollm数据保留，交给用户继续正常聊天测试
**结论边界**：验证有限真实几何簇形成与Recall；不宣称全局语义质量、规模、发布或完整安全。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
让真实LLM从Access提供的有限、内容无关几何候选中选择Placement；
相关MemoryStatement形成局部几何簇；
无关MemoryStatement形成不同局部；
Core通过Cell/Coverage/Lateral关系提供有界候选；
新session在无外置关系索引条件下自然Recall相关簇。

范围变化：
无。验证既有“Architecture is the Index”能力；
不新增graph、vector、embedding、source/topic/entity索引；
不建设安全、审计、发布或兼容设施。
```

### 0.1 为什么是这一能力

当前闭环可以工作并能修订，但仍可能退化成：

```text
所有new都写入默认q=0/r=0；
MemoryCursor只提供该单元；
Recall Agent负责全部语义筛选。
```

这种实现无法证明几何本身承载关系。

本任务必须证明：

```text
相关内容因LLM的几何选择进入同一局部关系场；
无关内容进入不同局部；
从一个局部入口进行Core有界传播时，
相关记忆进入候选，无关簇不会被同一局部传播扫入。
```

---

## 1. 任务前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 90% | 高 | 真实写入、revision、重启、跨session Recall | 多Cell真实局部关系尚未验证 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中 | 最小备份 | 本任务不扩展 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 最小事件 | 本任务不扩展 | 否 |
| ACCESS | `CAPABILITY_VALIDATED` | 95% | 高 | AccessMemoryLoop、原子revision、current Recall | 有限候选几何和真实簇编排未验证 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 当前暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 当前暂停 | 否 |
| OPENCLAW | `CAPABILITY_VALIDATED` | 80% | 中高 | 隐形Dream、Placement、revision、跨session注入 | 几何簇选择与相关簇Recall未验证 | 是 |
| LAB | `IMPLEMENTED` | 85% | 中 | 最小真实闭环报告 | 缺多Cell/多簇对照 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 65% | 中 | 插件安装、启用和Access-only依赖 | 当前任务与最小配置同步 | 是 |

---

## 2. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 90% | 95% | +5% | 真实多Cell局部簇和有界传播 | Core状态、重开、per-entry Recall | 大规模和跨簇Stitch |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | 最小备份 | 增量与版本迁移 |
| TRACE | 40% | 40% | 0% | 无变化 | 最小错误摘要 | 产品观察 |
| ACCESS | 95% | 100% | +5% | 内容无关候选生成、LLM选择、簇/新簇编排 | 候选合同、真实Placement、失败回滚 | 后续章程变化时重算 |
| HISTORY | 10% | 10% | 0% | 无变化 | 无 | 未实现 |
| AUDIT | 10% | 10% | 0% | 无变化 | 无 | 未实现 |
| OPENCLAW | 80% | 90% | +10% | 真实相关簇形成和跨session自然Recall | 多session Live | 其他模型和长期质量 |
| LAB | 85% | 90% | +5% | 最小几何簇/无关簇对照 | 单一报告 | 大规模质量暂停 |
| DISTRIBUTIONS | 65% | 70% | +5% | 新Placement合同和当前活动任务同步 | 安装/重启/手测 | 正式发布暂停 |

目标值仅为预测。Access达到100%只表示当前章程范围，不能宣称永久封版。

---

## 3. 单一主验收场景

建立两个真实语义簇。

### 簇A：项目发布

通过三个独立正常聊天turn形成：

```text
A1：Alpha项目发布窗口是周三下午三点。
A2：Alpha项目发布风险评审在周二上午十点。
A3：Alpha项目发布负责人是Priya。
```

要求：

```text
A1创建新簇anchor；
A2和A3由真实Placement LLM选择A1局部候选；
三个Statement位于同一有限几何局部；
不要求同一Cell，但必须通过ring-1、Coverage或显式局部关系相连。
```

### 簇B：办公设施

通过独立turn形成：

```text
B1：办公楼咖啡厅每天晚上六点关闭。
B2：办公楼访客前台在一楼东侧。
```

要求：

```text
真实Placement LLM判断与Alpha发布簇无关；
选择new_cluster；
Access分配独立cluster anchor；
簇B不能落入簇A的本次局部Recall预算。
```

---

## 4. 内容无关的几何候选生成

### 4.1 Access负责候选生成

Access基于：

```text
当前Cursor；
已有局部GeometryAddress；
Core已编译模板；
Cell occupancy；
固定预算；
```

生成有限候选。

不得读取或评分MemoryStatement文本。

### 4.2 候选类型

最低包括：

```text
existing_cell：
  当前局部已占用单元，允许语义高度相关内容共Cell。

lateral_ring_1：
  当前anchor的六个轴向相邻单元。

coverage_up：
  由已编译Coverage模板产生的有限上层候选。

coverage_down：
  由已编译Coverage模板产生的有限下层候选。

new_cluster：
  请求一个与当前局部保持最小几何距离的新anchor。
```

可按现有Core公共API裁剪，但至少必须有：

```text
existing/local；
lateral；
new_cluster。
```

### 4.3 candidate ID

向LLM输出：

```text
candidate_id；
relation_kind；
GeometryAddress；
occupancy摘要；
局部已存Statement摘要。
```

LLM返回：

```text
action；
candidate_id；
existing_handle（reuse/revision时）；
reason_text。
```

LLM不得任意编造GeometryAddress。

Access把`candidate_id`确定性映射到地址。

---

## 5. new_cluster分配

LLM只决定：

```text
该Statement应创建新簇。
```

Python/Access只负责确定性分配一个空闲anchor。

允许：

```text
canonical spiral sequence；
固定间距的轴向anchor序列；
基于当前已占anchor数量的内容无关分配。
```

禁止：

```text
statement hash决定位置；
关键词决定坐标；
source/topic/entity决定分区；
embedding/vector决定距离。
```

新簇anchor应与现有簇保持超过本次局部Recall预算的距离，或处于不会被簇A单入口传播覆盖的独立局部。

---

## 6. Placement Prompt

真实Placement LLM得到：

```text
新MemoryStatement；
有限当前局部Statement；
有限candidate list；
允许动作：
  new_local
  new_cluster
  reuse
  revision_current
  defer
```

必要时可继续支持`move`。

不得给：

```text
全局Statement列表；
任意坐标自由生成；
source/topic/entity路由；
图邻接；
向量结果；
Python相关性分数。
```

### Prompt要求

```text
相关、同一工作现场的信息优先选择local候选；
语义独立的信息可选择new_cluster；
完全重复选择reuse；
纠正选择revision_current；
不确定选择defer。
```

这是LLM语义判断，不用Python规则执行。

---

## 7. Core与Access边界

Core只验证和执行：

```text
候选GeometryAddress合法；
Cell写入；
Coverage/Lateral/Bridge传播；
有界Recall；
原子状态。
```

Access负责：

```text
候选生成；
candidate_id映射；
Statement/Handle编排；
Cursor；
失败回滚；
new_cluster空闲anchor分配。
```

OpenClaw只依赖Access，不直接import Core。

---

## 8. Cursor调整

Cursor保存有限：

```text
recent_cluster_anchors；
recent_used_entry_cells。
```

上限建议：

```text
cluster anchors <= 4
entry cells <= 8
```

不得保存：

```text
cluster语义名称；
Alpha/咖啡厅等topic标签；
source映射；
Statement关系表。
```

新session可以把有限多个anchor交给Access分别进行局部Recall。

报告必须保留每个anchor的独立Core Recall结果，证明几何局部差异。

---

## 9. 真实Recall验收

Gateway重启后，创建至少三个新session。

### Session R1：Alpha相关查询

自然提问：

```text
Alpha项目发布前我要关注什么？
```

必须：

```text
簇A anchor的Core局部Recall返回至少2条A类Statement；
簇B的B1/B2不出现在簇A单anchor的Core结果；
Recall Agent选择至少一条A类信息；
主代理自然使用，不提Nollm。
```

### Session R2：办公设施查询

自然提问：

```text
访客到办公室后去哪里登记，咖啡厅几点关门？
```

必须：

```text
簇B anchor的Core局部Recall返回B1/B2；
簇A不出现在簇B单anchorCore结果；
主代理自然回答。
```

### Session R3：NONE

无关问题：

```text
太阳系最大的行星是什么？
```

要求：

```text
不注入A/B记忆；
或Recall Agent明确NONE；
主代理正常回答。
```

---

## 10. 几何真实性硬条件

必须从Core状态和Recall结果确认：

```text
至少2个cluster anchors；
至少3个不同GeometryAddress；
簇A内部至少一条lateral或coverage局部关系；
簇B与簇A的单anchor局部Recall相互隔离；
没有全局scan；
没有source/topic/entity查找；
没有graph/vector/embedding；
没有statement hash placement；
```

如果全部Statement仍落在同一Cell：

```text
任务不通过；
不得用Recall Agent过滤结果冒充几何簇。
```

---

## 11. 失败处理

至少验证：

```text
候选地址已占用或非法；
new_cluster分配失败；
Core写入失败；
Handle写入失败。
```

要求：

```text
本次新Statement不成为孤立持久数据；
既有簇不损坏；
Cursor不更新；
后续正常turn继续；
插件不禁用；
Nollm数据不清空。
```

不建设新的故障框架。

---

## 12. 最小自动测试

只新增直接保护真实能力的测试：

```text
候选生成内容无关；
candidate_id唯一和有界；
六个lateral候选正确；
new_cluster分配不使用statement hash；
new_cluster与旧anchor保持最小距离；
LLM不能返回候选外地址；
local Placement；
new_cluster Placement；
失败不更新Cursor；
per-anchor Recall隔离；
OpenClaw无Core import。
```

旧M0活动项目书测试更新为V3.4角色，或直接删除过时断言。

---

## 13. 最小活动依据同步

在本任务中就地完成：

```text
加入上一任务书或将其标为已完成历史；
加入当前任务书；
修正Manifest tracked计数；
更新ACTIVE_PROJECT；
更新CURRENT_STATUS；
更新模块进度账。
```

只修现有文件，不新增治理系统。

---

## 14. 单一报告

只生成：

```text
docs/project/CAOLD_REAL_GEOMETRIC_CLUSTER_LOOP_REPORT.md
```

记录：

```text
实际模型；
Statement IDs；
candidate lists；
LLM candidate选择；
cluster anchors；
每个Statement GeometryAddress；
per-anchor Core Recall；
Recall Agent选择；
主代理可见回答；
失败回滚；
插件最终状态；
数据保留；
实际向量和完成度。
```

不要求完整聊天或隐藏推理。

---

## 15. Final验收

必须同时满足：

```text
真实普通聊天；
真实LLM Formation；
真实LLM候选几何选择；
至少两个真实几何簇；
至少三个不同GeometryAddress；
相关簇由Cell/Lateral/Coverage形成局部；
无关簇不进入相关簇单anchor Core Recall；
Gateway重启；
新session R1/R2真实Recall；
隐藏注入；
主代理自然使用；
NONE正常；
无Python语义Placement；
无graph/vector/embedding或外置关系索引；
写入失败不污染；
OpenClaw只依赖Access；
插件保持启用；
Nollm数据保留；
工作树干净；
完整历史Bundle验证通过。
```

允许记录：

```text
REAL_OPENCLAW_GEOMETRIC_CLUSTER_LOOP_VALIDATED_AT_<HEAD>
```

不表示：

```text
大规模几何质量已验证；
跨簇Stitch已验证；
所有模型都能正确Placement；
长期稳定或发布完成。
```

---

## 16. 交付优先

无论完整Live结果如何：

```text
真实修改必须commit；
工作树必须clean；
必须生成并验证Bundle；
未完成写IN_PROGRESS；
不得因为模型Placement不理想拒绝交付；
插件和数据不得清空。
```

建议Bundle：

```text
nollm_caold_real_geometric_cluster_loop_20260714_<shorthead>.bundle
```

最终只报告：

```text
branch / final HEAD
预计/实际向量
全部模块实际完成度
候选几何合同
cluster anchors和地址
真实Placement选择
per-anchor Core Recall
重启和新session使用
失败回滚
插件最终状态
Nollm数据保留状态
known limitations
Bundle filename / SHA-256
```
