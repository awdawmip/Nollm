# Nollm 架构修订 V3.11 Rev6：内容中立命题形成、可恢复吸收与渐进几何路由

**版本**：V3.11 Rev6
**日期**：2026-07-23
**性质**：替代未执行且无效的敏感分类 Rev6；纠正活动 Formation/Absorption 的内容资格偏差
**输入检查点**：`8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea`
**输入 Bundle**：`nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_8f19a9b.bundle`
**输入 Bundle SHA-256**：`1b573f62d2245ab65c1a52d437ca1e7d86b1bf59cc2a1e1420a2f7e41463f8a8`
**状态**：活动目标架构；不表示已实现

---

# 0. 修订结论

本修订撤销：

```text
敏感值分类；
secret/password/token rejection；
内容类别遮蔽 canonical memory；
assistant/memory-derived 来源禁入；
tool noise；
stable-only promotion；
短期事实不记；
no_memory永久终态；
deferred永久终态；
超长Capture静默跳过；
超过8条命题静默遗漏。
```

建立：

```text
内容中立的命题资格；
来源谱系而非来源门禁；
zero_new_propositions变化量；
retryable_defer；
评估上下文版本；
超大Capture continuation；
多pass Statement continuation；
内容中立的渐进几何routing preview；
历史内容过滤资产隔离；
canonical memory与explicit export副本分离。
```

---

# 1. 数据层次

## 1.1 Raw Capture

Raw Capture 永久保存：

```text
exact user bytes；
exact assistant bytes；
tool-visible output bytes（若Host合同要求）；
scope/session/run；
Provider/model；
time；
role provenance。
```

Capture 不判断：

```text
敏感；
重要；
短期；
噪声；
来源是否值得记。
```

## 1.2 Proposition Evaluation

评估记录：

```text
evaluation_id；
writer_schema_version；
context_fingerprint；
source_window coverage；
existing locality fingerprint；
outcomes；
continuation；
retry state。
```

它是可重做的操作记录，不是内容 retention 决定。

## 1.3 MemoryStatement

每条 Statement：

```text
一个完整独立命题；
一个 canonical content；
一份 provenance；
一个 Handle；
一个 Atom；
一个 Cell。
```

一个 Capture 可以形成零、一或多条 Statement。

## 1.4 Geometry

Core 不知道：

```text
敏感性；
来源角色；
重要性；
事实类别；
问题类型。
```

Core 只处理：

```text
GeometryAddress；
occupancy；
relation groups；
Junction；
Coverage；
bounded Recall。
```

---

# 2. 来源中立 Writer

## 2.1 Writer 输入

每个 role item 提供：

```text
capture_id；
role；
exact content；
origin_kind；
recalled_statement_ids；
derived_from_statement_ids；
tool action provenance；
time/scope。
```

`origin_kind` 可以是：

```text
user_originated；
assistant_originated；
tool_originated；
recalled_derived；
model_inferred；
mixed_origin。
```

这些字段只帮助 LLM 理解来源和重复关系。

## 2.2 Writer 不得采用的规则

```text
assistant不允许形成Statement；
memory-derived不允许形成Statement；
tool output默认噪声；
敏感内容拒绝；
天气/短期事实拒绝；
只有用户采用后才允许记录模型推论。
```

## 2.3 Writer 语义任务

LLM 判断：

```text
是否形成独立命题；
命题是否已存在；
是否reuse；
是否revision；
是否为新的模型推论；
是否需要更多上下文；
Direct/Entry Queries。
```

Writer 可以从 assistant/tool/recalled-derived 内容形成 Statement，但必须：

```text
保留来源；
声明 derived_from_statement_ids；
与已有 current Statements 比较；
重复内容优先reuse/zero delta；
真实新推论才能new。
```

## 2.4 Python/Access 边界

Access 只验证：

```text
schema；
Evidence quote；
Capture identity；
provenance；
预算；
排序；
状态指纹。
```

不得以：

```text
关键词；
secret regex；
来源角色；
固定评分；
内容长度；
主题类别；
```

决定命题资格。

---

# 3. 活动 Writer Outcome

## 3.1 Plan

```text
outcome=plan；
propositions>=1；
每条proposition有source/provenance；
```

