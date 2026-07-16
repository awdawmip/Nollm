# Nollm AOLD：真实对话记忆提交与召回端到端延迟基线任务书

**任务文件名**：`NOLLM_A_O_L_D_REAL_MEMORY_COMMIT_AND_RECALL_LATENCY_BASELINE_TASK_20260716.md`
**日期**：2026-07-16
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**任务性质**：真实运行测量、时间语义纠正和瓶颈定位；不新增记忆能力，不修改几何路线
**核心问题**：

```text
1. 一轮正常对话在主代理回答已经显示后，
   经过多久才成为可持久、可重开、可召回的 Nollm 记忆？

2. 后续新会话提出相关问题后，
   经过多久 Nollm 完成几何召回并准备好隐藏注入？

3. 从相关问题出现到用户最终看到包含该记忆的回答，
   总共需要多久？

4. 时间主要消耗在本地 Surface/Core/文件操作，
   还是消耗在真实 LLM Formation、Placement、Recall 和主代理调用？
```

**输入 Bundle**：`nollm_aold_semantic_revision_integrity_dense_live_20260716_26bd0ae.bundle`
**输入 Bundle SHA-256**：`6ea6998752c50bdda6057b2dba2d1cc8ed9e6c4e76c193a75f1d4e3a15ae8298`
**输入分支**：`codex/aold-semantic-revision-integrity-dense-live-closure`
**输入 HEAD**：`26bd0ae68470ef8d1396014884e305cc1c3ab7ef`
**输入 Tag**：`AOLD_SEMANTIC_REVISION_DENSE_LIVE_IN_PROGRESS_AT_26bd0ae68470ef8d1396014884e305cc1c3ab7ef`
**建议工作分支**：`codex/aold-real-memory-commit-recall-latency-baseline`
**主执行环境**：Windows 10/11、PowerShell、Node 24、当前真实 OpenClaw / LongCat-2.0 环境
**交付方式**：所有真实进展 commit；工作树 clean；仓库外生成并验证单一完整历史 Git Bundle
**插件最终状态**：保持安装和启用
**数据最终状态**：旧工作区全部保留；新建独立延迟测量工作区，不覆盖 V1～V6
**能力结论边界**：只形成真实延迟基线和瓶颈分类；不宣称完成性能优化、长期吞吐、PB 规模、多物理层 Placement、Stitch 或正式发布

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +10% | DISTRIBUTIONS +5%

主方向：
不新增记忆功能；
纠正现有 timing 字段含义；
建立从可见对话到 durable memory、
从查询到 hidden injection、
从查询到 visible answer 的真实端到端时间线；
区分 Provider 时间、本地几何时间、持久化时间和排队时间。

范围变化：
无架构范围变化；
当前 Placement Policy 继续保持 layer 0；
V3.9 快速有界近似 Coverage 和 Lazy Surface 保持工作基线；
不启动换层、Stitch、多入口、精确 polygon、PB 长跑或新的治理系统。
```

## 0.1 Gate 向量复述

每个内部 Gate 开始记录：

```text
当前预计向量：
C 0 | S 0 | T 0 | A +5 | H 0 | U 0 | O +10 | L +10 | D +5

当前主方向：
时间语义纠正
→ 真实写入时间线
→ 真实召回时间线
→ 冷热与密集场对比
→ 瓶颈分类
→ 只基于数据决定下一任务。
```

每个 Gate 结束记录：

```text
实际偏差；
新增受影响模块；
是否修改了记忆行为；
测量本身增加的开销；
是否发现新的真实阻断；
是否需要更新任务范围和推进向量。
```

不得静默扩张到 Core 算法重构、Trace 产品、History/Audit、Stitch、多物理层 Placement 或 Provider 更换。

---

# 1. 为什么当前必须先测量

## 1.1 当前已经具备真实链路

`26bd0ae` 已经证明：

```text
普通聊天；
真实 Dream Formation；
真实 Surface Placement；
Statement / Handle / Core 原子写入；
Gateway 重启；
新 Session 单入口 Recall；
隐藏注入；
密集 Cell；
Surface preview 截断后仍能召回未预览事实；
错误 destructive revision 未确认不写入；
无 Cursor、无语义索引、无 multi-entry Recall。
```

当前最需要回答的已不是“还能增加什么结构”，而是：

```text
它实际工作一次要多久；
慢在哪里；
延迟是否主要来自 Nollm 本地几何，
还是来自真实模型调用；
用户能否接受后台记忆和前台召回的等待。
```

## 1.2 当前已有 timing 不能直接回答用户问题

现有代码已经记录部分字段：

```text
surface_build_ms；
recall_core_ms；
placement_subagent_ms；
statement_persist_ms；
handle_bind_ms；
total_operation_ms；
dream_latency_ms；
formation_ms。
```

但存在以下语义问题：

```text
1. formation_ms 在每条 Statement Placement 中重复携带，
   且使用“从 Formation 开始到当前 Statement 开始 Placement”的累计时间；
   多 Statement 时后面的 formation_ms 可达到数分钟，
   不能解释为一次 Formation 模型调用耗时。

2. placement total_operation_ms 从 Placement 开始，
   不包含 message_sent 后的后台排队和 Formation。

3. recall total_operation_ms 到 hidden injection ready 为止，
   尚未与该主代理 run 的最终 message_sent 做关联，
   因此不能回答“用户多久看到答案”。

4. Node Date.now()、Python perf_counter_ns() 和 Provider 运行时间
   尚未形成一条统一的 correlation timeline。

