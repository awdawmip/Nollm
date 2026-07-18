# Nollm 架构修订 V3.11 Rev3：Prompt 有界 Lens Cartography、独立种子与关系入口召回

**版本**：V3.11 Rev3
**日期**：2026-07-18
**性质**：对 V3.11 Rev2 的活动纠偏；不废止 Recall Lens、真实 Junction、即时 Capture、异步吸收、V3.9 Coverage 或单入口 Recall
**输入检查点**：`f9f01f56906c5ce64df4a4702f61d954a8402fb8`
**输入 Bundle**：`nollm_caold_field_complete_atlas_realized_junction_causal_loop_20260718_f9f01f5.bundle`
**输入 Bundle SHA-256**：`a804e14167408a3fb81c79adad336aa69174d101325d4ff3349cf8a38fa0cdb6`
**输入状态**：`CAOLD_FIELD_COMPLETE_ATLAS_CAUSAL_LOOP_IN_PROGRESS`
**检查点重新定性**：`FIELD_COMPLETE_ATLAS_AND_REALIZED_JUNCTION_CHECKPOINT_AT_f9f01f5`
**状态**：活动目标架构；不表示已经实现

---

# 0. 修订结论

`f9f01f5` 已经修复：

```text
Atlas coverage certificate；
projection 不再抽样后冒充完整；
Atlas overflow；
Core realized-only Junction；
Writer plan 真正写入同一字段；
durable reopen；
Writer Lens relation groups 的强制入口可以经几何到达目标；
一个 Provider-backed 东京长分支。
```

但仍有四个直接影响 Architecture is the Index 的问题：

```text
1. Provider Reader 10/10 全部选择目标事实自己的 Cell，
   目标 path 全为空。
   它证明“LLM看到目标文本后会选目标”，
   没有证明“Writer塑造的关系入口会把目标找回来”。

2. write Atlas 虽然字段完整，却不是 LLM 负担有界：
   300 occupied Cells 的 Dream Sculptor Prompt 约400 KB；
   1027 Cell 紧凑字段约768 KB；
   Provider Writer平均约112秒。
   字段完整被错误等同为一次把整个字段序列化给LLM。

3. production fast Recall 仍取：
   occupied Cells stable-key 前32个。
   40 Cell字段中q=39的目标根本不进入Reader视野。
   写入Atlas完整，读取入口却再次退化为坐标前缀。

4. 非空字段中的完整独立事实若没有resolved Lens，
   `new_local/expand_surface` 会被拒绝。
   这迫使LLM把新事实错误依附到已有Locality，
   或永久retry/defer。
   自由新簇和关系中性种子没有真正实现。
```

本修订确立：

> **LLM 不应一次吞下完整字段；一个 LLM 先形成命题和未来问题，另一个受同一后台任务约束的 Cartographer 用这些问题逐步读取 Prompt 有界、字段完整的几何 Atlas。Writer 与 Cartographer 都不输出坐标。没有现成关系的完整事实作为关系中性种子写入，而不是被价值过滤或强制挂靠。未来 Reader 的因果证据必须从关系入口以非空几何路径到达目标，不能直接选择目标 Cell 自证。**

---

# 1. 能力重新定性

`f9f01f5` 可以证明：

```text
Atlas的source-cell union可覆盖当前FieldScope；
realized-only Junction代码合同成立；
Lens relation groups会影响Writer target Cell；
10个Provider Writer结果被真实写入；
每个Writer target可从两个relation-group Cell经两步lateral到达；
一个Provider东京arm长度2成立；
Manifest、Evidence和工作树可复现。
```

它没有证明：

```text
Reader从关系入口找到Writer target；
Reader成功依赖Lens塑造的几何；
大字段Prompt可接受；
大字段Recall入口完整；
独立新事实可以成为新簇种子；
东京/时间/天气三分支都能自然生长；
当前one-cell模型在真实场中足够。
```

---

# 2. 教 LLM 使用 LLM：角色分离

## 2.1 Proposition Writer

第一后台语义角色只看：

```text
不可变Capture；
同批次Capture provenance；
时间解析上下文。
```

输出：

```text
完整MemoryStatements；
每条Statement的1～4个future Recall Lenses；
exact basis spans；
source_capture_ids；
是否明显no-memory/defer。
```

Writer 不看 Atlas，不选择 Locality，不输出 action、Handle、坐标或 region ID。

这样：

```text
Statement形成不再被Field大小阻塞；
无相关Locality的完整事实仍能形成；
Writer Prompt与字段规模无关。
```

## 2.2 Field Cartographer

第二后台语义角色只看：

