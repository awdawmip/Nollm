# Nollm 架构修订 V3.11 Rev2：字段完整 Atlas、已实现 Junction 与真实 Writer→Field→Reader 因果链

**版本**：V3.11 Rev2  
**日期**：2026-07-18  
**性质**：对 V3.11 Rev1 的活动纠偏；不废止 Recall Lens、即时 Capture、异步吸收、V3.9 快速 Coverage 或单入口 Recall  
**输入检查点**：`440b7d43ade67a2c1b8f67aa0fabf24c2b7297ef`  
**输入 Bundle**：`nollm_caold_lens_causal_true_junction_hierarchical_atlas_20260718_440b7d4.bundle`  
**输入 Bundle SHA-256**：`f6d640f1581e59628e355291827944ad302b007534befaba769d4a0cf5d7b335`  
**输入状态**：`CAOLD_LENS_CAUSAL_JUNCTION_GROWTH_IN_PROGRESS_AT_440b7d4`  
**检查点重新定性**：`LENS_RELATION_GROUP_AND_JUNCTION_PROTOTYPE_CHECKPOINT_AT_440b7d4`  
**状态**：活动架构修订；不表示已经实现

---

# 0. 修订结论

`440b7d4` 已经真实实现：

```text
Recall Lens → relation groups；
Core 从所有 relation groups 生成候选；
关系组排序不再由自由 primary/contact 字段决定；
Surface-derived Atlas 原型；
synthetic 长分支；
真实 Writer/Reader/Critic 调用基础；
operation-local Lens；
one Statement / one Atom / one Cell。
```

但仍有三个因果断点：

```text
1. Atlas 对字段不是完整覆盖：
   300 occupied Cells 的实测 Atlas 只暴露 59 个物理 Cell，
   其余 241 个既不属于可选 leaf，也没有可继续下降的 path。
   当前“层级”是从若干抽样 projection 创建 parent/leaf，
   不是覆盖整个字段的层级分区。

2. Core 会返回 all_groups_realized=false 的候选，
   Access 又直接采用第一候选。
   例如 relation groups 位于 (0,0) 和 (6,0)，contact_radius=2，
   Core 返回 (2,0)，距离为 (2,4)，只有一个关系组真正接触，
   但该 Cell 仍会被当作 Junction 写入。

3. Provider Writer/Reader/Critic 不是一条因果链：
   Writer 只在独立空 workspace 中输出计划；
   Reader workspace 由脚本预先直接放入 target/unrelated Statement；
   Writer 计划没有应用到 Reader 字段。
   Reader 10/10 只能证明 Reader 能从预制字段选中目标，
   不能证明 Writer Lens/Junction 产生了可召回几何。
```

本修订确立：

> **Atlas 必须对当前字段形成有界但完整的结构覆盖；resolved Lens 只有在所有关系组都被实际接触时才能写入 Junction；Provider 验证必须把 Writer 输出真正应用到同一字段，再由独立 Reader 从该字段单入口召回。**

---

# 1. 能力边界

`440b7d4` 可以保留为：

```text
LENS_RELATION_GROUP_AND_JUNCTION_PROTOTYPE_CHECKPOINT_AT_440b7d4
```

它证明：

```text
Lens 与 relation groups 已绑定；
Core 多组评分原型成立；
Atlas 不再简单取 stable-key 前32个 occupied Cells；
合成双步 arms 可生成；
Evidence/Manifest 当前一致。
```

它没有证明：

```text
Atlas 覆盖全部字段；
LLM 可以看到任意相关区域；
resolved Lenses 均被真实几何实现；
Writer 的几何结果导致 Reader 成功；
真实长分支来自 Provider Writer；
unrelated negative control 与 Writer 字段同源；
one-cell 模型足以形成稳定语义分支。
```

---

# 2. 字段完整 Atlas

## 2.1 “完整”的含义

完整不是：

```text
把全部 Statement 文本塞进 Prompt；
把全部物理 Cell 作为 leaf 展示；
建立 Topic/Source/Entity 索引。
```

完整是：

```text
Atlas 中所有 top-level region 的 source-cell union
=
当前 FieldScope 中全部 occupied physical Cells。
```

每个 occupied Cell 必须：

```text
属于至少一个 Atlas region；
不会因 stable-key、even sampling 或候选上限直接消失；
能够通过 Atlas node/path 的几何身份被覆盖。
```