## 3.2 Zero New Propositions

```text
outcome=zero_new_propositions；
propositions=[]；
reason只描述本轮delta；
```

可用原因示例：

```text
全部内容已reuse；
当前材料没有形成新的独立命题；
当前回答只是已有命题的复述；
```

禁止原因：

```text
内容不重要；
敏感；
短期；
工具噪声；
assistant来源；
```

## 3.3 Retryable Defer

```text
outcome=retryable_defer；
retry_reason；
next_condition；
```

用于：

```text
Provider失败；
上下文不足；
Evidence引用歧义；
Atlas overflow；
stale plan；
技术预算不足；
revision等待确认。
```

它永不成为永久内容排除。

## 3.4 Incomplete Continuation

```text
outcome=incomplete_continuation；
已形成propositions；
remaining source windows；
continuation token；
```

用于单次命题上限或 Prompt 预算。

## 3.5 Structural Invalid

```text
Capture损坏；
状态文件损坏；
不可解析协议；
```

Raw Capture保留，修复后可重新评估。

---

# 4. Capture 与评估状态机

```text
captured
  → processing
  → admitted / reused / revised
  → evaluated_no_new_propositions
  → retryable_defer
  → incomplete_continuation
  → structural_invalid
```

## 4.1 evaluated_no_new_propositions

不是永久终态。

它绑定：

```text
writer schema；
Prompt version；
context fingerprint；
visible current Statement fingerprint；
source window coverage；
evaluation epoch。
```

只有在这些条件未变化时，worker可以避免重复空跑。

以下情况可重评：

```text
Writer版本变化；
相关上下文新增；
current Statement revision/forget；
用户显式re-evaluate/backfill；
旧评估缺少完整source coverage。
```

## 4.2 retryable_defer

```text
指数退避；
最大等待观察；
stale claim恢复；
永远保留Raw Capture；
Pending fallback按明确策略继续。
```

## 4.3 状态迁移兼容

旧状态：

```text
no_memory；
deferred。
```

迁移时：

```text
no_memory → evaluated_no_new_propositions_legacy；
deferred → retryable_defer_legacy；
```

不得直接当作永久完成。

---

# 5. 超大 Capture 与无遗漏 continuation

## 5.1 Dedicated Batch

若单 Capture 超过普通 batch char budget：

```text
单独运行；
不能continue跳过；
记录oversize=true。
```

## 5.2 Source Windows

若仍超过 Writer Prompt 预算：

```text
确定性字符窗口；
固定 overlap；
每window记录Capture exact range；
不按内容句型/敏感性切分；
全部range union覆盖原Capture；
```

窗口只是 Formation 输入，不改变 Raw Capture。

## 5.3 命题 continuation

每次最多 N 条 Statement 只是调用预算。

流程：

```text
pass 1：形成最多N条；
保存proposition digests和Evidence coverage；
pass 2：要求仅形成尚未输出的新命题；
...
直到 zero_new_propositions。
```

必须限制无限循环：

```text
最大passes；
若耗尽 → incomplete_budget_exhausted；
不得标admitted/no-delta完成；
后续worker可继续。
```

## 5.4 跨窗口重复

Overlap产生的重复由 LLM/Access 通过：

```text
reuse；
content digest；
Evidence provenance；
current Locality比较；
```

处理。

Python不做语义去重。

---

# 6. Placement 与来源无关

Placement 使用：

```text
Statement content；
Direct/Entry Queries；
Prompt-bounded Atlas；
Locality context。
```

不得使用：

```text
sensitive flag；
source role eligibility；
importance；
retention class；
short-term class。
```

assistant/model-inferred Statement 与 user-originated Statement 使用同一：

```text
related_growth；
independent_seed；
reuse；
revision_current；
Junction；
Admission。
```

来源仅进入 provenance。

---

# 7. 内容中立渐进几何路由

## 7.1 路由为什么需要内容

纯哈希 routing anchor 无法让 LLM 选择 Locality。

因此 routing card 可以展示：

```text
统一预算的raw Statement excerpt；
region occupancy；
entry IDs；
truncated flag；
```

但不得建立内容分类。

## 7.2 统一 excerpt 规则

例如：