5. 当前报告往往摘取单次成功值，
   没有统一区分：
   冷启动 / 热运行；
   新事实 / reuse / revision / defer；
   稀疏 / 密集 Locality；
   relevant / hidden-preview / NONE；
   first durable / all durable。
```

本任务必须先修正时间定义，再运行真实测试。不能把旧字段简单相加后给出结论。

## 1.3 当前历史样本只作方向提示

`26bd0ae` 冻结 Evidence 中可见：

```text
Surface build：
约 0.33～0.49 秒；

Core Recall：
约 0.096～0.128 秒；

Recall Agent / Traversal LLM：
约 20～90 秒；

Recall total_operation：
约 25～91 秒；

Placement 本地文件与 Core/Handle：
通常约数毫秒至数十毫秒；

Placement 模型调用：
通常约 45～112 秒；

现有 formation_ms：
19 秒至数百秒不等，
但含累计排队/串行 Placement 偏移，语义不正确。
```

这些值提示 Provider 调用可能占主导，但不能替代本任务的正式测量。

---

# 2. 活动依据和优先级

开始执行前必须按顺序读取：

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

冲突处理：

```text
最高原则
> Core 纯净模块边界
> 真实 LLM 语义所有权
> V3.9 快速结构几何
> 当前状态
> 本任务测量变化量
> 历史任务和报告。
```

禁止恢复：

```text
Cursor；
cluster anchor；
Topic/Source/Entity route；
graph/vector/embedding；
Python 语义 Placement；
multi-entry Recall；
生产 Decimal/polygon；
多物理层语义 Placement；
Stitch；
新的安全/审计系统。
```

---

# 3. 根目录 `AGENTS.md` 更新要求

Gate 0 必须更新并遵守根目录 `AGENTS.md`，至少加入：

```text
- The active task measures the existing layer-0 memory loop; it does not add new memory architecture.
- "Conversation becomes remembered" means Statement + current HandleBinding + Core Atom are durably committed and readable after reopen.
- Formation output alone is not remembered memory.
- "Recall ready" means the hidden injection payload is ready for the main agent.
- "Visible recall latency" ends when the correlated main-agent message_sent event is observed.
- Use monotonic clocks for durations inside one process.
- Use epoch timestamps only for cross-process/cross-hook correlation; never subtract unrelated monotonic clocks.
- Existing formation_ms is semantically cumulative and must not be used as pure Formation provider latency.
- Separate queue wait, prompt build, provider wait, parsing, Surface, Core, persistence, confirmation, and main-agent time.
- Do not optimize the system in the same task unless a measurement defect itself blocks truthful timing.
- Do not add a Trace product, telemetry service, database, daemon, persistent correlation index, or hidden-reasoning storage.
- Timing evidence must contain hashes/IDs and durations, not full conversations unless already required by the existing Live evidence contract.
- Measurement overhead must be quantified and disabled by default outside debug validation mode.
- Report warm, cold, dense, hidden-preview, NONE, multi-Statement, reuse, revision, defer and failure samples separately.
- No latency threshold may be promoted to a permanent architecture invariant from one Provider or one workstation.
```

不得把本任务全文复制进 `AGENTS.md`。

---

# 4. 任务开始前模块完成度

本任务按“真实运行可观测性”重新评估，不否定已有功能：

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 当前主要缺口 | 本任务是否影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 95% | 高 | 快速 Coverage、Lazy Surface、原子状态、有界 Recall | 本任务只读取既有 timing/结果，不改算法 | 否 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes 回归 | 增量与版本化 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 独立事件合同 | 本任务不扩展 Trace 产品 | 否 |
| ACCESS | `IMPLEMENTED` | 90% | 高 | Statement/Handle/Core 原子协调、operation timing | durable endpoint 和多 Statement 时间语义未形成统一合同 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 85% | 中高 | Formation、Placement、Recall、隐藏注入、部分 timing | 缺 visible-turn→durable 和 query→visible answer 全链关联 | 是 |
| LAB | `IMPLEMENTED` | 85% | 高 | 多类 deterministic/live runner | 缺统一 latency schema、统计和瓶颈分类 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 85% | 高 | plugin schema、debug evidence | 缺 latency validation profile 与默认关闭规则 | 是 |

这些数字只表示当前任务涉及的可运行、可测量成熟度，不是永久完成度。

---

# 5. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 95% | 95% | 0% | 不改算法，只回归 | package tests、Core stage timing | 多层、Stitch、长期规模 |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | package 回归 | 增量 Snapshot |
| TRACE | 40% | 40% | 0% | 不增加 Trace 产品 | 边界检查 | 长期 metrics |
| ACCESS | 90% | 95% | +5% | durable commit endpoint、分段 timing 语义 | 单元、重开、Live | 性能优化尚未执行 |
| HISTORY | 10% | 10% | 0% | 无变化 | 章程回归 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 章程回归 | 暂停 |
| OPENCLAW | 85% | 95% | +10% | 跨 hook/run correlation、写入和召回完整时间线 | Windows Live JSONL | Provider/机器差异 |
| LAB | 85% | 95% | +10% | 聚合分析、冷热/密集矩阵、瓶颈报告 | analyzer、结构化报告 | 长期样本仍有限 |
| DISTRIBUTIONS | 85% | 90% | +5% | debug-only latency profile、Schema/version | plugin check | 正式发行 |

本任务目标不是降低延迟，因此不存在“达到某秒数才能通过”的硬性能 Gate。

---

# 6. 测量对象的正式定义

## 6.1 “对话出现”的起点

当前 Nollm Formation 在主代理回答完成后，由：

```text
message_sent
```

触发后台 Dream。

因此本任务的正式起点为：

```text
T0_TURN_VISIBLE：
OpenClaw message_sent hook 被观察到的 epoch timestamp。
```

它代表：

```text
本轮主代理回答已经发送、用户可以看到该轮对话完成。
```

不得把它描述为：

```text
用户刚发送输入的时刻；
主代理开始推理的时刻。
```

若 OpenClaw 现有 API 可可靠提供 user-message-received 时间，可作为额外观察字段记录，但不能替代 `T0_TURN_VISIBLE`，也不能为取得该字段修改 OpenClaw 主产品。

## 6.2 “已经记住”的终点

只有同时满足以下条件，才称为 `DURABLY_REMEMBERED`：

```text
1. MemoryStatement 文件已经持久化；
2. current HandleBinding 已经持久化；
3. Core MemoryAtom 已经原子写入；
4. Handle 指向的 Atom 可读取；
5. Statement、Handle、Atom 三者身份一致；
6. Access/Core 关闭并重开后仍可读取；
7. 本次不是 defer、NONE、pending 或 provisional revision；
8. 没有孤立 Statement、孤立 Binding 或部分 Core 写入。
```

Formation 成功、Statement 仅在模型输出中出现、Placement decision 已产生，都不等于已经记住。

正式终点：

```text
T_DURABLE_COMMIT：
最终 Statement + Handle + Core 写入完成并通过立即 read-back 的时间。

