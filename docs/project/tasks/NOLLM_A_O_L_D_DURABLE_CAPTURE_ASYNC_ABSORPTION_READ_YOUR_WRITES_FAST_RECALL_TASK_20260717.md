# Nollm AOLD：原文即时持久化、异步批量吸收、近期记忆直读与低调用召回任务书

**任务文件名**：`NOLLM_A_O_L_D_DURABLE_CAPTURE_ASYNC_ABSORPTION_READ_YOUR_WRITES_FAST_RECALL_TASK_20260717.md`
**日期**：2026-07-17
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**任务性质**：一次性重构真实记忆前台/后台边界；直接解决用户等待时间，不再继续单纯测量现有慢链路
**输入 Bundle**：`nollm_aold_real_memory_commit_recall_latency_20260716_ca50a97.bundle`
**输入 Bundle SHA-256**：`2b138f4fddd084628a5415d5643221e746cd41d7681bb8c9228527e52846c23f`
**输入分支**：`codex/aold-real-memory-commit-recall-latency-baseline`
**输入 HEAD**：`ca50a97e0b9ea6a6358ff37ececbb5cfb4eaaa61`
**输入 Tag**：`AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS_AT_ca50a97e0b9ea6a6358ff37ececbb5cfb4eaaa61`
**建议工作分支**：`codex/aold-durable-capture-async-absorption-fast-recall`
**主执行环境**：Windows 10/11、PowerShell、Node 24、当前真实 OpenClaw / LongCat-2.0 环境
**交付方式**：大跨度单任务；内部 Gate；所有真实进展 commit；工作树 clean；仓库外单一完整历史 Git Bundle
**插件最终状态**：保持安装并启用
**数据最终状态**：V1～V6 旧工作区全部保留；新建独立工作区验证新链路；不得清空或覆盖旧用户数据
**能力结论边界**：完成 Capture、异步吸收、近期未吸收 Evidence 读取、批量语义处理和低调用 Recall；不启动多物理层 Placement、Stitch、PB 长跑、语义索引或产品级消息队列

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
可见回复完成
→ 原始用户/助手对话立即、原子、不可变落盘
→ 前台立刻结束
→ 后台可恢复地批量 Formation 与 Placement
→ Admission 后进入现有几何场
→ Admission 前由有界近期 Capture 提供 read-your-recent-writes
→ 已 Admission Recall 压缩隐藏模型调用数量
→ 用户不再等待后台“整理记忆”。

范围变化：
新增 Host Capture 与 Absorption 运行合同；
Capture 与 MemoryStatement/Placement/Admission 正式分离；
允许有界 Pending Capture fallback；
OpenClaw 模块职责扩展到持久 Capture spool 和后台吸收调度；
Access 是否新增 Capture/Batch 公共合同，由 Codex 在 Gate A 根据现有资产和依赖方向决定；
不改变 Core 几何、V3.9 Coverage、物理层 Policy 或单入口原则。
```

## 0.1 范围变化后的完成度基线说明

当前完成度来自旧职责范围：

```text
ACCESS 95%
OPENCLAW 92%
LAB 95%
DISTRIBUTIONS 90%
```

本任务扩大 OpenClaw 的职责范围。任务开始时应重新计算：

```text
OpenClaw 新范围基线预计：
70%～80%，待 Gate A 按实际 owner 决定后回填。

Access：
若仅复用现有 Statement/Handle/Core 公共合同，基线保持；
若成为 CaptureStore 或 BatchAdmission owner，须按新章程重新计算。

其他模块：
范围不变。
```

不得把范围扩大后的完成度下降解释为能力回退。

## 0.2 Gate 向量复述

每个内部 Gate 开始记录：

```text
当前预计向量：
C 0 | S 0 | T 0 | A +10 | H 0 | U 0 | O +15 | L +5 | D +5

当前主方向：
Capture 立即可靠
→ 前后台解耦
→ 后台可恢复和批量
→ Pending 近期记忆立即可用
→ Admission 后几何接管
→ 减少隐藏模型调用。
```

每个 Gate 结束记录：

```text
实际受影响模块；
预计/实际向量偏差；
是否引入新持久状态；
是否改变公共合同；
是否出现数据丢失或身份冲突；
是否需要更新任务范围、架构修订和模块章程。
```

执行中新增模块或某模块偏差超过 5%，必须更新任务书、向量和状态，不得静默扩张。

---

# 1. 当前问题与任务结论

## 1.1 已验证事实

`ca50a97` 已经证明：

```text
V3.9 本地几何和 Surface 不是主要耗时；
Surface/Core 通常约 0.8～2.5 秒；
真正文件持久化通常是毫秒至几十毫秒；
真实模型调用占写入时间约 96%；
真实模型调用占 Recall 时间约 98%；
相关 Recall 到 hidden injection 约 52～169 秒；
NONE 也约 27～58 秒；
写入中 Formation、Placement、确认和重决策可累计到数分钟。
```

当前慢的根因不是：

```text
文件写入；
Core Atom；
Q16 Coverage；
Lazy Surface；
HandleBinding。
```

而是：

```text
一次记忆写入被拆成多次串行大模型调用；
一次 Recall 被拆成 Surface 导航、入口选择、Recall Selection 等多次模型调用；
每一步可能创建新的隐藏子代理会话；
多条 Statement 又逐条重复 Placement。
```

## 1.2 本任务采用的新结论

```text
Capture 成功：
原始经历已经安全存在，但尚未整理。

Absorption/Admission 成功：
该经历已被 LLM 形成 MemoryStatement，并进入几何记忆场。

Pending Recall：
尚未 Admission 的最近原始 Capture 可以作为短期、有界、无索引的 read-your-recent-writes 安全网。