## 2.2 选择 Surface Order

Access 从 Order 0 开始，选择：

```text
满足所有非空 Surface projections 数量 <= atlas_node_budget
的最细 Order。
```

即：

```text
k* = min{k | occupied_projection_count(k) <= node_budget}
```

如果支持的最大 Order 仍超预算：

```text
Atlas 返回 explicit overflow；
Dream Sculptor defer/retry；
不得对 projections 做 even_sample 后冒充完整字段。
```

## 2.3 不允许 projection 抽样

禁止：

```text
selected = even_sample(all_projections, candidate_limit)
```

必须：

```text
选定 k* 后，包含该 Order 的全部非空 projections。
```

## 2.4 Region 与 leaf

第一版可以：

```text
每个 projection 是一个 region node；
每个 region 提供一个 bounded geometry support；
每个 region 提供最多3条 representative current Statements；
Atlas path 可以是单节点或 coarse→support 两节点。
```

但必须诚实区分：

```text
region covers N source Cells；
geometry support 仅是该 region 的有限确定性支撑；
representative Statements 不是 region 的完整语义。
```

不得把有限 support 写成全部 leaf。

## 2.5 Geometry support

Access 可从完整 region 的 source Cells 确定性选择 1～4 个支撑 Cell，用于 Core relation group。

选择算法必须：

```text
只看几何；
覆盖 region 的中心/边界；
稳定；
不读取 Statement/query；
记录 source_cell_count 与 support_cell_count；
对同一 state 可复现。
```

如果 1～4 个支撑 Cell 无法诚实代表过大的 region：

```text
该 region 标 support_overflow；
Lens 可以 unresolved；
不得静默抽样并称精确 locality。
```

## 2.6 Atlas 覆盖证书

Atlas 输出：

```text
occupied_field_cell_count；
covered_field_cell_count；
uncovered_field_cell_count；
region_count；
selected_aggregation_order；
overflow；
每个 region 的 source_cell_count；
support_cell_count。
```

活动 Atlas 必须满足：

```text
uncovered_field_cell_count = 0
```

否则不能进入 Dream Sculptor。

---

# 3. 已实现 Junction

## 3.1 resolved Lens 与 realized relation

```text
resolved Lens：
LLM 找到了 Atlas region/path。

realized relation：
Core 选出的 Cell 在 contact_radius 内接触该 Lens relation group。
```

resolved 不自动等于 realized。

## 3.2 Core 候选过滤

对多关系组请求：

```text
只有 all_groups_realized=true 的 Cell
才能进入可写 JunctionCandidate 列表。
```

或者 Core 明确返回：

```text
realized_candidates；
partial_candidates（诊断）；
no_bounded_junction。
```

活动 Access 只能应用 `realized_candidates`。

## 3.3 单关系组

一个 resolved relation group：

```text
允许普通边界生长；
候选必须在 contact_radius 内；
不需要伪称“多关系交汇”。
```

## 3.4 多关系组

两个以上 relation groups：

```text
每个 group distance <= contact_radius；
all_groups_realized=true；
才允许 action=new_local/expand_surface 写入。
```

若没有：

```text
Access 返回 lens_geometry_unrealized；
Capture/Statement 保持 retryable/defer；
允许一次 Sculptor correction：
  将部分 Lens 改为 unresolved；
  或选择其他 Atlas region；
不得直接使用 partial candidate。
```

## 3.5 公共 API 真值

Core 不应返回：

```text
max_group_distance > request.max_radius
```

的活动候选。

所有输出候选必须满足请求预算。

---

# 4. Writer→Field→Reader 因果链

## 4.1 同一字段

每个 Provider 场景必须：

```text
创建一个初始字段；
构建 Writer Atlas；
真实 Writer 输出 Lens plan；
校验并实际 apply 到该字段；
关闭并重开；
构建 Reader Surface/entries；
独立 Reader 选择一个 entry；
Core Recall；
检查是否找到 Writer 写入的同一 Handle。
```

禁止：

```text
Writer workspace 和 Reader workspace 相互独立；
脚本绕过 Writer 在 Reader 字段预先放入 target；
Reader target_statement_id 来自 fixture 而非 Writer durable outcome。
```

## 4.2 Counterfactual

在同一最终字段中创建或保留：

```text
一个无关 occupied branch/entry。
```

强制从该 entry 单入口 Recall：

```text
不得到达 Writer target。
```

