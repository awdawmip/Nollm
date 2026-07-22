# Nollm AOLD：LLM 原生 Evidence、陈旧计划拒绝、主代理 Recall 与几何选择性任务书

**任务文件名**：`NOLLM_A_O_L_D_LLM_NATIVE_EVIDENCE_STALE_PLAN_MAIN_AGENT_RECALL_SELECTIVITY_TASK_20260722.md`
**日期**：2026-07-22
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**任务性质**：Rev4 生产可靠性、调用拓扑和规模选择性闭环；Core 保持冻结工作基线
**输入 Bundle**：`nollm_aold_contextual_writer_shared_retrieval_growth_20260721_a4d8e31.bundle`
**输入 Bundle SHA-256**：`9bc3cbe6a8952461c555f9b4bd5fba283a194a4d0f764dd1c2d2c3cc7b9c66aa`
**输入分支**：`codex/aold-recall-entry-identity-contextual-writer-relational-growth`
**输入 HEAD**：`a4d8e3135ef894453e1d01dc5c19139d23d9c71f`
**输入 Tag**：无
**建议分支**：`codex/aold-llm-native-evidence-main-agent-recall-selectivity`
**主环境**：Windows 10/11、PowerShell、Node 24、真实 OpenClaw / 当前 Host 模型
**交付**：大跨度单任务；内部 Gate；普通问题直接修复；所有真实进展 commit；clean tree；仓库外单一完整历史 Git Bundle
**插件状态**：保持安装并启用
**数据状态**：旧工作区和冻结 Evidence 全部保留；新建独立 v7 工作区；不得覆盖旧数据
**能力边界**：不修改 Core 算法；不做 multi-cell、多物理层、Stitch、Topic/Entity、向量/图索引、multi-entry、Provider 更换或 PB 长跑

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +15% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +15% | DISTRIBUTIONS +5%

主方向：
撤回活动 legacy Writer 绕过；
将 LLM 字符 offset/index 输出改为自然 Evidence quote refs；
持久化 Statement exact provenance；
Cartographer apply 强制字段新鲜度；
用户 Recall 退出独立 hidden Reader；
主代理在同一 run 直接使用 Nollm 几何工具；
以 60～100 事实验证单入口选择性、延迟和扩展行为。

范围变化：
Access 新增 StatementProvenance 或等价 canonical Evidence 合同；
OpenClaw 新增 main-agent internal geometry tool；
Recall 用户面调用拓扑变化；
Core MemoryAtom、GeometryAddress、Coverage、Junction、Surface 和 Recall 算法不变。
```

## 0.1 Gate 向量复述

每个 Gate 开始记录：

```text
C0 | S0 | T0 | A+15 | H0 | U0 | O+15 | L+15 | D+5
```

每个 Gate 结束记录：

```text
Writer attempts；
Evidence 定位失败；
stale plan 拒绝；
hidden child calls；
main-agent tool calls；
default/expanded Locality 大小；
target reach 和 unrelated leakage；
实际模块推进；
是否出现范围扩张。
```

执行中如新增 Core、Snapshot、Trace、History 或 Audit 修改，或任一模块实际偏差超过 5%，必须先更新任务范围、推进向量和 canonical Ledger，不得静默扩张。

---

# 1. 输入检查点审核基线

## 1.1 Bundle 和仓库事实

```text
Bundle：
nollm_aold_contextual_writer_shared_retrieval_growth_20260721_a4d8e31.bundle

SHA-256：
9bc3cbe6a8952461c555f9b4bd5fba283a194a4d0f764dd1c2d2c3cc7b9c66aa

HEAD：
a4d8e3135ef894453e1d01dc5c19139d23d9c71f

Branch：
codex/aold-recall-entry-identity-contextual-writer-relational-growth

Working tree：
clean

Exact HEAD Tag：
无

Manifest：
2039 tracked / 2039 rows / 0 unclassified

