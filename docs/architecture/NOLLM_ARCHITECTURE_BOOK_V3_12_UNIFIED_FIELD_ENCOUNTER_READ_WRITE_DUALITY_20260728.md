# Nollm 架构书 V3.12：统一场相遇、读写对偶与事实／空位终态

**版本**：V3.12
**日期**：2026-07-28
**性质**：对 V3.11 Rev6 及其后续内容中立纠偏的根本操作模型修订
**主题**：读与写共享同一次场进入、同一套渐进几何导航、同一个 Locality 重建和同一套语义比较；只有在遇到对应事实或合法空位后，才决定召回、复用、修订、放置、NONE 或暂缓
**实现状态**：目标架构；不表示已经实现
**最近可核验输入检查点**：`8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea`
**输入 Bundle**：`nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_8f19a9b.bundle`
**输入 Bundle SHA-256**：`1b573f62d2245ab65c1a52d437ca1e7d86b1bf59cc2a1e1420a2f7e41463f8a8`
**动态基线规则**：执行时如仓库 `CURRENT_STATUS`、模块进度账和 clean HEAD 已领先上述检查点，应采用仓库登记的最新活动 HEAD，不得 reset 回旧检查点；必须记录差异并以当前代码事实为准

---

# 0. 架构结论

Nollm 不应在进入记忆场之前先决定：

```text
这是一次读取；
或
这是一次写入。
```

Nollm 只有一种核心语义操作：

```text
Field Encounter
场相遇
```

统一路径：

```text
当前刺激
  可能只有问题；
  可能只有待形成/待吸收命题；
  也可能同时包含问题和新命题
        ↓
固定结构预算生成 Active Surface
        ↓
真实 LLM 在同一 operation 中分页、打开 region、下降
        ↓
选择一个最终物理入口
        ↓
Core 通过 Coverage / Lateral / 已有 Bridge
重建一个有界 Locality
        ↓
Access 同时投影：
  Locality 内现有事实；
  Locality 内合法空位；
  几何边界扩展空位；
  关系中立 seed 空位
        ↓
真实 LLM 判断最终接触对象
        ↓
遇到对应事实：
  Recall / Reuse / Revision

遇到合法空位：
  Placement；
  若没有待写命题则 NONE

无法判断：
  Continue / Retryable Defer

预算耗尽：
  NONE 或 Retryable Exhausted
```

因此：

> **读写不是两条寻路流程，而是同一次场相遇在不同终态下产生的不同效果。**

---

# 1. 权威关系与修订范围

## 1.1 继续有效

本架构继续遵守：

```text
NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md；
V3.1 Core Purity；
V3.4 Core Function Priority；
V3.7 Rotated Physical Memory Field；
V3.9 Bounded Approximate Coverage；
V3.10 Durable Capture / Async Absorption；
V3.11 已验证的 Prompt-bounded Atlas、realized Junction、
Statement provenance、single-entry、Raw Capture 和 scope 隔离能力。
```

继续有效的硬物理参数：

```text
Δθ = 22.5°
θ0 = 0°
θL = L × 22.5° mod 60°
β = 2^(1/4)
β² = √2
```

继续有效的边界：

```text
Architecture is the Index；
Core 语义盲；
真实 LLM 负责语义判断；
无 graph/vector/embedding 主路径；
无 Topic/Entity/query/fact 关系索引；
无持久 Cursor、recent entry、query→cell；
single-entry Recall；
one Statement / Atom / Handle / Cell；
Surface 为可重建派生状态；
原始 Raw Capture 不丢失。
```

## 1.2 被本架构替换的操作模型

以下“先分读写、再各自导航”的活动设计被替换：

```text
Query
→ 独立 Recall routing
→ entry
→ Locality
→ answer

Capture
→ Writer
→ 独立 Cartographer routing
→ placement candidate
→ admission
```

替换为：

```text
Stimulus
→ Unified Field Encounter
→ fact contact / vacancy contact
→ effect resolution
```

## 1.3 被吸收而非删除的纠偏

后续内容中立任务中的以下要求并入本架构：

