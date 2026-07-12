# Nollm 架构修订 V3.3：语义记忆工具与隐形 Dream Agent

**版本**：V3.3
**日期**：2026-07-12
**性质**：对现行第一性原理中 Evidence 保全要求和 V3.2 exact-span 路线的正式修订
**稳定架构继承**：V3.1 的模块边界、Core 纯净性、依赖方向和可演进基线治理继续有效
**当前路线变化**：OpenClaw 使用从“主代理显式工具调用”改为“插件 Hook + 后台专用子代理”
**一句话定位**：

> **Nollm 是供 LLM 使用的长期记忆工具，不是语义正确性的保证者。**

---

## 0. 结论

Nollm 不应承担：

```text
保证 LLM 一定理解正确；
保证每次拆分、合并和改写都准确；
永久保存用户原始聊天；
把对话原文作为唯一事实源；
用 Python 规则修补模型语义；
安装后要求用户显式学习或调用 Nollm。
```

Nollm 应承担：

```text
向 LLM 提供稳定的记忆形成、放置、召回和遗忘工具；
为模型输出提供结构化、可持久、可组合的 MemoryStatement；
保证数据结构、几何操作、状态变更和持久化的一致性；
允许不同 LLM、Prompt 和使用策略产生不同记忆效果；
在宿主中尽量无感运行；
失败时不破坏主聊天。
```

记忆效果取决于：

```text
所使用的 LLM；
模型上下文；
Dream Prompt；
宿主提供的对话材料；
模型对 Nollm 工具的使用策略；
后续 Placement 和 Recall 策略。
```

因此：

```text
Nollm 提供能力与边界；
LLM 决定如何使用；
产品不对模型语义结果作绝对保证。
```

---

## 1. 对旧“Evidence-first”的正式修订

旧路线中的以下要求退出活动规范：

```text
原始用户聊天必须由 Nollm 永久保存；
MemoryStatement 必须是用户原文连续 span；
每个长期记忆必须可逐字回到原始聊天；
EvidenceStore 必须保存用户输入原件；
只有 exact-span 才能称为可信 Formation。
```

新的规范是：

```text
OpenClaw 会话材料是宿主拥有的临时语义输入；
Dream Agent 可以对会话材料进行语义压缩、拆分、合并和改写；
Nollm 的持久最小单元是 MemoryStatement；
用户原始聊天默认不属于 Nollm 持久状态；
是否另行保留 Transcript、原文或审计材料，由宿主、History、Audit 或产品策略决定。
```

旧原文、span 和 provenance 合同可以作为：

```text
迁移资产；
调试模式；
审计型发行版的可选能力；
parser/schema 回归；
```

不得继续作为默认 Nollm 语义路线。

---

## 2. Nollm 的三类材料

### 2.1 Conversation Material

定义：

```text
宿主在某次 Dream 运行时提供给模型的临时对话材料。
```

可以包含：

```text
当前用户消息；
当前主代理回复；
最近若干轮对话；
会话或项目的少量上下文；
宿主认为有助于记忆形成的临时信息。
```

性质：

```text
由 OpenClaw 或其他 Host 拥有；
只在子代理运行期间存在；
默认不写入 Nollm；
可以在运行结束后消失；
不是 Nollm 的 canonical persistent state。
```

### 2.2 MemoryStatement / Dream Shard

定义：

```text
由 LLM 形成的、能够独立承载意义、适合进入长期记忆系统的语义表达。
```

它允许：

```text
改写表达；
去除“请记住”“顺便说”等交互性措辞；
解析代词和省略主体；
合并跨轮信息；
拆分多个独立事实；
压缩重复；
保留必要的时间、条件、否定和不确定性；
将零散内容整理成自足表达。
```

它不保证：

```text
绝对真实；
绝对完整；
与用户原意完全一致；
不同模型输出一致；
不会遗漏或错误合并。
```

MemoryStatement 是 Nollm 默认持久语义单元。

### 2.3 Dream Trace

定义：

```text
开发、调试和模型比较时使用的临时运行记录。
```

可记录：

```text
模型和 Prompt 版本；
输入材料摘要或受控样本；
模型可见输出；
形成的 MemoryStatement；
defer 原因；
耗时、失败和重试。
```

性质：

```text
属于 Lab/Trace；
生产默认关闭或短期保留；
不进入 Core；
不成为长期记忆正确性的依赖；
不自动保存完整用户聊天。
```

---

## 3. 语义自由与确定性边界

### 3.1 LLM / Dream Agent 负责

```text
是否值得形成记忆；
形成几条 MemoryStatement；
拆分还是合并；
是否改写；
是否补全指代；
是否保留时间和条件；
是否 defer；
输出的语义内容。
```

### 3.2 Access 负责

```text
Schema；
类型；
UTF-8；
statement 数量和大小预算；
ID；
canonical bytes；
形成结果状态；
持久 MemoryStatement 的公共合同；
向后兼容和迁移。
```

### 3.3 Core 负责