Production boundaries：
0 violations / 0 cycles。
```

当前审核环境独立复现：

```text
Core/Snapshot/Trace/selected Access/OpenClaw/Lab：
140 passed。
```

Bundle 报告中的 Windows、Node、M0 和完整长时套件须在主环境重新执行。

## 1.2 已验证并必须保持的能力

```text
operation-unique Progressive Atlas entries；
Contextual Writer；
Direct Query / Entry Query 分离；
九条 Capture durable；
六条 related growth；
三条 independent seed；
wrong date = 0；
东京、会议、天气三个 distinct Reader entry；
target-hidden relation-entry causal Recall；
unrelated negative；
restart；
NONE；
Core reentry 与 Access rollback 可靠性修复；
即时 Capture；
异步 worker；
Prompt-bounded Atlas；
realized-only Junction；
one Statement / one Atom / one Handle / one Cell。
```

## 1.3 当前 P0：活动 legacy Writer 可绕过 Rev4

活动 parser 同时接受：

```text
contextual Writer v2；
legacy Writer v1。
```

Legacy v1 不验证：

```text
absolute date basis；
resolved references；
Direct/Entry Query；
context provenance。
```

已独立构造：

```text
Capture：
今天东京下雨了。

Legacy result：
2035年1月1日东京下雨了。
```

当前 parser 接受。

生产 Host 必须只接受最新活动 schema。Legacy 只能作为显式离线 migration。

## 1.4 当前 P0：LLM 手算字符位置导致大量无意义重试

九个成功 Capture 的终态 attempt：

```text
9, 11, 1, 1, 1, 1, 5, 1, 1
```

总计：

```text
31 attempts。
```

正式 Trace 至少包含：

```text
3 次 span mismatch；
2 次 unsupported outer text；
1 次 span index 被误作字符 offset；
1 次 invalid planned outcome；
1 次 unsupported absolute date basis。
```

这主要是工具边界错误，不是语义能力不足。

## 1.5 当前 P0：ResolvedReference basis 没有交叉绑定

当前可出现：

```text
basis_capture_ids：
指向日期 Context Capture；

basis_span_indexes：
指向 Source Capture 中“那天晚上”的 span。
```

两者没有机械保证对应。

因此“exact provenance”仍可能是逻辑拼接，而不是可重建 Evidence 链。

## 1.6 当前 P0：Cartography apply 接受陈旧计划

`apply_field_cartography_result` 会重建当前 compatibility Atlas，并在 selected Cell 仍存在时继续映射。

它没有强制比较原计划的：

```text
atlas_fingerprint；
page_fingerprint；
core_state_sha256；
visible Handle digest。
```

在 20～100 秒 Provider 等待期间，Locality 可能已经改变。

## 1.7 当前 P0：用户 Recall 仍额外调用隐藏 Reader

真实 Rev4：

```text
Tokyo query：约31.8秒；
meeting query：约19.7秒；
weather query：约23.5秒；
NONE：约33.7秒。
```

这些时间发生在主代理回答之前。

用户此前已明确：该数量级不可接受。

## 1.8 当前 P1：Locality 注入过宽

九条事实小场：

```text
Tokyo query 注入7条；
meeting query 注入6条；
weather query 注入6条；
target-hidden query 注入7条。
```

无关 seed 没有泄漏，但簇内选择性不足。

## 1.9 当前 P1：Evidence 绑定描述不准确

报告声称：

```text
Git-blob verifier passed at 75383c6。
```

实际：

```text
75383c6 中 summary 缺少 completion binding；
verifier 在75383c6不通过；
最终 a4d8e31 才通过。
```

冻结 Summary 也没有完整 hash-bind raw Writer/Cartographer Trace。

---

# 2. 当前能力重新定性

记录：

```text
CONTEXTUAL_WRITER_SHARED_RETRIEVAL_GROWTH_CHECKPOINT_AT_a4d8e31
```

建议上一任务实际推进向量：

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +8% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +7% | DISTRIBUTIONS +5%
```

不得将当前检查点描述为用户面低延迟 Recall 完成能力。

---

# 3. 活动依据

开始执行前按顺序读取：

```text
1. NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. 当前活动项目书与 Core Function Priority
3. V3.7 Rotated Physical Memory Field
4. V3.9 Bounded Approximate Coverage
5. V3.10 Durable Capture / Async Absorption
6. V3.11 Rev5 Architecture Amendment
7. CURRENT_STATUS
8. canonical Module Progress Ledger
9. 本任务书
10. A/O/L/D 模块章程
11. 根目录 AGENTS.md
```

冲突优先级：