T_DURABLE_REOPEN_VERIFIED：
在本批次预定 reopen 验证中确认仍可读取的时间。
```

主要用户指标使用：

```text
turn_to_durable_commit_ms =
T_DURABLE_COMMIT - T0_TURN_VISIBLE
```

重开验证单独报告，不把人为等待重启的时间混入每条写入延迟。

## 6.3 一轮形成多条 Statement 时

一轮对话可能形成 0～N 条 Statement。

必须分别报告：

```text
turn_to_first_durable_ms：
本轮第一条成功 current memory 的 durable commit 时间；

turn_to_all_durable_ms：
本轮所有被接受 Statement 完成 durable commit 的时间；

statement_placement_latency_ms：
每条 Statement 自己进入 Placement 到 durable commit 的时间；

statement_start_offset_ms：
该 Statement Placement 开始相对 T0 的偏移。
```

不得把最后一条 Statement 的 `statement_start_offset_ms` 误记为 Formation 模型耗时。

若本轮全部 defer 或没有形成 Statement：

```text
turn_to_terminal_no_memory_ms
```

并记录 terminal reason。

## 6.4 “记起来”的内部终点

相关问题进入主代理前，Nollm 在：

```text
agent_turn_prepare
```

执行 Recall。

正式起点：

```text
Q0_QUERY_PREPARE：
agent_turn_prepare hook observed timestamp。
```

内部召回完成：

```text
Q_INJECTION_READY：
Surface Traversal、physical entry、Core Recall、Recall Agent 选择和 injection render 完成，
隐藏注入已准备返回主代理的时间。
```

主要内部指标：

```text
query_to_injection_ready_ms =
Q_INJECTION_READY - Q0_QUERY_PREPARE
```

对于 NONE：

```text
query_to_recall_terminal_ms
```

终点是系统确定不注入的时间。

## 6.5 “用户看到记忆回答”的终点

通过同一个主代理 `run_id/session_key` 关联：

```text
Q_VISIBLE_ANSWER：
该主代理 run 的 message_sent hook observed timestamp。
```

主要用户可见指标：

```text
query_to_visible_answer_ms =
Q_VISIBLE_ANSWER - Q0_QUERY_PREPARE

injection_ready_to_visible_answer_ms =
Q_VISIBLE_ANSWER - Q_INJECTION_READY
```

这样必须区分：

```text
Nollm Recall 时间；
主代理在拿到隐藏记忆后的回答时间。
```

如果无法可靠关联同一个 run，不得猜测，应标记：

```text
visible_answer_correlation_unavailable
```

---

# 7. 时钟与时间语义合同

## 7.1 单进程 duration

Node 内部使用：

```text
process.hrtime.bigint()
或 performance.now()
```

Python 内部使用：

```text
perf_counter_ns()
```

记录纳秒原值或转换后的整数微秒/毫秒。

禁止使用 `Date.now()` 测量极短本地步骤。

## 7.2 跨进程 / 跨 hook correlation

使用：

```text
epoch_ms；
session_key hash；
run_id；
turn_correlation_id；
request_id；
statement_id；
placement_request_id；
recall_request_id。
```

跨进程只使用同一 Windows 主机的 epoch timestamp。

不得：

```text
相减 Node monotonic 与 Python monotonic；
相减不同主机时钟；
用文件 mtime 代替事件时间；
用日志行顺序冒充真实时间。
```

## 7.3 时钟健康检查

Live 开始前记录：

```text
Node epoch_ms；
Python epoch_ms；
二者采样差值；
Windows system time source；
是否发生系统睡眠或时钟调整。
```

若 Node/Python wall-clock 差值：

```text
> 100 ms：
报告 warning；