```text
canonical memory 对内容类别中立；
来源角色只作 provenance；
不得用 sensitive/secret/temporary/tool-noise
决定是否进入 canonical memory；
no_memory 不作为永久终态；
defer 可重试；
oversize 与命题数量上限必须 continuation；
预算不能变成内容淘汰；
scope 隔离优先于内容分类；
历史 secret/stable promotion 不得回到活动路径。
```

V3.11 Rev6 中以内容类别进行 routing preview redaction 的局部方案不再作为活动要求。私有 Surface 的访问安全由真实 Host scope、workspace 和 operation 绑定保证；统一 preview 使用内容中立、固定预算、可复现的截取规则。

---

# 2. 为什么读写分离是错误抽象

当前读写分离产生四种结构性浪费。

## 2.1 重复理解

```text
Formation LLM 理解一次当前经历；
Placement/Cartographer 再理解一次；
以后 Recall 又理解一次。
```

## 2.2 重复导航

```text
Placement 浏览 Surface、进入 Locality；
Recall 又浏览同一 Surface、进入同类 Locality。
```

## 2.3 过早确定操作性质

新刺激在进入场之前并不知道：

```text
它是否已存在；
是否是旧事实修订；
是否与现有事实相关但不同；
是否完全无关；
是否只需要读取；
是否同时需要读取和放置。
```

先标记“read”或“write”，等于在接触记忆场之前替场作出结论。

## 2.4 进场等待最终位置

把写入理解为独立 Placement，会要求新命题在正式进入场前完成一次专门的语义搜索；这使语义进场时间由串行 Provider 调用决定。

统一 Field Encounter 后，系统只进行一次场探索；发现事实即处理事实，发现空位即处理空位。

---

# 3. 六类陈述类型

架构和任务书中的重大要求继续标注为：

| 类型 | 含义 |
|---|---|
| `INVARIANT` | 所有合法实现必须成立 |
| `PHYSICAL_CONTRACT` | 旋转、尺度、Coverage 等物理模型 |
| `POLICY` | 当前可版本化实现选择 |
| `BUDGET` | 资源和调用上限 |
| `OBSERVATION` | 某次运行或数据集结果 |
| `HYPOTHESIS` | 尚待验证的推断 |
| `LIMITATION` | 当前明确未实现能力 |

本架构的核心“读写共享 Field Encounter”属于 `INVARIANT`。

---

# 4. 核心不变量

## 4.1 操作中立

`INVARIANT`：

```text
Field Encounter 请求不得含有：
  intent = read；
  intent = write；
  mode = recall；
  mode = placement。
```

请求可以包含或不包含待写命题，但这只是可提交载荷是否存在，不是预先决定操作结果。

## 4.2 同一路径

`INVARIANT`：

```text
问题、待吸收命题和混合刺激共享：
  Active Surface；
  progressive pages；
  open_region；
  final entry；
  bounded Locality；
  fact comparison；
  vacancy projection。
```

## 4.3 终态决定效果

`INVARIANT`：

```text
遇到对应事实后才允许：
  Recall / Reuse / Revision。

遇到合法空位后才允许：
  Placement。

未遇到事实且无待写命题：
  NONE。

无法可靠判断：
  Continue 或 Retryable Defer。
```

## 4.4 Probe 与 Commit 分离

`INVARIANT`：

```text
统一语义操作
≠
Core 把读取和 mutation 混成无边界事务。
```

Field Encounter 在提交前保持只读。最终写入通过单独的条件原子提交完成，但仍属于同一 operation。

## 4.5 路径不持久化

`INVARIANT`：

```text
Surface page；
region path；
selected entry；
Locality view；
vacancy candidate；
LLM decision context
```

均为 operation-local，结束即删除。

## 4.6 Capture 独立

`INVARIANT`：

```text
Raw Capture 先于或独立于 Field Encounter 持久化；
Field Encounter 失败不得导致 Raw Capture 丢失；
Capture 成功不等于 Admission；
Field Encounter 路径不是 Evidence。
```

---

# 5. 系统总流程

## 5.1 用户问题

```text
User query
→ publish immutable user Capture
→ main agent opens Field Encounter
→ progressive geometry navigation
→ final entry
→ Locality + legal vacancies
→ corresponding fact found
→ Recall result
→ main agent natural answer
→ publish assistant Capture
```