```text
原始 Evidence 可回溯
> 用户面不重复调用 LLM
> LLM语义/Core几何边界
> Architecture is the Index
> Cartography state新鲜
> 单入口Recall
> 规模选择性
> 当前实现兼容。
```

---

# 4. 给 Codex 的自由与停止边界

## 4.1 可以自主决定

```text
StatementProvenance 是扩展 Statement schema 还是 sidecar；
EvidenceQuoteRef 的 occurrence/context 消歧细节；
Cartography freshness 使用全 Core SHA 还是窄范围 fingerprint；
主代理内部工具使用 OpenClaw tool、hook 或等价机制；
Atlas top page 和 region tool 是否合并；
默认 Locality statement/char/step/beam预算；
expanded Locality 的增量或全量返回格式；
legacy Writer migration 文件布局；
规模 fixture 的主题和空间布局；
测试文件、脚本和报告名称。
```

普通工程问题直接选择最简单正确方案继续，不需询问。

## 4.2 不可协商结果

```text
1. 活动 Provider response 不能自动降级到 legacy Writer。
2. LLM 不再输出字符 offset 和 span 数组 index。
3. 每条 durable Statement 拥有可重开的 canonical Evidence provenance。
4. basis Capture 与 Evidence ref 必须机械一致。
5. Cartography 计划陈旧时零写入并重算。
6. 用户默认 Recall 不创建独立 hidden Reader child-agent。
7. 主代理只能选择 operation-local entry，不得生成坐标。
8. 一次 Recall 仍只有一个最终 entry。
9. 默认 Locality 使用几何排序，不使用 Python 语义过滤。
10. 扩展必须保持同一 entry。
11. 规模验证不得恢复 stable-key prefix、Topic、embedding或multi-entry。
12. Core 不修改。
13. Rev4 的九事实关系生长、wrong-date=0、unrelated negative不得回退。
14. 旧工作区和原始 Capture 不删除。
15. 未完成也必须commit、clean和完整Bundle。
```

## 4.3 真实停止条件

只在以下情况停止：

```text
OpenClaw主代理运行时无法提供任何内部工具能力；
无法在不暴露内部结构的情况下让主代理选择entry；
Statement provenance 必然成为关系索引；
窄范围 freshness 无法保证且全 Core SHA导致永久饥饿；
同一entry有界扩展无法维持单入口；
旧数据迁移会损坏原始Statement/Capture。
```

普通 Provider、JSON、Prompt、测试和性能问题直接修复继续。

---

# 5. 根目录 `AGENTS.md`

至少加入：

```text
- The active Writer schema is Rev5 only; legacy Writer parsing is offline migration only.
- LLMs quote Evidence; deterministic code computes exact spans.
- Do not ask an LLM for Unicode offsets, Python slices or span-array indexes.
- Every durable Statement retains canonical provenance independent of debug traces.
- Resolved-reference basis IDs must point to the exact Evidence refs they claim.
- Cartography plans are state-bound; stale plans are zero-write and recalculated.
- The default user Recall path creates no independent hidden Reader child-agent.
- The main agent uses an internal single-entry Nollm geometry tool in its own run.
- The main agent may expand only from the same selected entry.
- Default Locality is small and geometry-ranked; Python does not semantically filter it.
- Preserve one Statement/Atom/Handle/Cell, Prompt-bounded Atlas, realized Junction and all Rev4 relation-growth evidence.
- Core is frozen in this task.
```

---

# 6. 全部模块任务前完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 93% | 中高 | V3.9几何、realized Junction、运行时可靠性 | 本任务只回归 | 否 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes | 增量/版本化 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 独立sink合同 | metrics | 否 |
| ACCESS | `IMPLEMENTED` | 94% | 中高 | Context Writer验证、Cartography、Admission | exact provenance、stale plan、Locality预算 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 94% | 中高 | Capture、Writer/Cartographer、relation Reader | legacy bypass、hidden Reader、主代理工具 | 是 |
| LAB | `IMPLEMENTED` | 92% | 中高 | 九事实关系生长 | 缺规模、stale、no-child A/B | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 94% | 中高 | Rev4 Wire和配置 | Rev5 schema/tool/default预算 | 是 |

---