Geometry Recall：
Admission 后，关系和传播继续由 Nollm 几何承担。
```

用户主回复不得等待：

```text
Formation；
Placement；
revision confirmation；
Core Admission；
后台重试。
```

## 1.3 本任务替代的活动任务

暂停并降为历史测量任务：

```text
NOLLM_O_L_D_SINGLE_USER_SERIAL_MEMORY_LATENCY_CLOSURE_TASK_20260717.md
```

原因：

```text
现有数据已经足以证明调用拓扑不可接受；
继续精确测量数分钟慢链路不能解决用户问题；
本任务直接重构前后台边界，完成后再测新链路。
```

保留 `ca50a97` 的 timing instrumentation，作为改造前对照和新链路验证工具。

---

# 2. 给 Codex 的自由与边界

## 2.1 Codex 可以自行决定

Codex 应先盘点现有代码和历史资产，再选择最简实现。可以自主决定：

```text
Capture 文件目录结构；
Capture ID 生成方式；
使用单文件、分目录、append-only journal 或等价文件方案；
mutable sidecar、状态日志或目录状态机；
CaptureStore 最终 owner 是 OpenClaw 还是 Access；
后台 worker 是插件内单 worker、短生命周期调度器或等价实现；
批次触发条件；
批次最大 turn 数、字符数和等待时间；
Formation/Placement 如何合并或复用同一隐藏会话；
失败重试与退避细节；
Pending fallback 的 TTL、条数和字符预算；
是否新增 Access batch API，或复用现有逐条原子 API；
类名、文件名和内部接口；
测试 fixture 和报告结构。
```

选择后必须在架构决定中记录：

```text
为什么选择；
复用了哪些历史资产；
为什么没有选择其他复杂方案；
owner 和依赖方向；
失败恢复方式；
数据迁移和兼容方式。
```

## 2.2 Codex 不需要停下来确认

以下属于普通工程判断，应直接选择最简单正确方案并继续：

```text
命名；
文件布局；
状态字段；
内部类拆分；
测试组织；
日志格式；
批量大小；
普通文档修正；
非架构性兼容问题；
Windows 路径和 fsync 细节；
局部重构。
```

只有以下真实阻断才停止：

```text
无法在不丢失原文的情况下建立 Capture；
OpenClaw Host 无法取得用户和助手原始文本；
无法保证重复 Hook 幂等；
现有 Access 原子合同无法避免部分 Admission；
Pending fallback 必然需要语义索引；
后台恢复会破坏现有用户数据；
依赖方向必须让生产模块反向依赖 Lab；
真实 Host 限制使用户主回复必须等待 Provider。
```

即使停止，也必须提交已完成进展、clean tree 和 IN_PROGRESS Bundle。

## 2.3 不可协商结果

无论采用何种实现，必须成立：

```text
1. 可见回复后立即保存完整原文；
2. Capture 路径不调用模型、不构建 Surface、不调用 Python bridge；
3. Capture 成功后，Gateway/进程崩溃不得丢失原文；
4. Capture 与吸收状态分离，原文不可被重试状态覆盖；
5. 后台任务可在重启后恢复；
6. 同一可见 turn 不得重复 Admission；
7. 后台吸收不阻塞后续正常聊天；
8. Pending Capture 在短期内可跨 Session 被主代理使用；
9. Pending fallback 不建立 query/keyword/topic/vector 索引；
10. Admission 后退出 Pending fallback，避免重复注入；
11. 现有 Core 几何和单入口 Recall 不回退；
12. 常见写入不再为每条 Statement 重复启动完整 Surface/Placement 会话；
13. Recall 不再使用多次隐藏模型调用完成微导航和结果筛选；
14. 旧工作区和原始 Evidence 不删除；
15. 所有状态可从文件和 canonical state 重建。
```

---

# 3. 活动依据

开工前按顺序读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/project/NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md
3. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_3_SEMANTIC_MEMORY_TOOL_20260712.md
4. docs/project/NOLLM_PROJECT_BOOK_V3_4_CORE_FUNCTION_PRIORITY_20260713.md
5. docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_7_ROTATED_MULTI_SCALE_PHYSICAL_MEMORY_FIELD_20260714.md
6. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_9_BOUNDED_APPROXIMATE_HEX_COVERAGE_20260715.md
7. docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md
8. docs/project/NOLLM_CURRENT_STATUS.md
9. docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
10. 本任务书
11. A/O/L/D 模块章程
12. 根目录 AGENTS.md
```

解释优先级：

```text
原始 Evidence 不丢失
> 用户主聊不等待后台 Dream
> 真实 LLM 保持语义所有权
> Architecture is the Index
> Core 纯净
> 文件优先和可恢复
> 当前任务实现选择
> 历史任务和旧测试捷径。
```

V3.3 已明确：

```text
Normal visible reply delivered
→ background Dream Agent
→ StatementStore / pending placement
```

本任务将该方向真正补全为：

```text
visible reply
→ durable raw Capture
→ async Formation/Placement
→ Admission
```

而不是让原文只存在于临时内存和 Provider Prompt 中。

---

# 4. 根目录 `AGENTS.md` 更新要求

Gate 0 必须更新并遵守根目录 `AGENTS.md`，至少加入：

