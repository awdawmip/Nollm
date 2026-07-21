# Nollm AOLD：Recall Entry 身份、上下文 Writer 与共享召回场生长任务书

**任务文件名**：`NOLLM_A_O_L_D_RECALL_ENTRY_IDENTITY_CONTEXTUAL_WRITER_RELATIONAL_GROWTH_TASK_20260721.md`  
**日期**：2026-07-21  
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**任务性质**：修复 Rev3 Live 的真实产品 bug 和 LLM 教学缺口；冻结 Core 可靠性修复，不新增几何能力  
**输入 Bundle**：`nollm_caold_runtime_integrity_atomic_proposition_growth_20260721_c40f8bf.bundle`  
**输入 Bundle SHA-256**：`16a77df3eabac4a135c3e20f3bf109d56afab8dad19011817a5d46d5feeba771`  
**输入分支**：`codex/caold-runtime-integrity-atomic-proposition-growth-evidence-closure`  
**输入 HEAD**：`c40f8bf6a5be6184e5e56236c96d2817fed4bee5`  
**输入 Tag**：无  
**建议分支**：`codex/aold-recall-entry-identity-contextual-writer-relational-growth`  
**主环境**：Windows 10/11、PowerShell、Node 24、真实 OpenClaw / LongCat-2.0  
**交付**：大跨度单任务；内部 Gate；普通问题直接修复；所有真实进展 commit；clean tree；仓库外单一完整历史 Git Bundle  
**插件状态**：保持安装并启用  
**数据状态**：全部旧工作区和冻结 Evidence 保留；新建独立 v6 工作区；不得回写旧冻结文件  
**能力边界**：不修改 Core 几何；不做 multi-cell、多物理层、Stitch、Topic/Entity、语义索引、外部队列或 PB 长跑

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +15% | DISTRIBUTIONS +5%

主方向：
修复 Progressive Atlas entry 身份碰撞；
撤回无效 one-cell反例；
为Writer加入有界同会话叙事上下文和命题级Evidence provenance；
将Recall Lens拆成Direct Query与Entry Query；
重新教Cartographer寻找共享召回邻域而非已有答案；
原样重跑九条原子事实；
形成东京、时间、天气关系臂；
三个不同单入口到达T0；
保留c40f8bf可靠性和Evidence修复。

范围变化：
Access的operation-local entry identity和Writer provenance合同扩大；
OpenClaw Writer/Cartographer Wire升级；
Core、MemoryAtom、GeometryAddress、Junction、Coverage不变。
```

## 0.1 Gate 向量复述

每个 Gate 开始：

```text
C0 | S0 | T0 | A+10 | H0 | U0 | O+10 | L+15 | D+5
```

每个 Gate 结束记录：

```text
entry总数/重复数；
context来源；
错误日期数；
related_growth；
distinct Reader entries；
relation-entry paths；
实际向量和范围偏差。
```

新增 Core 修改或模块偏差超过5%，必须更新任务范围，不得静默扩张。

---

# 1. 输入检查点审核事实

## 1.1 基础现场

```text
Bundle verify：通过；
完整历史：是；
SHA-256：
16a77df3eabac4a135c3e20f3bf109d56afab8dad19011817a5d46d5feeba771；

HEAD：
c40f8bf6a5be6184e5e56236c96d2817fed4bee5；

branch：
codex/caold-runtime-integrity-atomic-proposition-growth-evidence-closure；

working tree：
clean；

exact HEAD tag：
无；

Manifest：
2030 tracked / 2030 rows / 0 unclassified；

production violations/cycles：
0/0。
```

独立复现：

```text
Core/Snapshot/Trace：
98 passed；

changed Access reliability tests：
39 passed；