# 7. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付 | 剩余限制 |
|---|---:|---:|---:|---|---|
| CORE | 93% | 93% | 0% | 回归 | 多层、Stitch、长期规模 |
| SNAPSHOT | 50% | 50% | 0% | 回归 | 增量Snapshot |
| TRACE | 40% | 40% | 0% | 回归 | 长期metrics |
| ACCESS | 94% | 98% | +15%向量 | quote resolver、provenance、freshness、bounded Locality | 长期scale |
| HISTORY | 10% | 10% | 0% | 无变化 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 暂停 |
| OPENCLAW | 94% | 98% | +15%向量 | Writer v3、main-agent tool、zero child Reader | 其他Host |
| LAB | 92% | 98% | +15%向量 |规模选择性、延迟和负例 | 长期统计 |
| DISTRIBUTIONS | 94% | 97% | +5% | Rev5活动合同和预算 | 正式发布 |

不写永久 100%。

---

# 8. Gate 0：活动状态与反例固化

工作：

```text
更新AGENTS；
新增Rev5架构；
更新ACTIVE_PROJECT/CURRENT_STATUS/Ledger；
将a4d8e31定性为checkpoint；
修正75383c6/a4d8e31 verifier措辞；
加入以下自动反例：
  legacy wrong-date accepted；
  mismatched reference basis；
  stale Cartography apply；
  LLM offset/index failures；
  hidden Reader latency；
  6/7 over-injection。
```

Gate 0 PASS：

```text
旧问题可以在输入实现上复现；
状态不夸大；
Core明确冻结；
保护性commit。
```

建议提交：

```text
checkpoint(aold): adopt LLM-native Evidence and main-agent Recall
```

---

# 9. Gate A：活动 Writer v3 与 Quote Resolver

## 9.1 Writer Wire

新增或等价活动 schema：

```text
nollm_openclaw_contextual_proposition_writer_v3
```

每条 Proposition 至少：

```text
draft_id；
content_utf8；
source_capture_ids；
context_capture_ids；
evidence_refs；
resolved_references；
direct_queries；
entry_queries；
outcome。
```

禁止：

```text
start/end；
basis_span_indexes；
任意 q/r；
Atlas candidate。
```

## 9.2 Quote Resolver

必须覆盖：

```text
中文；
日文；
英文；
emoji；
代理对；
换行；
重复quote；
相同quote跨role；
left/right context；
occurrence；
空quote；
零命中；
多命中；
不同Unicode normalization；
超长Capture。
```

输出 canonical：

```text
capture_id；
role；
start；
end；
quote_sha256；
capture_sha256。
```

## 9.3 Active legacy isolation

生产 parse：

```text
只接受v3；
任何v1/v2普通Provider response明确拒绝；
不自动convert。
```

Offline migration：

```text
显式函数/CLI；
测试；
标记provenance_precision=legacy/coarse；
不得进入普通Host path。
```

## 9.4 Provider稳定性

至少20个自然Capture：

```text
first-attempt contract valid >=80%；
offset/index failure = 0；
最终durable >=90%；
outer JSON安全repair最多1次；
semantic failure与format failure分开。
```

Provider未达到阈值时保持IN_PROGRESS，不得恢复offset字段。

Gate A PASS：

```text
legacy绕过关闭；
quote定位确定；
Writer不手算索引；
真实attempt显著下降。
```

建议提交：

```text
feat(access): resolve LLM-native Evidence quote anchors
fix(openclaw): retire active legacy Writer responses
```

---

# 10. Gate B：Canonical Statement Provenance

## 10.1 Owner

由 Access 拥有。

不得：

```text
放入Core；
放入OpenClaw-only debug trace；
建立Statement→related Statements关系。
```

## 10.2 内容

至少：

```text
schema_version；
statement_id；
content_sha256；
source_capture_ids；
context_capture_ids；
exact evidence spans；
resolved references；
writer schema/prompt version；
created_at；
revision predecessor；
migration precision。
```

## 10.3 原子性

Statement Admission：

```text
Statement；
Provenance；
Handle；
Core Atom
```

必须具有明确失败语义。

Codex可：

```text
将Provenance随Statement同文件原子写；
或在Access composition中纳入sidecar回滚。
```

不能出现：

```text
Statement current，但provenance永久缺失；
provenance成功，Statement失败；
retry生成重复provenance。
```

## 10.4 Revision