```text
- The active task decouples durable raw Capture from asynchronous Formation, Placement and Admission.
- The visible reply path may perform only bounded local Capture I/O; it must not call a provider, Python bridge, Surface, Core or Placement.
- A staging temp file is not the canonical record. Canonical Capture is created only after flush and atomic publish.
- Canonical raw Capture is immutable and must not be deleted after Admission by default.
- Absorption state is mutable and separate from raw Capture bytes.
- Gateway restart must resume pending work without duplicate Admission.
- The common case should use one Formation operation and one batch Placement operation per batch, not one full hidden workflow per Statement.
- A destructive revision may use one additional confirmation; it must remain zero-write until confirmed.
- Pending recent Capture fallback is bounded by scope, count, age and characters; it is not a semantic index.
- Pending fallback must not create an extra hidden provider call. It is supplied to the main agent as recent unabsorbed Evidence.
- Once a Capture reaches a terminal absorbed state, it leaves the pending fallback.
- Admitted geometric Recall must use at most one hidden semantic selection call in the common case; do not run a second Recall-selection agent after Core Recall unless a documented blocker requires it.
- The main agent may perform final relevance judgment over a bounded, clearly marked hidden context.
- Do not build Kafka, SQLite, Redis, a queue service, a daemon product, a scheduler framework, ACL, audit platform or persistent query index.
- Reuse existing Access atomicity, StatementStore, HandleStore, timing and OpenClaw subagent assets.
- Make ordinary implementation decisions independently and continue; stop only for data-loss or architecture blockers.
- Incomplete work must still be committed, clean and bundled.
```

---

# 5. 全部模块任务前完成度

| 模块 | 生命周期 | 当前完成度 | 置信度 | 已验证能力 | 当前主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 95% | 高 | 快速 Coverage、Lazy Surface、原子状态、单入口 Recall | 本任务不改 Core | 否 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes | 增量和版本化 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 独立事件合同 | 长期 metrics | 否 |
| ACCESS | `IMPLEMENTED` | 95% | 高 | Statement/Handle/Core 原子协调、revision 保护 | 缺可选批量 Admission/幂等 Capture 关联合同 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 92% | 中高 | Formation、Placement、Recall、隐藏注入、timing | 原文未先持久化；后台不可恢复；模型调用过多 | 是 |
| LAB | `IMPLEMENTED` | 95% | 高 | 几何、Live、延迟分析 | 缺崩溃恢复、积压、Pending Recall、批处理验证 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 90% | 高 | plugin 配置和安装 | 缺 Capture/worker/Pending fallback 配置 | 是 |

---

# 6. 任务执行后目标完成度

由于 OpenClaw 职责范围扩展，Gate A 后先回填重算基线。建议目标：

| 模块 | 旧范围完成度 | 新范围任务目标 | 预计净推进 | 本任务交付 | 剩余限制 |
|---|---:|---:|---:|---|---|
| CORE | 95% | 95% | 0% | 不改几何和持久状态 | 多层、Stitch |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | 增量 Snapshot |
| TRACE | 40% | 40% | 0% | 不新增 Trace 产品 | 长期 metrics |
| ACCESS | 95% | 95%～98% | +10% 向量 | 批量/幂等 Admission 或等价公共复用 | 长期批吞吐 |
| HISTORY | 10% | 10% | 0% | 无变化 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 暂停 |
| OPENCLAW | 92%旧范围 | 88%～92%新范围 | +15% 向量 | Capture、worker、批吸收、Pending fallback、低调用 Recall | 长期多 Provider |
| LAB | 95% | 98% | +5% | 崩溃/恢复/性能/Live 验证 | 长期运行 |
| DISTRIBUTIONS | 90% | 95% | +5% | 版本和配置 | 正式发行 |

禁止为了让表格好看写永久 `100%`。

---

# 7. 目标架构

## 7.1 前台 Capture

```text
User message
→ Main agent visible answer
→ message_sent / verified visible endpoint
→ obtain exact user + assistant turn
→ write staging file
→ flush
→ atomic publish immutable Capture
→ return from hook
```

Capture 路径禁止：

```text
Provider call；
subagent；
Python bridge；
Surface；
Core；
Statement Formation；
Placement；
JSON repair；
revision confirmation。
```

## 7.2 后台 Absorption

```text
immutable pending Capture(s)
→ durable worker claims batch
→ one Formation operation
→ zero or more MemoryStatements
→ one batch Placement operation or equivalent low-call operation
→ Access validates each result
→ Statement + Handle + Core Admission
→ terminal absorption state
```

## 7.3 Pending read-your-recent-writes

```text
new Session query
→ read bounded recent non-terminal Captures
→ render exact recent Evidence as hidden context
→ normal geometric Recall may run in parallel/sequence
→ main agent receives:
     admitted geometric memory
     + recent unabsorbed Evidence
→ main agent answers
```

Pending fallback：

```text
不调用额外 Recall LLM；
不按 query 搜索；
不按关键词过滤；
不建 embedding；
不保存 query→capture；
仅使用固定 scope + recency + count + char budget。
```

## 7.4 Admission 后

```text
Capture remains immutable Evidence；
MemoryStatement becomes semantic current state；
Handle/Core provide geometric relation and Recall；
Capture exits pending fallback；
normal Recall uses geometry。
```

---

# 8. Gate A：历史资产盘点、Owner 决定和架构修订

## 8.1 必须盘点

至少检查：

```text
OpenClaw message_sent / agent_end hooks；
ConversationMaterial；
Dream Formation；
current in-flight suppression；
latency/correlation IDs；
FileStatementStore / FileEvidenceStore；
AccessRuntime atomic apply；
revision confirmation；
current workspace lock；
existing pending placement references；
historical Capture/admission assets；
Windows atomic file helpers；
plugin install/update paths。
```

不得重复建设已有能力。

## 8.2 Owner 决定

Codex 必须在以下两种或更优等价方案中选择：

### 方案 A：OpenClaw-owned Capture spool

```text
OpenClaw 拥有 Host 原文 Capture；
Access 只接收形成后的 MemoryStatement；
OpenClaw worker 调用 Access；
最小化 Access 公共面变化。
```

### 方案 B：Access-owned CaptureStore

```text
Access 定义通用不可变 Capture/状态合同；
OpenClaw 通过 Access 公共 API 写入；
其他 Host 未来可以复用。
```

选择标准：

```text
谁拥有原始 Host material；
依赖方向是否单向；
是否需要 Access 理解 OpenClaw session；
是否复用现有 Store 原子性；
是否会让 Core 或 StatementStore 混入原始整轮对话；
实现和迁移复杂度。
```