如果没有对应事实：

```text
Field Encounter reaches vacancy / exhausted
→ no pending proposition
→ NONE
→ main agent continues without memory injection
```

## 5.2 后台命题吸收

```text
Raw Capture
→ one hidden Encounter Writer session
→ form candidate proposition
→ continue in the same session into Field Encounter
→ progressive geometry navigation
→ Locality + vacancies
→ exact fact found:
     reuse
→ old version found:
     provisional revision / confirmation
→ no corresponding fact, related locality:
     local or junction vacancy
→ no corresponding fact, unrelated:
     neutral seed vacancy
→ conditional atomic commit
→ reopen verification
```

禁止恢复：

```text
Writer session结束
→ 再创建独立Cartographer session
```

常见吸收路径应由一个隐藏 Host session 覆盖“形成命题＋进入场＋终态选择”。

## 5.3 混合刺激

用户同一条消息可能同时：

```text
询问旧记忆；
陈述一个新事实。
```

流程：

```text
publish user Capture
→ form pending proposition candidate
→ one Field Encounter
→ recall related old fact
→ compare new proposition
→ same operation chooses:
     reuse / revision / related vacancy / neutral vacancy
→ main agent回答
→ mutation在条件提交阶段完成或进入后台确认
```

不要求为“读取部分”和“写入部分”分别重新浏览字段。

---

# 6. Capture、Formation、Encounter、Admission 的职责

## 6.1 Capture

```text
保存原始 user / assistant / tool 可见材料；
零语义；
零 Provider；
零 Core；
append-only；
可重开。
```

## 6.2 Formation

Formation 只回答：

```text
当前材料是否产生一个或多个完整、独立、有意义的命题；
命题的精确 Evidence provenance 是什么。
```

Formation 不回答：

```text
这是写操作；
应写入哪个 Cell；
应召回什么；
是否存在空位。
```

## 6.3 Field Encounter

Field Encounter 回答：

```text
当前刺激在字段中遇到了什么；
对应事实是否存在；
若不存在，哪个合法空位可承接；
当前语义关系属于 same / revision / related-distinct / unrelated / uncertain。
```

## 6.4 Admission

Admission 是 Field Encounter 终态产生的持久 mutation：

```text
new；
reuse binding；
confirmed revision；
move；
future stitch。
```

Admission 不是导航过程。

---

# 7. Field Encounter 公共合同

## 7.1 Request

建议公共合同：

```text
FieldEncounterRequest
  operation_id
  scope_id
  workspace_id
  stimulus_material
  optional_pending_proposition
  field_scope
  surface_budget
  locality_budget
  vacancy_budget
  expected_state_identity
```

### `stimulus_material`

可包含：

```text
query text；
current user utterance；
bounded conversation context；
operation-local model inference。
```

不得持久化为 query 索引。

### `optional_pending_proposition`

可为空；若非空，至少包含：

```text
proposition_id；
content_utf8；
Evidence refs；
origin kinds；
derived_from_statement_ids；
formation schema/version。
```

其存在只表示：

```text
如果 Field Encounter 遇到合法空位，
存在可以提交的内容。
```

不表示必须写入。

## 7.2 Operation state

```text
FieldEncounterOperation
  operation_id
  run/session/scope/workspace
  core_state_identity
  current_page
  page_stack
  selected_region_path
  selected_entry
  Locality identity
  candidate fact cards
  candidate vacancy cards
  tool call count
  created_at / TTL
```

全部 operation-local。

## 7.3 Actions

活动动作：

```text
surface
open_region
enter_locality
expand_same_entry
select_fact
select_vacancy
none
defer
cancel
```

不得有：

```text
read
write
placement_mode
recall_mode
select_entries
query_search
topic_route
```

## 7.4 Terminal result

```text
FieldEncounterResult
  terminal_kind:
    fact
    vacancy
    ambiguous
    exhausted

  selected_fact_id?
  selected_vacancy_id?
  semantic_relation?
  recalled_statement_ids
  state_identity
  path_digest
  commit_eligibility
```

`path_digest` 只用于同 operation 验证，不成为跨会话入口。

