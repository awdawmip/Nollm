# Nollm 架构书 V3.13 Rev1：Field Encounter 直接激活与神经适配延后

**版本**：V3.13 Rev1
**日期**：2026-08-04
**性质**：对 V3.13“几何激活边界、模型适配器与 Legacy 退出”的当前环境纠偏
**活动基础**：V3.12 Unified Field Encounter
**当前环境**：Windows-first；OpenClaw 外部插件；当前 Host/Provider 仅稳定支持文本或工具结果进入上下文；真实 Provider/Host Live 尚未完成
**核心目标**：尽快完成“真实对话 → 真实 LLM 记忆形成 → Nollm 几何场写入 → 后续单入口召回 → 主代理隐藏使用”的完整闭环，并真实测量读写时延
**根目录约束**：`AGENTS.md` 必须存在并保持严格 0 bytes
**实现状态**：目标架构；不表示 Provider Live 已验证

---

# 0. 最终结论

V3.13 原方案在长期边界上是安全的，但对当前 Nollm 目标和运行环境引入了过多尚无现实消费者的生产抽象：

```text
正式 MODEL_ADAPTER 模块；
MemoryActivationPacket；
ModelIdentity；
DerivedActivation；
派生缓存；
scope activation epoch；
Soft Prefix / KV / Attention 的生产接口；
大范围 Legacy 清理与 Provider Live 同任务推进。
```

当前代码已经具备：

```text
FieldEncounterResult
  recalled_statement_ids
  state_identity
  path_digest
  effect

Access 当前 Statement 读取

OpenClaw 精确文本注入
  _direct_locality_injection
  render_recall_injection
```

因此当前正确主路径应当是：

```text
Unified Field Encounter
→ FieldEncounterResult
→ Access 读取这些 ID 当前绑定的 MemoryStatement
→ OpenClaw 在本次 run 内生成精确隐藏文本
→ 主代理回答
```

不新增：

```text
Activation Packet；
正式 Model Adapter；
持久 activation cache；
scope activation epoch；
模型身份注册表；
Prefix/KV/Attention 生产合同。
```

长期研究仍然允许：

```text
Soft Prefix；
Prefix KV；
Attention Bias；
Memory Encoder。
```

但它们只作为 `HYPOTHESIS / PAUSED_RESEARCH` 保存在研究说明中，不进入当前活动架构、任务、发行组合或公共 API。

> **当前 Nollm 需要证明几何场能真实写入、真实找到、真实注入，而不是提前建设“未来如何把召回转成神经状态”的基础设施。**

---

# 1. 为什么必须修订 V3.13

## 1.1 违反核心功能优先

当前最关键缺口仍是：

```text
真实 Provider/Host query-only；
真实 write-only；
真实 mixed turn；
读写共享同一 Field Encounter；
真实重启与并发；
真实调用数；
真实写入和读取时延。
```

在这些尚未闭合前引入新模块和缓存体系，会把开发资源从真实闭环转向未来接口。

## 1.2 当前环境只有一个生产消费者

当前外部 OpenClaw 插件能够可靠使用的是：

```text
隐藏文本上下文。
```

它不能直接：

```text
注入每层 KV；
控制 Attention Head；
修改 Residual Stream；
加载模型专属 Prefix Cache。
```

只有一个消费者时，为 Text/Soft Prefix/KV/Attention 提前建立统一生产 Adapter 属于过度抽象。

## 1.3 Packet 重复现有 Encounter 结果

现有 `FieldEncounterResult` 已提供：

```text
operation identity；
terminal；
semantic relation；
recalled Statement IDs；
state identity；
path digest；
effect。
```

再构造 Packet 会重复：

```text
Statement IDs；
state identity；
path identity；
预算；
scope；
生命周期。
```

并引入第二份需要保持一致的 operation-local 数据。

## 1.4 epoch 解决了尚不存在的问题

当前生产文本注入：

```text
每次操作重新读取 current Statement；
本次 run 结束即丢弃；
不存在跨 run 的 Prefix/KV cache。
```