禁止同时建立两套 canonical Capture。

## 8.3 架构文件

新增活动修订，建议名称：

```text
docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_10_DURABLE_CAPTURE_ASYNC_ABSORPTION_20260717.md
```

更新：

```text
ACTIVE_PROJECT；
CURRENT_STATUS；
canonical Ledger；
Access/OpenClaw charter；
route；
AGENTS。
```

架构修订只定义：

```text
Capture/Absorption/Admission 分离；
owner；
持久状态；
依赖方向；
Pending fallback；
调用预算；
失败恢复。
```

不复制任务实施细节。

## 8.4 Gate A PASS

```text
唯一 canonical Capture owner；
没有重复 Store；
没有 Core 变化；
旧资产复用清单完成；
范围和完成度已重算；
活动依据唯一；
保护性 commit。
```

建议提交：

```text
checkpoint(aold): adopt durable capture and asynchronous absorption architecture
```

---

# 9. Gate B：不可变原文 Capture

## 9.1 Capture 内容

必须无损保存：

```text
capture schema/version；
capture_id；
workspace/profile identity；
runtime session identity；
main run identity；
visible endpoint kind/time；
user role/text；
assistant role/text；
turn ordering；
content byte lengths；
content hashes；
host/plugin version；
capture created time。
```

不得保存：

```text
系统 Prompt；
工具内部隐私；
隐藏推理；
无关 transcript；
Provider secret。
```

## 9.2 原文必须完整

```text
不可只存摘要；
不可只存 MemoryStatement；
不可只存 hash；
不可静默截断；
不可在 canonical Capture 中改写文本。
```

若单轮过大：

```text
可以拆成多个有顺序的 payload 文件；
或使用正文文件 + metadata；
但必须能完整重建原始 user/assistant turn。
```

## 9.3 原子发布

推荐语义：

```text
write <capture_id>.tmp
→ flush file
→ close
→ atomic rename/publish
→ optional directory durability where supported
→ capture is visible to worker
```

Codex 可选择等价方案。

必须测试：

```text
写一半崩溃；
flush 前崩溃；
rename 前崩溃；
rename 后状态未写；
重复 Hook；
message_sent + agent_end 双观察；
同一 run 重放。
```

结果：

```text
canonical Capture 要么不存在，要么完整；
不得出现半个 JSON；
重复观察只对应一个 Capture。
```

## 9.4 Capture 延迟

正式目标：

```text
Capture hook 不调用 Provider/Python/Core；
p50 <= 25 ms；
p95 <= 100 ms；
hard validation ceiling <= 250 ms。
```

若当前 Windows 磁盘无法达到：

```text
如实报告；
优先保证完整性；
不得通过取消 flush 伪造速度；
允许任务保持 IN_PROGRESS，但继续完成其他能力。
```

## 9.5 Gate B PASS

```text
完整原文；
不可变；
原子；
幂等；
崩溃安全；
前台低延迟；
旧主回复不受影响。
```

建议提交：

```text
feat(openclaw): capture visible turns durably before background absorption
```

---

# 10. Gate C：Absorption 状态与重启恢复

## 10.1 状态必须与原文分离

状态至少能表达：

```text
PENDING；
CLAIMED/PROCESSING；
FORMATION_READY；
PLACEMENT_READY 或等价中间态；
ADMITTED；
ABSORBED_NO_MEMORY；
DEFERRED；
RETRYABLE_FAILURE；
PERMANENTLY_BLOCKED（仅真实不可恢复格式/合同问题）。
```

Codex 可减少中间状态，但必须区分：

```text
原文安全；
尚未处理；
处理中；
终态已 Admission；
终态无记忆；
可重试失败。
```

## 10.2 幂等性

```text
capture_id 是吸收幂等根；
同一 capture/batch 重放不得生成重复 Statement；
同一 Statement 重放不得重复 Atom/Handle；
Admission 完成后重启不得重新 Placement；
Provider 返回后、状态写前崩溃必须可恢复；
Access apply 后、worker terminal 写前崩溃必须可检测已完成。
```

可复用：

```text
现有 statement_id；
idempotencyKey；
HandleBinding；
Access readback；
workspace lock。
```

## 10.3 Worker

要求：

```text
每 workspace 至多一个受支持 worker；
不依赖外部服务；
启动时扫描 pending/retryable；
能识别并恢复 stale claimed work；
后台低优先级；
插件关闭时尽力停止；
Gateway restart 后自动继续；
主聊失败开放。
```

不要求抵抗恶意进程或私自改文件。

## 10.4 积压

至少记录：

```text
pending count；
oldest pending age；
processing batch；
last success；
last error；
retry count；
worker alive；
admitted count；
no-memory count。
```

这是运行诊断，不是 Audit 产品。

## 10.5 Gate C PASS

```text
Capture 后 kill/restart 仍会继续；
重复启动不重复 Admission；
worker 死亡可诊断；
原文永远保留；
无外部队列/数据库。
```

建议提交：

```text
feat(openclaw): recover asynchronous absorption from durable capture spool
```

---

# 11. Gate D：批量 Formation 与 Placement

## 11.1 批次目标

Common path：

```text
若干 Capture
→ 一次 Formation operation
→ 一次 Placement operation
→ 多条独立原子 Admission。
```

目标不是强制一个固定算法，而是消除：

```text
每个 Capture 单独 Formation；
每条 Statement 重新浏览全部 Surface；
每个页面动作新建子代理；
每条 Statement 新建完整 Placement 会话。
```

## 11.2 批次边界

Codex 自主选择：

```text
最大等待时间；
最大 Capture 数；
最大总字符；
是否按 workspace/session proximity 分组；
是否在空闲期立即触发；
是否形成 batch manifest。
```

建议初始范围：

```text
max wait 5～30 秒；
max captures 3～8；
max raw chars 8K～24K；
worker concurrency 1。
```