---

# 8. 统一状态机

```text
CREATED
  ↓
SURFACE
  ↓
REGION*
  ↓
ENTRY_SELECTED
  ↓
LOCALITY_RECONSTRUCTED
  ↓
CONTACT_EVALUATION
  ├─ FACT_CONTACT
  ├─ VACANCY_CONTACT
  ├─ AMBIGUOUS
  └─ EXHAUSTED
        ↓
EFFECT_RESOLUTION
  ├─ RETURN_RECALL
  ├─ RETURN_NONE
  ├─ RETURN_REUSE
  ├─ PROVISIONAL_REVISION
  ├─ CONDITIONAL_PLACE
  └─ RETRYABLE_DEFER
        ↓
COMMIT_OR_RETURN
        ↓
CLOSED
```

`REGION*` 表示零到多次渐进下降。

---

# 9. Surface 与渐进导航

## 9.1 初始 Surface 与操作性质无关

相同：

```text
Core state；
FieldScope；
结构预算；
Profile
```

必须产生相同 root Surface，不受以下内容影响：

```text
query；
pending proposition；
user intent；
read/write预设；
历史命中。
```

## 9.2 有限语义观察

几何先决定：

```text
region；
region membership；
parent/child observation；
leaf entries。
```

Access 再按固定、内容中立规则展示极少量真实 Statement preview，帮助 LLM 看懂几何现场。

禁止：

```text
Python 读取 query 后选择 preview；
关键词/实体聚类；
embedding；
Topic label；
持久 route label。
```

## 9.3 内容中立 preview

统一算法：

```text
每 region 固定 representative count；
按 GeometryAddress / Handle 稳定顺序；
固定 codepoint 截取预算；
统一 truncated 标志；
不根据内容类别隐藏、淘汰或修改 canonical memory。
```

私有 preview 的读取由真实 scope/workspace/operation 约束。

## 9.4 单入口

无论最终发生 Recall 还是 Placement：

```text
同一次 Field Encounter 最终只选择一个物理 entry。
```

空位必须从该入口 Locality 或其合法几何 frontier 中产生；关系中立 seed 是明确的特殊 vacancy 类，不是第二个 Recall 入口。

---

# 10. Locality 中同时展示事实与空位

## 10.1 Existing fact cards

每个现有事实卡至少包含：

```text
operation-local fact_id；
current Statement；
Handle；
几何路径摘要；
是否可作为 revision target；
provenance摘要；
truncated/expand状态。
```

## 10.2 Vacancy cards

每个空位卡至少包含：

```text
operation-local vacancy_id；
vacancy_kind；
GeometryAddress；
capacity/boundary状态；
与当前 entry 的几何关系；
realized relation groups；
free faces；
state identity；
expires with operation。
```

## 10.3 空位类别

```text
LOCAL_VACANCY
  当前 Locality 内有容量，适合相关但不同的命题。

BOUNDARY_VACANCY
  当前 Locality 的合法边界扩展。

JUNCTION_VACANCY
  Core 真实实现多个 relation groups 的 Junction 候选。

NEUTRAL_SEED_VACANCY
  与现有局部保持关系中立隔离的新 seed。
```

空位不是事实，不进入 Core state，直到条件提交成功。

---

# 11. “找到空位”不能退化为找第一个空 Cell

禁止：

```text
stable-key spiral
→ first empty Cell
→ placement
```

合法 vacancy 必须由几何生成并满足：

```text
地址合法；
Cell容量允许；
Coverage边界可计算；
与选中 Locality 的关系类型明确；
不因插入顺序形成未声明强关系；
neutral seed满足固定隔离；
Junction必须all_groups_realized；
state identity仍有效。
```

Python 只生成几何候选，不判断语义是否相关。

---

# 12. 语义比较合同

真实 LLM 在选中 Locality 后，对 pending proposition 与现有事实进行比较。

活动关系：

```text
same
revision
related_distinct
unrelated
uncertain
```

## 12.1 same

```text
现有事实已经表达同一命题；
不新增 Atom；
可返回 Recall；
有pending proposition时执行reuse/provenance支持。
```

## 12.2 revision