```text
语义盲 MemoryAtom；
地址与 Cell；
Coverage / Lateral / Bridge；
有界 Recall；
原子状态操作；
canonical current-state persistence。
```

Core 不判断 MemoryStatement 是否正确。

### 3.4 Python 不负责

```text
按句号拆分；
关键词识别长期价值；
正则判断事实/问题/指令；
修补 LLM 语义；
用评分公式决定记忆；
用 hash 模拟 Placement；
对个别 case 写硬编码答案。
```

Python 只拒绝结构不合法、超预算或无法持久化的输出。

---

## 4. “工具而不是保证”的产品合同

Nollm 保证：

```text
公共 API 的结构正确；
持久对象 canonical；
写入和恢复的工程一致性；
几何执行确定；
预算有界；
失败状态可观察；
模块依赖真实。
```

Nollm 不保证：

```text
模型永不产生错误记忆；
模型不会遗漏；
模型总能判断长期价值；
召回内容永远最相关；
安装后一定改善每个用户；
不同模型具有相同效果。
```

质量结论必须写成：

```text
某模型 + 某 Prompt + 某上下文策略
在某批真实会话上的观察结果。
```

不得写成：

```text
Nollm 保证准确记忆；
Formation 已解决；
模型理解已经通过；
```

---

## 5. 用户无感原则

目标：

```text
安装 Nollm 前后，
普通用户不需要改变聊天方式，
也不应频繁看到 Nollm 的存在。
```

默认不得：

```text
要求用户说“请调用 Nollm”；
把 Formation 工具暴露给主代理；
在正常回复中显示工具调用；
额外发送“已保存”“正在做梦”消息；
要求用户填写第二套 API Key；
因 Dream 运行阻塞主回复；
因 Dream 失败打断聊天。
```

默认行为：

```text
用户正常聊天；
主代理正常回答；
回复交付后，插件在后台启动 Dream Agent；
Dream Agent 形成 MemoryStatement 或 defer；
无额外用户可见消息；
失败时静默放弃本轮记忆形成并记录诊断。
```

调试模式可以显式显示状态，但必须由开发者主动开启。

---

## 6. 默认模型策略

### 6.1 默认：继承 OpenClaw 当前会话模型

```text
memoryModel.mode = inherit
```

特点：

```text
不要求用户配置新 API；
复用现有 Provider、认证和模型选择；
安装路径最短；
记忆风格与主代理较一致。
```

### 6.2 可选：OpenClaw 专用 Dream 模型

```text
memoryModel.mode = dedicated
memoryModel.model = provider/model
```

适用：

```text
降低成本；
降低延迟；
使用更适合抽取和压缩的模型；
将记忆形成与主代理模型解耦。
```

模型覆盖必须通过 OpenClaw 正式配置和允许列表，不由插件直接调用 Provider HTTP。

### 6.3 高级扩展：外部 Memory Agent 后端

独立 API、本地模型或其他 Agent Runtime 可以作为未来后端：

```text
memoryModel.mode = external
```

但它不是默认安装要求，也不属于本轮实现。

### 6.4 统一抽象

无论使用何种模型，架构上统一为：

```text
DreamAgent
  input: ConversationMaterial
  output: DreamFormationResult
```

默认后端是 OpenClaw plugin-owned subagent。

---

## 7. OpenClaw 隐形 Dream 架构

```text
User normal chat
    ↓
OpenClaw main agent
    ↓
Normal visible reply delivered
    ↓
Plugin message/session hook
    ↓
Bounded ConversationMaterial
    ↓
Plugin-owned background subagent
    ↓
DreamFormationResult:
  emit MemoryStatements / defer
    ↓
Access structural validation
    ↓
StatementStore / pending placement
```

关键条件：

```text
Dream Agent 不向用户发送消息；
deliver=false；
主回复不等待 Dream 完成；
Dream 失败不改变主回复；
Formation 不作为主代理可见工具；
插件不直连模型 Provider；
子代理使用 OpenClaw 正式 runtime。
```

OpenClaw 插件 Hook 负责发现合适的消息/会话生命周期事件；后台子代理由 OpenClaw plugin runtime 管理。

---

## 8. 写入阶段

### 8.1 当前阶段

```text
ConversationMaterial
→ Dream Agent
→ MemoryStatement
→ Access StatementStore
```

当前阶段可以先只写入 StatementStore 或 Pending Placement Queue。

不自动宣称：

```text
已经进入几何场；
已经 Placement；
已经可 Recall；
已经形成永久用户偏好。
```

### 8.2 后续 Placement 阶段

```text
MemoryStatement
→ Placement Agent
→ new / reuse / revision / stitch / defer
→ Core validates and executes
```

Placement 仍由 LLM 负责语义选择，Core 只做确定性验证。

---

## 9. 召回阶段的隐形方向

后续召回采用与 OpenClaw Active Memory 类似的宿主形态：

```text
用户正常提问
→ 回复前的 bounded memory subagent
→ 使用 Nollm Recall 工具
→ 得到紧凑相关现场或 NONE
→ 作为隐藏上下文进入主代理
→ 主代理正常回答
```