这些只是 Policy，可根据真实 Host 调整。

## 11.3 Formation 调用预算

Common case：

```text
每 batch 1 次 Formation；
允许 1 次受限 JSON repair/retry；
不得对每个 Capture 再调用 Formation。
```

Formation 输出必须保留：

```text
每条 Statement 对应的 source capture_id(s)；
独立 statement_id；
emit/defer；
无语义时允许整个 batch no-memory。
```

## 11.4 Placement 调用预算

Codex 应优先实现：

```text
一次 batch Placement Prompt；
为每条 Statement 返回一个 action + visible candidate；
Access 逐条验证并原子应用。
```

如现有结构使单次 batch Placement 过于危险，可以选择：

```text
同一隐藏 subagent operation/session 中处理全部 Statements；
复用同一 Surface/Locality view；
减少模型 session 初始化；
不为每条 Statement 重建全部 Surface。
```

但 Common case 必须达到：

```text
每 batch Placement provider calls <= 1；
或有充分代码证据说明暂时需要更多，
且每条 Statement 不得重复完整导航。
```

例外：

```text
每个真正 destructive revision 可增加 1 次确认；
拒绝后最多 1 次 batch 内重决策；
不得无限循环。
```

## 11.5 Admission

```text
每条 Statement 独立校验；
一条失败不得污染其他条；
批次报告明确 applied/defer/no-memory/error；
原始 Capture 只有在所有相关 Statement 进入终态后才离开 pending fallback；
部分成功必须可恢复。
```

Codex 可选择：

```text
新增 Access batch API；
或复用现有逐条 Access 原子 API。
```

选择依据是正确性和复用，不是接口数量。

## 11.6 Gate D PASS

```text
多 Capture 一次 Formation；
常见批次一次 Placement；
模型调用数量显著低于旧路径；
多 Statement 不重复全 Surface；
revision 安全不回退；
失败可恢复；
Admission 后 current state 正确。
```

建议提交：

```text
feat(aold): absorb captured turns through batched formation and placement
```

---

# 12. Gate E：Pending read-your-recent-writes

## 12.1 目的

用户刚说过的内容即使尚未完成 Formation/Placement，也必须在：

```text
新 Session；
Gateway 重启后；
后台积压期间；
Provider 暂时失败时
```

仍有机会被主代理使用。

## 12.2 输入选择

只允许固定结构条件：

```text
同一用户/agent/workspace 隔离范围；
状态尚未达到 terminal absorbed；
按 captured_at 倒序；
固定最大条数；
固定最大总字符；
固定最大年龄或显式 backlog policy。
```

禁止：

```text
query 关键词匹配；
Topic；
Source route；
实体提取；
embedding；
向量相似度；
倒排索引；
LLM 预筛选；
query→capture cache。
```

## 12.3 注入方式

优先方案：

```text
在 agent_turn_prepare 中，
将有界 Pending Capture 原文作为清晰标注的隐藏近期 Evidence，
直接提供给主代理。
```

必须：

```text
不新增隐藏 Provider 调用；
主代理自己判断是否相关；
与 admitted memory 分区标记；
不宣称其已进入几何场；
不把原始 Capture 当事实确认；
保留 user/assistant role 和时间顺序。
```

示例语义：

```text
Recent unabsorbed conversation evidence:
- This material is captured verbatim and may not yet be consolidated.
- Use only when relevant.
- It is not proof of truth and may be superseded by later turns.
```

## 12.4 预算

Codex 根据 Token 实测选择，建议：

```text
最多 4～8 个 pending Capture；
最多 2K～8K 字符；
默认年龄 10～30 分钟；
若 backlog 较老，可只注入最近窗口，但原文件仍保留。
```

不得因超预算删除 Capture。

## 12.5 Admission 后退出

当 Capture 进入：

```text
ADMITTED；
ABSORBED_NO_MEMORY；
DEFERRED_FINAL
```

或任务定义的其他终态后：

```text
不再进入 Pending fallback；
原始 Capture 仍保留/归档；
避免同时以 raw pending 和 admitted Statement 重复注入。
```

部分吸收需有明确策略，不能重复整轮长期注入。

## 12.6 Gate E PASS

真实验证：

```text
1. 普通聊天完成；
2. Capture 已落盘；
3. 暂停/阻断 worker，确保尚未 Admission；
4. 新 Session 立即询问；
5. 主代理通过 Pending Evidence 自然回答；
6. 无额外隐藏 Recall LLM；
7. 启动 worker完成 Admission；
8. 再次新 Session；
9. Pending 不再注入；
10. 正常几何 Recall 可找到对应 Statement。
```

建议提交：

```text
feat(openclaw): provide bounded read-your-recent-writes from pending captures
```

---

# 13. Gate F：低调用 Geometry Recall

## 13.1 目标

Admission 后仍然保持：

```text
一个最终几何入口；
Core Coverage/Lateral/Bridge 有界传播；
current Statement projection；
隐藏注入；
主代理自然回答。
```

但 Common path 不再：

```text
LLM 一次次翻页；
LLM 一次次下钻；
LLM 选择入口后又启动第二个 Recall Selection Agent；
为同一 query 创建多个完整 child sessions。
```

## 13.2 允许 Codex 自由选择的路线

Codex 可以选择以下任一或更优等价方案：

### 路线 A：一次隐藏 Entry Selection

```text
一次性构造预算内完整可见 Active Surface；
一次隐藏 LLM 调用选择 entry 或 NONE；
Core Recall；
把有界 Locality 直接注入主代理；
主代理作最终相关性判断。
```

### 路线 B：单一隐藏 operation

```text
一个隐藏 subagent session 内完成必要导航；
不为每个微动作创建新 session；
Core Recall 后不再调用第二个 selection agent；
最终 Locality 注入主代理。
```

### 路线 C：结构单例快速路径