Manifest/boundary：
passed。
```

完整 Access/Windows Node/M0 使用 Bundle 报告结果，当前 Linux 审核环境未全部独立完成。

## 1.2 应保留成果

```text
Core trace reentry拒绝；
close/import during operation拒绝；
Junction完整评分；
Access FAILED/rollback diagnostics；
commit/readback states；
corrupt Statement item fallback；
revision freshness；
live/frozen Evidence rotation；
Provider identity实取；
9条atomic Capture durable；
one Statement/Atom/Handle/Cell。
```

## 1.3 P0：fast Recall entry identity collision

当前 Access Progressive Atlas 中，不同 region 生成：

```text
progressive-entry:0
```

当前 fast Recall：

```python
entries_by_id = {
  item["entry_id"]: ...
  for region in page.regions
  for item in region.support_entries
}
```

结果：

```text
后region覆盖前region；
9个region可能只剩1个entry；
所有查询反复选择同一Cell。
```

Frozen Live 正好表现为：

```text
东京/时间/天气/无关Recall
→ 全部 selected_entry = (4,0)
→ meeting record Statement；
T0 recall=0；
distinct entries=1。
```

因此：

```text
“one-cell Provider counterexample”
无效。
```

## 1.4 P0：Writer无叙事上下文

Writer只看当前Capture：

```text
“那天晚上我整理了会议记录”
“大阪同一天是晴天”
“东京的雨在傍晚停了”
```

无法可靠绑定前序日期/事件。

已出现：

```text
东京雨停事实被写成2026-07-20；
实际上下文是2026-07-21。
```

## 1.5 P0：Cartographer把relation误解成已有答案

实际输出表明：

```text
取消浅草后去了东京站
→ 因旧region不含东京站答案而independent_seed；

整理会议记录
→ 因旧region不含整理记录答案而independent_seed；

大阪晴天
→ 因旧region不含大阪天气答案而independent_seed。
```

这阻断：

```text
事件延续；
同日关系；
地点行程；
天气对照。
```

正确关系应是共享未来召回路径，而非旧region已经回答新命题。

## 1.6 P1：状态占位符

以下最终文件仍含：

```text
<HEAD>
```

至少：

```text
CURRENT_STATUS；
canonical Ledger；
main report；
summary JSON。
```

最终交付必须绑定实际 HEAD。

---

# 2. 当前能力重新定性

将 `c40f8bf` 记录为：

```text
RUNTIME_INTEGRITY_AND_RELATION_ENTRY_COLLISION_CHECKPOINT_AT_c40f8bf
```

不得继续称：

```text
true one-cell Provider counterexample。
```

建议实际推进：

```text
CORE +5 | ACCESS +8 | OPENCLAW +5 | LAB +7 | D +5
```

该 `CORE +5` 属于 c40f8bf 已完成的可靠性修复，不是本任务目标。

---

# 3. 开工依据

按顺序读取：

```text
FIRST_PRINCIPLES；
PROJECT_BOOK V3.1；
CORE_FUNCTION_PRIORITY V3.4；
V3.7；
V3.9；
V3.10；
V3.11 Rev4；
CURRENT_STATUS；
Ledger；
本任务书；
A/O/L/D charters；
AGENTS。
```

---

# 4. `AGENTS.md`

至少加入：

```text
- c40f8bf is a runtime-integrity checkpoint; its one-cell counterexample is invalid because fast Recall entry IDs collided.
- Every selectable Atlas entry must be unique in its operation/page.
- Never deduplicate Atlas entries by a region-local entry ID.
- Writer receives bounded chronological narrative context, clearly separated from absorption sources.
- Context-only Captures do not re-enter absorption state.
- Absolute time/location normalization requires explicit Evidence provenance.
- Recall Lens distinguishes direct queries from broader entry queries.
- Cartographer resolves a region when it is a plausible shared retrieval neighborhood, not only when it already contains the new answer.
- Do not persist entry queries, relation types, Atlas paths or narrative context.
- Keep one Statement/Atom/Handle/Cell.
- Do not modify Core in this task.
```

---

# 5. 全部模块任务前完成度

| 模块 | 生命周期 | 完成度 | 置信度 | 缺口 | 影响 |
|---|---|---:|---|---|---|
| CORE | CAPABILITY_VALIDATED | 93% | 中高 | 本任务只回归 | 否 |
| SNAPSHOT | IMPLEMENTED | 50% | 中高 | 增量 | 否 |
| TRACE | IMPLEMENTED | 40% | 中 | metrics | 否 |
| ACCESS | IMPLEMENTED | 93% | 中高 | entry身份、context provenance | 是 |
| HISTORY | PROPOSED | 10% | 低 | 暂停 | 否 |
| AUDIT | PROPOSED | 10% | 低 | 暂停 | 否 |
| OPENCLAW | IMPLEMENTED | 92% | 中高 | Writer context、Lens semantics、Reader bug | 是 |
| LAB | IMPLEMENTED | 90% | 中高 | Live反例无效、需重跑 | 是 |
| DISTRIBUTIONS | IMPLEMENTED | 92% | 中高 | Rev4 wires/policies | 是 |

---

# 6. 任务后目标完成度

| 模块 | 前 | 目标 | 交付 |
|---|---:|---:|---|
| CORE |93|93|可靠性回归|
| SNAPSHOT |50|50|回归|
| TRACE |40|40|回归|
| ACCESS |93|97|唯一entry、context provenance|
| HISTORY |10|10|无|
| AUDIT |10|10|无|
| OPENCLAW |92|97|Context Writer、Entry Lens、Reader|
| LAB |90|97|九事实Live和三入口|
| DISTRIBUTIONS |92|96|Rev4 schema/policies|

不写永久100%。

---

# 7. Gate 0：状态和反例冻结

工作：

```text
更新AGENTS/ACTIVE_PROJECT/STATUS/Ledger；
加入Rev4；
撤回one-cell counterexample；
修复所有<HEAD>占位；
将entry collision加入自动失败fixture；
保护性commit。
```

必须记录：

```text
旧Live entry count；
dict overwrite数量；
实际可选Cell；
为什么结论无效。
```

---

# 8. Gate A：Atlas Entry身份

## 8.1 实现

选择：

```text
全局唯一entry_id；
或Reader返回region_id+entry_id。
```

身份必须绑定：

```text
atlas_fingerprint；
region_id；
GeometryAddress。
```

## 8.2 Validators

```text
Page拒绝duplicate selectable identity；
Prompt构建前entry count一致；
Selection后唯一映射；
mutation后旧ID失效；
compat旧Wire。
```

## 8.3 Bug fixture

```text
9 regions；
每region local index=0；
最终Reader entries=9；
9个唯一IDs；
可分别选择9个Cell；
不得dict overwrite。
```

Gate A PASS：

```text
Frozen Live旧查询在修复后不再只能看到(4,0)。
```

---

# 9. Gate B：Narrative Context Window

## 9.1 Context选择

只使用：

```text
同scope/workspace/session；
当前Capture之前；
按时间倒序后恢复顺序；
固定数量和字符预算；
可选少量当前Statements。
```

不得使用query/keyword/embedding。

## 9.2 Writer Wire Rev2

建议：

```text
nollm_openclaw_contextual_proposition_writer_v2
```

每条Proposition：

```text
draft_id；
content_utf8；
source_capture_ids；
evidence_spans；
context_statement_refs；
resolved_references；
direct_queries；
entry_queries。
```

Codex可精简字段，但必须保留来源和Direct/Entry区别。

## 9.3 Source/Context状态

```text
source Capture状态由本batch结果推进；
context-only Capture不重新推进；
context Statement不复制；
provenance可reopen验证。
```

## 9.4 时间和指代

至少支持并验证：

```text
今天；
同一天；
那天晚上；
之后；
那里；
该会议。
```

不要求构建通用NLP parser；由LLM解析，结构化basis让Access机械验证。

## 9.5 错误拒绝

```text
不存在basis的2026-07-20；
旧context完整复制；
assistant建议冒充用户事实；
context跨scope；
未来Capture；
provenance缺失。
```

---

# 10. Gate C：Direct/Entry Lens与Cartographer

## 10.1 Prompt

明确：

```text
direct query：
  新命题直接回答；

