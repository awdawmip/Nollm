# Nollm CAOLD：LLM 编译召回视角、交汇放置与逆向场生长任务书

**任务文件名**：`NOLLM_C_A_O_L_D_LLM_COMPILED_RECALL_LENS_JUNCTION_GROWTH_TASK_20260717.md`  
**日期**：2026-07-17  
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**可验证结果**：真实 LLM 在一次批量 Dream 操作中形成完整 Statement、模拟未来 Recall Lenses、选择有限 Localities；Core 将事实写入边界/交汇 Cell；后续自然事实逆向生长后，可从东京、绝对时间和天气三个独立单入口到达原事实  
**输入 Bundle**：`nollm_aold_durable_capture_async_absorption_20260717_4f8b1c4.bundle`  
**输入 Bundle SHA-256**：`8336569247865e25db94d50b237e58926d77f8421b9b7efcab1753b93647d521`  
**输入分支**：`codex/aold-durable-capture-async-absorption-fast-recall`  
**输入 HEAD**：`4f8b1c479a2634d3c1b6ae8039116154864275aa`  
**输入状态**：`AOLD_DURABLE_CAPTURE_ASYNC_ABSORPTION_IN_PROGRESS`  
**建议分支**：`codex/caold-llm-recall-lens-junction-growth`  
**主环境**：Windows 10/11、PowerShell、Node 24、当前真实 OpenClaw / LongCat-2.0  
**交付**：大跨度单任务；内部 Gate；普通问题就地修复；所有进展 commit；工作树 clean；仓库外单一完整历史 Git Bundle  
**插件状态**：保持安装并启用  
**数据状态**：旧工作区全部保留；新建 V3.11 工作区；禁止清空、覆盖或强制迁移旧用户数据  
**任务边界**：实现 layer-0 单 Cell Junction Growth；不实现 multi-cell footprint、多物理层语义 Placement、Stitch、多 Chart、PB 长跑或语义索引

---

# 0. 任务推进向量

```text
任务推进向量：
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +15% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +15% | DISTRIBUTIONS +5%

主方向：
先闭合 V3.10 scope/idempotency/provenance 基础；
将 Formation 与 Placement 升级为 LLM Dream Sculptor；
让模型模拟未来 Recall Lenses；
Access 构造有限 Locality Atlas；
Core 生成并求解边界/交汇候选；
事实单点写入、未来事实逆向生长；
用 Writer/Reader/Critic 自博弈验证写入—读取循环一致性；
完成东京/时间/天气三方向独立单入口 Observation。

范围变化：
Core 新增 geometry-only Junction candidate/solver；
Access 新增 Locality Atlas 和 Dream Sculptor plan validation；
OpenClaw 新增 Dream Sculptor Wire/Prompt；
Lab 新增 DC1 资产适配与 LLM self-play；
Distributions 新增版本和预算；
V3.10 Capture/Async Absorption 继续保留并先完成正确性收口。
```

## 0.1 向量解释

```text
CORE +10：
从普通 put/邻接候选增加局部边界和交汇候选计算，不增加语义。

ACCESS +15：
Locality Atlas、Lens/Plan 验证、Junction 编排、batch provenance。

OPENCLAW +10：
一次 Dream Sculptor 调用、Prompt 课程、后台批吸收、低调用 Recall。

LAB +15：
旧 DC1 复用、self-play、cycle consistency、自然三方向场生长 Live。

DISTRIBUTIONS +5：
Wire/Prompt/geometry policy 版本和配置。
```

## 0.2 Gate 开始和结束

每个 Gate 开始复述：

```text
C +10 | S 0 | T 0 | A +15 | H 0 | U 0 | O +10 | L +15 | D +5
```

每个 Gate 结束记录：

```text
实际推进向量；
偏差原因；
新增公共合同；
新增 canonical state；
是否违反单事实单 Atom、单入口 Recall、无持久 Lens；
是否需要更新任务范围。
```

---