```text
若候选宇宙机械唯一：
零隐藏模型调用；
直接 Core Recall；
将 Locality 注入主代理。
```

必须记录 chosen route 和理由。

## 13.3 调用预算

Common relevant Recall：

```text
隐藏 Provider calls <= 1；
主代理自身调用不计入隐藏调用。
```

机械单例：

```text
隐藏 Provider calls = 0。
```

允许异常：

```text
一次受限 invalid JSON repair；
但不得形成无限导航循环。
```

NONE：

```text
若结构上空场，允许零调用 NONE；
若需要语义判断，最多一次隐藏调用。
```

## 13.4 Locality 注入

Core Recall 后可将有限 Locality 直接交给主代理，因为：

```text
主代理本身是真实 LLM；
它可以判断最终相关性；
无需再为相同事实列表启动一个独立 Recall Selection LLM。
```

必须控制：

```text
Statement 数；
字符预算；
Evidence 引用；
传播路径摘要；
不暴露内部工具；
不把 Recall path 当事实证明。
```

## 13.5 Gate F PASS

```text
相关 Recall Common path隐藏调用<=1；
单例路径=0；
Core Recall和单入口保持；
密集 hidden-preview 事实仍可到达；
NONE不回退；
用户可见回答自然；
本地几何性能不退化；
旧多调用路径退出活动产品。
```

建议提交：

```text
feat(openclaw): collapse admitted recall to one hidden semantic operation
```

---

# 14. Gate G：配置、迁移与运行诊断

## 14.1 配置

新增或等价配置：

```text
capture_enabled；
capture_workspace/path；
capture_flush_policy；
absorption_enabled；
absorption_batch_max_captures；
absorption_batch_max_chars；
absorption_max_wait_ms；
absorption_retry_policy；
pending_fallback_enabled；
pending_fallback_max_captures；
pending_fallback_max_chars；
pending_fallback_max_age_ms；
recall_hidden_call_budget；
debug evidence path。
```

默认必须：

```text
不破坏旧工作区；
新安装启用安全默认；
旧配置缺字段可启动；
插件更新不清空 Capture；
关闭插件后原文仍在文件。
```

Codex 可减少配置数量并使用合理默认，避免配置爆炸。

## 14.2 迁移

旧 V1～V6：

```text
不回填历史 Capture；
不重新吸收历史聊天；
不改变 Statement/Handle/Core；
继续正常 Recall。
```

新工作区：

```text
启用 Capture/Absorption。
```

如需在现有工作区启用：

```text
仅新增 Capture 目录和状态；
不重写旧 Store。
```

## 14.3 诊断

`diagnose.ps1` 或等价输出：

```text
Capture enabled；
worker enabled/alive；
pending count；
oldest pending age；
processing batch；
last admitted time；
last error；
retry count；
pending fallback enabled/budget；
recent capture integrity；
plugin enabled/version；
old workspace presence。
```

不得输出完整私密原文。

## 14.4 Gate G PASS

```text
安装/更新/启用/禁用；
重启恢复；
诊断；
配置兼容；
旧数据不变；
无额外服务。
```

---

# 15. 失败与恢复矩阵

必须覆盖：

```text
Hook 重复；
用户文本缺失；
assistant message_sent 成功但 agent_end 重复；
Capture temp 写失败；
flush 失败；
atomic publish 失败；
publish 后 worker 未看到；
worker claim 后崩溃；
Formation timeout；
Formation invalid JSON；
Formation 部分 Statements；
Placement timeout；
revision confirmation timeout；
Statement 写入失败；
Core 写入失败；
Handle bind 失败；
Admission 完成后状态更新前崩溃；
Gateway restart；
插件更新；
Pending fallback 读取损坏状态；
Capture 文件完整但 sidecar 丢失；
backlog 过大；
Provider 长时间不可用。
```

结果要求：

```text
主回复不受影响；
原文不丢；
Capture 可重试；
部分 Admission 不污染；
重复运行幂等；
状态可重建；
Pending fallback 有界；
不卸载插件；
不清空工作区；
下一正常聊天继续。
```

---

# 16. 性能和调用预算

## 16.1 前台

```text
visible reply → canonical Capture publish：
p50 <= 25 ms
p95 <= 100 ms
hard validation ceiling <= 250 ms

Capture hook provider calls = 0
Capture hook Python bridge calls = 0
Capture hook Surface/Core calls = 0
```

## 16.2 Pending Recall

```text
read pending files + render hidden context：
p95 <= 100 ms
hard ceiling <= 500 ms
hidden Provider calls for pending fallback = 0
```

## 16.3 后台吸收

不设置总 Provider 秒数硬 Gate，但设置调用拓扑：

```text
common batch Formation calls <= 1
common batch Placement calls <= 1
repair/retry <= 1
destructive revision confirmation <= 1 per actual revision
worker concurrency default = 1
```

报告：

```text
captures per batch；
statements per batch；
provider calls per capture；
provider calls per admitted statement；
batch queue wait；
batch total；
admission throughput；
backlog drain rate。
```

## 16.4 Admitted Recall

```text
common hidden semantic calls <= 1
mechanical singleton hidden calls = 0
local Surface/Core target <= 2 s
```

若 Provider 单次仍很慢，如实报告；本任务不更换模型，但调用数量必须降低。

---

# 17. 自动测试矩阵

## 17.1 Capture

```text
exact user/assistant bytes；
Unicode；
换行；
超长 turn；
deterministic ID；
duplicate Hook；
temp crash；
flush failure；
publish crash；
immutable bytes；
no prompt/system content；
no model/bridge/Core call；
latency budget。
```

## 17.2 Worker

```text
startup scan；
single worker；
stale claim recovery；
restart；
retry；
idempotency；
partial success；
terminal state；
no-memory；
defer；
backlog；
shutdown。
```

## 17.3 Batch

