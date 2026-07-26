# Nollm 架构修订 V3.11 Rev6.1：单一活动内容中立管线、真实 Tool Evidence 与逐 Capture Continuation

**日期**：2026-07-24  
**输入检查点**：`a6551feb89322826f4faa3b0c98c8b8c6152d5d4`  
**输入 Bundle**：`nollm_aold_content_neutral_memory_20260723_a6551fe.bundle`  
**输入 Bundle SHA-256**：`50d7602dd742acb4c79fd7b4217382b3026eecb45697f1f01b034321e3d63e63`  
**性质**：对 V3.11 Rev6 内容中立实现的闭环修订；不修改 Core 几何  
**状态**：活动目标架构；不表示已经实现

---

# 0. 修订结论

`a6551fe` 已经建立正确的内容中立最高原则，并在主要 Writer v4 路径中实现：

```text
来源角色不作为资格门禁；
no_memory 退出活动 Writer；
semantic defer 可重试；
超长 Capture 建立 source windows；
超过8条命题可以 continuation；
routing preview 不按内容类别遮蔽；
历史 memory-provider 被隔离。
```

但活动系统仍有四个未闭合点：

```text
1. 插件在没有 CaptureStore 时自动启用旧 Formation 路径；
   旧路径仍包含 tool noise、no_memory、assistant内容禁入、
   question/instruction defer 和字符上限终止。

2. continuation 和 evaluation 以批次联合状态写回每个 Capture；
   不同 Capture 的 Statement IDs、覆盖范围和 evaluation identity
   可能互相污染。

3. “tool-originated内容同等有资格”目前只有 origin标签，
   没有 immutable tool output Evidence bytes；
   Writer Evidence role仍只有 user/assistant。

4. Provider Gate未执行，却被报告解释成活动权威禁止；
   当前权威事实上要求真实Provider验证。
```

本修订确立：

> **活动运行时只能存在一个内容中立 Formation 入口。任何 Legacy Formation、promotion、secret rejection、durability filter 或 question/tool-noise filter 都必须离开正常插件路径。每个 Capture 拥有独立的 source coverage、Statement lineage 和 continuation。Tool 输出若参与命题，必须先成为 immutable、scope-bound 的 Tool Evidence，而不是仅靠标签推断。**

---

# 1. 单一活动 Formation 管线

## 1.1 活动入口

正常插件运行只允许：

```text
Durable Capture / Tool Evidence
→ Proposition Writer v4+
→ Field Cartographer v2+
→ Access Admission
```

不得根据配置缺失自动回退到：

```text
DreamFormation v1；
Dream Sculptor v2；
AOLD Formation selector；
nollm-memory-provider；
nollm-memory-companion。
```

## 1.2 缺少前置条件

若活动管线缺少：

```text
capture workspace；
memory workspace；
statement-store Profile；
Provider/model；
Python bridge。
```

结果必须是：

```text
Capture仍持久化；
absorption状态retryable_defer；
diagnose明确指出缺失配置；
零Legacy语义调用。
```

不得启动旧 Formation。

## 1.3 Legacy 只允许显式离线迁移

Legacy parser、prompt、tests 和历史 Evidence可以保留，但必须：

```text
物理目录或模块状态明确为HISTORICAL/MIGRATION；
不被活动bridge action allowlist暴露；
不被registerDreamAgent调用；
需要显式offline_migration=True或独立命令；
输出标记migrated_from_version；
不得声称exact provenance。
```

---

# 2. Tool Evidence 是真实 Evidence，不是标签

## 2.1 当前缺口

当前 Capture仅保存：

```text
user_utf8；
assistant_utf8；
memory_tool_actions；
recalled_statement_ids。
```

`origin_kinds=["tool"]` 只能说明用过工具，不能证明：

```text
工具实际输出了什么；
哪段工具结果支撑Statement；
工具输出是否被assistant改写。
```

## 2.2 Immutable ToolEvidenceRecord

新增 operation/run-scoped immutable记录，例如：

