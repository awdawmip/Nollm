# Nollm AOLD：内容中立命题形成、可恢复吸收与渐进几何路由任务书

**任务文件名**：`NOLLM_A_O_L_D_CONTENT_NEUTRAL_FORMATION_RECOVERABLE_ABSORPTION_PROGRESSIVE_ROUTING_TASK_20260723.md`
**日期**：2026-07-23
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**任务性质**：撤销内容资格过滤，纠正 Formation/Absorption 状态和预算遗漏，再恢复内容中立的渐进几何路由；不修改 Core
**输入 Bundle**：`nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_8f19a9b.bundle`
**输入 Bundle SHA-256**：`1b573f62d2245ab65c1a52d437ca1e7d86b1bf59cc2a1e1420a2f7e41463f8a8`
**输入分支**：`codex/aold-role-aware-capture-routing-surface-real-main-agent-live`
**输入 HEAD**：`8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea`
**无效产物**：此前未执行的敏感分类 Rev6 整包作废，不得复用
**建议分支**：`codex/aold-content-neutral-formation-recoverable-absorption-routing`
**主环境**：Windows 10/11、PowerShell、Node 24、真实 OpenClaw / 当前 Host Provider
**交付**：大跨度单任务；内部 Gate；所有真实进展 commit；clean tree；仓库外单一完整历史 Git Bundle
**插件状态**：保持安装；在内容中立 Gate完成前不得执行正式 Provider Live
**数据状态**：旧 Raw Capture、Statement、Handle、Core state 和冻结 Evidence 全部保留；不得批量重写 canonical 内容
**能力边界**：不修改 Core、Coverage、Junction、MemoryAtom、one Statement/Atom/Handle/Cell 或 single-entry Recall；不做 multi-cell、多物理层、Stitch、Topic/Entity、vector/graph/embedding、query/fact索引

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +15% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +15% | DISTRIBUTIONS +5%

主方向：
撤销所有基于敏感性、来源角色、时效、工具类型和长度的记忆资格判断；
将no_memory/deferred永久终态改为zero-delta、retry和可重评状态；
修复超大Capture饥饿和Statement上限无continuation；
隔离历史secret/stable promotion资产；
建立统一、不分类内容的渐进几何routing preview；
完成内容多样性、来源多样性、oversize、continuation和Provider回归。