> 1000 ms：
跨进程端到端数据标记 invalid，
但各进程 monotonic stage timing 仍可保留。
```

不得自动修改系统时间。

---

# 8. Correlation Identity

## 8.1 Turn correlation

每轮普通聊天生成：

```text
turn_correlation_id =
sha256(session_key + run_id + visible_assistant_message_hash)
```

只记录 hash，不需要在 latency evidence 中重复完整消息。

## 8.2 Formation correlation

```text
formation_request_id；
formation_run_id；
turn_correlation_id；
material_id；
statement_ids[]。
```

## 8.3 Placement correlation

每条 Statement：

```text
placement_request_id；
turn_correlation_id；
statement_id；
statement_index；
statement_count；
selected_entry；
final_action；
final_outcome。
```

## 8.4 Recall correlation

```text
recall_request_id；
session_key hash；
main_run_id；
query_hash；
entry_cell；
selected_statement_ids；
injection_hash；
visible_answer_hash。
```

不得创建持久的：

```text
query→cell；
session→entry；
turn→semantic route。
```

这些 ID 只用于 debug validation JSONL 和当前报告。

---

# 9. 写入时间线 Schema

建议新增 Schema：

```text
nollm_memory_commit_latency_v1
```

每轮至少记录以下事件。

## 9.1 Hook 与排队

```text
turn_visible_epoch_ms；
hook_handler_returned_epoch_ms；
hook_handler_duration_us；
background_started_epoch_ms；
background_queue_wait_ms。
```

## 9.2 Formation

```text
formation_prompt_build_us；
formation_provider_ms；
formation_parse_us；
formation_format_repair_ms；
formation_full_retry_ms；
formation_model_call_count；
formation_statement_count；
formation_terminal_status。
```

必须删除或弃用当前含义模糊的：

```text
formation_ms
```

允许保留兼容字段，但必须：

```text
deprecated=true；
不得用于正式统计。
```

正式字段：

```text
formation_provider_total_ms；
formation_local_total_ms；
turn_to_formation_complete_ms。
```

## 9.3 每条 Statement Placement

```text
statement_index；
statement_start_offset_ms；
surface_build_ms；
surface_order_count；
surface_projection_count；
surface_page_count；
placement_traversal_provider_ms；
placement_decision_provider_ms；
placement_json_repair_ms；
revision_confirmation_ms；
revision_redecision_ms；
physical_entry_resolution_ms；
decision_validation_us；
statement_persist_us；
core_apply_us；
handle_bind_us；
durable_readback_us；
placement_provider_total_ms；
placement_local_total_ms；
statement_to_durable_ms；
turn_to_statement_durable_ms；
final_action；
final_outcome；
terminal_reason；
model_call_count。
```

当前 Access 已记录：

```text
decision_validation_ms；
statement_persist_ms；
placement_apply_ms；
handle_bind_ms。
```

应明确拆分：

```text
Core mutation 与 Handle bind；
placement_apply_ms 不得既包含 bridge/process 启动又被解释为 Core 写入。
```

若不修改 Access 公共返回结构即可获得这些字段，优先在 OpenClaw bridge 外层记录；只有无法区分时才做最小 Access timing 增补。

## 9.4 Turn 聚合

```text
turn_to_first_durable_ms；
turn_to_all_durable_ms；
accepted_statement_count；
deferred_statement_count；
reuse_count；
new_local_count；
revision_count；
terminal_no_memory；
total_provider_ms；
total_local_ms；
provider_share；
local_share。
```

---

# 10. Recall 时间线 Schema

建议新增：

```text
nollm_memory_recall_latency_v1
```

## 10.1 Recall 内部

```text
query_prepare_epoch_ms；
surface_build_ms；
surface_order_count；
surface_projection_count；
surface_page_count；
surface_traversal_provider_ms；
traversal_correction_ms；
physical_entry_resolution_ms；
physical_entry_model_call_skipped；
core_recall_ms；
recall_selection_provider_ms；
injection_render_us；
query_to_injection_ready_ms；
model_call_count；
selected_statement_count；
recall_outcome；
timeout_stage；
provider_timeout_stage。
```

当前 `recall_agent_ms` 同时累计：

```text
Surface Traversal 模型；
纠错模型；
最终 Recall selection 模型。
```

必须拆分，不能继续只报告一个总和。

## 10.2 用户可见链路

```text
main_run_id；
injection_ready_epoch_ms；
main_message_sent_epoch_ms；
query_to_visible_answer_ms；
injection_to_visible_answer_ms；
visible_answer_correlated；
visible_answer_hash；
visible_message_count。
```

## 10.3 NONE

NONE 必须独立统计：

```text
query_to_none_terminal_ms；
Surface/model 调用数；
是否进入 Core Recall；
是否产生隐藏注入；
main visible answer latency。
```

不能把 NONE 与 relevant Recall 混合计算一个 p50。

---

# 11. 测量本身的开销限制

本任务不是建设产品级 Trace。

## 11.1 默认关闭

新增配置：

```text
latency_validation_enabled = false
```

只有验证 Profile 显式启用时记录完整 latency JSONL。

正常生产仍保留现有必要 timing，但不写高频额外事件。

## 11.2 内容最小化

Latency JSONL 默认只记录：

```text
hash；
ID；
计数；
状态；
时间；
地址；
Statement ID；
模型/provider；
错误阶段。
```

不重复记录：

```text
完整聊天；
完整 Prompt；
隐藏推理；
完整模型输出；
用户私密文本。
```

如需判断场景，只使用预先定义的：

```text
scenario_id
```

## 11.3 开销测量

使用确定性本地 fixture 对比：

```text
latency_validation_enabled=false
latency_validation_enabled=true
```

至少 100 次本地 bridge/Access 调用。

要求：

```text
本地非 Provider 路径额外开销 p95 <= 5%；
或绝对增加 <= 5 ms，取较宽松者。
```

若超过：

```text
简化事件数量；
批量写 JSONL；
禁止引入数据库、线程服务或长期 daemon。
```

---

# 12. 真实 Windows/OpenClaw 测量设计

## 12.1 工作区

新建：

```text
nollm-aold-memory-latency-v1
```

从 V6 复制：

```text
StatementStore；
HandleStore；
Core canonical state；
当前插件必要配置。
```

不得复制：

```text
Surface cache；
Traversal state；
candidate IDs；
session entry hints；
测试中间临时文件。
```

旧 V1～V6 全部保留。

## 12.2 插件配置

```text
enabled = true；
write_mode = statement-store；
latency_validation_enabled = true；
debug_trace = true；
独立 evidence_path；
persist_subagent_transcripts = false；
模型继续继承当前真实 Host；
不更换 Provider。
```

## 12.3 测量前预热

进行：

```text
一次 Gateway restart；
一次健康探测；
一次不计入正式样本的普通 relevant Recall；
一次不计入正式样本的普通聊天 Formation。
```

预热样本单独保留，不进入 warm 分布。

---

# 13. 写入延迟 Live Matrix

## 13.1 样本数量

最低：

```text
12 个完成的普通聊天 turn；
至少 8 个 turn 产生 durable current memory；
至少 1 个 turn 形成多条 Statement；
至少 1 个 reuse；
至少 1 个真实 same-fact revision；
至少 1 个 defer/no-memory；
至少 1 个 Gateway restart 后的 cold turn。
```

目标：

```text
20 个普通聊天 turn；
至少 15 个 durable-memory turn。
```

如果 Provider 或运行窗口不足：

```text
达到最低样本即可交付；
不足最低样本时交付 IN_PROGRESS；
不得复制同一 receipt 充数。
```

## 13.2 对话形式

必须是自然聊天，不得在用户可见消息中使用：

```text
“请写入记忆”；
“请调用 Nollm”；
“把这条放在某 Cell”；
“返回 JSON”；
“选择 new_local”；
任意 command-like Placement 测试。
```

允许自然地讨论：

```text
项目安排；
联系人；
时间；
地点；
设备细节；
后续真实更正；
明显重复确认；
短暂闲聊或无长期价值内容。
```

## 13.3 写入场景标签

场景只在验证 runner 中预先标记：

```text
W_NEW_SINGLE：
预期形成一条独立 current fact；

