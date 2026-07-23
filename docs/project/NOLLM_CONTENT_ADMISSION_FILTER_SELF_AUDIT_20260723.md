# Nollm 内容资格与过滤机制严格自查报告

**日期**：2026-07-23
**输入检查点**：`8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea`
**输入 Bundle**：`nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_8f19a9b.bundle`
**输入 Bundle SHA-256**：`1b573f62d2245ab65c1a52d437ca1e7d86b1bf59cc2a1e1420a2f7e41463f8a8`
**性质**：活动代码、活动文档、迁移资产和上一版无效设计的内容资格自查
**结论**：存在多处将技术预算、来源角色和历史 promotion policy 错误转化为“内容能否成为记忆”的机制，必须先纠正再继续真实 Live。

---

# 1. 自查基准

Nollm 的内容资格原则应当是：

```text
任何独立、有意义、可由 Evidence 支撑的命题，
无论其敏感性、来源角色、时效、主题、格式、长度或主观重要性，
都具有进入命题形成和几何放置流程的资格。
```

这不等于每次都必须产生新 Statement。

正确的零新增含义是：

```text
当前评估上下文中没有形成新的独立命题，
或现有命题应 reuse/revision，
或当前技术条件不足需要重试。
```

它绝不能被解释为：

```text
该类内容不值得记；
该来源不允许记；
该内容太敏感不能记；
该内容太短期不能记；
该内容太长所以永久跳过。
```

---

# 2. P0：活动 Writer 按来源角色禁止内容成为记忆

当前活动 Prompt 规定：

```text
assistant role mode = context_only 或 memory_derived
不得作为 source Evidence，
不得成为新 Statement 的唯一基础。
```

同时规定：

```text
Generic assistant advice is not user memory
unless the user supplied or adopted it.
```

该规则错误地把 provenance 元数据变成了内容资格门禁。

它会一刀切排除：

```text
LLM 新推导出的结论；
LLM 对多条事实的综合判断；
LLM 自主形成的计划；
LLM 工作时形成的假设；
主代理对新证据的独立解释；
工具结果与模型分析共同形成的新命题。
```

正确边界：

```text
user / assistant / tool / recalled-derived / model-inferred
只记录来源谱系，
不决定是否有资格进入 Formation。
```

防止自我回声应通过：

```text
已有 Statement 对比；
reuse；
revision；
Evidence provenance；
derived_from_statement_ids；
zero_new_propositions；
```

而不是禁止 assistant 或 memory-derived 内容。

---

# 3. P0：`no_memory` 是内容淘汰通道

当前活动规则将 `no_memory` 限定为：

```text
no standalone proposition；
empty/tool noise；
exact no-new-information。
```

仍然存在三类越权。

## 3.1 `tool noise` 没有合法内容定义

以下内容都可能被错误归为 tool noise：

```text
程序错误；
模型失败；
命令输出；
系统状态；
调试日志；
数据库返回；
部署事件；
一次重试失败的原因。
```

它们可能是未来最重要的 Evidence。

## 3.2 问题与指令不等于无命题

历史 Formation 资产仍保留：

```text
only a question/instruction → defer
```

但问题和指令可以形成：

```text
用户希望调查东京天气；
用户要求下周提交报告；
用户正在寻找某案件的证据；
用户希望主代理以后采用某种工作方式。
```

## 3.3 exact no-new-information 应进入 reuse/no-delta

已经存在的命题不应被认定为“不值得记”。

正确结果可能是：

```text
reuse existing Statement；
增加新的 Evidence provenance；
确认 current Handle 不变；
当前没有新 Statement delta。
```

因此活动名称应退出 `no_memory`，改为：

```text
zero_new_propositions
```

它描述本轮变化量，不评价内容价值。

---

# 4. P0：`no_memory` 与 `deferred` 是永久终态

当前 Capture 扫描会跳过：

```text
admitted；
no_memory；
deferred。
```

Writer 或 Cartographer 一次输出上述终态后：

```text
Capture 不再自动评估；
退出 Pending read-your-writes；
新上下文无法改变旧结论；
一次模型失败可能永久取消几何 Admission 资格。
```

正确状态模型：

```text
captured；
processing；
retryable_defer；
evaluated_no_new_propositions；
admitted/reused/revised；
structural_invalid。
```

其中：

```text
retryable_defer：
  始终按有界退避重试；

evaluated_no_new_propositions：
  绑定 writer_schema、context_fingerprint 和 evaluation_epoch；
  当前上下文不重复空跑；
  当上下文、Writer版本、相关current Statements或显式re-evaluate条件变化时可重新评估；

structural_invalid：
  Raw Capture仍保留；
  明确诊断；
  修复后可重新进入。
```

不得把 LLM 一次判断变成永久内容资格裁决。

---

# 5. P0：技术预算造成静默内容淘汰

## 5.1 超大 Capture 永久饥饿