```text
旧Statement provenance保持；
新Statement有新provenance；
确认关系可引用predecessor；
不重写旧Evidence。
```

## 10.5 Recall

Recall item 可提供：

```text
Evidence refs/statement provenance digest。
```

但不得根据 provenance 搜索或排序。

Gate B PASS：

```text
重开可读；
revision可追；
旧数据不伪造；
Admission故障零孤儿；
Access tests通过。
```

建议提交：

```text
feat(access): persist canonical Statement Evidence provenance
```

---

# 11. Gate C：Cartography Freshness

## 11.1 Token

实现：

```text
CartographyPlanToken；
或等价immutable identity。
```

包含：

```text
writer proposition digest；
atlas/page fingerprint；
selected region/entry；
affected-locality state digest；
existing Handle digest；
schema/prompt version。
```

## 11.2 Apply

测试至少：

```text
完全相同state → apply；
selected Cell加入Atom → stale；
selected Cell删除Atom → stale；
current Handle revision → stale；
relation group变化 → stale；
无关远Cell变化 → 按文档允许或拒绝；
Core import/reopen → 正确处理；
stale zero-write；
worker重新Cartography；
重试不重复Statement。
```

## 11.3 长Provider模拟

使用 barrier/fake provider：

```text
Cartographer等待；
另一个合法operation改变Field；
恢复结果；
必须拒绝。
```

Gate C PASS：

```text
陈旧语义计划不能写；
无无限重试；
无全局语义索引。
```

建议提交：

```text
fix(access): reject stale Cartography plans before Admission
```

---

# 12. Gate D：主代理内部 Nollm 几何工具

## 12.1 Host能力盘点

Codex先确认：

```text
OpenClaw主代理可注册何种内部tool；
tool是否可隐藏；
tool调用是否仍属于同一run/session；
是否能返回operation-local state；
是否能限制参数schema。
```

选择最小方案。

## 12.2 Tool API

建议能力：

```text
surface；
open_region；
recall；
expand；
none。
```

可以合并为：

```text
nollm_memory
```

并用 `action` 区分。

## 12.3 安全合同

参数只允许：

```text
operation_id；
region_id；
entry_id；
budget option ID。
```

不允许：

```text
q/r；
layer；
Statement ID随意查找；
Topic；
query text route；
多个entry。
```

## 12.4 Active path

默认用户查询：

```text
不创建hidden Reader child session；
不调用独立Reader model；
主代理使用tool；
selected entry → Core Recall；
bounded Locality返回同一run。
```

旧Reader：

```text
保留Lab baseline；
active distribution关闭；
诊断显示legacy_reader=false。
```

## 12.5 NONE

主代理可以：

```text
查看Surface后返回none；
或不调用tool。
```

系统不强迫每个query Recall。

Gate D PASS：

```text
child-agent calls=0；
一个entry；
工具内部不外显；
R1/R2/R3/P1/Rev4查询不回退；
main visible answer自然。
```

建议提交：

```text
feat(openclaw): expose single-entry geometry Recall to the main agent
```

---

# 13. Gate E：Bounded Locality 与 Same-entry Expansion

## 13.1 默认预算

Codex根据V3.9/Rev4数据选择，初始建议：

```text
max_results=4；
max_chars=3000；
max_steps较小；
beam/fanout保持现有安全值；
bridge按现有policy。
```

## 13.2 返回

每条 item：

```text
Statement ID；
content；
Evidence digest/ref；
geometry score；
path；
entry-relative rank。
```

整体：

```text
has_more；
budget_exhausted；
expansion options；
result count/chars；
entry ID。
```

## 13.3 Expand

```text
同一operation；
同一entry；
预算单调增加；
不重复已有items或明确返回全窗口；
最多固定次数；
mutation后旧operation失效。
```

## 13.4 不允许

```text
Python semantic ranking；
关键词；
日期/地点过滤；
第二个LLM选择；
多entry合并。
```

Gate E PASS：

```text
默认小窗口；
目标不足时可扩展；
同一entry；
Core结果稳定；
Access tests。
```

建议提交：

```text
feat(access): return bounded expandable geometry Localities
```

---

# 14. Gate F：规模和选择性验证

## 14.1 字段

新建：

```text
nollm-aold-main-agent-geometric-recall-v7
```