用户默认不看到：

```text
Recall tool；
记忆查询；
几何路径；
内部摘要；
```

只有调试模式或用户主动管理记忆时显式展示。

本修订只确定方向，不在当前任务中实现完整 Recall。

---

## 10. Access 合同修订

### 10.1 新活动合同

建议公共对象：

```text
ConversationMaterial
DreamFormationRequest
DreamFormationResult
DreamMemoryDraft
MemoryStatement
StatementFormer
StatementStore
FileStatementStore
```

`DreamMemoryDraft` 至少包含：

```text
draft_id
content_utf8
```

可选的模型提示字段：

```text
memory_scope_hint
stability_hint
uncertainty_hint
```

这些字段只是 LLM 建议，不是事实保证，也不进入 Core 语义判断。

### 10.2 退出活动合同

```text
RawEvidenceRecord
EvidenceSpan
StatementSelection
exact-span assemble
FileEvidenceStore
put_original / get_original
```

处理：

```text
保留 compatibility re-export；
保留迁移测试；
标记 LEGACY_REFERENCE 或 REPLACEMENT_READY；
在替代和存储迁移完成前不删除。
```

### 10.3 StatementStore

`StatementStore` 保存：

```text
MemoryStatement
```

不声称保存：

```text
原始 Evidence；
用户原文；
完整 Transcript；
法律或审计证据。
```

现有 `FileEvidenceStore` 的文件格式如能无损解释为 StatementStore，可提供版本迁移或兼容读取。

---

## 11. Dream Prompt 最小职责

Prompt 应表达：

```text
你是后台记忆形成代理；
根据提供的会话材料，形成零条或多条独立、有意义、适合长期使用的 MemoryStatement；
你可以改写、合并、拆分和补全指代；
不要为当前寒暄、临时动作或无长期价值内容强行形成记忆；
不要把猜测写成确定事实；
不确定时 defer；
只输出指定 Schema。
```

Prompt 不应：

```text
要求 exact span；
要求逐字复制；
要求保存原始聊天；
让模型决定 GeometryAddress；
让模型直接写 Core；
让模型向用户回复；
```

---

## 12. 失败与降级

### Dream Agent 失败

```text
超时；
模型不可用；
Schema错误；
空输出；
超预算；
插件异常。
```

默认行为：

```text
本轮 defer；
主聊天不受影响；
可选诊断记录；
不自动切换到 Python 语义规则。
```

### 模型配置失败

默认 `inherit` 无法解析时：

```text
使用明确配置的 OpenClaw modelFallback；
仍失败则跳过本轮；
不要求用户在聊天中处理。
```

### 质量不佳

```text
通过 Prompt、模型、上下文窗口和后续修订能力改善；
不通过堆叠 Python 语义规则改善。
```

---

## 13. 评测原则

主要评测：

```text
安装前后主聊天行为是否无明显变化；
主回复是否不等待 Dream；
后台运行成功率；
Formation emit/defer比例；
语句数量和长度；
模型/Prompt/上下文策略差异；
人工抽样的 useful / harmless / wrong；
后续修订和遗忘是否可用；
成本和延迟；
错误是否污染 Core。
```

不设置为硬通过线：

```text
语义准确率 100%；
人工接受率必须达到固定百分比；
每轮必须形成记忆；
不同模型结果一致；
```

工程硬条件：

```text
主聊天不被阻塞；
无用户可见额外消息；
无 Python semantic fallback；
结构输出可验证；
失败不写入损坏状态；
Core/Snapshot/Trace边界不回退。
```

---

## 14. 数据与隐私边界

默认：

```text
OpenClaw负责会话Transcript生命周期；
Nollm只保存形成后的MemoryStatement；
Dream subagent transcript默认临时并在运行后删除；
Lab调试记录需显式开启；
```

需要原文、审计或法规保留时：

```text
由Host、History、Audit或特定Distribution配置；
不是nollm-minimal默认行为。
```

这不是安全或权限系统设计，而是模块所有权和默认数据最小化。

---

## 15. 迁移结论

以下文件/能力退出活动路线：

```text
V3.2 exact-span Formation 主路线；
AOLD Raw Evidence Chat Truth任务；
原始聊天逐字相等Gate；
主代理显式nollm_form_statement工具；
合成Perfect Fixture语义证明。
```

以下成果保留：

```text
OpenClaw插件安装、启用、诊断和生命周期脚本；
真实模型调用经验；
Access canonical对象和错误处理；
Live运行记录；
Core/Snapshot/Trace/Access模块化基础；
Statement Formation历史测试作为迁移资产。
```

---

## 16. 下一任务

```text
NOLLM_AOLD_INVISIBLE_DREAM_AGENT_TASK_20260712.md
```

完成该任务后，根据真实后台运行决定：

```text
继续调整 Dream Formation；
或生成 MemoryStatement Placement Agent任务。
```

不自动进入 Placement。