```text
schema_version；
tool_evidence_id；
scope_id_sha256；
workspace_id_sha256；
session_key_sha256；
main_run_id_sha256；
tool_call_id_sha256；
tool_name；
tool_result_utf8或canonical result bytes；
result_sha256；
observed_epoch_ms；
visibility：
  main_agent_visible | internal；
provider/model；
plugin/version。
```

要求：

```text
exact bytes；
append-only；
scope/workspace隔离；
重复tool call幂等；
失败结果也可记录；
不按内容类别过滤；
不因“日志/错误/凭证/短期”拒绝；
不进入Core。
```

## 2.3 Formation Evidence

Writer Evidence role扩展为：

```text
user；
assistant；
tool。
```

每个 Tool Evidence quote：

```text
tool_evidence_id；
quote_utf8；
deterministic exact span。
```

工具输出若没有被捕获：

```text
不得仅凭memory_tool_actions伪称tool Evidence；
只能标tool-associated，不能标tool-originated exact provenance。
```

## 2.4 Scope

Tool Evidence只能被同一：

```text
Host scope；
workspace；
run/session关系；
```

的 Capture引用。

---

# 3. 逐 Capture Continuation

## 3.1 当前错误模型

当前 batch 计算：

```text
priorStatementIds = 所有Capture状态的并集；
priorContinuation = 第一个带continuation的状态；
completeSourceCoverage = 整个batch的所有source windows。
```

随后把这些值写回每个 Capture。

这会导致：

```text
Capture B的state包含Capture A的Statement ID；
Capture B的coverage包含Capture A范围；
多Capture zero-delta evaluation后，
按单Capture重算coverage永远不相等；
不同Capture continuation进度互相覆盖。
```

## 3.2 新模型

每个 Capture拥有独立：

```text
CaptureAbsorptionProgress：
  capture_id；
  source_window_version；
  total_windows；
  covered_ranges；
  uncovered_ranges；
  continuation_pass；
  prior_statement_ids；
  prior_proposition_digests；
  evaluation_identity；
  last_outcome；
  retry state。
```

Batch只负责：

```text
共享一次Provider调用；
共享Cartographer session；
不共享每个Capture的语义完成状态。
```

## 3.3 Writer batch wire

Writer仍可一次处理多个Capture，但每条proposition和continuation必须指明：

```text
source_capture_ids；
covered source windows；
remaining source windows；
本Capture是否还有剩余命题。
```

允许：

```text
Capture A完成；
Capture B继续；
Capture C retryable_defer；
```

同一batch内独立落状态。

## 3.4 前序命题上下文

下一 continuation pass不能只给：

```text
prior_statement_ids。
```

还应给有界、确定性的：

```text
prior proposition content digest；
必要时完整已形成Statement文本；
对应source ranges；
continuation pass。
```

目的是让LLM避免重复输出同一命题。

这些内容：

```text
只用于当前Capture continuation；
不作为新的source Evidence；
不跨scope；
不持久化为索引。
```

## 3.5 完成状态

如果先前pass已Admission，最后pass返回zero delta：

```text
Capture最终状态必须反映已有成功：
admitted / reused / revised / completed_with_statements。
```

不得把它标成：

```text
evaluated_no_new_propositions。
```

`evaluated_no_new_propositions` 只适用于：

```text
完整source coverage；
整个Capture从未产生Statement delta。
```

## 3.6 Pass预算

`writer_max_continuation_passes`必须有真实语义：

```text
每次worker execution最大连续pass数；
达到后：
  状态仍incomplete_continuation；
  保存cursor；
  有界退避；
  下一次worker继续。
```

不得只是每N次写一条error文本，也不得永久停止。

---

# 4. Zero-delta 与重新评估

## 4.1 Capture级 evaluation identity

每个 Capture独立计算：

```text
writer schema/prompt；
本Capture完整source coverage；
本Capture context fingerprint；
本Capture provenance directives；
相关current-memory observation identity；
evaluation epoch。
```

不得使用整个batch coverage hash写入单Capture。

## 4.2 重新评估

支持：

```text
Writer版本变化；
上下文变化；
相关current memory变化；
显式requestReevaluation；
Legacy状态迁移；
operator/user重新评估请求。
```

