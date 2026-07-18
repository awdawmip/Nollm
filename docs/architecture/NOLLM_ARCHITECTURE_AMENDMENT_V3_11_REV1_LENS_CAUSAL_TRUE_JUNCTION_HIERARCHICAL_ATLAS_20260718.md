# Nollm 架构修订 V3.11 Rev1：Recall Lens 因果编译、真实 Junction 与层级 Locality Atlas

**版本**：V3.11 Rev1
**日期**：2026-07-18
**性质**：对 V3.11 原型的活动纠偏；不废止即时 Capture、异步吸收、V3.9 快速 Coverage 或单入口 Recall
**输入检查点**：`dd95606b36acae753ce137c5c449f6fa16a070b4`
**输入 Bundle**：`nollm_caold_llm_recall_lens_junction_growth_20260717_dd95606.bundle`
**输入 Bundle SHA-256**：`032bf5c6b169ae800d21f1307f515454a363441efdb3b7971a62624cdfa83f64`
**检查点重新定性**：`LLM_RECALL_LENS_JUNCTION_PROTOTYPE_CHECKPOINT_AT_dd95606`
**状态**：活动目标架构；不表示本修订已经实现

---

# 0. 修订结论

V3.11 的核心方向正确：

```text
完整原文先 Capture；
真实 LLM 形成完整 Statement；
LLM 临时模拟未来 Recall 视角；
LLM 只选择有限 Locality；
Core 只接收几何；
一条 Statement 仍是一条 Atom、一个 Handle、一个 Cell；
Recall Lens 不持久化；
后续事实通过场生长形成多方向可达。
```

但 `dd95606` 尚未证明 Recall Lens 已经“编译成几何”。

当前原型存在四个根本缺口：

```text
1. Lens candidate 与 primary/contact Placement 可互相矛盾，Access 仍会接受；
2. Core Junction 先最小化 primary 距离，再考虑 contact，实质是 primary 边界放置，不是真实多关系交汇；
3. Locality Atlas 取稳定坐标排序前 N 个 occupied Cell，规模增长后会遗漏绝大多数相关局部；
4. 100-case self-play 和东京/时间/天气 deterministic Observation 是手工构造的放置—召回自证，不是因果验证。
```

本修订确立：

> **Recall Lens 只有在它的 Locality 选择被 Access 确定性编译为 Core 的关系组，并且这些关系组真实改变 Junction 候选和后续可达结构时，才称为“LLM-compiled”。**

---

# 1. 能力重新定性

`dd95606` 可以证明：

```text
operation-local Recall Lens Wire 存在；
Lens basis span 可验证；
Lens 文本未进入持久状态；
真实 LLM 可以在一次 Dream Sculptor 调用中形成 Statement、Lens 和 Placement 候选；
Core 有语义盲的局部空 Cell 候选器；
六个真实 Statement 可形成紧凑单层局部；
多个单入口可在 lateral 预算中到达中心事实；
Capture、异步 worker 和低调用 Recall 有阶段性实现。
```

它没有证明：

```text
Lens 与 Placement 具有因果绑定；
contact Locality 真实影响最终 Cell；
多个关系 Locality 被压缩进同一 Junction；
三条 Recall 视角塑造了三条生长方向；
大字段中的相关 Locality 能进入 Atlas；
不同语义入口不是紧凑簇的偶然可达；
真实 Writer/Reader/Critic 自博弈通过。
```

禁止继续使用：

```text
LLM_COMPILED_RECALL_LENS_JUNCTION_GROWTH_VALIDATED
```

直到本修订的因果 Gate 通过。

---

# 2. 写入—读取对偶

## 2.1 Writer 的工作

真实 LLM 在一次 Dream operation 中：

```text
1. 从不可变 Capture 形成完整 Statement；
2. 模拟未来读者可能提出的 1～4 个自然问题；
3. 将每个问题映射到有限层级 Atlas 中一个或多个 Locality path；
4. 按未来最主要的进入方式排序 Recall Lenses；
5. 提出 reuse / revision / new / expand / defer。
```

LLM 不：

```text
输出 q/r；
计算距离；
选择具体 Junction Cell；
生成 Topic/Entity；
持久化 Lens；
维护 fact→entries；
预测永久重要性。
```

## 2.2 Access 的工作