W_NEW_MULTI：
同一轮自然形成多条独立 Statement；

W_REUSE：
自然重复现有 current fact；

W_REVISION_TRUE：
同一主体、同一槽位、明确新值替代旧值；

W_ADDITIVE：
同一主体新增另一个独立事实，不应 destructive revision；

W_NO_MEMORY：
普通闲聊或短期内容，允许不形成/不写入；

W_COLD_AFTER_RESTART：
Gateway restart 后第一条 memory turn；

W_DENSE_LOCALITY：
进入已有 8+ current facts 的 Locality。
```

场景标签是分析标签，不强制模型动作。模型与系统最终行为如实记录。

## 13.4 每条 durable memory 验证

立即验证：

```text
Statement exists；
Handle current binding exists；
Core Atom exists；
Handle address matches Atom；
content hash matches；
no orphan；
workspace state changes exactly as reported。
```

每 4 个 turn 或每次 Gateway restart 后：

```text
关闭并重开 Access/Core；
批量验证全部本任务 durable memories。
```

---

# 14. Recall 延迟 Live Matrix

## 14.1 样本数量

最低：

```text
12 个新 Session recall query；
其中：
4 relevant warm；
2 relevant cold-after-restart；
2 hidden-preview dense；
2 NONE；
2 repeated-topic but independent new Session。
```

目标：

```text
20 个 recall query。
```

## 14.2 Relevant Warm

要求：

```text
Gateway 已运行；
Surface cache 为正常 operation-local 状态；
新 Session；
一个最终 entry；
选择至少一条 current Statement；
生成 hidden injection；
主代理自然回答。
```

## 14.3 Cold After Restart

至少两次：

```text
Gateway restart；
健康探测；
立即发起 relevant query；
记录 restart 完成到 query 的间隔；
禁止预先运行相关 Surface/Recall。
```

## 14.4 Hidden-preview Dense

至少两次：

```text
目标事实不在当前 Surface 首屏最多 3 条预览中；
truncated=true；
通过一个入口和几何 Locality 找到；
不得预先把目标文本塞入 query route；
不得多入口扇出。
```

## 14.5 NONE

至少两次无关问题：

```text
Recall terminal NONE；
无隐藏 MemoryStatement 注入；
主代理正常回答；
记录 Nollm terminal 时间和用户 visible answer 时间。
```

## 14.6 多事实回答

至少一次 relevant query：

```text
从一个入口召回 3 条 current facts；
其中至少 1 条不在 Surface 首屏预览；
记录 selected_statement_count；
记录 query_to_injection 和 visible answer。
```

---

# 15. Cold / Warm 定义

## 15.1 Cold

```text
Gateway 刚重启；
Python bridge 进程未预热；
Core/Statement/Handle 首次打开；
Surface derived cache 为空；
本任务首次 Provider call 可单独标 provider_cold。
```

不得把：

```text
Windows 整机启动；
Provider 网络异常；
人为等待；
CLI restart timeout 后的未知状态
```

混成同一个 cold 指标。

## 15.2 Warm

```text
Gateway 健康；
至少完成一个同类型 operation；
不使用持久 query/entry cache；
仍从 canonical state 重新执行正常链路。
```

## 15.3 报告

分别给出：

```text
cold n / p50 / max；
warm n / p50 / p90 / p95 / max；
cold-warm delta。
```

样本不足时，不计算伪精确 p95。

---

# 16. 统计规则

## 16.1 必须报告单样本

原始 JSONL 中保留每个正式样本。

报告中至少列出：

```text
scenario_id；
turn/query ID；
outcome；
model calls；
turn_to_first_durable；
turn_to_all_durable；
query_to_injection；
query_to_visible；
provider total；
local total；
timeout/correction/retry。
```

## 16.2 分位数

```text
n < 5：
只列单样本、median、min、max；