```text
每region确定性选择最多K条representatives；
每条取同样的前N codepoints或等价固定窗口；
所有内容类别使用同一规则；
短Statement可完整显示；
长Statement统一截断；
不识别密码、编号、邮箱、URL、医疗、法律等类别；
不替换、遮蔽或泛化内容。
```

该 preview：

```text
operation-local；
不持久化；
不作为新的事实；
不修改canonical Statement；
不按query预筛。
```

## 7.3 Progressive Open Region

主代理工具支持：

```text
surface；
open_region；
recall；
expand；
none。
```

当 top page 超预算：

```text
使用更粗Surface order；
展示全部当前层children；
选择一个region下降；
不得stable-key抽样或整体overflow失忆。
```

## 7.4 单入口

最终：

```text
只能选择一个entry；
recall返回一个bounded Locality；
expand保持同一entry；
```

Preview中偶然包含完整短事实不改变单入口Core合同，也不构成内容过滤理由。

产品证据应分别记录：

```text
surface-only answer；
recall-backed answer；
```

但不能为提升target-hidden指标而按内容类别遮蔽。

---

# 8. Canonical 与 Export

## 8.1 Canonical

```text
Raw Capture；
Statement；
provenance；
Handle；
Atom/Cell。
```

不允许内容分类变换。

## 8.2 Explicit Export

用户明确创建外部分享副本时：

```text
可以调用独立export policy；
输出标记noncanonical；
记录导出配置；
不回写canonical；
不影响内部Recall。
```

历史 diagnostics redaction 只能保留在此边界。

---

# 9. 历史资产隔离

以下资产必须重新标记：

```text
integrations/openclaw/nollm-memory-provider
→ HISTORICAL_INVALID_FOR_CONTENT_ADMISSION。
```

禁止从中迁移：

```text
secret rejection；
stable-sentence promotion；
weather/temporary suppression；
content keyword admission；
```

允许保留：

```text
历史测试；
外部preflight export redaction；
回溯报告；
```

但需要显式说明不属于 canonical memory path。

---

# 10. Forget 与 Retention

允许：

```text
用户显式forget；
workspace关闭；
用户配置的全局/范围 retention；
法律或Host要求的整体数据生命周期策略。
```

禁止：

```text
按敏感性、主题、来源、短期性自动缩短 retention；
模型自行永久删除Capture；
zero_new_propositions删除原文。
```

---

# 11. 模块所有权

## Access

拥有：

```text
内容中立Writer schema机械验证；
Evaluation identity；
Statement provenance；
continuation coverage；
progressive routing cards；
Placement/Recall组合。
```

不拥有：

```text
敏感分类；
内容价值；
来源资格；
语义promotion。
```

## OpenClaw

拥有：

```text
immutable Capture；
role/source provenance；
worker状态；
retry/continuation；
真实Writer/Cartographer；
main-agent工具。
```

## Lab

拥有：

```text
内容多样性测试；
来源多样性；
oversize/continuation；
legacy policy回归；
routing usability；
Provider Live证据。
```

## Distributions

只声明：

```text
active content-neutral Writer版本；
state migration；
budgets；
Profile；
legacy policy禁用。
```

Core不变。

---

# 12. 禁止路线

```text
sensitive/secret/password/token admission filter；
按内容类别redact canonical memory；
stable-only promotion；
weather/temporary suppression；
assistant/tool来源禁入；
no_memory价值判断；
permanent semantic defer；
超长Capture静默跳过；
命题上限静默丢剩余；
关键词/regex内容资格；
Topic/Entity；
vector/graph/embedding；
query/fact索引；
multi-entry；
multi-cell；
多物理层；
Stitch。
```

---

# 13. 最终架构概括

```text
所有原始内容先保存。

LLM判断命题、重复、修订和新推论，
但来源和内容类别不决定资格。

技术预算只产生分页、续跑和重试，
不产生永久遗忘。

几何路由可以统一展示有限原文片段，
但不识别哪些内容“敏感”。

访问安全由scope和workspace承担，
外部分享副本与canonical memory严格分离。
```

> **Nollm 可以记住任何内容；它只需要知道这些内容从哪里来、属于谁、放在哪里，而不需要判断它们是否应该被记住。**