Access 将经验证的 Lens 编译为：

```text
ordered relation groups
```

每个 relation group 是：

```text
一个 Recall Lens
→ 一个或多个层级 Atlas leaf Locality
→ 对应的一组真实 GeometryAddress。
```

Access 不再接受与 Lens 无关的自由 `primary_candidate_id` / `contact_candidate_ids`。

## 2.3 Core 的工作

Core 接收：

```text
PhysicalFieldScope；
relation_groups: tuple[tuple[GeometryAddress,...], ...]；
occupied cells；
固定半径和预算。
```

Core 不接收：

```text
Lens 文本；
未来 query；
Statement；
Topic；
来源；
语义权重；
LLM reason。
```

Core 计算：

```text
一个或多个真实 JunctionCandidate；
每个候选对每个 relation group 的距离；
接触组数量；
最大组距离；
总组距离；
occupied neighbor；
free faces；
稳定 tie-break。
```

## 2.4 Reader 的工作

读取时：

```text
当前 query
→ 层级 Active Surface / Atlas
→ 一个最终 entry
→ Core 单入口传播
→ bounded Locality
→ 主代理使用。
```

写入时的 Lens 不保存，读取时重新理解当前问题。

---

# 3. Recall Lens 的因果合同

## 3.1 Lens 是有序的

一条 Statement 有 1～4 个 Lens。

顺序含义：

```text
第一个 resolved Lens：
主要未来进入视角；

后续 resolved Lens：
希望同时接触的次级视角；

unresolved Lens：
当前字段没有可见 Locality，不得伪造联系。
```

这不是全局轴，也不是永久优先级。

## 3.2 Lens 输出

每个 Lens 至少包含：

```text
lens_id；
future_query；
exact Capture basis spans；
atlas_path_ids；
leaf_locality_candidate_ids；
unresolved。
```

`atlas_path_ids` 和 leaf IDs 必须来自当前冻结 Atlas。

## 3.3 Placement 不再独立选择 Locality

新计划不再允许：

```text
Lens 指向 Locality A；
primary_candidate_id 选择 Locality B；
Access 仍接受。
```

Access 确定性编译：

```text
第一 resolved Lens leaf set → relation_group[0]
第二 resolved Lens leaf set → relation_group[1]
...
```

如果模型需要说明某 Lens 只是思考而不用于放置：

```text
unresolved=true
```

不得再输出一套与 Lens 平行的 primary/contact 语义选择。

## 3.4 Action

```text
reuse：
现有 Handle 必须出现在至少一个 resolved Lens 的 leaf Locality 中；

revision_current：
同上，并进入一次确认；

new_local / expand_surface：
至少一个 resolved Lens；
Core 依据 relation_groups 求 Junction；

defer：
无法形成安全 Statement 或无合法 Atlas path。
```

---

# 4. 真实 Junction 数学合同

## 4.1 Relation group 距离

对候选 Cell `x` 和 relation group `G_i`：

```text
d_i(x) = min_{g in G_i} hex_distance(x,g)
```

Core 不理解 `G_i` 的语义。

## 4.2 Candidate universe

候选集合必须从所有 relation groups 产生：

```text
U = union over all group cells of bounded hex neighborhoods
```

禁止只围绕第一 primary Cell 枚举。

第一实现预算：

```text
group_count <= 4
cells_per_group <= 4
max_radius <= 4
candidate universe <= deterministic bounded ceiling
```

应在完整集合评分后再截断输出；不得按 stable key 先截断 64 个再评分。

## 4.3 Junction 评分

第一活动评分建议：

```text
1. 最大化在 contact_radius 内可接触的 relation group 数；
2. 最小化 max_i d_i(x)；
3. 最小化 sum_i d_i(x)；
4. 优先真实 boundary / occupied adjacency；
5. 在关系已满足时保留更多 free faces；
6. stable GeometryAddress tie-break。
```

Codex 可以通过数学和 fixture 微调次序，但必须满足：

```text
contact groups 对候选集合和最终排名有可观察影响；
交换主 Lens 顺序不能机械抹去其他组；
多关系候选不能总是退化成离第一组最近的邻居。
```

## 4.4 Realized relation groups

每个 JunctionCandidate 报告：

