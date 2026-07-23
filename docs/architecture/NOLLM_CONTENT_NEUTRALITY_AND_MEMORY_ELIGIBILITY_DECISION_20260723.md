# Nollm 内容中立与记忆资格非歧视决定

**日期**：2026-07-23
**性质**：活动架构决定；优先于历史 promotion、secret rejection、source-role exclusion 和 `no_memory` 规则
**输入检查点**：`8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea`

---

# 1. 决定

Nollm 对 canonical memory 的内容保持中立。

```text
任何独立、有意义、可由 Evidence 支撑的命题，
无论其内容类别、敏感性、来源角色、时效、主题、格式、长度、
主观重要性或产生方式，
都具有进入命题形成和几何放置流程的资格。
```

Nollm 不建立：

```text
敏感内容黑名单；
秘密/凭证拒绝规则；
稳定事实 promotion；
天气/短期事实 suppression；
assistant 来源禁入；
tool output 噪声分类；
内容重要性阈值；
按内容类别的 retention。
```

---

# 2. 内容资格与实际写入不是同一概念

内容中立不意味着每次 Capture 都必须创建新 Statement。

一次评估可以产生：

```text
new proposition；
reuse existing proposition；
revision_current；
new model inference；
zero new proposition delta；
retryable technical defer。
```

区别在于：

```text
这些结果描述当前变化量和操作状态，
不评价内容值不值得记。
```

---

# 3. 来源只作为 provenance

允许的来源包括：

```text
user-originated；
assistant-originated；
tool-originated；
recalled-derived；
model-inferred；
mixed-origin。
```

来源身份只用于：

```text
回放；
解释；
重复/reuse判断；
revision证据；
追踪派生链；
用户审查。
```

来源不得自动决定：

```text
是否可以成为Statement；
是否必须隐藏；
是否属于低价值；
是否永久defer。
```

---

# 4. 防止自我回声

记忆派生回答仍然可以包含新的、有意义的推论。

因此防回声不能采用：

```text
memory_derived assistant永远禁入。
```

正确机制：

```text
Writer看到 recalled_statement_ids 和现有 Locality；
比较当前命题与已有命题；
相同内容 → reuse / zero_new_propositions；
真实新推论 → new model-inferred Statement；
旧值被新值替代 → revision_current；
来源谱系写入 provenance。
```

Python/Access 不以关键词、hash、来源角色或固定评分替代 LLM 判断。

---

# 5. 敏感内容

Nollm 可以记录：

```text
密码；
门禁码；
身份证号；
医疗信息；
财务信息；
法律策略；
私人关系；
政治观点；
工具日志；
任何其他完整命题。
```

Nollm 不因为这些内容的类别：

```text
拒绝 Capture；
拒绝 Formation；
拒绝 Admission；
改变 Placement；
降低 Recall；
缩短 retention；
自动遮蔽 canonical bytes。
```

安全由以下合同承担：

```text
scope；
workspace；
Host identity；
访问权限；
explicit export；
explicit forget；
备份与关闭。
```

---

# 6. Canonical 与 Export 分离

Canonical：

```text
Raw Capture；
MemoryStatement；
Statement provenance；
HandleBinding；
Core Atom/Cell。
```

必须保持原样和内容中立。

Explicit export/share copy：

```text
可以依据用户选择创建非canonical副本；
可有单独的分享/脱敏策略；
必须明确标记；
绝不能反向修改canonical memory。
```

---

# 7. 技术预算不得成为内容淘汰

以下预算：

```text
batch chars；
Prompt bytes；
Statements per call；
Cartographer turns；
Surface page size；
Recall result count。
```

只决定：

```text
分批；
分页；
continuation；
延迟；
显式 incomplete 状态。
```

不得决定：

```text
内容是否有资格被记；
Capture是否永久跳过；
剩余命题是否静默丢失。
```

---

# 8. 活动状态名称

退出：

```text
no_memory；
terminal semantic deferred；
stable promotion；
sensitive rejection。
```

活动名称：

```text
zero_new_propositions；
retryable_defer；
incomplete_continuation；
structural_invalid；
admitted；
reused；
revised。
```

`zero_new_propositions` 绑定评估上下文版本，可在新上下文或显式 re-evaluate 时重新评估。

---

# 9. 路由可见性

Routing preview 使用统一、内容中立的有限展示规则。

```text
不识别密码、证件号、医疗或其他类别；
不按内容词汇进行遮蔽；
不改变canonical Statement；
不依据当前query预筛；
同一算法作用于所有内容。
```

路由预览可能显示完整短 Statement 或部分长 Statement，这是私有 scope 内的工具可见性，不是内容资格判断。

是否向外分享由 export 合同决定。

---

# 10. 约束

任何新增代码、Prompt、测试、配置或文档若出现以下逻辑，必须视为架构回归：

```text
if sensitive → reject/mask memory；
if password/token/secret → no admission；
if weather/temporary → no memory；
if assistant/tool → ineligible；
if long → silently skip；
if more than N propositions → silently drop remainder；
if one LLM defer → permanent exclusion。
```

> **Nollm 记录关系、来源、时间、作用域和几何；它不裁判内容是否配得上被记住。**