因此没有需要全 scope epoch 失效的持久派生状态。

当前撤销/修订正确性只需：

```text
下一次 Encounter 从当前 Handle binding 重新读取；
旧 operation 不跨 run 复用；
不持久化 injection。
```

只有未来真正引入跨 run 神经缓存时，才需要设计 cache invalidation。

## 1.5 Legacy 清理范围过宽

仓库二次清理审查要求：

```text
先恢复删除依据；
逐项证明替代；
达到 REMOVABLE 才删除。
```

这不等于当前任务必须同时拆完：

```text
m0_ports；
三个 GRF adapter；
Formation-loop 三文件；
全部 Legacy regression。
```

当前任务只处理：

```text
直接阻塞 Unified Field Encounter Provider Live 的旧路径；
已经被真实 Live 替代且达到 REMOVABLE 的重复实现。
```

其余 Legacy 迁移另立任务，不阻塞真实记忆闭环。

---

# 2. 继续有效的不变量

## 2.1 第一性原理

```text
Evidence first；
File first；
Architecture is the Index；
LLM 负责语义；
Core 负责确定性几何、状态与预算；
无 graph/vector/embedding 主路径；
无 Python semantic placement；
无外置关系索引；
原始 Capture 不丢失。
```

## 2.2 V3.12 Unified Field Encounter

```text
读写不在起点分叉；
同一 Surface；
同一渐进路径；
单一 Entry；
同一 Locality；
事实终态 → Recall / Reuse / Revision；
空位终态 → Placement / NONE；
Probe 与条件 Commit 分离；
路径 operation-local。
```

## 2.3 物理几何

```text
Δθ = 22.5°
θ0 = 0°
β = 2^(1/4)
β² = √2
Physical Layer 与 Aggregation Order 分离
Coverage / Lateral / Bridge
single-entry
one Statement / Atom / Handle / Cell
```

---

# 3. 当前生产架构

## 3.1 查询链

```text
User query
→ Raw Capture
→ main-agent Field Encounter
→ progressive Surface
→ one physical entry
→ bounded Locality
→ LLM select_fact / NONE
→ FieldEncounterResult
→ resolve current MemoryStatements
→ exact hidden text injection
→ main agent answer
→ assistant Raw Capture
```

## 3.2 写入链

```text
Raw Capture
→ one hidden Writer session
→ Formation
→ same session enters Field Encounter
→ fact / vacancy terminal
→ reuse / revision / placement / defer
→ conditional commit
→ reopen verification
```

## 3.3 mixed turn

```text
one user message
→ one Field Encounter operation
→ recall old fact
→ resolve pending new/revision effect
→ one full Surface traversal
→ answer + conditional commit
```

---

# 4. 直接激活（Direct Encounter Activation）

## 4.1 定义

Direct Encounter Activation 是一个 operation-local 动作，不是新的模块、公共类型或持久状态。

输入：

```text
FieldEncounterResult；
当前 Access StatementStore；
固定 injection budget；
当前 Host run。
```

输出：

```text
隐藏文本；
selected statement IDs；
可选 Evidence refs；
可选 path trace（只供诊断，不作为事实证明）。
```

## 4.2 处理顺序

```text
1. 接收 FieldEncounterResult.recalled_statement_ids；
2. 按返回顺序读取当前绑定的 MemoryStatement；
3. 跳过不存在或不再 current 的绑定；
4. 按固定 max_statements / max_chars 截取；
5. 生成 exact text injection；
6. 本次 run 使用；
7. run 结束后丢弃。
```

## 4.3 不允许

```text
把 query 交给 Python 再排序；
关键词摘要；
embedding；
“重要性”打分；
来源角色过滤；
持久化 injection；
持久化 statement→injection；
跨会话复用旧 injection；
把 path 当事实证明。
```

## 4.4 current 语义

当前版本不新增：

```text
CURRENT / SUPERSEDED / RETRACTED / QUARANTINED 状态系统。
```

直接使用现有事实：