范围变化：
无新架构模块；
Access/OpenClaw公共Wire和Capture状态合同升级；
Core保持完全不变。
```

## 0.1 Gate向量复述

每个 Gate 开始：

```text
C0 | S0 | T0 | A+15 | H0 | U0 | O+15 | L+15 | D+5
```

每个 Gate 结束记录：

```text
实际受影响模块；
预计/实际偏差；
是否新增内容分类；
是否存在来源角色禁入；
是否有Capture静默遗漏；
是否有永久semantic defer；
是否修改Core；
是否需要更新任务范围。
```

出现 Core 修改或模块偏差超过5%，必须更新任务名、向量和Ledger。

---

# 1. 输入审核基线

## 1.1 Git现场

```text
Bundle verify：通过；
完整历史：是；
HEAD：8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea；
branch：codex/aold-role-aware-capture-routing-surface-real-main-agent-live；
working tree：clean；
tracked：2068；
production violations/cycles：0/0。
```

## 1.2 应保留能力

```text
Raw visible-turn Capture；
Evidence quote resolver；
Statement provenance；
run/session operation scope；
Prompt-bounded Atlas；
realized Junction；
entry identity；
Direct/Entry Query；
independent seed；
related growth；
Core可靠性；
live/frozen Evidence分离；
one Statement/Atom/Handle/Cell；
single-entry Recall。
```

## 1.3 必须纠正的P0

```text
assistant context_only/memory_derived禁止成为source；
Generic assistant advice默认不允许形成命题；
no_memory/tool noise；
no_memory/deferred永久终态；
超大Capture被batch continue永久跳过；
每次最多8 Statements无continuation；
历史memory-provider secret rejection/stable promotion；
无效Rev6敏感分类设计。
```

---

# 2. 当前能力重新定性

`8f19a9b` 记录为：

```text
ROLE_AWARE_CAPTURE_WITH_CONTENT_ELIGIBILITY_DRIFT_CHECKPOINT_AT_8f19a9b
```

它证明 Raw Capture 和来源元数据存在，但来源元数据被错误用作资格门禁。

建议审核后基线完成度：

| 模块 | 生命周期 | 当前完成度 | 置信度 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|
| CORE | CAPABILITY_VALIDATED | 93% | 中高 | 回归 | 否 |
| SNAPSHOT | IMPLEMENTED | 50% | 中高 | 增量 | 否 |
| TRACE | IMPLEMENTED | 40% | 中 | metrics | 否 |
| ACCESS | IMPLEMENTED | 86% | 中 | 内容资格Wire、状态、continuation | 是 |
| HISTORY | PROPOSED | 10% | 低 | 暂停 | 否 |
| AUDIT | PROPOSED | 10% | 低 | 暂停 | 否 |
| OPENCLAW | IMPLEMENTED | 84% | 中 | role禁入、永久终态、oversize | 是 |
| LAB | IMPLEMENTED | 80% | 中 | 缺内容中立和无遗漏证据 | 是 |
| DISTRIBUTIONS | IMPLEMENTED | 88% | 中 | 历史policy污染、Wire声明 | 是 |

---

# 3. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 交付能力 | 剩余限制 |
|---|---:|---:|---:|---|---|
| CORE | 93% | 93% | 0% | 完整回归 | 多层/Stitch |
| SNAPSHOT | 50% | 50% | 0% | 回归 | 增量 |
| TRACE | 40% | 40% | 0% | 回归 | metrics |
| ACCESS | 86% | 96% | +15%向量 | 内容中立Wire、evaluation/continuation | 长期规模 |
| HISTORY | 10% | 10% | 0% | 无 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无 | 暂停 |
| OPENCLAW | 84% | 95% | +15%向量 | 可恢复worker、来源中立、无饥饿 | 多Host |
| LAB | 80% | 94% | +15%向量 | 多样性/oversize/Provider证据 | 长期统计 |
| DISTRIBUTIONS | 88% | 93% | +5% | 活动Wire与历史隔离 | 正式发行 |

不得写永久100%。

---

# 4. Gate 0：权威原则和自查入库

工作：

```text
加入内容中立决定；
加入严格自查报告；
更新FIRST_PRINCIPLES；
更新AGENTS/ACTIVE_PROJECT/CURRENT_STATUS/Ledger；
将无效敏感分类Rev6标记VOID；
将8f19a9b重新定性；
保护性commit。
```

`FIRST_PRINCIPLES` 至少加入：

```text
Nollm对canonical memory内容中立；
来源只作provenance；
敏感/短期/工具/assistant不影响资格；
技术预算只产生continuation；
安全依赖scope而非内容类别；
export副本与canonical分离。
```

`AGENTS.md` 至少加入：

```text
- Never classify canonical memory as sensitive, secret, temporary, tool noise, low-value or ineligible.
- Source role is provenance, not admission eligibility.
- Recalled-derived assistant content may form a genuinely new inference; compare through LLM reuse/revision/new, not a blanket ban.
- `no_memory` is not an active outcome. Use zero_new_propositions.
- Semantic defer is retryable and never permanently excludes Capture.
- Oversize Captures and statement limits require continuation; they may not silently skip content.
- Production code may not branch on password/token/secret/weather/temporary/source-role terms for memory eligibility.
- Canonical memory is never redacted by content category.
- Export/share copies may have independent policy and never write back.
- Historical nollm-memory-provider promotion/rejection policy is invalid for active content admission.
- Core remains unchanged.
```

Gate 0 PASS：

```text
唯一活动权威明确；
无效Rev6不可执行；
P0清单进入状态；
向量/完成度重算。
```

建议提交：

```text
checkpoint(aold): adopt content-neutral memory authority
```

---

# 5. Gate A：活动 Writer v4 内容中立

## 5.1 Wire

建议：

```text
nollm_openclaw_content_neutral_proposition_writer_v4
```

输入 role item：

```text
capture_id；
role；
content_utf8；
origin_kind；
recalled_statement_ids；
derived_from_statement_ids；
tool provenance；
time/scope。
```

删除：

```text
user_role_mode/assistant_role_mode作为eligibility；
source/context_only/memory_derived禁入语义。
```

可以保留 origin metadata，但所有来源均可成为 Evidence。

## 5.2 Prompt

必须明确：

```text
不要按敏感性、时效、重要性、来源角色或工具类型判断资格；
比较已有Statement；
相同→reuse/zero delta；
真实新推论→new model-inferred；
新值替代旧值→revision；
每条命题记录来源谱系。
```

删除：

```text
Generic assistant advice is not memory；
context_only/memory_derived must never be quoted；
empty/tool noise；
no_memory。
```

## 5.3 Outcomes

活动只接受：

```text
plan；
zero_new_propositions；
retryable_defer；
incomplete_continuation。
```

Legacy `no_memory|defer`：

```text
只能在显式migration parser；
普通Provider response拒绝。
```

## 5.4 Provenance

每条 proposition：

```text
source Evidence refs；
origin kinds；
derived_from_statement_ids；
source/context Capture IDs；
Direct/Entry Queries。
```

Access只机械验证。

## 5.5 测试

使用合成内容多样性 fixture：

```text
门禁码；
长编号；
医疗检查；
法律策略；
天气；
临时安排；
程序错误；
工具输出；
assistant推论；
recalled-derived新结论；
用户问题；
用户指令。
```

要求：

```text
无生产关键词分支；
所有均进入同一Writer合同；
结果由LLM语义决定而非类别；
来源字段只影响provenance。
```

Gate A PASS：

```text
role blanket ban=0；
secret/sensitive/temporary/tool eligibility branches=0；
active no_memory=0；
Provider v4 parser严格。
```

建议提交：

```text
feat(openclaw): make proposition formation content-neutral
```

---

# 6. Gate B：Capture状态迁移与可重评

## 6.1 新状态

实现：

```text
captured；
processing；
retryable_defer；
evaluated_no_new_propositions；
incomplete_continuation；
structural_invalid；
admitted；
reused；
revised。
```

## 6.2 评估身份

`evaluated_no_new_propositions` 保存：

```text
writer_schema；
Prompt version；
context_fingerprint；
current_memory_fingerprint；
source coverage；
evaluation epoch；
```

worker只在身份不变时跳过重复空评估。

## 6.3 重评触发

```text
Writer升级；
上下文新增；
相关current revision/forget；
explicit re-evaluate/backfill；
coverage不完整；
legacy状态迁移。
```

## 6.4 retryable_defer

```text
有界退避；
不退出Pending资格，或使用明确Pending策略；
Provider恢复后自动继续；
不需要新聊天触发。
```

## 6.5 Legacy migration

```text
no_memory → evaluated_no_new_propositions_legacy；
deferred → retryable_defer_legacy；
```

迁移必须append-only，不改Raw Capture。

Gate B PASS：

```text
一次LLM终态不再永久排除；
context变化可重评；
Provider暂时失败自动恢复；
状态诊断可复算。
```

建议提交：

```text
fix(openclaw): replace terminal semantic states with re-evaluable outcomes
```

---

# 7. Gate C：超大Capture和命题continuation

## 7.1 Dedicated oversize batch

修改 batch builder：

```text
普通batch装不下下一Capture且batch非空→结束当前batch；
batch为空且单Capture超预算→返回dedicated oversize work item；
不得continue丢弃。
```

## 7.2 Source windows

当单Capture使Writer Prompt超64KB：

```text
确定性窗口；
固定overlap；
精确range；
coverage certificate；
continuation cursor；
```

不得按内容类别切分。

## 7.3 Statement continuation

单pass最多8条可以保留，但必须：

```text
continuation pass；
已输出Statement digests；
要求剩余新命题；
zero_new_propositions终止；
max passes耗尽→incomplete_budget_exhausted；
worker后续继续。
```

## 7.4 Coverage证书

每个Capture记录：

```text
total chars；
windows；
covered ranges；
uncovered ranges；
passes；
formed propositions；
remaining；
```

完成硬Gate：

```text
uncovered ranges=0；
无静默跳过；
无重复Admission；
Raw Capture不变。
```

## 7.5 Fixtures

至少：

```text
单Capture 2x batch budget；
单Capture >64KB；
20个独立命题；
跨window命题；
重复overlap；
Provider timeout mid-continuation；
restart；
partial success。
```

Gate C PASS：

```text
oversize starvation=0；
statement remainder loss=0；
continuation可重启；
duplicate/orphan=0。
```

建议提交：

```text
fix(openclaw): continue oversized Captures and multi-proposition absorption
```

---

# 8. Gate D：Access provenance 与派生链

## 8.1 Statement provenance扩展

记录：

```text
origin_kinds；
derived_from_statement_ids；
source/tool/assistant Evidence spans；
evaluation_id；
continuation pass；
```

## 8.2 规则

```text
assistant/model/tool Statement与user Statement使用同一Store和Core合同；
来源不改变Placement；
派生链不进入Core；
派生链不成为query索引；
revision保留新旧provenance；
```

## 8.3 防回声

Lab验证：

```text
旧Statement→assistant复述→reuse/zero delta；
旧Statement+新推论→new derived Statement；
新推论再次复述→reuse；
```

真实语义由Provider LLM判断，Python只验证 IDs和Evidence。

Gate D PASS：

```text
blanket source ban=0；
真实新推论可Admission；
纯回声duplicate=0；
provenance reopen。
```

---

# 9. Gate E：内容中立渐进几何routing

## 9.1 不透明hash问题

修复 tuple/list bug和hash-only fallback。

## 9.2 Uniform preview

Routing card使用：

```text
固定representative count；
固定codepoint budget；
所有内容同一截取算法；
不识别敏感类别；
不做关键词redaction；
truncated flag；
```

例如：

```text
每region最多2条representatives；
每条最多64 codepoints；
总page<=active Prompt budget。
```

具体预算由Codex实测。

## 9.3 Progressive actions

主代理工具必须支持：

```text
surface；
open_region；
recall；
expand；
none。
```

128/300/1000 Statement：

```text
字段完整；
Prompt有界；
不因top page overflow失忆；
无stable-key抽样；
最终一个entry。
```

## 9.4 可见性真值

报告：

```text
preview完整短Statement数量；
truncated数量；
page bytes；
Surface-only回答；
Recall-backed回答。
```

不得为提高target-hidden指标增加内容分类遮蔽。

## 9.5 Scope

完整内容可能出现在私有routing preview，因此必须：

```text
真实Host scope；
workspace隔离；
跨scope拒绝；
工具内部可见；
```

安全依赖scope，不依赖redaction。

Gate E PASS：

```text
hash-only anchors=0；
content classification branches=0；
progressive large field可导航；
single-entry=100%。
```

建议提交：

```text
feat(access): expose uniform content-neutral progressive routing previews
```

---

# 10. Gate F：历史资产隔离与发行真值

## 10.1 memory-provider

将：

```text
integrations/openclaw/nollm-memory-provider
```

标记：

```text
HISTORICAL_INVALID_FOR_CONTENT_ADMISSION。
```

README/manifest/header明确：

```text
secret rejection；
stable promotion；
weather suppression；
不得迁回活动链路。
```

## 10.2 Preflight redaction

若保留：

```text
只服务显式export/support报告；
noncanonical；
不用于Capture/Formation/Admission/Recall。
```

## 10.3 Distribution

同步：

```text
active Writer v4；
active outcome schema；
legacy state migration；
oversize/continuation budgets；
content-neutral policy；
no sensitive classifier；
```

## 10.4 静态Gate

扫描活动生产路径，禁止出现以下作为eligibility分支：

```text
sensitive；
secret；
password；
token；
credential；
weather；
temporary；
tool noise；
assistant ineligible；
stable promotion。
```

允许：

```text
外部export工具；
测试fixture文本；
历史资产明确隔离。
```

Gate F PASS：

```text
活动内容资格分类=0；
历史污染不可误启用；
发行口径一致。
```

---

# 11. Gate G：Provider内容中立验证

内容中立 Gate 完成后才运行真实 Provider。

## 11.1 内容多样性

使用普通自然聊天形成至少24条Statement，覆盖：

```text
短期天气；
一次性安排；
长期偏好；
门禁码或合成凭证；
医疗记录；
财务记录；
法律策略；
程序错误；
工具输出；
assistant新推论；
recalled-derived新推论；
问题和指令；
长Capture；
多命题Capture。
```

使用合成值，避免真实个人凭证进入测试包。

## 11.2 硬Gate

```text
任何类别都未被生产代码预先拒绝；
Provider按命题语义输出plan/reuse/revision/zero delta；
来源多样；
oversize完成；
continuation完成；
无永久defer；
Raw Capture全部存在；
provenance可重开；
duplicate/orphan=0。
```

## 11.3 Recall

至少：

```text
不同内容类型均可从正确scope Recall；
单入口；
large field progressive；
restart；
NONE；
```

不得在Recall前根据内容类别隐藏或删减canonical memory。

---

# 12. Gate H：测试、Evidence与交付

## 12.1 测试分组

```text
Core/Snapshot/Trace回归；
Access；
OpenClaw Python；
OpenClaw Node；
Lab；
M0/Manifest/boundary。
```

## 12.2 Evidence

```text
validation/aold_content_neutral_memory_20260723.jsonl
validation/aold_content_neutral_memory_summary_20260723.json
```

绑定：

```text
Writer raw/outcome；
source provenance；
state transitions；
re-evaluation；
oversize coverage；
continuation；
routing preview；
Provider/model；
Recall；
static classifier scan；
legacy isolation。
```

## 12.3 报告

```text
docs/project/AOLD_CONTENT_NEUTRAL_MEMORY_REPORT.md
```

必须回答：

```text
是否仍有敏感分类；
是否仍有来源角色禁入；
no_memory/deferred如何迁移；
超长Capture是否全部覆盖；
>8命题是否续跑；
assistant/tool/model推论如何记录；
防回声是否依靠LLM reuse而非禁入；
routing preview是否统一；
历史asset如何隔离；
实际向量和限制。
```

## 12.4 Freeze

```text
停止/旋转live Evidence；
冻结exact bytes；
SHA/lines/bytes；
Summary/Report；
Manifest；
Git blob复算；
commit；
Bundle。
```

---

# 13. 自动测试矩阵

## Writer/Access

```text
all origin kinds eligible；
no content category branches；
zero_new；
retryable defer；
resolved provenance；
derived statements；
reuse/revision/new；
legacy schema rejection。
```

## Capture/Worker

```text
no_memory migration；
deferred migration；
context change re-evaluate；
Provider recover；
oversize dedicated batch；
64KB windows；
20 propositions；
continuation restart；
partial success；
no silent skip。
```

## Routing

```text
tuple/list representatives；
uniform excerpts；
short full preview；
long truncated preview；
no classifier/redaction；
open_region；
128/300/1000 fields；
single entry；
scope isolation。
```

## Historical isolation

```text
memory-provider cannot be active dependency；
secret rejection policy absent from active code；
export redaction cannot mutate canonical files。
```

## Provider Live

```text
content diversity；
assistant inference；
tool output；
weather；
synthetic credential；
long/multi proposition；
Recall/restart/NONE。
```

---

# 14. 性能与调用边界

保持：

```text
Capture前台0 Provider/bridge/Core；
Writer common 1 call/batch/pass；
Cartographer one session/batch；
Prompt<=64KB；
main-agent hidden Reader=0；
one final entry。
```

新增观察：

```text
oversize passes；
continuation passes；
retry wait；
re-evaluation count；
routing page bytes；
Provider backlog。
```

预算不得变成内容淘汰。

---

# 15. 停止条件

只有：

```text
活动Host无法表达来源谱系；
现有Capture状态无法无损迁移；
continuation无法避免重复或遗漏且需要架构决策；
真实Provider长期不可用；
旧数据存在不可恢复损坏。
```

普通Prompt、JSON、测试、命名、性能问题直接修复继续。

无论完成与否：

```text
commit；
clean；
完整Bundle；
不补造；
旧数据保留。
```

---

# 16. 完成状态

全部通过：

```text
CONTENT_NEUTRAL_MEMORY_FORMATION_AND_RECOVERABLE_ABSORPTION_VALIDATED_AT_<HEAD>
```

否则：

```text
AOLD_CONTENT_NEUTRAL_MEMORY_IN_PROGRESS_AT_<HEAD>
```

不得在本任务中恢复正式Live验收，除非Gate A-F全部通过。

---

# 17. 明确非目标

```text
Core修改；
敏感分类；
canonical redaction；
multi-cell；
多物理层；
Stitch；
Topic/Entity；
vector/graph/embedding；
query/fact索引；
multi-entry；
Provider更换；
PB；
正式发布；
History/Audit产品。
```

---

# 18. 建议提交序列

```text
checkpoint(aold): adopt content-neutral memory authority
feat(openclaw): make proposition formation source-neutral
fix(openclaw): replace terminal semantic outcomes with re-evaluable states
fix(openclaw): continue oversized and multi-proposition Captures
feat(access): persist origin and derivation provenance
feat(access): expose uniform progressive routing previews
chore(distributions): quarantine historical content filters
validation(aold): prove content-neutral admission and no silent loss
docs(aold): record content-neutral memory capability
```

---

# 19. Git Bundle

建议：

```text
nollm_aold_content_neutral_memory_20260723_<shorthead>.bundle
```

仓库外：

```powershell
git bundle create ..\nollm_aold_content_neutral_memory_20260723_<shorthead>.bundle --all
git bundle verify ..\nollm_aold_content_neutral_memory_20260723_<shorthead>.bundle
Get-FileHash ..\nollm_aold_content_neutral_memory_20260723_<shorthead>.bundle -Algorithm SHA256
```

---

# 20. 最终回复要求

最终只报告：

```text
branch/HEAD/commits；
内容中立权威；
来源角色；
zero_new/retry状态；
oversize/continuation；
历史policy隔离；
routing preview；
Provider多样性；
Recall；
测试/Manifest/boundary；
实际向量/完成度；
限制；
Bundle/SHA。
```