```text
新命题替代或更新现有当前事实；
先产生provisional revision；
确认前零写；
确认时重算state和provisional identity。
```

## 12.3 related_distinct

```text
不是同一事实；
属于当前 Locality 或 realized Junction；
应选择合法 vacancy；
不得合并成旧事实。
```

## 12.4 unrelated

```text
现有 Locality 无对应关系；
若有pending proposition，选择neutral seed vacancy；
若无pending proposition，返回NONE。
```

## 12.5 uncertain

```text
在预算内继续比较；
预算不足则retryable_defer；
不得强制写入或复用。
```

Python 不得通过 hash、关键词、固定分数或伪相似度产生上述关系。

---

# 13. 终态效果矩阵

| 刺激携带待写命题 | Encounter 终态 | 语义关系 | 效果 |
|---|---|---|---|
| 否 | fact | relevant | Recall |
| 否 | vacancy | — | NONE |
| 否 | exhausted | — | NONE |
| 否 | ambiguous | — | Continue / no-memory fallback |
| 是 | fact | same | Reuse；可同时Recall |
| 是 | fact | revision | Provisional Revision |
| 是 | vacancy | related_distinct | Local/Boundary/Junction Placement |
| 是 | vacancy | unrelated | Neutral Seed Placement |
| 是 | ambiguous | uncertain | Retryable Defer |
| 是 | exhausted | — | Retryable Exhausted |
| 是，且同时有问题 | fact/vacancy | 任一合法关系 | Recall 与 mutation effect 可在同 operation 形成 |

最终持久 mutation 必须经过条件提交。

---

# 14. Core：只读 Probe 与原子 Commit

## 14.1 Core 不理解 Field Encounter 语义

Core 继续只负责：

```text
Surface结构；
Coverage/Lateral/Bridge传播；
Cell occupancy；
Locality重建；
合法 vacancy 几何候选；
capacity/boundary/budget验证；
原子 mutation；
canonical state；
reopen。
```

Core 不理解：

```text
query；
pending proposition；
same/revision/related/unrelated；
Recall还是Placement；
用户；
会话；
来源角色；
内容类别。
```

## 14.2 Probe

Access 使用现有或组合后的 Core 公共能力完成只读阶段：

```text
surface / page；
bounded recall；
occupancy；
frontier；
Junction candidate；
state export/hash。
```

第一任务默认不新增 Core 公共 API。

## 14.3 Conditional Commit

建议 Access 内部提交合同：

```text
EncounterCommitRequest
  operation_id
  expected_core_state_identity
  terminal_result_identity
  pending_proposition_identity
  selected_vacancy_or_fact_identity
  mutation_commands
```

提交前重新检查：

```text
Core state未陈旧；
fact仍current；
vacancy仍空且合法；
capacity仍允许；
provisional revision仍一致；
operation未过期；
scope/workspace未变化。
```

失败：

```text
零写；
返回 stale_encounter；
重新进入或重算 Locality。
```

---

# 15. 读写对偶的具体形式

## 15.1 对偶对象

```text
Fact contact
↔
Vacancy contact
```

## 15.2 对偶结果

```text
Fact contact + no pending proposition
→ Recall

Vacancy contact + pending proposition
→ Placement
```

## 15.3 中间情形

```text
Fact contact + pending proposition
→ Reuse / Revision

Vacancy contact + no pending proposition
→ NONE
```

因此“读”和“写”不是完全相同的结果，但它们由同一场接触结构决定。

---

# 16. 同一 operation 的复用

Field Encounter 结束前可以同时产生：

```text
recalled_statement_ids；
selected_fact_or_vacancy；
pending mutation effect；
answer context。
```

禁止在同一轮再次启动另一套完整 Surface Traversal，除非：

```text
state已变化；
操作过期；
LLM明确请求新的独立刺激；
预算已耗尽且进入后续重试。
```

当前轮的路径只在 operation 内复用，不能保存成下一轮 Cursor。

---

# 17. Provider 调用拓扑

## 17.1 前台查询

目标：

```text
主代理自身 run
→ Field Encounter 工具循环
→ Recall / NONE
```

禁止默认创建独立 hidden Reader child-agent。