entry query：
  未来读者不知道新答案时，
  会先进入的共享关系问题。
```

## 10.2 Cartographer

解析Entry Query，不解析Direct Query为已有答案。

提供：

```text
正面东京/会议/天气对照示例；
负面审计/备份示例；
不得硬编码具体词规则。
```

## 10.3 Relation Gate

至少：

```text
T2 Tokyo Station → T1/Tokyo region；
T4 meeting notes → T3/meeting region；
T5 Osaka sunny → T0/date-weather region；
T6 rain stopped → T0/weather region；
audit/backup unresolved → independent seed。
```

真实Provider结果允许个别差异，但总体：

```text
related_growth>=5；
unrelated independent_seed>=2。
```

## 10.4 Local detail

当representatives不足：

```text
同一Cartographer session request_local_detail；
不创建新session；
不打开全Field。
```

---

# 11. Gate D：Writer语义完整性

建立确定性和Provider测试：

```text
same-day；
pronoun；
event continuation；
multilingual；
wrong date；
wrong location；
assistant paraphrase。
```

必须冻结：

```text
Context Window；
Writer raw；
validated provenance；
rejection reason。
```

硬Gate：

```text
unsupported absolute date count=0；
cross-scope context count=0；
context duplicate admission=0。
```

---

# 12. Gate E：九条原子事实Provider重跑

新工作区：

```text
nollm-aold-contextual-relational-growth-v6
```

使用普通自然聊天，不使用记忆命令。

## 12.1 T0与arms

```text
T0；
东京2条；
时间/会议2条；
天气2条；
无关2条。
```

## 12.2 Placement

```text
Writer context；
Cartographer Entry Queries；
related_growth/independent_seed；
oneStatement/Atom/Cell；
reopen。
```

要求：

```text
9 Captures durable；
9或语义合理数量Statements；
wrong date=0；
related_growth>=5；
unrelated independent seeds>=2；
duplicate/orphan=0。
```

## 12.3 Recall

修复entry身份后：

```text
东京/时间/天气查询selected entries不同；
distinct entries>=3；
T0 Recall成功；
target-hidden causal Gate；
每个arm一个单入口；
unrelated不达；
restart；
NONE。
```

路径：

```text
非空为硬Gate；
长度>=2为优先Observation，不强制扭曲字段。
```

---

# 13. Gate F：可靠性与Evidence回归

必须保持c40f8bf修复：

```text
Core reentry；
Junction rank；
Access fatal rollback；
readback states；
corrupt item；
revision freshness；
worker retry；
live/frozen Evidence；
provider identity。
```

冻结：

```text
新run-scoped live path；
Gateway/writer切换；
Git blob verifier；
最终HEAD绑定；
Manifest在报告后生成。
```

---

# 14. 自动测试矩阵

## Access

```text
duplicate entry identity；
region+entry uniqueness；
context source separation；
provenance；
time references；
Direct/Entry Lens validation；
Cartographer related cases；
independent cases；
old Wire migration。
```

## OpenClaw

```text
Writer context prompt；
scope isolation；
context budgets；
Reader 9-entry fixture；
selection mapping；
Provider format repair；
one hidden Recall；
restart。
```

## Lab

```text
reproduce c40f8bf collision；
verify fixed entry count；
wrong-date rejection；
nine-fact growth；
relation-entry causal；
unrelated negative；
freeze verifier。
```

## Regression

```text
Core；
Snapshot；
Trace；
Access full；
OpenClaw Python/Node；
M0；
Rev3 causal 10/10；
Manifest/boundaries。
```

---

# 15. 性能

```text
Capture p95<=100ms；
Writer common calls=1/batch；
Writer Prompt<=64KB；
context<=active budget；
Cartographer one session/batch；
Reader common hidden calls<=1；
Atlas prompt<=64KB；
Core local不退化。
```

记录：

```text
context chars；
entry count；
duplicate count；
prompt bytes；
Provider seconds；
worker drain。
```

---

# 16. Evidence和报告

Evidence：

```text
validation/aold_contextual_relational_growth_20260721.jsonl
validation/aold_contextual_relational_growth_summary_20260721.json
```

主报告：

```text
docs/project/AOLD_CONTEXTUAL_WRITER_RELATIONAL_GROWTH_REPORT.md
```

报告必须回答：

```text
entry collision如何发生/修复；
Reader真实看到多少entries；
Narrative context；
错误日期；
Direct/Entry Lens；
9条Placement；
三种distinct entries；
T0 paths；
unrelated/restart/NONE；
可靠性回归；
actual vector；
Bundle。
```

---

# 17. 完成状态

全部满足：

```text
CONTEXTUAL_WRITER_SHARED_RETRIEVAL_GROWTH_VALIDATED_AT_<HEAD>
```

否则：

```text
AOLD_CONTEXTUAL_RELATIONAL_GROWTH_IN_PROGRESS_AT_<HEAD>
```

不得再次把入口身份bug或Writer context缺失解释为one-cell几何失败。

---

# 18. 非目标

```text
Core修改；
multi-cell；
多物理层；
Stitch；
多Chart；
持久Lens/relation type；
Topic/Entity；
query/fact entry map；
vector/graph/embedding；
multi-entry Recall；
Provider更换；
PB；
正式发布。
```

---

# 19. Git与Bundle

建议提交：

```text
checkpoint(aold): withdraw collision-invalid one-cell conclusion
fix(access): make progressive Atlas entries operation-unique
feat(openclaw): provide bounded narrative context to proposition writer
feat(aold): separate direct and shared-entry Recall lenses
test(aold): rerun contextual nine-fact relation growth
docs(aold): record contextual relational growth capability
```

最终Bundle：

```text
nollm_aold_contextual_writer_shared_retrieval_growth_20260721_<shorthead>.bundle
```

最终回复：

```text
branch/HEAD；
entry identity；
Writer context/provenance；
Direct/Entry Lens；
related/independent placements；
distinct Reader entries；
relation paths；
wrong-date/duplicate/orphan；
tests/Manifest/boundary；
actual vector/completion；
limitations；
Bundle/SHA。
```