```text
Writer Statements/Lenses；
Prompt有界的Atlas当前页；
operation-local traversal state。
```

Cartographer 为每个 Lens：

```text
选择一个Atlas region并继续下降；
选择一个可执行leaf Locality；
或标unresolved。
```

它还提出：

```text
related_growth；
independent_seed；
reuse/revision inspection；
defer。
```

Cartographer 不修改 Statement，不输出 q/r，不创建 Topic/Entity。

## 2.3 Local Resolver

如果某个已选 Locality 内存在多个 current Statements，且需要判断：

```text
reuse；
revision_current；
additive new；
different subject；
```

Access 可以在同一 Cartographer operation/session 中提供一个有限 local detail page。

只有该异常路径需要额外 Cartographer turn；不得为所有新事实预先发送全部 current Statements。

## 2.4 Core

Core 继续只接收：

```text
relation groups；
或 relation-neutral frontier request；
occupied Cells；
固定预算。
```

不接收 Writer text、Lens text、query 或 Atlas语义。

---

# 3. Prompt 有界、字段完整的 Progressive Atlas

## 3.1 字段完整不等于一次全发

Atlas 完整性仍要求：

```text
top-level region source-cell union
=
FieldScope全部occupied Cells。
```

但 LLM 每次只看到：

```text
当前层所有region的有界描述；
或一个已选region的全部child regions。
```

不一次发送所有leaf。

## 3.2 Top-level Order

Access 选择满足以下全部条件的最细 Surface Order：

```text
全部非空projections数量 <= max_regions_per_page；
serialized Atlas page <= max_prompt_bytes；
每个projection有可继续下降或可执行support。
```

建议初始 Policy：

```text
max_regions_per_page = 16～32；
max_prompt_bytes = 32～64 KB；
max_depth <= 4；
max_cartographer_turns <= 4。
```

Policy 可实测调整，不是数学不变量。

## 3.3 完整 region page

禁止：

```text
stable-key prefix；
even sample；
只发前N个region；
query语义预筛选。
```

当前 page 必须包含该 parent 下全部非空 child regions。

若 child 数仍超预算：

```text
使用更粗的中间层；
或 explicit atlas_page_overflow；
不得抽样。
```

## 3.4 Descend

Cartographer 返回：

```text
open_region；
select_locality；
unresolved；
defer。
```

Access 确定性打开该 region 的下一层完整 child page。

所有 Lenses 在一个 Cartographer session 中批量导航，避免每个 Lens/Statement建立独立会话。

## 3.5 Leaf

Leaf 必须提供：

```text
1～4个真实physical support Cells；
完整source_cell_count；
support radius；
最多3条representative Statements；
truncated；
是否需要local detail。
```

representatives 只是导航提示，不代表全部内容。

## 3.6 Prompt 预算证书

每个 page 记录：

```text
region_count；
serialized_utf8_bytes；
estimated_token_units；
covered_source_cell_count；
uncovered_source_cell_count；
parent identity；
depth；
overflow。
```

活动 page：

```text
uncovered=0；
bytes<=policy budget。
```

---

# 4. Placement 模式

## 4.1 Related Growth

至少一个 Lens resolved：

```text
resolved Lens leafs
→ relation groups
→ realized-only Junction
→ one Cell Admission。
```

多 resolved Lens 必须都被真实实现；否则 correction、部分 unresolved 或 retry。

## 4.2 Independent Seed

一条完整新命题在当前字段找不到可信关系时：

```text
all Lenses unresolved
+
Writer proposition valid
+
Cartographer action=independent_seed
→ Access调用关系中性frontier
→ 创建新Locality seed。
```

它不是：

```text
no_memory；
语义defer；
错误挂靠；
Topic节点。
```

Core 使用现有语义盲 frontier/容量/active-radius 规则。

## 4.3 Reuse/Revision

只有在 selected Locality 的 local detail 中看见 exact current Handle 时才能：

```text
reuse；
revision_current。
```

revision 继续一次确认。

无法检查完整 current context时：

```text
new independent/related fact；
或retry/defer；
不得猜测revision。
```

---

# 5. Relation-entry Recall

## 5.1 Production 入口视图

退出活动路径：

```text
occupied_cells stable-key first32
```

Recall 使用与写入相同的 Prompt-bounded complete Atlas：

```text
query
→ one hidden Reader/Cartographer operation
→ region descent
→ one physical support entry
→ Core single-entry Recall。
```

不得通过 query、Topic 或 embedding 预筛 Atlas。

## 5.2 调用预算

用户前台仍要求：

```text
common hidden calls <=1
```

因此 production Reader 优先使用：

```text
一个包含完整top-level regions和每region有限support entries的Prompt；
Reader同时选择region和一个support entry。
```