# 1. 开工前必须读取

按顺序读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/project/NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md
3. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_3_SEMANTIC_MEMORY_TOOL_20260712.md
4. docs/project/NOLLM_PROJECT_BOOK_V3_4_CORE_FUNCTION_PRIORITY_20260713.md
5. 恢复到仓库中的 V3.7 物理记忆场权威副本
6. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_9_BOUNDED_APPROXIMATE_HEX_COVERAGE_20260715.md
7. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_10_DURABLE_CAPTURE_ASYNC_ABSORPTION_20260717.md
8. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_11_LLM_COMPILED_RECALL_LENS_JUNCTION_GROWTH_20260717.md
9. docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md
10. docs/project/NOLLM_CURRENT_STATUS.md
11. docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
12. 本任务书
13. C/A/O/L/D 模块章程
14. 根目录 AGENTS.md
```

解释优先级：

```text
Evidence 不丢失
> LLM 语义所有权
> Architecture is the Index
> 单事实单 Atom
> 单入口 Recall
> Core 语义盲
> V3.11 写入—读取对偶
> 当前任务实现选择
> 历史任务和报告。
```

---

# 2. 根目录 AGENTS.md

至少加入：

```text
- V3.11 teaches the LLM to simulate future recall lenses before choosing locality.
- Do not ask whether a complete fact is important enough to remember.
- no_memory is limited to no standalone proposition, empty/tool noise, or exact no-new-information cases.
- Recall Lenses are operation-local teaching artifacts, not persistent topics, indexes or Core state.
- Do not persist axis_id, future_query, query->entry, fact->entries, contact candidate IDs or LLM reasoning.
- Reuse DC1 axis/ray concepts only as an ephemeral prompt and Lab asset; do not restore Cortex Store, rule registry, receipts or fixed ontology.
- A Dream Sculptor call may form Statements and plan Placement in one batch.
- The LLM selects supplied Locality candidate IDs; it never outputs q/r coordinates.
- Core computes geometry-only Junction candidates from distance, boundary, occupancy and free faces.
- V3.11 first implementation stores one Statement as one Atom in one Junction Cell.
- Do not implement multi-cell footprint, duplicated Atom, automatic Bridge, Stitch or multi-layer Placement in this task.
- Natural multi-entry is observed only after field growth and through independent single-entry recalls.
- The Tokyo/date/weather scenario is an Observation fixture, not a global three-entry invariant.
- Prompt evaluation uses Writer/Reader/Critic self-play in Lab; production common path remains one Dream Sculptor call.
- Preserve V3.10 durable Capture and background absorption, but close scope, turn-idempotency, drain, provenance and partial-outcome gaps first.
- Ordinary implementation choices are Codex-owned; stop only for data-loss, privacy, dependency-direction or unavoidable architecture blockers.
```

不得把架构书和任务书全文复制进 AGENTS。

---

# 3. 输入现场与已验证基线

生成：

```text
docs/project/V311_STARTING_STATE.md
```

记录：

```text
Bundle filename/SHA；
branch/HEAD/status/tag；
git graph；
clean tree；
Manifest；
module boundaries；
Core/Access/OpenClaw tests；
V3.9 geometry；
V3.10 Capture latency；
Pending fallback；
batch Formation/Placement；
known V3.10 gaps。
```

不得把 `4f8b1c4` 写成已完成 Async Absorption。

已知必须先修：

```text
跨 scope 混批；
同一 turn 双 Capture；
worker 不持续 drain；
临时模型不可用被 terminal defer；
Capture→Statement provenance 错误；
partial success；
revision 未进入确认；
Pending 遮蔽 geometry Recall。
```

---

# 4. 全部模块任务前完成度

| 模块 | 生命周期 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 95% | 高 | V3.9 几何、单点 Atom、Surface、Recall | 无 Junction 边界/交汇求解 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes | 增量/版本 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 独立合同 | 长期 metrics | 否 |
| ACCESS | `IMPLEMENTED` | 92% | 中高 | 原子 Admission、Surface 候选 | Atlas/Lens/Plan/Junction/provenance | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 75% | 中 | Capture、Pending、batch 基础 | V3.10 正确性、Dream Sculptor | 是 |
| LAB | `IMPLEMENTED` | 85% | 中高 | 几何和 Live 资产 | DC1 复用、自博弈、cycle | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 90% | 中高 | plugin/config | V3.11 版本/预算 | 是 |

---

# 5. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付 | 剩余限制 |
|---|---:|---:|---:|---|---|
| CORE | 95% | 98% | +10% 向量 | Junction candidates/solver | multi-cell、Stitch、多层 |
| SNAPSHOT | 50% | 50% | 0% | 回归 | 增量 |
| TRACE | 40% | 40% | 0% | 回归 | 长期 metrics |
| ACCESS | 92% | 98% | +15% 向量 | Atlas、Plan、Junction、provenance | 长期场优化 |
| HISTORY | 10% | 10% | 0% | 无变化 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 暂停 |
| OPENCLAW | 75% | 90% | +10% 向量 | Dream Sculptor 和 Live | 多 Provider |
| LAB | 85% | 97% | +15% 向量 | self-play/cycle/三方向场 | 长期统计 |
| DISTRIBUTIONS | 90% | 95% | +5% | Wire/Prompt/Policy | 正式发布 |

完成度是新范围估值，不代表封版。

---

# 6. Gate 0：活动依据与 V3.10 正确性基础

## 6.1 活动依据

```text
恢复/纠正缺失的 V3.7 权威；
加入 V3.11 架构；
更新 ACTIVE_PROJECT、CURRENT_STATUS、Ledger；
更新 AGENTS；
将旧 DC1 标为 REUSE_AS_PROMPT_AND_LAB_REFERENCE；
将 4f8b1c4 定性为 checkpoint；
形成保护性 commit。
```

## 6.2 V3.10 先闭合

一次完成：

```text
scope/workspace partition；
explicit single-user mode；
one visible turn one Capture；
message_sent canonical / agent_end fallback；
worker continuous drain；
retry/backoff；
temporary unavailable remains Pending；
per-Capture source provenance；
partial success；
revision confirmation handoff；
Pending + admitted geometry composition；
corrupt Capture diagnostics。
```

不再另立外部任务。

## 6.3 PASS

```text
无跨 scope batch；
无重复 Capture；
无需新聊天自动 drain；
临时失败不退出 Pending；
partial success 不重放成功项；
Pending 不遮蔽 geometry；
回归通过。
```

建议提交：

```text
checkpoint(aold): close V3.10 correctness before junction growth
```

---

# 7. Gate A：历史 DC1 资产适配

## 7.1 盘点

```text
docs/cortex/DC1_CORTEX_COMPILER_CONVENTIONS.md；
reference/python/nollm/dream_geometry/cortex/types.py；
compiler.py；
Query Probe；
AxisRay/GrowthStep；
relative-time tests；
DC1 fixtures/reports。
```

分类：

```text
REUSE_CONCEPT：
  axis/ray duality；Evidence basis；relative-time discipline；growth/query duality。