至少：

```text
60～100 Statements；
6～10 Localities；
20 independent unrelated seeds；
一个10+事实dense Locality；
东京/时间/天气关系场保留；
多个session；
restart。
```

Provider-backed至少：

```text
20个新Statements；
其余可用deterministic fixtures扩规模；
两类证据分开。
```

## 14.2 查询

至少：

```text
20 relevant；
10 relation-entry target-hidden；
10 dense hidden-target；
10 NONE/unrelated；
5需要expand；
2 cold restart。
```

## 14.3 指标

```text
target reach >=90%；
default result p95 <=5 Statements；
default chars p95 <=3000；
unrelated leakage <=1 item/query；
single-entry=100%；
hidden child-agent=0；
expanded target reach；
NONE false injection；
distinct entry distribution；
query→visible。
```

如阈值未满足：

```text
如实IN_PROGRESS；
先调Access预算；
不得修改Core物理参数或加入语义filter。
```

## 14.4 A/B

同一字段比较：

```text
旧hidden Reader；
新main-agent tool；
默认Locality；
expandedLocality。
```

报告：

```text
额外Provider调用；
延迟；
target reach；
注入量；
可见回答质量观察。
```

Gate F PASS：

```text
用户面Reader额外20～34秒消失；
几何选择性达到当前实验目标；
Rev4因果链不回退。
```

建议提交：

```text
test(aold): validate scaled single-entry Recall selectivity
```

---

# 15. Gate G：Evidence 与治理

## 15.1 新 Evidence

```text
validation/aold_llm_native_main_agent_recall_20260722.jsonl
validation/aold_llm_native_main_agent_recall_summary_20260722.json
```

必须绑定：

```text
raw Writer events；
Cartographer events；
tool events；
Provider/model；
attempt IDs；
validation failures；
provenance；
stale plan；
A/B queries；
scale metrics；
workspace hashes。
```

## 15.2 主报告

```text
docs/project/AOLD_LLM_NATIVE_EVIDENCE_MAIN_AGENT_RECALL_REPORT.md
```

直接回答：

```text
Writer重试为何下降；
Evidence如何回溯；
legacy是否退出；
stale计划是否拒绝；
用户Recall还有几次child-agent；
query→visible；
默认/expanded Locality；
规模选择性；
已知限制。
```

## 15.3 提交绑定

报告明确区分：

```text
code/evidence commit；
final binding/docs commit；
verifier passes at final HEAD。
```

## 15.4 Freeze

```text
live writer旋转；
冻结raw；
line/bytes/SHA；
Summary；
Report；
Manifest；
Git blob复算；
commit；
不再追加。
```

Gate G PASS：

```text
Evidence可复现；
最终HEAD无占位符；
Manifest在报告后生成；
工作树clean。
```

---

# 16. 自动测试矩阵

## 16.1 Access

```text
quote unique/multiple/not-found；
Unicode；
role；
capture hash；
resolved basis cross-link；
provenance atomicity；
revision provenance；
legacy migration；
stale plan；
bounded Locality；
same-entry expand；
operation invalidation。
```

## 16.2 OpenClaw

```text
Writer v3 Prompt/Wire；
legacy response reject；
main-agent tool registration；
tool hidden；
parameter allowlist；
no child Reader；
Pending composition；
NONE；
failure-open；
restart；
plugin install/update。
```

## 16.3 Lab

```text
legacy wrong-date negative；
mismatched basis；
31-attempt旧基线；
20 Capture Writer stability；
stale race；
60～100 fact scale；
A/B latency；
target-hidden；
unrelated；
freeze verifier。
```

## 16.4 回归

```text
Core；
Snapshot；
Trace；
Access full；
OpenClaw Python；
Node；
M0 active；
V3.9；
V3.10；
Rev3/Rev4 causal；
runtime integrity；
Manifest；
boundaries。
```

---

# 17. 性能与调用预算

```text
Capture p95 <=100ms；
Writer common calls=1/batch；
Writer Prompt<=64KB；
Writer first-attempt valid>=80%；
Cartographer one session/batch；
stale retry有界；
用户Recall child-agent calls=0；
主代理tool local p95记录；
default Locality p95<=5 Statements；
default chars p95<=3000；
Core local不退化。
```