若字段大到必须多层下降：

```text
优先合并到主代理的同一工具操作/session；
或显式记录slow_path；
不得恢复每页新建child session。
```

Codex可根据OpenClaw实际工具能力选择最少Provider轮次方案，但必须退出坐标前缀。

## 5.3 Direct target 与 relation reach

生产允许 Reader 直接选择目标 Cell。

但因果验证必须区分：

```text
direct_target_recall：
目标Cell可见，path=[]；

relation_entry_recall：
目标Cell和目标Statement preview从entry候选中排除，
Reader只能选择Writer resolved Lens的relation entry，
目标path必须非空。
```

只有后者证明 Lens→Geometry→Recall。

## 5.4 每个 Lens 的强制入口

对 Writer 每个 resolved Lens：

```text
从该 relation group 的至少一个support Cell
独立单入口 Recall
→ 到达目标Handle
→ path非空。
```

多个 Lens 分别执行，不合并入口。

## 5.5 大场完整性

至少验证：

```text
40 occupied Cells，目标位于stable-key第40位；
新Reader Atlas仍能暴露目标所在region；
旧first32路径明确失败；
新路径成功。
```

---

# 6. Provider Writer→Cartographer→Field→Reader

每个真实案例：

```text
Capture；
Provider Writer形成Statement+Lenses；
Prompt-bounded Cartographer解析Atlas；
related_growth或independent_seed；
Access/Core实际Admission；
durable reopen；
独立Reader不见Writer Lens；
Reader候选隐藏target Cell/preview；
Reader从relation entry到达target；
same-field unrelated entry不达。
```

记录：

```text
Writer raw；
Cartographer全部turn raw；
Atlas page certificates；
Placement mode；
Junction/seed；
target Handle；
relation-entry path；
direct-target control；
unrelated control；
final state SHA。
```

---

# 7. 东京—时间—天气

## 7.1 T0

```text
2026年7月18日东京下雨。
```

如果字段中没有可信东京/时间/天气关系：

```text
independent_seed。
```

不得因 Lens unresolved 拒绝完整事实。

## 7.2 Arms

通过正常Capture/Writer/Cartographer逐步形成：

```text
东京arm >=2；
时间arm >=2；
天气arm >=2；
unrelated arm >=2。
```

## 7.3 Recall

三个独立查询：

```text
目标Cell隐藏；
从三个arm外端或其Atlas support进入；
path>=2；
同一T0 Handle；
unrelated同预算不达。
```

---

# 8. 模型调用与效率

## 8.1 后台吸收

Common batch：

```text
Writer calls = 1；
Cartographer session = 1；
Cartographer turns <=4；
每个Statement不重新建立session；
revision confirmation例外。
```

关键指标：

```text
prompt bytes；
turn count；
provider seconds；
captures/Statements per batch；
backlog drain rate。
```

## 8.2 禁止巨大单 Prompt

Gate：

```text
300 Cell字段任何单个Writer/Cartographer Prompt <=64 KB；
1000+ Cell字段任何单个Prompt <=64 KB；
不得出现400～768 KB Atlas Prompt。
```

若当前Provider需要更小，Codex可下调。

## 8.3 Capture

即时Capture和V3.10 worker正确性不回退。

---

# 9. 持久状态

持久：

```text
raw Capture；
MemoryStatement；
HandleBinding；
Core Atom/Cell；
worker状态。
```

不持久：

```text
Recall Lens；
future_query；
Atlas pages/paths；
Cartographer traversal；
relation-entry candidates；
query→entry；
fact→entries。
```

---

# 10. 禁止路线

```text
用importance过滤完整事实；
强制独立事实挂靠；
一个768KB完整Atlas Prompt；
stable-key first32 Recall；
target Cell直达冒充relation causality；
Topic/Entity；
query/fact entry map；
embedding/vector/graph；
multi-entry Recall；
多Cell Atom；
多物理层；
Stitch；
生产语义摘要索引。
```

---

# 11. 最终架构概括

```text
Writer只负责把经历变成命题和未来问题。

Cartographer拿着这些问题，
逐页读取一个完整但Prompt有界的几何地图，
把问题翻译成真实Locality。

有关系就长在关系交汇处；
没有关系就成为新的中性种子。

未来Reader不能靠直接看见目标文本证明成功，
而要能够从Writer当初选择的关系入口，
沿非空几何路径找到同一个Atom。
```

> **教 LLM 使用 LLM，不是让一个模型一次吞下整个字段，而是让一个 Writer 提出未来问题，让一个 Cartographer 用这些问题操作几何，让未来 Reader 只依赖最终字段。**