PORT_WITH_SIMPLIFICATION：
  bounded lens schema；basis spans；query probe fixtures。

REFERENCE_ONLY：
  fixed RESERVED_AXES；rule refs；receipts；Cortex Store；durable proposals；multi-step rays。

DELETE_ACTIVE：
  any persistent axes/topics/index.
```

## 7.2 新 operation-local 类型

建议：

```text
RecallLens；
LensBasisSpan；
DreamSculptorPlan；
LocalityCandidateRef；
JunctionSemanticPlan。
```

不得进入 Core 或独立持久 Store。

## 7.3 PASS

```text
资产复用报告；
无复制旧 Cortex 产品路径；
无持久 Lens Store；
relative time 测试；
预算测试。
```

建议提交：

```text
refactor(aold): adapt DC1 rays into ephemeral recall lenses
```

---

# 8. Gate B：Formation 语义边界纠正

## 8.1 Prompt 删除

禁止：

```text
is this worth remembering；
durable importance；
short-lived facts should be omitted；
weather expires；
likely future usefulness。
```

改为：

```text
是否存在独立、完整、Evidence-backed 命题。
```

## 8.2 no_memory 对照

必须允许形成：

```text
今天东京下雨了；
明天下午三点开会；
这杯咖啡太苦了；
今天取消浅草行程；
一个短期但完整的项目安排。
```

允许 no_memory：

```text
好的；
嗯；
空消息；
纯工具状态；
没有新增命题的表面重复。
```

重复事实最终走 reuse，不依赖 Formation 丢弃。

## 8.3 相对时间

```text
Capture reference instant + timezone
→ Statement absolute time；
原相对表达保留在 Capture；
以后不按当前日期重新解释。
```

## 8.4 PASS

Provider-backed contrast：

```text
短期完整事实不因“价值低”被过滤；
相对时间正确；
无 hallucination；
source spans 精确。
```

---

# 9. Gate C：Locality Atlas

## 9.1 Access API

新增或等价：

```text
build_locality_atlas(request_id, budget, field_scope)
```

结果 finite、frozen、operation-local。

## 9.2 候选来源

```text
真实 Surface；
occupied cells；
boundary cells；
代表 Statements；
relation-neutral frontier。
```

禁止：

```text
query keyword；
Topic；
Source；
embedding；
全局 ID route；
历史入口。
```

## 9.3 边界识别

```text
occupied Cell；
至少一个空 lateral neighbor；
或局部 occupancy/Coverage 边缘。
```

计算：

```text
free_face_count；
occupied_neighbor_count；
boundary；
local congestion。
```

## 9.4 Atlas tests

```text
空场；
单 Locality；
多个分离 Localities；
密集 Locality；
分页/预算；
mutation fingerprint invalidation；
无语义字段；
stable order。
```

## 9.5 PASS

```text
有限；
可重建；
无语义索引；
小场性能；
Prompt token 预算。
```

建议提交：

```text
feat(access): project bounded locality atlas for dream sculptor
```

---

# 10. Gate D：Core Junction Candidate 与求解

## 10.1 Owner

Codex 自主决定：

```text
Core public read-only Junction API；
或 Access 调用 Core-owned geometry helper。
```

但逻辑所有权必须属于 Core 几何。

建议类型：

```text
JunctionCandidate；
JunctionRequest；
JunctionResult。
```

输入只含：

```text
field scope；
selected locality representative/boundary cells；
max radius；
candidate limit；
write policy。
```

不含 Statement 文本和 Lens。

## 10.2 候选范围

```text
selected Localities 附近 bounded radius；
boundary cells；
相邻空 cells；
relation-neutral frontier；
最多64内部候选；
输出最多8。
```

## 10.3 排序

考虑：

```text
合法域；
primary 距离；
contact 最大距离和总距离；
free faces；
occupancy/congestion；
stable tie-break。
```

禁止：

```text
语义评分；
Statement hash；
插入顺序第一个空 Cell。
```

## 10.4 第一版单 Cell

仍调用现有原子 put 路径。

不新增：

```text
multi-cell footprint；
contact marker；
复制 Atom；
自动 Bridge。
```

## 10.5 PASS

```text
Tokyo-only Atlas 选择开放边界；
Tokyo+date 选择有限交汇；
远距离 contact 回退 primary frontier；
free-face 优先；
deterministic repeat；
negative q/r；
active radius；
性能。
```

建议提交：

```text
feat(core): solve deterministic boundary and junction placement candidates
```

---

# 11. Gate E：Dream Sculptor Wire 与调用

## 11.1 Wire

实现：

```text
nollm_openclaw_dream_sculptor_v1
```

支持 batch。

## 11.2 Prompt 课程

包含：

```text
角色说明；
Recall Lens 方法；
东京下雨正例；
价值过滤反例；
知识图谱反例；
坐标反例；
强制多入口反例；
revision/additive/different subject；
unresolved Lens。
```

不要求输出隐藏 reasoning。

## 11.3 调用拓扑

优先：

```text
Capture batch + Atlas
→ Statements + Plans，一次 call。
```

若必须两次：

```text
Formation + Field Sculptor；
共用 frozen Atlas；
不能按 Statement 重复会话；
报告原因和 token/call 数据。
```

## 11.4 校验

Access 验证：

```text
source_capture_ids；
basis spans；
candidate IDs；
primary/contact 预算；
action；
relative time；
Lens 数量；
unresolved；
state fingerprint。
```

无效：

```text
最多 retry 一次；
再失败保持 Pending；
零写入。
```

## 11.5 Revision

```text
revision_current provisional；
现有一次 confirmation；
reject 后一次 redecision；
不破坏其他 batch 结果。
```

## 11.6 PASS

```text
batch 3～5 Captures；
common one-call；
多个 Statements；
Lens 完整；
candidate 合法；
Admission；
Capture 终态；
无重复。
```

建议提交：

```text
feat(openclaw): sculpt statements and junction plans in one dream operation
```

---

# 12. Gate F：逆向生长 Placement

## 12.1 场景

```text
只有 primary Locality；
primary+contact；
全部 unresolved；
远距离 contact；
dense boundary；
frontier。
```

## 12.2 后续事实

后续事实重新执行 Dream Sculptor：

```text
不读取旧 Lens；
只查看当前 Atlas 的代表 Statements；
自然选择已有 Junction 附近 Locality；
Core 继续边界生长。
```

## 12.3 生产状态检查

必须不存在：

```text
axis_id；
lens text；
contact IDs；
fact→entries；
Topic；
query path。
```

## 12.4 PASS

```text
场位置变化来自新事实；
旧 Atom 不复制；
Junction 周围形成分支；
revision/remove 正确；
reopen 一致。
```

建议提交：

```text
feat(aold): grow local relation branches around junction placements
```

---

# 13. Gate G：Recall 对偶与低调用

## 13.1 Query 侧

```text
一次最终 entry；
Core Recall；
main agent 使用 Locality。
```

允许单次隐藏 Prompt 内部理解临时 query lens，但不持久化。

## 13.2 调用预算

```text
common hidden semantic calls <=1；
singleton 可0；
无第二 Statement-selection Agent；
Pending+admitted 组合。
```

## 13.3 PASS

```text
location query；
absolute time query；
phenomenon query；
unrelated NONE；
dense hidden-preview；
query path 不持久。
```

建议提交：

```text
feat(openclaw): align single-entry recall with ephemeral query lenses
```

---

# 14. Gate H：LLM Self-Play 与 Cycle Consistency

## 14.1 Writer/Reader/Critic

```text
Writer：真实 Dream Sculptor。
Reader：真实 Recall entry selector。
Critic：比较实际 Handle reachability，不用自然语言自评替代 Core 结果。
```

## 14.2 Fixture 类别

至少：

```text
东京/日期/天气；
人物/项目/截止日期；
设备/地点/故障；
法律案件/主体/时间；
同一主体 revision；
additive fact；
不同主体同字段；
无现成 Locality；
远距离 Locality。
```

## 14.3 指标

```text
Statement formation rate；
value-filter error rate；
primary lens reach；
secondary lens reach；
wrong locality；
unresolved rate；
free-face；
calls per batch；
calls per statement；
single-entry path；
duplicate/orphan。
```

## 14.4 Prompt 迭代

最多 3 个 Prompt 版本。

每版必须：

```text
有明确失败分类；
以 cycle 数据选择；
不为单个 Case 堆关键词特例。
```

## 14.5 PASS

```text
至少100个 deterministic/Provider 混合 cases；
关键 contrast 通过；
无 Python 语义规则；
cycle 报告。
```

建议提交：

```text
test(lab): teach and validate LLM field sculpting by self-play
```

---

# 15. Gate I：东京—时间—天气真实场

## 15.1 工作区

```text
nollm-caold-recall-lens-junction-growth-v1
```

保留所有旧工作区。

## 15.2 自然聊天序列

不得说：

```text
请创建天气分支；
请放到某 Cell；
请生成三个入口。
```

使用普通聊天形成：

```text
T0：今天东京下雨了。
T1：用户在东京取消了浅草行程。
T2：2026年7月17日用户参加了线上会议。
T3：大阪当天也下雨了。
T4～Tn：若干东京、日期、天气相关独立事实。
```

具体措辞由 Codex 自然设计。

## 15.3 检查

```text
T0 完整 Statement；
不因短期天气 no_memory；
T0 一个 Atom 一个 Handle；
T0 Junction Cell；
后续事实围绕不同方向生长；
无持久 Lens；
无复制。
```

## 15.4 三次独立 Recall

分别在新 Session 查询：

```text
东京方向问题；
2026年7月17日方向问题；
下雨/天气方向问题。
```

每次：

```text
一个最终 entry；
独立 Core Recall；
目标 T0 Handle 到达；
记录 entry/path；
不合并三个入口。
```

## 15.5 结果边界

三方向通过是：

```text
该场景下的场生长 Observation。
```

不是：

```text
每个事实至少三个入口；
全项目发布 Gate；
新的 fact→entries 合同。
```

## 15.6 PASS

```text
Provider-backed；
Gateway restart；
Pending→Admission 交接；
三方向独立到达；
NONE；
用户自然回答；
旧数据保留。
```

建议提交：

```text
test(caold): validate Tokyo time weather junction growth
```

---

# 16. Gate J：性能、回归、状态和 Bundle

## 16.1 性能

```text
Capture 保持 p95<=100ms 目标；
Atlas 小场<=1s 目标；
Junction local<=100ms 目标；
common batch Dream calls=1 目标；
common Recall hidden<=1；
本地 Core 不退化。
```

## 16.2 回归

```text
Core；
Snapshot；
Trace；
Access；
OpenClaw Python/Node；
M0；
V3.9 Coverage；
V3.10 Capture/Pending/worker；
revision；
dense Recall；
Manifest/boundary/plugin。
```

## 16.3 状态

更新：

```text
ACTIVE_PROJECT；
CURRENT_STATUS；
canonical Ledger；
V3.11 主报告；
实际推进向量；
全部模块完成度；
known limitations。
```

## 16.4 Bundle

```text
所有进展 commit；
clean tree；
完整历史 bundle；
verify；
SHA。
```

---

# 17. 测试矩阵

## Core

```text
Junction candidate type；
boundary detection；
free faces；
multi-locality distance；
stable solve；
frontier fallback；
active radius；
read-only state；
put/reopen；
no semantic input。
```

## Access

```text
Atlas；
Lens schema；
basis spans；
candidate validation；
Junction request；
batch provenance；
partial outcomes；
revision；
no persistent Lens；
one Atom/Handle。
```

## OpenClaw

```text
Dream Sculptor Wire；
Prompt；
one-call common；
relative time；
value-filter contrast；
Pending worker；
scope/idempotency；
Recall one-call；
hidden injection。
```

## Lab

```text
DC1 reuse；
Tokyo fixture；
self-play；
cycle；
Prompt versions；
three single-entry recalls；
no forced multi-entry。
```

## Boundaries

```text
Core no Statement/Query/Lens imports；
production no Cortex Store；
no topic/source/entity index；
no fact→entries；
no vector/graph/embedding；
no multi-cell Atom。
```

---

# 18. Evidence 与报告

Evidence：

```text
validation/caold_recall_lens_junction_growth_20260717.jsonl
validation/caold_recall_lens_junction_growth_summary_20260717.json
```

主报告：

```text
docs/project/CAOLD_LLM_COMPILED_RECALL_LENS_JUNCTION_GROWTH_REPORT.md
```

必须回答：

```text
LLM 如何从 Evidence 形成 Statement；
是否仍做价值过滤；
每 Statement 生成哪些 Recall Lenses；
选择哪些 Localities；
Core 如何选择 Junction；
有多少自由面；
后续事实怎样生长；
东京/时间/天气三个入口如何独立到达；
生产 state 是否无 Lens/Topic/index；
模型调用；
性能；
失败；
实际向量；
Bundle。
```

Freeze：

```text
完成 Live；
停止追加；
计算 SHA；
生成 Summary/Report；
更新 Manifest；
check；
commit；
从 Git blob 复核。
```

---

# 19. 完成状态

全部核心 Gate 通过才允许：

```text
LLM_COMPILED_RECALL_LENS_JUNCTION_GROWTH_VALIDATED_AT_<HEAD>
```

条件：

```text
V3.10 正确性闭合；
短期完整事实不被价值过滤；
DC1 概念复用但无持久 Cortex；
Locality Atlas；
Core Junction solver；
Dream Sculptor common one-call；
单 Atom 单 Cell；
逆向生长；
Provider-backed 东京场；
三个独立单入口 Observation；
无语义索引；
回归/Manifest/clean/Bundle。
```

否则：

```text
CAOLD_RECALL_LENS_JUNCTION_GROWTH_IN_PROGRESS_AT_<HEAD>
```

仍提交真实进展。

---

# 20. 明确非目标

```text
multi-cell footprint；
contact marker；
事实复制；
多物理层语义 Placement；
Stitch/Bridge 自动化；
多 Chart；
持久 axis/ray；
Cortex Store；
rule registry；
Topic/Entity；
embedding/vector/graph；
multi-entry Recall；
PB 长跑；
正式发布；
模型微调。
```

---

# 21. 建议提交序列

```text
checkpoint(caold): adopt recall-lens junction-growth architecture
fix(aold): close durable capture absorption correctness
refactor(lab): adapt DC1 rays into ephemeral recall lenses
feat(access): build locality atlas for dream sculptor
feat(core): solve boundary and junction placement candidates
feat(openclaw): plan statements and placement in one dream call
feat(aold): grow relation branches around junction cells
test(lab): validate placement recall cycle by LLM self-play
test(caold): prove Tokyo time weather single-entry reachability
docs(caold): record V3.11 capability and limitations
```

---

# 22. Git Bundle

建议：

```text
nollm_caold_llm_recall_lens_junction_growth_20260717_<shorthead>.bundle
```

验证：

```powershell
git bundle create ..\nollm_caold_llm_recall_lens_junction_growth_20260717_<shorthead>.bundle --all
git bundle verify ..\nollm_caold_llm_recall_lens_junction_growth_20260717_<shorthead>.bundle
Get-FileHash ..\nollm_caold_llm_recall_lens_junction_growth_20260717_<shorthead>.bundle -Algorithm SHA256
```

---

# 23. 最终回复要求

只报告：

```text
branch/HEAD/commits；
V3.10 基础修复；
DC1 复用；
Formation 边界；
Atlas；
Junction solver；
Dream Sculptor 调用；
self-play/cycle；
东京/时间/天气三方向；
性能；
tests/boundary/manifest；
实际向量/完成度；
limitations；
Bundle/SHA。
```

---

# 24. 最终任务概括

```text
不要教 LLM 分类和选坐标。

要教它：
先形成完整事实；
再想象未来的自己会怎样找；
再从有限 Locality 中选择关系；
把精确空间交给 Core。

不要预先建东京、日期、天气节点。

先把“东京下雨”放在可生长的边界/交汇处；
让后来事实围绕它生长；
最终从东京、日期、天气三个独立单入口都能回到同一事实。

方向由内容长出来，
不是由索引写进去。
```