## 17.2 后台吸收

目标：

```text
一个隐藏 Encounter Writer session
→ 形成命题
→ 同session使用Field Encounter工具
→ 选择fact或vacancy
→ commit
```

禁止：

```text
Formation Provider call
→ 新建Cartographer Provider call
```

## 17.3 调用次数是预算，不是语义

`BUDGET`：

```text
普通单命题批次：
  一个隐藏Host session；
  可有多次同session tool turn；
  不创建第二语义agent session。

主代理query：
  hidden Reader child = 0。
```

实际延迟和调用数必须实测，不得预写 SLA。

---

# 18. Persistence 与派生状态

## 18.1 Canonical persistent state

```text
Raw Capture；
MemoryStatement；
Statement provenance；
Handle bindings；
Core Physical Cell / Atom / Bridge state；
必要的 absorption/evaluation 状态。
```

## 18.2 Derived deletable state

```text
Surface；
routing previews；
region pages；
candidate fact/vacancy IDs；
Locality view；
operation path；
state fingerprint cache。
```

## 18.3 禁止持久化

```text
query→entry；
query→region；
pending proposition→entry；
fact→entries；
recent encounter；
last vacancy；
LLM path；
operation candidate IDs。
```

---

# 19. 内容中立与作用域安全

## 19.1 canonical 内容中立

生产代码不得因为以下类别拒绝形成或进入 memory：

```text
password；
secret；
credential；
weather；
temporary；
medical；
financial；
legal；
assistant；
tool；
short-lived；
low-value。
```

语义结果由 LLM 比较决定：

```text
same / revision / new / zero delta / defer。
```

## 19.2 preview 内容中立

Routing preview 使用统一截取，不因类别使用不同算法。

## 19.3 安全边界

```text
scope；
workspace；
Host identity；
operation binding；
tool visibility；
explicit forget；
explicit export/share policy。
```

不是：

```text
内容分类过滤。
```

---

# 20. Failure 与恢复

至少处理：

```text
无效operation/page/region/fact/vacancy ID；
stale Core state；
过期operation；
选择未展示对象；
Surface overflow；
Locality budget exhausted；
Provider timeout；
JSON无效；
Formation continuation；
revision confirmation超时；
vacancy已被占用；
commit成功但readback失败；
Gateway restart；
mixed turn部分完成。
```

要求：

```text
Raw Capture不丢；
Recall失败开放；
未确认revision零写；
stale encounter零写；
partial commit不得产生孤儿Statement；
commit结果区分committed / not_committed / unknown_after_commit；
下一次可重试；
插件不清空旧数据。
```

---

# 21. 模块所有权

## Core

保持：

```text
物理几何；
Surface；
Coverage/Lateral/Bridge；
occupancy；
Locality传播；
几何vacancy候选；
原子state mutation。
```

不新增语义。

## Access

新增并拥有：

```text
FieldEncounterRequest/Operation/Result；
progressive page与path；
Locality事实卡；
vacancy卡；
事实/空位终态验证；
effect resolver；
conditional commit；
stale重算；
query-only / proposition-only / mixed组合。
```

## OpenClaw

拥有：

```text
main-agent Field Encounter工具；
隐藏 Encounter Writer session；
Formation后同session继续导航；
operation生命周期；
Raw Capture hook；
visible answer；
Provider/model证据。
```

## Lab

拥有：

```text
读写双流程反例；
统一状态机fixtures；
query-only/write-only/mixed Live；
same/revision/related/unrelated；
vacancy种类；
single-session调用证据；
延迟和消融；
无外置索引扫描。
```

## Distributions

只声明：

```text
Field Encounter wire版本；
operation budgets；
active profile；
tool actions；
legacy Recall/Placement paths禁用；
feature flags。
```

Snapshot、Trace、History、Audit 不改变。

---

# 22. Wire 建议

```text
nollm_openclaw_field_encounter_v1
nollm_access_field_encounter_v1
nollm_encounter_writer_v1
```

示例终态动作：

```json
{
  "action": "select_fact",
  "fact_id": "operation-local-id",
  "relation": "same"
}
```