```text
HandleStore 当前绑定；
revision_current；
forget；
Statement 当前可解析性。
```

若以后引入正式撤销状态，必须另立范围变化任务。

## 4.5 in-flight 语义

一次主代理 run 在开始注入后发生 revision/forget：

```text
本 run 使用开始时已解析的 operation-local snapshot；
下一 run 必须重新 Encounter；
不得跨 run 复用。
```

这与普通 LLM 上下文快照语义一致，不需要额外 epoch。

---

# 5. OpenClaw 所有权

OpenClaw 继续拥有：

```text
真实 Host 调用；
Field Encounter 工具循环；
operation-local state；
精确隐藏文本格式化；
Provider/模型生命周期；
失败开放；
用户可见回答。
```

OpenClaw 不拥有：

```text
MemoryStatement canonical state；
Core mutation；
语义索引；
模型神经缓存；
未来 KV 的 canonical contract。
```

当前无需新增 `nollm-model-adapter`。

---

# 6. Access 所有权

Access 继续拥有：

```text
MemoryStatement；
Evidence；
Handle binding；
Field Encounter；
Statement 当前读取；
effect resolution；
conditional commit；
Evidence fallback。
```

Access 不新增：

```text
MemoryActivationPacket；
模型身份；
Tokenizer；
KV；
Attention；
派生 cache；
activation epoch。
```

若 Direct Activation 需要一个内部 helper，可放在：

```text
OpenClaw integration；
或 Access 已有 Recall result projection。
```

不得扩大 `nollm_access.__all__`，除非真实第二消费者出现。

---

# 7. Core 所有权

Core 完全不变：

```text
MemoryAtom；
GeometryAddress；
Cell occupancy；
Coverage/Lateral/Bridge；
Surface；
bounded Recall；
atomic state；
canonical persistence。
```

Core 不理解：

```text
injection；
prompt；
token；
model；
Provider；
query；
MemoryStatement；
Activation。
```

---

# 8. 重复实现收敛

当前 OpenClaw 至少存在：

```text
_direct_locality_injection
render_recall_injection
```

任务应核验是否还有：

```text
legacy Recall injection；
main-agent injection；
fast Recall injection；
Field Encounter injection。
```

目标：

```text
一个活动 exact-text renderer；
不同入口只提供相同结构化输入；
旧 renderer 只有在测试和 Live 证明替代后才删除。
```

renderer 应是：

```text
Host internal helper；
无 Provider 调用；
无语义排序；
无持久状态；
输入/输出可测试。
```

---

# 9. 性能架构

当前主要性能目标：

```text
减少 Provider session 数；
减少重复 Surface traversal；
减少重复 Formation/Cartography；
避免新增 serialization/Packet/cache 层。
```

必须测量：

```text
Capture publish；
Formation；
Surface root/page；
Locality；
semantic selection；
direct injection；
commit/reopen；
query→visible；
Capture→commit；
Provider calls；
Host sessions；
tool turns；
prompt bytes。
```

当前不优化：

```text
KV显存；
Prefix长度；
Attention kernel；
模型专属 cache。
```

---

# 10. Failure 与 fallback

## 10.1 无召回

```text
recalled_statement_ids = []
→ NONE
→ 不注入
→ 主聊天继续。
```

## 10.2 Statement 已变化

```text
Encounter 返回 ID 后无法解析当前 Statement
→ 跳过该项；
→ 若全部失效则 NONE；
→ 不使用旧缓存。
```

## 10.3 renderer 失败

```text
不注入；
记录诊断；
主聊天继续。
```

## 10.4 Provider 失败

```text
Recall/Writer 失败开放；
Raw Capture 不丢；
写入零污染或明确 unknown-after-commit；
插件不卸载。
```

---

# 11. Legacy 处理边界

## 11.1 当前必须修复

```text
Current task 指针；
HEAD 层次；
空 lifecycle plan 的权威矛盾；
task-specific boundary report；
直接阻塞 Provider Live 的 ambient PYTHONPATH / ownership 问题。
```