当前 batch 构建遇到超过字符预算的 Capture 会 `continue`。

若单个 Capture 本身超过 `absorption_batch_max_chars`：

```text
每次扫描都跳过；
永远无法进入 Writer；
没有明确 terminal/error/continuation。
```

正确行为：

```text
单个超大 Capture 使用 dedicated batch；
仍超 Prompt 预算时建立确定性 source windows；
保存 continuation cursor；
窗口拥有 exact Capture provenance；
全部范围处理完前状态不得进入完成态。
```

## 5.2 最多八条 Statement 无 continuation

Writer 单次最多输出八条命题。

若一个 Capture 包含更多独立命题：

```text
没有 continuation pass；
没有 remaining-source 状态；
其余命题可能静默遗漏。
```

正确行为：

```text
每pass最多N条只是一项调用预算；
已形成命题的digest进入下一pass上下文；
继续请求剩余新命题；
直到 zero_new_propositions；
达到任务总预算则状态为 incomplete_budget_exhausted，不能冒充完成。
```

预算只能决定分批和延迟，不能决定记忆资格。

---

# 6. P0：上一版无效 Rev6 引入敏感内容分类

上一版未执行的 Rev6 设计曾提出：

```text
password / code / secret；
长编号；
邮箱；
URL；
token；
证件号；
preview redaction；
generic private locality card。
```

该设计全部撤销。

它错误地把：

```text
避免 Surface 在选入口前展示完整答案
```

扩张为：

```text
识别内容类别并决定哪些字符可见。
```

新的 routing preview 必须使用统一、内容中立的规则：

```text
同一固定字符预算；
同一确定性代表选择；
不识别敏感类别；
不按内容词汇遮蔽；
不修改 canonical Statement；
不影响 Placement 或 Recall。
```

短 Statement 可能完整出现在 preview 中，这是私有记忆工具的可见性结果，不是记忆资格问题。

访问安全由 scope/workspace 控制，而不是由内容分类控制。

---

# 7. P0：历史 memory-provider 存在内容拒绝策略

历史目录：

```text
integrations/openclaw/nollm-memory-provider/
```

包含：

```text
secret-like statements are rejected；
deterministic explicit stable-sentence promotion；
天气类短期事实不 promoted；
secret in string content is rejected by Python。
```

该目录当前属于迁移/历史资产，不是 formation-loop 活动路径。

但仅标记 `MIGRATION_ASSET` 不足以阻止未来误复用。

应重新标记：

```text
HISTORICAL_INVALID_FOR_CONTENT_ADMISSION
```

并建立测试禁止：

```text
secret rejection；
stable-only promotion；
weather suppression；
content keyword eligibility；
```

进入活动 OpenClaw/Access 路径。

---

# 8. 边界澄清：什么可以保留

## 8.1 外部分享副本的脱敏

以下场景可保留独立分享策略：

```text
用户明确导出的诊断包；
准备公开发送的 Evidence 副本；
外部支持工单附件；
仓库外共享报告。
```

必须满足：

```text
不修改 Raw Capture；
不修改 Statement；
不修改 provenance；
不修改 Core；
不影响 Placement；
不影响 Recall；
只作用于显式 export/share copy；
输出明确标记为非canonical。
```

这不是记忆内容过滤。

## 8.2 Scope 与权限控制

Nollm 可以完整保存任何内容，但必须限制：

```text
谁能读取；
哪个用户scope；
哪个workspace；
哪个Host身份；
是否允许导出；
是否允许forget。
```

安全边界是：

```text
访问主体和作用域
```

而不是：

```text
内容属于什么类别。
```

## 8.3 显式 Forget

用户明确要求删除、撤回或清空某段记忆时，可以通过正式 forget 合同执行。

这属于：

```text
用户控制的数据生命周期
```

不是：

```text
系统根据内容类型主动删除。
```

---

# 9. 其他应同步纠正的隐性语言

以下措辞应从活动规则中删除或改写：

```text
important enough to remember；
stable sentence promotion；
tool noise；
assistant content is not memory；
short-lived facts are no_memory；
sensitive values should be hidden from memory；
low-value Capture；
terminal semantic defer。
```

替换为：

```text
complete proposition；
new proposition delta；
reuse/revision/new/inference；
source provenance；
operation-local technical defer；
evaluation context version；
continuation coverage；
explicit user forget。
```

---

# 10. 最终自查结论

当前 `8f19a9b` 尚未在活动 formation-loop 中实现敏感内容识别或密码/证件号遮蔽。

但已存在以下必须先修复的内容资格偏差：

```text
来源角色一刀切禁入；
no_memory/tool-noise语义；
no_memory/deferred永久终态；
超长Capture永久饥饿；
Statement数量上限无continuation；
历史secret/stable promotion污染源。
```

在这些问题纠正前，不应继续真实 Provider Live。