Provider主代理本身的回答时间作为观察，不形成永久SLA。

---

# 18. 内部 Gate 与建议提交

## Gate 0
状态、反例和Rev5活动依据。

```text
checkpoint(aold): adopt LLM-native Evidence and main-agent Recall
```

## Gate A
Writer v3与Quote Resolver。

```text
fix(openclaw): retire active legacy Writer responses
feat(access): resolve LLM-native Evidence quote anchors
```

## Gate B
Statement Provenance。

```text
feat(access): persist canonical Statement provenance
```

## Gate C
Cartography freshness。

```text
fix(access): reject stale Cartography plans
```

## Gate D
主代理工具。

```text
feat(openclaw): expose internal single-entry geometry tool
```

## Gate E
Bounded Locality。

```text
feat(access): return bounded expandable Localities
```

## Gate F
规模和A/B。

```text
test(aold): validate scaled selectivity and no-child Recall
```

## Gate G
Evidence、状态和Bundle。

```text
docs(aold): record LLM-native main-agent Recall capability
```

普通问题直接修复继续，不再拆外部小任务。

---

# 19. 最终 Gate

全部满足：

```text
active legacy response拒绝；
LLM offset/index字段退出；
quote resolver通过Unicode/重复/歧义；
durable Statement exact provenance；
basis cross-link真实；
stale Cartography zero-write；
用户Recall hidden child-agent=0；
main-agent tool同一run；
one final entry；
default Locality p95<=5；
同entry expand；
60～100事实规模；
target reach>=90%；
unrelated leakage<=1；
NONE/restart；
Rev4关系生长不回退；
Core无修改；
完整测试；
Manifest tracked=rows；
0 unclassified；
0 production violations/cycles；
Evidence Git-blob复算；
clean tree；
完整历史Bundle。
```

---

# 20. 完成状态

全部完成：

```text
LLM_NATIVE_EVIDENCE_AND_MAIN_AGENT_GEOMETRIC_RECALL_VALIDATED_AT_<HEAD>
```

否则：

```text
AOLD_LLM_NATIVE_MAIN_AGENT_RECALL_IN_PROGRESS_AT_<HEAD>
```

无论状态：

```text
commit；
clean；
完整Bundle；
不补造；
旧数据保留。
```

---

# 21. 明确非目标

```text
Core算法；
multi-cell；
多物理层；
Stitch；
多Chart；
持久Lens；
Topic/Entity；
query/fact entry map；
vector/graph/embedding；
multi-entry；
Provider更换；
PB；
正式发布；
完整History/Audit产品。
```

---

# 22. Git Bundle

建议文件名：

```text
nollm_aold_llm_native_evidence_main_agent_recall_20260722_<shorthead>.bundle
```

仓库外执行：

```powershell
git bundle create ..\nollm_aold_llm_native_evidence_main_agent_recall_20260722_<shorthead>.bundle --all
git bundle verify ..\nollm_aold_llm_native_evidence_main_agent_recall_20260722_<shorthead>.bundle
Get-FileHash ..\nollm_aold_llm_native_evidence_main_agent_recall_20260722_<shorthead>.bundle -Algorithm SHA256
```

---

# 23. 最终回复要求

最终只报告：

```text
branch / HEAD / commits；
Writer first-attempt success；
legacy reject；
Evidence quote/provenance；
stale plan；
main-agent tool；
hidden child-agent count；
default/expanded Locality；
scale target reach/leakage；
latency；
tests/Manifest/boundary；
实际推进向量和完成度；
known limitations；
Bundle/SHA。
```

---

# 24. 最终任务概括

```text
Rev4 已经证明：
LLM可以形成正确命题、选择共享召回路径，
并让东京、会议、天气从不同入口找到同一事实。

下一步不是继续增加模型或几何概念。

要把LLM不擅长的字符定位交给确定性代码；
让Statement永久保存可重建的Evidence链；
拒绝等待期间已经陈旧的Cartography计划；
让正在回答用户的主代理直接操作Nollm几何；
从一个入口先取小Locality，需要时原入口扩展；
并在60～100事实中证明它仍然选择性可用。
```

> **减少 LLM 之间的转述，让 LLM 直接使用 Nollm，才是降低延迟并保持 Architecture is the Index 的正确下一步。**