Counterfactual 与 Reader 必须使用：

```text
相同 Core state；
相同 target Handle；
相同 RecallBudget；
不同 entry。
```

## 4.3 Writer validity

Writer 成功不仅是 JSON 合法，还必须：

```text
Statement durable；
relation groups 来自完整 Atlas；
Junction all_groups_realized；
Handle/Atom/Statement reopen；
Lens 文本不持久化。
```

## 4.4 Reader validity

Reader 成功必须：

```text
独立 session；
不知道 Writer raw Lens；
只看 query + 最终字段可见 entries；
一个 entry；
到达 Writer target Handle；
unrelated counterfactual 不到达。
```

## 4.5 Critic

Critic 是 Lab 辅助，不作为生产正确性唯一来源。

可以接受：

```text
raw JSON；
或安全提取唯一 fenced JSON object，
同时记录 repair 类型。
```

但主要因果结论必须由确定性字段证据计算：

```text
Writer applied；
target Handle；
Reader entry/path；
counterfactual path；
Lens ablation；
Junction realization。
```

---

# 5. Lens 因果反事实

每个多关系场景至少验证：

```text
原 Lens groups → Junction Cell X；
删除一个 relation group → Cell 或候选排名改变；
替换一个 group 为无关 region → no_bounded_junction 或 Cell改变；
保持 Statement 不变、改变 Lens → geometry改变；
保持 Lens 不变、改变自由 reason_text → geometry不变。
```

如果 Lens 改变而几何完全不变：

```text
必须证明是几何等价；
否则不计为因果实现。
```

---

# 6. Provider 长分支

## 6.1 禁止直接种 target

真实长分支不能：

```text
Core.put Lab target seed；
脚本选择包含指定 Statement 的 candidate；
脚本替 Writer 决定 relation region。
```

允许：

```text
初始 relation-neutral empty field；
或预先存在但与测试主题无关的背景字段。
```

所有测试事实通过：

```text
Capture
→ Provider Writer
→ complete Atlas
→ realized Junction
→ Admission。
```

## 6.2 场结构

至少：

```text
T0；
东京 arm >=2；
时间 arm >=2；
天气 arm >=2；
unrelated arm >=2。
```

每个 arm 的新事实由 Provider Writer 自己选择 Lens region。

## 6.3 Recall

```text
三个 arm 外端；
三个独立 Reader；
一个 entry；
路径长度 >=2；
同一 T0 Handle；
unrelated arm 同预算不达 T0。
```

如 one-cell 模型无法在有界重试内形成分支：

```text
如实提交 IN_PROGRESS；
记录 one-cell model evidence；
下一任务才可研究 multi-cell footprint。
```

---

# 7. 性能

## 7.1 Atlas

目标：

```text
300 occupied Cells：
field coverage=100%；
<=2秒；

1000 Atoms：
<=5秒；

不写 Core；
不读取 query；
不创建语义索引。
```

## 7.2 Junction

```text
relation groups <=4；
geometry support cells/group <=4；
candidate evaluation bounded；
单请求 target <=100ms，hard ceiling<=500ms。
```

## 7.3 Provider

Writer 后台延迟可以较长，但必须：

```text
每 batch common Writer calls <=1；
Reader common hidden calls <=1；
不为 Critic 增加生产调用。
```

---

# 8. 禁止路线

```text
Atlas sampling后宣称完整；
stable-key/even-sample 丢弃字段；
partial Junction 当 realized Junction；
把 all_groups_realized=false 写入；
Writer/Reader 独立预制字段；
脚本直接放 target 冒充 Writer；
Critic 文本替代确定性因果证据；
Lens持久化；
Topic/Entity；
query/fact entry map；
vector/graph/embedding；
multi-entry Recall；
multi-cell Atom；
多物理层；
Stitch。
```

---

# 9. 最终架构概括

```text
LLM 只能从真实覆盖整个字段的 Atlas 中选择关系区域。

Access 把这些选择编译成有限几何支撑组。

Core 只有在一个 Cell 真正接触所有 resolved groups 时，
才允许它成为 Junction。

Writer 写出的事实必须实际进入字段，
Reader 必须从这个真实结果中找回它。

否则，Lens、Junction 和 Reader 成功只是三段互不相干的演示。
```

> **Architecture is the Index 的最低因果要求是：Writer 改变字段，字段改变 Reader 的单入口可达性。**