```text
group_distances；
groups_within_contact_radius；
all_groups_realized；
max_group_distance；
total_group_distance；
free_face_count；
occupied_neighbor_count。
```

这些是运行证据，不进入语义事实。

## 4.5 无真实交汇

若多个 resolved Lens 在预算内不存在有意义的 Junction：

```text
Core 如实返回 no_bounded_junction；
Access 不得称为 junction；
允许：
  仅实现第一 Lens 的 primary growth；
  将其他 Lens 标为 unrealized observation；
  或 defer。
```

不得为完成测试强制把远距离 contact 当成已实现关系。

---

# 5. 层级 Locality Atlas

## 5.1 当前错误

以下实现不能扩展：

```text
occupied cells stable-key 排序；
取前 candidate_limit；
用最前 8 个 Cell 生成 frontier。
```

数据增长后，LLM 只会看到坐标排序前缀，相关 Locality 可能永远不可见。

## 5.2 Atlas 来源

Atlas 必须来自现有可重建多尺度 Surface：

```text
PhysicalFieldScope
→ structure-budget-selected Surface Orders
→ bounded coarse regions
→ bounded descendant paths
→ occupied/boundary leaf Localities。
```

不得使用 query、Topic、Source、embedding 或语义排序来选择初始结构。

## 5.3 单次 Prompt 的层级 Atlas

为了保持一次 Dream Sculptor 调用，第一实现生成一个有界层级包：

```text
AtlasNode:
  node_id
  aggregation_order
  geometry identity
  child node IDs
  occupied/native counts
  truncated
  representative current Statements
  boundary/free-face statistics

AtlasPath:
  root/coarse → ... → leaf Locality
```

总预算固定，例如：

```text
nodes <= 64
leaf localities <= 32
representatives per leaf <= 3
depth <= 3 或按真实预算选择
```

LLM 在一次输出中为每个 Lens 选择完整 path 和 leaf。

## 5.4 小字段

字段很小时：

```text
Atlas 可以直接展示全部 occupied/boundary leaf；
无需伪造 coarse level。
```

## 5.5 Atlas 不持久化

```text
Atlas 是 operation-local derived state；
删除后可重建；
mutation/import/reopen 后失效；
candidate/path IDs 不跨 operation。
```

---

# 6. 逆向生长

## 6.1 第一事实

`今天东京下雨了` 可以先成为 Junction seed。

如果还没有东京、日期或天气 Locality：

```text
Lens 可以 unresolved；
Core 只创建一个关系中性 seed；
保留 free faces。
```

## 6.2 后续事实

后续事实重新运行 Dream Sculptor：

```text
东京取消浅草行程
→ Lens 指向东京相关 leaf；

同日线上会议
→ Lens 指向日期相关 leaf；

大阪下雨
→ Lens 指向天气相关 leaf。
```

它们应沿不同已形成的分支边界继续生长。

## 6.3 不持久化方向名称

不保存：

```text
这个 face = 东京；
这个 face = 时间；
这个 face = 天气。
```

方向含义由附近完整 Statements 和几何生长共同显现。

## 6.4 观察要求

三入口不是初始硬约束。

只有在后续字段真实长出三个分支后，才观察：

```text
东京分支外端；
时间分支外端；
天气分支外端；
```

分别单入口到达原事实。

---

# 7. 验证方法纠偏

## 7.1 “self-play”名称

纯脚本构造 wire、程序选择 candidate、再从落点召回自身，只能称：

```text
synthetic contract conformance
```

不得称：

```text
LLM self-play；
semantic placement validation；
wrong-locality validation。
```

## 7.2 真正的 Writer/Reader/Critic

Lab 中使用相互隔离的真实 LLM operation：

### Writer

只看：

```text
Capture + Atlas
```

输出 Statement、Lens 和 Atlas paths。

### Reader

不知道 Writer 的 Lens 和选择，只看：

```text
最终几何字段 + 测试 query
```

选择一个 entry 并 Recall。

### Critic

只看：

```text
Capture；
Writer plan；
最终 Cell；
Reader entry/path/result；
counterfactual controls。
```

判断：

```text
Lens 是否因果实现；
是否只是紧凑簇偶然可达；
错误 Locality 是否被拒绝；
未实现 Lens 是否诚实标记。
```

Critic 只进入 Lab 报告，不进入生产状态。