显式重新评估必须通过：

```text
diagnose/repair命令；
或活动Host内部管理动作。
```

不要求用户编辑Raw Capture。

## 4.3 Pending

`evaluated_no_new_propositions`可以退出高频Pending展示，但：

```text
Raw Capture永远存在；
状态可重新评估；
不得称为内容无资格；
diagnose必须显示evaluation identity和重新评估能力。
```

---

# 5. 诊断与活动状态

`diagnose.ps1`不得继续把：

```text
no_memory；
deferred
```

作为活动终态。

必须统计：

```text
captured；
processing；
retryable_defer；
retryable_defer_legacy；
evaluated_no_new_propositions；
evaluated_no_new_propositions_legacy；
incomplete_continuation；
structural_invalid；
admitted；
reused；
revised；
completed_with_statements（若采用）。
```

同时报告：

```text
continuation captures；
uncovered source windows；
oldest retry；
explicit reevaluation availability；
legacy semantic path enabled=false；
tool Evidence count/corruption；
active Writer schema。
```

---

# 6. 全面历史资产隔离

至少审查并标记：

```text
integrations/openclaw/nollm-memory-provider；
integrations/openclaw/nollm-memory-companion；
integrations/openclaw/grf-adapter；
formation-loop中的adapter.py；
dream_adapter.py；
sculptor.py；
旧placement/reader路径。
```

每项必须明确：

```text
ACTIVE；
MIGRATION；
HISTORICAL_INVALID_FOR_CONTENT_ADMISSION；
REMOVABLE；
```

活动import graph不得从正常Host入口到达内容过滤资产。

分享/诊断副本的redaction工具可保留，但必须标注：

```text
EXPORT_ONLY；
never reads/writes canonical memory admission；
never imported by active Formation。
```

---

# 7. Progressive Routing 保持内容中立

Routing preview：

```text
使用统一固定字符预算；
不识别密码、证件号、医疗、法律、天气或工具内容；
不修改canonical Statement；
不影响Admission/Placement/Recall；
operation-local；
字段完整；
Prompt有界。
```

本修订不引入：

```text
敏感分类；
关键词遮蔽；
Topic/Entity；
query索引；
语义摘要数据库。
```

Provider Live必须检验：

```text
短Statement可按同一规则完整出现；
长Statement统一截断；
不同内容类型不存在差异化逻辑。
```

---

# 8. Provider 内容中立验证

真实Provider场景至少包含：

```text
门禁码/凭证形态；
医疗；
财务；
法律策略；
政治观点；
天气；
临时计划；
程序错误；
工具成功结果；
工具失败结果；
assistant新推论；
recalled-derived新推论；
问题；
指令；
长Capture；
一个Capture超过8条命题；
多Capture batch；
reuse；
revision；
zero delta；
retryable defer。
```

验证内容：

```text
同一Writer schema；
无category-specific rejection；
无source-role ban；
Tool Evidence exact provenance；
每Capture statement IDs独立；
每Capture source coverage完整；
continuation restart；
最终状态正确；
Provider调用和重试可复算。
```

---

# 9. 禁止路线

```text
任何内容黑名单；
secret/password/weather/tool-noise条件分支；
按来源角色禁止Formation；
活动Legacy自动fallback；
批次联合continuation写回每个Capture；
只存tool标签不存tool Evidence却声称tool provenance；
静默截断剩余命题；
用Provider未执行冒充权威禁止；
恢复multi-entry或语义索引；
修改Core。
```

---

# 10. 最终架构概括

```text
所有内容先按同一合同进入Evidence。

活动系统只有一个Writer和一个Cartographer入口；
配置不完整时等待，不回退到旧语义规则。

用户、assistant和tool都有真实、可定位的Evidence；
来源只记录谱系。

每个Capture独立知道：
已经覆盖哪些原文；
形成了哪些Statement；
还剩哪些范围；
下一次从哪里继续。

Batch只节省模型调用，
不合并不同Capture的记忆身份。

真实Provider最终证明：
内容类别不改变记忆资格，
技术预算只改变分批和延迟。
```