5 <= n < 20：
列 p50、p90、max；
p95 标记 not statistically meaningful；

n >= 20：
列 p50、p90、p95、max。
```

不得用插值产生看似精确到毫秒的结论；报告可四舍五入到：

```text
0.1 秒
```

用户关注端到端体验，本地微步骤可保留毫秒。

## 16.3 成功率

分别报告：

```text
Formation terminal success；
durable memory rate；
Placement defer rate；
Provider timeout rate；
invalid JSON / repair rate；
revision confirmation rate；
Recall relevant success；
Recall NONE precision observation；
visible answer correlation rate。
```

本任务不把有限样本的“准确率”写成永久模型质量。

---

# 17. 瓶颈分类

每个写入和召回 operation 计算：

```text
provider_total_ms；
local_geometry_ms；
local_persistence_ms；
queue_wait_ms；
main_agent_ms；
other_local_ms。
```

## 17.1 写入

```text
Provider：
Formation；
Surface Traversal LLM；
Placement decision；
JSON repair/retry；
revision confirmation/redecision。

Local geometry：
Surface build；
physical entry resolution；
candidate projection。

Persistence：
Statement persist；
Core mutation；
Handle bind；
readback。

Queue：
message_sent → background start；
多 Statement 串行等待。
```

## 17.2 Recall

```text
Provider：
Surface Traversal LLM；
correction；
Recall selection LLM；
主代理回答。

Local：
Surface build；
physical entry；
Core Recall；
Statement projection；
injection render。
```

## 17.3 分类结论

报告必须回答：

```text
1. 写入时间中 Provider 占比多少？
2. 多 Statement 串行 Placement 放大多少？
3. 本地 Surface/Core 是否仍是主要瓶颈？
4. Recall 的主要延迟在入口 Traversal、Recall selection，
   还是主代理生成答案？