```json
{
  "action": "select_vacancy",
  "vacancy_id": "operation-local-id",
  "relation": "related_distinct"
}
```

禁止：

```json
{
  "mode": "write",
  "target_cell": "arbitrary-address"
}
```

禁止：

```json
{
  "mode": "read",
  "query": "passed-to-python-search"
}
```

---

# 23. 迁移原则

## 23.1 复用现有资产

优先复用：

```text
Prompt-bounded Atlas；
progressive Surface pages；
main-agent run-scoped operation；
bounded Locality；
realized Junction；
independent seed；
revision provisional/confirmation；
Raw Capture；
Statement provenance；
Access atomic coordination；
OpenClaw tool hooks。
```

不得重造第二套：

```text
Field graph；
vector route；
Topic table；
new Surface engine；
new Core runtime。
```

## 23.2 旧路径处理

以下活动路径在替代验证完成后退出：

```text
独立 Recall operation state machine；
独立 Placement/Cartographer operation state machine；
Writer结束后另起Cartographer session；
read/write mode flags；
不同格式的Recall page和Placement Atlas page。
```

处理顺序：

```text
建立统一合同；
双路径适配到统一合同；
验证行为等价；
切换活动Wire；
旧路径进入MIGRATION_REFERENCE；
达到REMOVABLE后删除。
```

不得在无替代时直接删除。

---

# 24. Validation Invariants

## 24.1 结构一致

```text
同state/scope/budget：
query-only、write-only、mixed的root Surface完全一致；
差异只来自LLM选择，不来自Python语义路由。
```

## 24.2 读终态

```text
对应事实→Recall；
无对应事实→NONE；
不产生mutation；
single-entry；
无hidden Reader child。
```

## 24.3 写终态

```text
same→reuse；
revision→provisional/confirmed；
related-distinct→local/junction vacancy；
unrelated→neutral seed；
uncertain→retryable defer；
无独立Cartographer session。
```

## 24.4 混合终态

```text
一条用户消息同时包含问题和新事实；
同一operation完成旧事实Recall和新命题effect resolution；
不进行第二次完整Surface Traversal。
```

## 24.5 原子性

```text
stale→零写；
vacancy竞争→零写或重试；
provisional未确认→零写；
commit/readback状态明确；
duplicate/orphan=0。
```

## 24.6 防漂移

```text
无query/fact index；
无Topic/Entity；
无vector/graph/embedding；
无persistent path；
无multi-entry；
无Python语义关系判断；
Core无query或Statement语义。
```

---

# 25. 性能目标的正确表达

本架构不把本地毫秒优化当作主要目标。

需要测量：

```text
Capture publish latency；
query→first Surface；
Surface/open/locality本地耗时；
Field Encounter Host session数；
Provider wall time；
query→visible answer；
Capture→Encounter terminal；
terminal→commit/reopen；
旧双流程与统一流程调用数差异。
```

目标方向：

```text
Capture继续前台毫秒级；
普通写入不再串行创建Formation和Cartographer两个语义session；
同一轮读写不再重复完整Surface导航；
读取和写入共享缓存与operation状态；
最终归位无需第二次全场搜索。
```

这些是待验证目标，不是已完成结论。

---

# 26. 非目标

本架构不启动：

```text
multi-cell footprint；
多物理层Placement；
Stitch最终合同；
多Chart Atlas；
Topic/Entity；
vector/graph/embedding；
query/fact index；
multi-entry Recall；
History/Audit产品；
PB规模；
Provider更换；
模型训练；
正式发布；
安全内容分类器。
```

---

# 27. 最终架构概括

```text
Capture保存经历；
Formation产生命题；
Field Encounter进入记忆场。

进入场时不说自己要读还是要写。

同一套Surface，
同一条渐进路径，
同一个入口，
同一个Locality，
同时面对已有事实和合法空位。

遇到对应事实：
  读取、复用或修订。

遇到合法空位：
  有待写命题则放置；
  没有待写命题则NONE。

Core只负责几何和原子提交；
LLM只在有限可见候选中判断语义；
路径只活在本次operation中。
```

> **Nollm 的基本动作不是 read，也不是 write，而是进入场并与场相遇；读写只是相遇后的两种结果。**