```text
multiple Captures one Formation；
multiple Statements one Placement operation；
source capture provenance；
one invalid Statement does not corrupt others；
revision confirmation；
redecision bound；
Admission readback；
duplicate replay。
```

## 17.4 Pending fallback

```text
same scope；
cross-session；
cross-user isolation；
max count；
max chars；
max age；
no query matching；
no Provider call；
Admission removes pending injection；
no duplicate raw+Statement；
corrupt state fail-open。
```

## 17.5 Recall

```text
hidden call count；
single entry；
mechanical singleton；
dense hidden-preview；
multi-fact；
NONE；
Core path；
no second Recall selection；
main-agent injection budget；
restart。
```

## 17.6 Regression

```text
Core package；
Snapshot；
Trace；
Access；
OpenClaw Python；
OpenClaw Node；
M0；
R1/R2/R3；
P1；
semantic revision；
dense Live；
Manifest；
boundaries；
plugin check。
```

---

# 18. Windows 真实 Live

## 18.1 工作区

新建：

```text
nollm-aold-durable-capture-async-absorption-v1
```

可复制 V6 的：

```text
StatementStore；
HandleStore；
Core state；
必要配置。
```

不得复制：

```text
旧 pending state；
candidate IDs；
Traversal state；
Surface cache；
历史测试临时队列。
```

## 18.2 Live A：即时 Capture

至少 10 轮正常聊天：

```text
主代理回答自然显示；
每轮 Capture 完整；
前台 Capture 延迟；
无后台等待；
无 duplicate；
Gateway 继续响应下一轮。
```

## 18.3 Live B：Pending read-your-writes

流程：

```text
暂停 worker；
普通聊天产生一条明确事实；
确认 Capture durable、未 Admission；
新 Session 立即询问；
主代理从 Pending Evidence 回答；
无隐藏 Recall Provider call；
重启 Gateway；
再次新 Session询问仍可用。
```

## 18.4 Live C：后台批量吸收

```text
积累至少 3～5 个 pending Capture；
启动 worker；
形成至少一个 multi-Capture batch；
Formation/Placement 调用数符合预算；
Statements/Handles/Atoms正确；
重启后保持；
pending count下降；
原始 Capture仍存在。
```

## 18.5 Live D：Admission 交接

```text
同一事实 Admission 前：
由 Pending fallback 使用。

Admission 后：
Pending fallback 不再包含；
通过几何单入口 Recall 使用；
不得重复注入两份。
```

## 18.6 Live E：低调用 Recall

至少：

```text
3 relevant warm；
1 relevant cold；
2 dense hidden-preview；
2 NONE；
1 mechanical singleton；
1 multi-fact answer。
```

记录：

```text
hidden provider call count；
local timing；
query→injection；
query→visible；
selected entry；
Core paths；
pending/admitted来源。
```

## 18.7 Live F：崩溃恢复

在受控测试工作区：

```text
Capture publish 后停止 Gateway；
worker claim 后停止；
Formation 完成后停止；
Admission 完成、terminal state 前停止。
```

重启验证：

```text
原文存在；
没有重复 Statement/Atom/Handle；
worker继续；
最终进入正确终态。
```

---

# 19. 内部 Gate 与提交

## Gate 0：活动任务纠偏

```text
撤回纯串行慢链测量作为主任务；
更新 AGENTS/ACTIVE_PROJECT/STATUS/Ledger；
记录 ca50a97 为旧调用拓扑基线；
commit。
```

## Gate A：Owner 和架构修订

```text
资产盘点；
唯一 Capture owner；
V3.10 amendment；
charters；
范围重算；
commit。
```

## Gate B：即时 Capture

```text
原文、原子、幂等、延迟、崩溃测试；
commit。
```

## Gate C：可恢复 worker

```text
状态机、claim/recovery、诊断；
commit。
```

## Gate D：批量吸收

```text
Formation/Placement 调用压缩；
幂等 Admission；
commit。
```

## Gate E：Pending read-your-writes

```text
跨 Session；
零额外 Provider；
Admission交接；
commit。
```

## Gate F：低调用 admitted Recall

```text
最多一次隐藏语义调用；
无第二 selection Agent；
single-entry；
commit。
```

## Gate G：Windows Live

```text
Capture；
Pending；
batch；
handoff；
Recall；
crash/restart；
commit。
```

## Gate H：状态与交付

```text
主报告；
实际推进向量；
完成度；
Evidence Freeze；
Manifest；
clean tree；
Bundle。
```

普通失败就地修复并继续。不要为每个 Gate 新建外部任务书。

---

# 20. Evidence 与报告

## 20.1 主 Evidence

建议：

```text
validation/aold_durable_capture_async_absorption_20260717.jsonl
validation/aold_durable_capture_async_absorption_summary_20260717.json
```

记录：

```text
Capture latency；
capture hashes；
worker state transitions；
batch IDs；
provider calls；
Admission results；
Pending fallback；
Recall call counts；
crash/restart；
workspace hashes；
plugin state。
```

默认不重复保存完整原文；Capture 文件本身是原文证据，Evidence 只引用 capture_id/hash。

## 20.2 主报告

只新增一个：

```text
docs/project/AOLD_DURABLE_CAPTURE_ASYNC_ABSORPTION_REPORT.md
```

必须直接回答：

```text
可见回复后多久原文安全落盘；
原文是否在崩溃后仍存在；
新 Session 在尚未 Admission 时多久能使用；
后台一批调用几次模型；
Capture 到 Admission 通常多久；
Admission 后是否只走几何；
相关 Recall 还需几次隐藏模型调用；
前台用户等待是否已与吸收解耦；
积压和恢复如何；
旧数据是否保留。
```

## 20.3 Freeze

```text
停止 Live 写入；
冻结 Evidence；
计算 line/bytes/SHA；
生成 Summary/Report；
加入 Manifest；
Manifest --check；
从 Git blob 复算；
commit；
Bundle。
```