5. cold restart 增加多少？
6. dense hidden-preview 比普通 relevant Recall 增加多少？
7. NONE 是否仍然需要昂贵模型调用？
```

---

# 18. 基于数据决定后续任务

本任务结束时不得自动优化。只生成一个候选优先级表。

## 18.1 若 Formation/Placement Provider 占写入时间 > 70%

下一候选动作可以是：

```text
减少不必要模型调用；
多 Statement 共用一次 Locality traversal；
减少 Prompt 大小；
重新审视 Formation 与 Placement 是否可在同一真实 Host 调用中分工；
但不得用 Python 语义替代。
```

## 18.2 若多 Statement 串行等待占比高

下一候选动作：

```text
同一 Formation batch 的只读 Surface 复用；
有限并行或批量 Placement 研究；
仍保持每条 Statement 独立语义决定和原子写入。
```

不得在本任务中直接实现。

## 18.3 若 Surface/Core 本地时间 > 20% 或 > 2 秒

下一候选动作：

```text
分析 Surface cache；
减少重复 bridge 启动；
增量 derived projection；
Profile-aware local optimization。
```

不得恢复语义索引。

## 18.4 若 Recall Provider 占比 > 70%

下一候选动作：

```text
减少 Surface Traversal 调用；
单例机械消解；
缩小 Prompt；
评估是否可在一个 Recall Agent 调用中完成导航与选择；
不使用关键词路由。
```

## 18.5 若 injection ready 很快、visible answer 很慢

结论应是：

```text
Nollm Recall 不是主要瓶颈；
主代理 Provider 生成占主导。
```

不得为此修改 Core。

## 18.6 若 NONE 成本很高

下一候选动作可以研究：

```text
结构性、非语义的快速空场终止；
有限 Surface 首屏 NONE；
仍由真实 LLM 负责相关性；
不得增加 query→Topic/Cell route。
```

---

# 19. 内部实施 Gate

## Gate 0：活动依据和 timing 语义冻结

工作：

```text
核验 Bundle/HEAD/Tag/clean tree；
更新 AGENTS.md；
生成 timing glossary；
标记旧 formation_ms deprecated；
定义 durable memory 和 recall-ready；
更新 ACTIVE_PROJECT/CURRENT_STATUS/Ledger 为 latency baseline IN_PROGRESS；
Checkpoint commit。
```

PASS：

```text
所有主要字段有唯一含义；
没有把 Formation 输出当 durable memory；
没有把 injection-ready 当 visible answer；
没有启动性能优化。
```

建议提交：

```text
checkpoint(aold): freeze end-to-end memory latency semantics
```

## Gate 1：Correlation 与分段 instrumentation

工作：

```text
Node high-resolution timing；
Python high-resolution timing；
turn/run/request/statement correlation；
message_sent → background；
formation；
per-statement placement；
durable readback；
query → injection；
query → visible answer；
debug-only JSONL。
```

PASS：

```text
单进程 monotonic；
跨进程 epoch correlation；
formation_ms 累计误义已消除；
多 Statement 时间不重复记账；
用户可见回答可以按 run_id 关联。
```

建议提交：

```text
feat(openclaw): correlate visible turns durable commits and recall answers
```

## Gate 2：Deterministic timing correctness

工作：

```text
fake clock / controlled clock tests；
事件顺序；
多 Statement；
reuse/revision/defer；
Recall relevant/NONE；
visible answer correlation；
instrumentation on/off overhead。
```

PASS：

```text
无负 duration；
stage sum 与 total 在声明误差内；
事件缺失明确标记；
timing 不改变 state；
overhead 通过。
```

建议提交：

```text
test(aold): validate memory latency event semantics
```

## Gate 3：Windows 写入延迟 Live

工作：

```text
独立工作区；
预热；
最低 12 / 目标 20 普通聊天；
冷/热；
新事实、多 Statement、reuse、真实 revision、defer；
durable readback；
重开验证。
```

PASS：

```text
至少 8 个 durable-memory turn；
每条有完整 timeline；
无强制 Placement；
旧数据保留；
失败如实记录。
```

建议提交：

```text
test(aold): measure real conversation to durable memory latency
```

## Gate 4：Windows 召回延迟 Live

工作：

```text
最低 12 / 目标 20 新 Session query；
warm/cold；
dense hidden-preview；
multi-fact；
NONE；
query→injection；
query→visible answer。
```

PASS：

```text
相关 Recall、NONE 和 visible answer 均可关联；
至少两次 restart cold；
一个入口；
无 Cursor、多入口或语义路由。
```

建议提交：

```text
test(aold): measure recall injection and visible answer latency
```

## Gate 5：统计、瓶颈和下一候选动作

工作：

```text
analyzer；
原始样本表；
分位数；
Provider/local/queue/main-agent 占比；
冷热差；
多 Statement 放大；
失败率；
候选优化优先级。
```

PASS：

```text
没有伪精确分位数；
没有把一次机器结果写成永久 SLA；
没有在本任务内擅自优化；
能够直接回答用户两个核心问题。
```

建议提交：

```text
docs(aold): record real memory commit and recall latency baseline
```

## Gate 6：回归、状态和 Bundle

工作：

```text
完整 tests；
Evidence freeze；
报告；
实际向量；
完成度；
Manifest；
boundary；
clean tree；
完整历史 Bundle。
```

PASS：

```text
最终 Evidence line/size/SHA 一致；
最终报告已纳入 Manifest；
插件保持启用；
旧工作区保留；
Bundle verify 通过。
```

---

# 20. 自动测试矩阵

## 20.1 Access

```text
durable commit endpoint only after Statement + Core + Handle；
readback failure is not completed memory；
multi-Statement first/all timing；
reuse has no duplicate Core write；
revision confirmation timing；
defer terminal timing；
timing does not change state；
high-resolution nonnegative durations。
```

## 20.2 OpenClaw Python

```text
bridge timing fields typed；
surface/core timing preserved；
no full text required；
no persistent correlation state；
recall outcome NONE/relevant；
Access readback result mapping。
```

## 20.3 OpenClaw Node

```text
message_sent observed time；
background queue time；
formation provider duration；
per-statement offset；
placement provider/local split；
agent_turn_prepare start；
injection-ready；
main message_sent correlation；
run_id mismatch rejected；
missing visible answer reported unavailable；
debug-only config；
no hidden reasoning persistence。
```

## 20.4 Lab

```text
JSONL schema validation；
event joining；
no double counting；
stage totals；
sample-size-aware percentiles；
cold/warm grouping；
relevant/NONE grouping；
Provider/local share；
Evidence freeze；
Markdown report generation。
```

## 20.5 Regression

```text
R1/R2/R3；
P1；
dense hidden-preview；
revision confirmation；
legal traversal；
single-entry；
Coverage/Surface existing tests；
Manifest/boundary。
```

---

# 21. Live Evidence 文件

只新增一个冻结主 Evidence：

```text
validation/aold_real_memory_commit_recall_latency_20260716.jsonl
```

以及一个结构化汇总：

```text
validation/aold_real_memory_commit_recall_latency_summary_20260716.json
```

## 21.1 JSONL 必须包含

```text
schema_version；
event_type；
scenario_id；
turn_correlation_id / recall_request_id；
run_id hash；
statement_id；
timestamps；
durations；
model/provider；
outcome；
selected entry；
selected Statement IDs；
cold/warm；
error/timeout stage；
state hashes before/after where needed。
```

## 21.2 Freeze 顺序

```text
1. 完成全部 Live；
2. 停止追加；
3. 计算 line count / byte size / SHA；
4. 生成 summary；
5. 报告引用最终 SHA；
6. 加入 Manifest；
7. 再执行 Manifest --check；
8. commit；
9. 不得再追加。
```

---

# 22. 主报告

只新增一个主报告：

```text
docs/project/AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_REPORT.md
```

最低必须直接回答：

```text
一条普通对话从显示完成到：
- Formation 完成多久；
- 第一条 durable memory 多久；
- 全部 durable memory 多久；
- 重开后仍可读取是否成立。

一次相关查询从出现到：
- Surface ready 多久；
- Core Recall 完成多久；
- hidden injection ready 多久；
- 用户看到最终答案多久。