## 7.3 Counterfactual

必须有：

```text
同一 Statement、相同 Atlas，替换 Lens Locality：
  最终候选应变化或计划被拒绝；

保持 Lens 不变、自由更改 primary：
  必须被拒绝；

删除 contact relation group：
  真实 Junction 排名应变化；

随机无关紧凑簇：
  不能因任意邻居可达就称多视角成功；

unrelated occupied branch：
  在同一预算下不能错误到达目标。
```

---

# 8. 东京—时间—天气标准场

## 8.1 场结构

不能只建立中心 + 三个直接邻居。

至少形成：

```text
中心 T0：
2026年7月17日东京下雨。

东京 arm：
至少 2 个后续东京事实；

时间 arm：
至少 2 个同日但不同主题事实；

天气 arm：
至少 2 个其他地点/天气变化事实；

unrelated arm：
至少 2 个无关事实。
```

每条 arm 从真实 LLM Lens/Atlas path 逐步生长。

## 8.2 Recall

从三个语义 arm 的外端，进行三次独立查询：

```text
东京入口；
绝对日期入口；
天气入口。
```

要求：

```text
每次一个最终 entry；
目标 T0 可达；
路径长度至少 2，不能只是一个 lateral 邻居；
三个 entry 不同；
同一 Handle；
不合并入口；
不依赖 Bridge；
重启后重复。
```

## 8.3 负对照

```text
unrelated arm 外端
→ 在相同 RecallBudget 下不应到达 T0。
```

如预算过大会让整个小字段全部互达：

```text
缩小验证预算；
扩大 arm 间隔；
不得用全簇广播证明关系。
```

---

# 9. V3.10 保留与补充闭合

本修订不撤回：

```text
即时 Capture；
scope partition；
单 turn canonical Capture；
持续 worker service；
retry；
Pending + admitted context；
批量 Dream；
一次隐藏 Recall。
```

必须补充检查：

```text
一个 batch 中多个 revision_current：
  每个 provisional 都必须独立确认或 retry；

confirmation timeout/invalid：
  必须 retryable，并继续 Pending；
  不得直接 terminal deferred；

Live 原始 Sculptor 输出：
  必须在运行时 Evidence 中冻结；
  不得只在事后从 Host 日志恢复摘要。
```

---

# 10. 模块所有权

## Core

新增/修正：

```text
RelationGroupJunctionRequest；
真实多组几何评分；
group distance evidence。
```

不拥有 Lens、Atlas text、Statement 或 query。

## Access

拥有：

```text
层级 Atlas；
Lens path validation；
Lens → relation_groups 编译；
Atlas state fingerprint；
Junction apply；
provisional revision；
durable provenance。
```

## OpenClaw

拥有：

```text
Dream Sculptor Prompt/Wire；
Capture worker；
真实 Writer call；
fast Recall Reader call；
运行时 raw evidence。
```

## Lab

拥有：

```text
synthetic conformance；
Writer/Reader/Critic；
counterfactual；
长分支场；
性能和因果报告。
```

## Distributions

只声明：

```text
schema/prompt/policy version；
Atlas/Junction budgets；
插件组合。
```

---

# 11. 禁止路线

```text
Lens 持久化；
Topic/Entity 节点；
query→entry；
fact→entries；
固定轴；
持久 face 语义；
图边；
vector/embedding；
multi-entry Recall；
复制 Atom；
为了三入口直接写三份；
Core 接收 Statement/Lens；
按 stable coordinate 前缀冒充 Atlas；
用紧凑星形簇冒充逆向生长；
用 synthetic wire 冒充 LLM self-play。
```

---

# 12. 最终架构概括

```text
LLM 在写入时模拟未来读者，
但模拟结果只在当前操作中存在。

Access 把这些未来视角编译成真实几何关系组。

Core 在所有关系组之间求一个真正的局部交汇，
而不是只贴着第一个 Locality 放置。

后续事实沿不同边界继续长，
方向的含义由完整事实和空间共同形成。

读取时不读旧 Lens，
只从当前问题选择一个入口，
由字段本身把事实找回来。
```

> **只有当改变 Recall Lens 会改变几何，改变几何会改变后续单入口可达性时，Recall Lens 才真正成为 Architecture is the Index 的编译语言。**