---

# 21. 最终 Gate

必须满足：

```text
原文 Capture p95 <= 100 ms，或如实记录环境阻断；
Capture 路径 0 Provider / 0 bridge / 0 Core；
Capture immutable and crash-safe；
worker restart recovery；
no duplicate Admission；
batch Formation common <=1 call；
batch Placement common <=1 call或有严格说明；
Pending fallback 0额外 Provider；
Pending 跨 Session可用；
Admission 后 Pending退出；
admitted Recall common hidden calls <=1；
single-entry不回退；
Core无修改或仅测试回归；
无 graph/vector/embedding；
无 Topic/Source/query index；
无外部消息队列/数据库；
旧工作区保留；
插件安装启用；
Manifest完整；
工作树clean；
完整历史Bundle验证。
```

---

# 22. 完成状态

全部核心能力通过时：

```text
DURABLE_CAPTURE_ASYNC_ABSORPTION_READ_YOUR_WRITES_FAST_RECALL_VALIDATED_AT_<HEAD>
```

如果 Provider、Host Hook 或真实 Live 阻断任一关键能力：

```text
AOLD_DURABLE_CAPTURE_ASYNC_ABSORPTION_IN_PROGRESS_AT_<HEAD>
```

即使 IN_PROGRESS，也必须：

```text
所有修改commit；
工作树clean；
原始Capture保全；
旧数据保留；
完整历史Bundle；
如实报告。
```

不得用 fixture 冒充 Provider-backed Live。

---

# 23. 明确非目标

```text
多物理层语义 Placement；
Stitch/Unstitch；
Bridge endpoint重构；
多 Chart；
PB压测；
正式发布；
产品级消息队列；
数据库；
常驻调度服务；
ACL/权限系统；
Audit平台；
History产品；
语义索引；
embedding；
vector/graph；
生产 Decimal polygon；
删除旧 Capture/Evidence；
强制模型第一轮永远正确。
```

---

# 24. 建议测试命令

PowerShell：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-trace/src",
  "$PWD/packages/nollm-access/src",
  "$PWD/integrations/openclaw/formation-loop/python",
  "$PWD/reference/python"
) -join ";"

python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests
python -m pytest -q packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests
python -m pytest -q integrations/openclaw/formation-loop/tests
python -m pytest -q reference/python/tests/m0
python -m pytest -q lab/nollm-lab/tests

# 实际脚本名称由 Codex 按仓库风格决定
python lab/nollm-lab/absorption/run_capture_atomicity_validation.py
python lab/nollm-lab/absorption/run_absorption_recovery_validation.py
python lab/nollm-lab/absorption/run_batch_call_budget_validation.py
python lab/nollm-lab/absorption/run_pending_read_your_writes_validation.py
python lab/nollm-lab/absorption/run_low_call_recall_validation.py
python lab/nollm-lab/absorption/run_absorption_live_summary.py

Push-Location integrations/openclaw/formation-loop
npm test
npm run plugin:check
Pop-Location

python tools/generate_module_ownership_manifest.py
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py

git diff --check
git status --short
```

脚本名称可调整，验收职责不得删除。

---

# 25. Git 与 Bundle

建议提交序列：

```text
checkpoint(aold): adopt durable capture async absorption architecture
feat(openclaw): publish immutable visible-turn captures
feat(openclaw): recover absorption work from durable spool
feat(aold): batch formation placement and admission
feat(openclaw): inject bounded recent pending evidence
feat(openclaw): collapse admitted recall provider calls
test(aold): validate capture recovery batching and read-your-writes
docs(aold): record async absorption live capability
```

最终 Bundle：

```text
nollm_aold_durable_capture_async_absorption_20260717_<shorthead>.bundle
```

仓库外：

```powershell
git bundle create ..\nollm_aold_durable_capture_async_absorption_20260717_<shorthead>.bundle --all
git bundle verify ..\nollm_aold_durable_capture_async_absorption_20260717_<shorthead>.bundle
Get-FileHash ..\nollm_aold_durable_capture_async_absorption_20260717_<shorthead>.bundle -Algorithm SHA256
```

---

# 26. 最终回复要求

只需清楚报告：

```text
Capture：
  回答显示→原文落盘 p50/p95/max；
  Provider/bridge/Core calls；
  崩溃恢复。

Pending read-your-writes：
  Admission前跨Session是否可用；
  本地准备时间；
  额外Provider calls。

Absorption：
  batch数量；
  captures/statements；
  Formation/Placement calls；
  Capture→Admission；
  retry/backlog；
  重启恢复。

Admitted Recall：
  hidden calls；
  local time；
  query→injection；
  query→visible；
  dense/NONE。

数据：
  old workspace保留；
  Capture原文保留；
  duplicate/orphan数量。

交付：
  branch/HEAD/tests；
  实际向量；
  模块完成度；
  Bundle/SHA。
```

不得声称：

```text
所有Provider都一样快；
永久实时；
PB规模；
正式发布；
长期零故障。
```

---

# 27. 最终任务概括

```text
主代理回答完成后，
先用本地文件把原始经历可靠留下，
而不是等待多个隐藏模型把它整理完。

后台可以慢，
但必须可恢复、可批量、不会重复、不会污染。

后台尚未完成时，
最近原文通过有界 Pending Evidence 让新会话立即读到；
不建立第二套检索系统。

后台完成后，
MemoryStatement 和几何场接管；
Pending 原文退出活动注入，但继续作为 Evidence 保留。

写入模型调用按批次压缩，
召回隐藏模型调用压缩到最多一次，
Core 几何不回退。
```

> **这次不再继续测量旧慢链路，而是一次完成“原文立即不丢、后台慢慢吸收、未吸收也能马上记起、吸收后由几何接管”的完整工作流。**