冷启动与热运行分别多久；
密集 hidden-preview 比普通 Recall 多久；
NONE 多久；
Provider、本地几何、持久化、主代理分别占多少。
```

## 22.1 报告首页建议格式

```text
Conversation → Durable Memory
  warm p50:
  warm p90:
  cold:
  fastest:
  slowest:
  first durable:
  all durable:

Query → Hidden Injection
  warm p50:
  cold:
  dense hidden-preview:
  NONE:

Query → Visible Answer
  warm p50:
  cold:
  Nollm share:
  main-agent share:
```

没有足够样本的字段写：

```text
insufficient sample
```

不得空填或估算。

---

# 23. 完成条件

允许完成状态：

```text
REAL_MEMORY_COMMIT_AND_RECALL_LATENCY_BASELINE_RECORDED_AT_<HEAD>
```

必须同时满足：

```text
timing 语义已纠正；
旧 cumulative formation_ms 不再进入正式统计；
至少 12 写入 turn；
至少 8 durable-memory turn；
至少 12 recall query；
至少 2 cold recall；
至少 2 dense hidden-preview；
至少 2 NONE；
query→injection 和 query→visible 均有证据；
Provider/local/main-agent 分离；
Evidence 冻结；
状态、Ledger、Manifest、clean tree、Bundle 通过。
```

若 Live 样本不足、visible answer 无法关联或 Provider 长期不可用：

```text
AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS_AT_<HEAD>
```

仍必须：

```text
commit；
clean tree；
完整历史 Bundle；
已完成数据如实交付；
不得补造。
```

---

# 24. 明确非目标

本任务不做：

```text
降低 Provider 延迟；
更换 Provider/模型；
合并 Formation 与 Placement；
批量并行 Placement；
多物理层 Placement；
Stitch/Unstitch；
Bridge 端点；
多入口 Recall；
语义索引；
Topic/Source route；
PB 长跑；
持久 Surface cache；
生产 Trace 系统；
安全审计平台；
正式 SLA。
```

本任务只回答：

```text
现在到底需要多久，
以及时间花在哪里。
```

---

# 25. 状态与进度账

更新：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
```

必须记录：

```text
输入 HEAD；
最终 HEAD；
任务状态；
预计/实际向量；
全部模块实际完成度；
样本规模；
主要 p50/p90/p95；
冷/热；
Provider/local/main-agent 占比；
已知限制；
下一候选优化，但不自动启动。
```

禁止：

```text
把测得的某秒数写成永久性能保证；
使用 sealed/final；
因为 Provider 快慢修改几何硬参数；
把 Debug Evidence 变成产品 Audit。
```

---

# 26. 测试命令建议

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

python lab/nollm-lab/latency/run_latency_schema_validation.py
python lab/nollm-lab/latency/run_latency_instrumentation_overhead.py
python lab/nollm-lab/latency/analyze_memory_latency.py `
  --evidence validation/aold_real_memory_commit_recall_latency_20260716.jsonl `
  --summary validation/aold_real_memory_commit_recall_latency_summary_20260716.json `
  --report docs/project/AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_REPORT.md

python tools/generate_module_ownership_manifest.py
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py

Push-Location integrations/openclaw/formation-loop
npm test
npm run plugin:check
Pop-Location

git diff --check
git status --short
```

脚本名称可以按现有仓库风格调整，但职责不得删除。

---

# 27. Git 与 Bundle

建议提交：

```text
checkpoint(aold): activate real memory latency baseline
feat(access): expose durable memory commit timing
feat(openclaw): correlate turn commit recall and visible answer timing
test(aold): validate latency semantics and measurement overhead
test(aold): record real write and recall latency samples
docs(aold): publish memory latency baseline and bottleneck analysis
```

最终 Bundle：

```text
nollm_aold_real_memory_commit_recall_latency_20260716_<shorthead>.bundle
```

仓库外生成：

```powershell
git bundle create ..\nollm_aold_real_memory_commit_recall_latency_20260716_<shorthead>.bundle --all
git bundle verify ..\nollm_aold_real_memory_commit_recall_latency_20260716_<shorthead>.bundle
Get-FileHash ..\nollm_aold_real_memory_commit_recall_latency_20260716_<shorthead>.bundle -Algorithm SHA256
```

---

# 28. 最终回复要求

最终只需清楚报告：

```text
1. 一轮对话显示后，第一条记忆多久持久化；
2. 一轮对话显示后，全部记忆多久持久化；
3. 相关查询多久准备好隐藏注入；
4. 用户多久看到带记忆的回答；
5. cold / warm / dense / NONE 的差异；
6. Provider、本地几何、持久化、主代理各占多少；
7. 失败率和样本数；
8. 哪个环节最值得下一步优化；
9. branch / HEAD / tests / Bundle SHA。
```

不得在没有证据时声称：

```text
已经达到实时；
已经达到某 SLA；
所有模型相同；
所有机器相同；
长期稳定；
PB 规模成立。
```

---

# 29. 最终任务概括

```text
“记住”不是模型生成了一条 Statement，
而是 Statement、Handle 和 Core Atom 已经持久一致。

“记起来”不是 Core 找到了 Atom，
而是隐藏注入已经准备好；
用户真正感受到的终点则是主代理回答已经显示。

本任务不继续发明结构，
只把这两段真实时间完整测出来，
并确认时间到底花在 Nollm 本地，
还是花在真实 LLM 调用。
```

> **先把真实延迟测清楚，再决定优化哪里；不能继续凭感觉优化，也不能把 Provider 等待误算成几何开销。**