## 11.2 当前可以删除

仅限：

```text
已经被 Direct Encounter Live 替代；
活动 import = 0；
迁移能力有替代；
完整回归通过；
lifecycle = REMOVABLE。
```

## 11.3 当前不要求删除

```text
m0_ports；
三个 GRF adapter；
Formation-loop adapter/dream_adapter/sculptor；
全部 migration assets；
全部 Legacy regressions。
```

除非它们直接阻塞 Live 且替代已经完成。

---

# 12. 神经 Adapter 的研究地位

外部插件与注意力适配器研究继续保留，但其状态为：

```text
HYPOTHESIS；
PAUSED_RESEARCH；
NON_ACTIVE_ARCHITECTURE。
```

不得创建：

```text
正式 MODEL_ADAPTER 模块；
生产 distribution；
公共 Prefix/KV API；
模型身份数据库；
持久神经 cache。
```

## 12.1 重新启动条件

只有同时满足：

```text
V3.12/Rev1 Provider Live 已闭合；
Text injection 有真实质量/Token/时延基线；
存在可控制的自托管推理引擎；
至少一个 Lab 原型消费者；
Text 已证明成为瓶颈；
Soft Prefix 有可能带来可测收益；
撤销和模型升级实验环境可用。
```

才生成单独研究任务。

## 12.2 晋升为正式模块的条件

至少出现两个真实 Adapter 消费者，例如：

```text
Text Host Adapter；
Soft Prefix runtime Adapter。
```

并证明公共合同不是为一个实现抽象后，才讨论正式模块。

---

# 13. 发行组合

当前不变：

```text
bare
  Core

minimal
  Core + Access + Snapshot

OpenClaw active composition
  minimal + OpenClaw integration

debug
  active composition + Trace + selected Lab tools
```

不增加：

```text
model-adapter；
native-attention-lab distribution；
模型专属依赖。
```

---

# 14. 验证不变量

## 14.1 Direct Activation

```text
使用 FieldEncounterResult 原始顺序；
读取 current Statement；
精确文本；
固定预算；
无额外 LLM 调用；
无新持久文件；
相同输入输出确定；
run结束后无残留。
```

## 14.2 Query

```text
hidden Reader child = 0；
single-entry；
NONE不注入；
无 mutation；
自然回答。
```

## 14.3 Write

```text
one Writer Host session；
Cartographer child = 0；
conditional commit；
Raw Capture loss = 0；
duplicate/orphan = 0。
```

## 14.4 Mixed

```text
one Encounter operation；
one full traversal；
Recall + effect；
无第二次全场导航。
```

## 14.5 防漂移

```text
无 Packet；
无 Model Adapter module；
无 activation epoch；
无 model cache；
无 query/fact index；
无 graph/vector/embedding；
无 persistent path；
Core无语义。
```

---

# 15. 实施顺序

```text
R0 修复活动权威和测试环境
→
R1 原样运行 V3.12 Provider Live 基线
→
R2 收敛 exact-text injection 重复实现
→
R3 运行 Direct Encounter Activation Live
→
R4 测量读写调用与时延
→
R5 只删除被真实替代的活动路径
→
R6 状态和Bundle
```

不是：

```text
先建未来 Adapter
→ 再等 Provider Live。
```

---

# 16. 明确非目标

```text
MemoryActivationPacket；
MODEL_ADAPTER；
scope activation epoch；
DerivedActivation cache；
ModelIdentity registry；
生产 Soft Prefix；
生产 KV；
生产 Attention Bias；
LoRA记忆；
完整撤销状态机；
大规模 Legacy 清理；
多入口；
multi-cell；
多物理层 Placement；
Stitch；
History/Audit 产品；
PB规模；
Git历史重写。
```

---

# 17. 最终一句话

> **当前最优架构不是在 Field Encounter 后增加一套“激活系统”，而是让现有 Encounter 结果直接、一次性、无缓存地成为主代理的隐藏记忆上下文；只有当第二种真实模型注入方式出现时，才抽象 Model Adapter。**
