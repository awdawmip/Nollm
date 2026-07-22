# Nollm AOLD：主代理工具作用域、真实 Provider Live 与语义选择性闭环任务书

**任务文件名**：`NOLLM_A_O_L_D_MAIN_AGENT_TOOL_SCOPE_PROVIDER_LIVE_SEMANTIC_SELECTIVITY_CLOSURE_TASK_20260722.md`
**日期**：2026-07-22
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**任务性质**：Rev5 产品链路真实性闭环；不新增记忆架构，不修改 Core 几何
**输入 Bundle**：`nollm_aold_llm_native_evidence_main_agent_recall_20260722_ec83e0c.bundle`
**输入 Bundle SHA-256**：`ab53df967fd9c107c6fbdb6dd4cbfdbeea916a2a52265d41a77e6eda1c6d2a24`
**输入分支**：`codex/aold-llm-native-evidence-main-agent-recall-selectivity`
**输入 HEAD**：`ec83e0cb22299f2d62d0d6e021911595f8c783a9`
**输入精确 Tag**：无
**建议工作分支**：`codex/aold-main-agent-tool-scope-provider-live-selectivity`
**主执行环境**：Windows 10/11、PowerShell、Node 24、真实 OpenClaw、当前 Host Provider/模型
**交付方式**：大跨度单任务；内部 Gate；普通问题直接修复；所有真实进展 commit；工作树 clean；仓库外生成并验证一个完整历史 Git Bundle
**插件最终状态**：保持安装并启用；真实验证必须使用可 Admission 的 `statement-store` 活动配置
**数据最终状态**：全部旧工作区、Capture、Statement、Handle、Core state 和冻结 Evidence 保留；新建独立 Rev5 Live 工作区
**能力边界**：不修改 Core、Coverage、Junction、物理参数或单入口原则；不启动 multi-cell、多物理层、Stitch、多 Chart、Topic/Entity、vector/graph/embedding、multi-entry Recall、Provider 更换或 PB 长跑

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +10% | DISTRIBUTIONS +5%

主方向：
保持 Writer v3、Evidence Quote、canonical Statement provenance、
Prompt-bounded Atlas、realized Junction 和 bounded Locality；
修复主代理工具 operation 的 run/session/scope 身份和生命周期；
保证使用 Recall 后的主代理回答不会重新形成同一记忆；
修复非默认 Atlas Policy 无法 Recall；
撤回自证明的 deterministic target/NONE/leakage 指标；
在真实 OpenClaw 和 Provider 中形成至少20条当前记忆；
让主代理在同一 run 中直接调用几何工具；
完成 relevant、target-hidden、dense、NONE、restart、expand 和可见延迟；
只根据真实结果决定下一步。

范围变化：
无架构范围扩张；
Rev5 继续作为活动架构；
本任务只闭合实现、运行合同、证据和发行配置。
```

## 0.1 内部 Gate 向量复述

每个 Gate 开始时记录：

```text
C 0 | S 0 | T 0 | A +5 | H 0 | U 0 | O +15 | L +10 | D +5
```

每个 Gate 结束时记录：

```text
实际受影响模块；
预计/实际向量偏差；
是否修改公共合同；
是否增加 Provider 调用；
是否重新引入隐藏 Reader；
是否出现跨 run/session operation 混用；
是否改变 Core tree；
是否需要更新任务范围。
```

新增 Core 修改或任一模块偏差超过 5%，必须先更新任务书、任务名、向量和 canonical Ledger，不得静默扩张。

---

# 1. 输入 Bundle 审核结论

## 1.1 基础现场

```text
Bundle verify：
通过，完整历史；

Bundle SHA-256：
ab53df967fd9c107c6fbdb6dd4cbfdbeea916a2a52265d41a77e6eda1c6d2a24；

HEAD：
ec83e0cb22299f2d62d0d6e021911595f8c783a9；

branch：
codex/aold-llm-native-evidence-main-agent-recall-selectivity；

working tree：
clean；

exact HEAD tag：
无。
```

独立复现：

```text
Rev5 focused Python：
33 passed；

Core/Snapshot/Trace selected：
通过；

Manifest：
tracked = 2054；
rows = 2054；
unclassified = 0；

production violations = 0；
production cycles = 0；

Evidence committed SHA/line/bytes：
与报告表一致。
```

当前 Linux 环境没有 `node_modules`，未独立重建报告中的 Node 52 项。完整 Python 套件在当前环境运行超过十分钟，仅完成约 64%，未取得完整独立结果；Windows 报告结果须在本任务重新复现。

## 1.2 已验证并必须保留的能力

```text
活动 Writer 只接受 v3；
legacy v1 仅显式离线迁移；
LLM 输出自然 Evidence quote；
Access 确定性计算 exact codepoint spans；
resolved reference basis 与 exact Evidence refs 交叉绑定；
Statement provenance 独立持久、可重开、不同内容拒绝覆盖；
provenance 写失败时不留下 Statement/Handle/Atom；
Cartography plan 绑定 Core state 和 Atlas identity；
stale Core/Atlas plan 零写入；
主代理内部 nollm_memory 工具已注册；
工具 model-visible 参数不包含 q/r/layer/query/Statement lookup；
legacy hidden Reader active path关闭；
默认 Locality 最多4条/3000字符；
同一entry只允许一次扩展到8条/6000字符；
Core tree相对输入未改变；
80 Statement deterministic fixture可形成8个几何Locality；
本地Python Locality函数在当前测试中维持亚秒量级。
```

这些成果不得回退。

## 1.3 当前能力应重新定性

`ec83e0c` 应记录为：

```text
LLM_NATIVE_EVIDENCE_AND_MAIN_AGENT_TOOL_IMPLEMENTATION_CHECKPOINT_AT_ec83e0c
```

它证明实现和确定性函数存在，但没有证明：

```text
真实主代理会调用工具；
工具operation不会跨run/session冲突；
使用Recall后的回答不会被再次吸收；
真实query会选择正确entry；
真实NONE成立；
真实Provider Writer first-attempt稳定；
statement-store活动配置可完整工作；
用户可见延迟下降；
60～100事实的语义选择性。
```

---

# 2. 当前报告和证据中的根本问题

## 2.1 “Provider 被禁止”没有活动依据

报告、Current Status 和 Summary 写：

```text
live OpenClaw/model calls are prohibited by the active repository instruction
```

但当前最终仓库中：

```text
AGENTS.md 没有该禁令；
ACTIVE_PROJECT 没有该禁令；
当前任务书反而明确要求 Provider-backed 20 Statement Gate；
nollm-openclaw distribution 宣称 live_activation=invisible-dream-agent；
插件 main_agent_recall_enabled 默认 true。
```

因此 Provider Gate 未运行属于任务未完成，不是合法的架构阻断。

Gate 0 必须：

```text
删除虚构的禁止理由；
如实记录“未执行”；
恢复当前核心功能优先期的真实 OpenClaw Live 授权；
不得继续用旧历史禁令阻止产品验证。
```

## 2.2 80 Statement “target reach”是自证明

当前 scale runner 的 default case：

```text
先从正确 fixture entry执行Recall；
再从Recall返回items中挑一个Statement作为target；
再检查这个target是否仍在同一个结果中。
```

所以：

```text
target_reach = 100%
```

是定义上的恒真，不是查询命中率。

expanded case 同样：

```text
从expanded结果中选target；
再检查expanded含有target。
```

它只证明 expanded 窗口比 default 大，不能证明语义查询成功。

## 2.3 NONE 没有实际运行

当前十个 NONE event 是脚本直接写入：

```text
entry_id = null；
result_count = 0；
target_reached = false。
```

没有：

```text
主代理；
工具调用；
Surface；
模型判断；
用户可见回答。
```

因此不能称 NONE Gate。

## 2.4 unrelated leakage 被硬编码为0

runner 没有检查返回 Statement 属于哪个 Locality，而是直接写：

```text
unrelated_leakage = 0
```

Summary 的：

```text
max_unrelated_leakage = 0
```

不是测量结果。

## 2.5 local tool p95不包含实际工具链

当前约625ms来自：

```text
Python进程内直接调用 recall_main_agent_locality()
```

不包含：

```text
OpenClaw tool dispatch；
TypeScript operation state；
Python bridge进程启动；
base64/JSON传输；
主代理工具往返；
visible response。
```

只能称：

```text
Python bounded-locality function observation。
```

---

# 3. 主代理工具当前生产风险

## 3.1 operation_id 由模型提供且全局共享

当前工具参数要求模型传：

```text
operation_id
```

插件用一个进程级：

```text
Map<operation_id, operation state>
```

保存状态。

没有绑定：

```text
sessionKey；
runId；
user/scope；
toolCallId；
workspace partition；
created_at/TTL。
```

两个并发 run 若使用相同 operation_id：

```text
后一个surface可以覆盖前一个；
前一个recall可能使用后一个entries；
none可以删除另一个run的operation；
expand可能作用于另一个run。
```

这是正确性和隔离问题。

## 3.2 operation 不会在成功后可靠清理

当前 operation 仅在：

```text
none；
某些bridge error；
超过64时淘汰最老项
```

删除。

成功 recall/expand 后仍留在全局 Map；没有：

```text
agent_end清理；
session_end清理；
TTL；
run完成清理。
```

## 3.3 主代理 Recall 不会标记“本run已由记忆满足”

旧 hidden Recall 在成功注入时执行：

```text
recallSatisfiedSessions.add(sessionKey)
```

最终回答不会再次进入 Formation。

新工具成功 Recall 没有 session/run context，也不会设置该标记。

结果可能是：

```text
主代理通过Nollm Recall得到旧事实；
回答用户；
该回答随后被Capture；
后台Writer再次形成旧事实或其改写；
造成自我回声和重复记忆。
```

该问题必须按 run 身份修复，不能继续使用粗粒度 session Set。

## 3.4 region_id 参数未参与校验

工具 schema 暴露：

```text
region_id
```

但活动 TypeScript execute 不使用它。

必须：

```text
删除无效参数；
或将(region_id,entry_id)作为完整选择身份并验证。
```

## 3.5 非默认 Surface Policy 会导致 Recall 必然 stale

独立复现：

```text
build_main_agent_surface(max_entries=8)
→ surface成功；

recall_main_agent_locality()
→ 使用默认ProgressiveAtlasPolicy(32)重建；
→ selected entry changed；
→ Recall失败。
```

当前 plugin config 允许：

```text
recall_surface_max_cells != 32
```

但 operation 没有保存并传回实际 policy。

必须让：

```text
surface和recall使用完全相同的Atlas policy/fingerprint。
```

## 3.6 expansion 在bridge成功前已消耗

当前：

```text
operation.expanded = true
→ 再调用bridge。
```

如果 bridge 失败：

```text
用户无法重试同一entry的expand。
```

应在成功后再提交状态，或失败时回滚。

## 3.7 operation ID 应由系统签发

模型只应操作：

```text
服务端返回的operation token；
当前可见region/entry ID；
固定budget ID。
```

不应自己创建 operation identity。

Codex应优先：

```text
surface动作不要求operation_id；
插件用toolCallId/run context/random nonce生成；
返回operation_id；
后续动作回传；
按run/session/scope绑定。
```

如果 OpenClaw SDK 提供 tool execution context，必须使用真实 context；如不提供，Codex应使用：

```text
server-issued high-entropy token
+
after_tool_call / agent_end hook
+
run-scoped registry
```

实现等价约束。

---

# 4. 活动发行配置矛盾

当前：

```text
distribution live_activation = invisible-dream-agent；
dreamAgent.enabled = true；
requires statement-store；
```

但：

```text
distribution dreamAgent.writeMode = shadow；
install.ps1 默认 WriteMode = shadow；
plugin write_mode 默认 shadow。
```

在 shadow 模式：

```text
Capture可以发生；
后台Absorption不会进入Statement/Handle/Core Admission。
```

这与“真实长期记忆已启用”的能力表述不同。

本任务不得简单把安全默认改成写入而不说明。

必须至少形成两个明确 Profile：

```text
shadow-observation：
  Capture/模型观察；
  不Admission；

active-memory：
  statement-store；
  durable Admission；
  main-agent Recall；
  本任务Live使用。
```

要求：

```text
manifest/README/install/diagnose/OpenClaw config口径一致；
当前运行Profile可机器诊断；
报告明确使用哪个Profile；
不能用shadow结果证明记忆闭环。
```

Codex可判断产品安装默认保持shadow还是切换active-memory，但必须：

```text
不再混用名称；
提供显式、已验证的active-memory安装命令；
用户数据不清空；
回退可关闭。
```

---

# 5. 活动依据与优先级

开工前按顺序读取：

```text
1. FIRST_PRINCIPLES_AND_ANTI_DRIFT；
2. PROJECT_BOOK V3.1；
3. CORE_FUNCTION_PRIORITY V3.4；
4. V3.7 Rotated Physical Memory Field；
5. V3.9 Bounded Approximate Coverage；
6. V3.10 Durable Capture / Async Absorption；
7. V3.11 Rev5；
8. CURRENT_STATUS；
9. canonical Ledger；
10. 本任务书；
11. A/O/L/D charters；
12. 根目录 AGENTS.md。
```

冲突优先级：

```text
真实用户链路
> 原始Evidence和数据不丢失
> run/session隔离
> 真实Provider证据
> LLM语义/Core几何边界
> Architecture is the Index
> 单入口Recall
> 现有确定性fixture。
```

---

# 6. `AGENTS.md` 更新要求

至少加入：

```text
- ec83e0c is an implementation checkpoint; its deterministic target/NONE/leakage metrics are not semantic Recall evidence.
- The active repository does not prohibit OpenClaw Live or model calls for this task.
- Provider-backed validation is mandatory and uses a dedicated active-memory workspace.
- Main-agent memory operations are server-issued and bound to one run/session/scope.
- A model does not invent operation identity.
- Tool state has TTL and is removed after run completion, NONE, fatal error or final expansion.
- Recall success must mark the exact run as recall-satisfied so its answer is not reabsorbed as new memory.
- Surface and Recall must use the exact same Progressive Atlas policy.
- Tool parameters that are not validated must be removed.
- Synthetic scale targets are declared before Recall; never choose the target from the returned result.
- NONE must be observed through a real main-agent run.
- Leakage is computed from returned Statement identities, never hard-coded.
- Local tool timing includes the actual OpenClaw→bridge→Access roundtrip when reported as tool latency.
- Shadow and active-memory distribution profiles are distinct and machine-diagnosable.
- Do not modify Core or add memory architecture in this task.
```

---

# 7. 全部模块任务前完成度

审核后基线：

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 当前主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 93% | 中高 | V3.9几何、Junction、runtime完整性 | 本任务只回归 | 否 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes | 增量/版本 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 独立sink合同 | metrics | 否 |
| ACCESS | `IMPLEMENTED` | 96% | 高 | quote resolver、provenance、bounded Locality | policy identity和真实选择性证据 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 88% | 中 | 工具注册、legacy Reader关闭 | operation隔离、capture suppression、真实Live | 是 |
| LAB | `IMPLEMENTED` | 86% | 中 | 80事实函数压力 | 自证明指标、无Provider/main-agent证据 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 90% | 中 | Rev5 Wire声明 | shadow/active事实矛盾 | 是 |

完成度低于 Bundle 记录，原因是 Provider Gate未执行、确定性指标不构成语义证据，以及工具运行身份尚未闭合。

---

# 8. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付 | 剩余限制 |
|---|---:|---:|---:|---|---|
| CORE | 93% | 93% | 0% | 完整回归 | 多层、Stitch |
| SNAPSHOT | 50% | 50% | 0% | 回归 | 增量 |
| TRACE | 40% | 40% | 0% | 回归 | metrics |
| ACCESS | 96% | 98% | +5%向量 | policy-bound Locality、真实选择性 | 长期规模 |
| HISTORY | 10% | 10% | 0% | 无 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无 | 暂停 |
| OPENCLAW | 88% | 97% | +15%向量 | run-scoped tool、Provider Live、visible answer | 其他Host |
| LAB | 86% | 96% | +10%向量 | 非自证语义矩阵、Live A/B | 长期统计 |
| DISTRIBUTIONS | 90% | 95% | +5% | profile真值和诊断 | 正式发行 |

不得写永久 100%。

---

# 9. Gate 0：状态、虚构禁令和证据重新定性

工作：

```text
核验Bundle/HEAD/clean；
更新AGENTS/ACTIVE_PROJECT/STATUS/Ledger；
删除“Provider被活动规则禁止”的错误表述；
将ec83e0c记录为implementation checkpoint；
将80事实结果重新定性为：
  deterministic bounded-locality function fixture；
标记：
  target reach不可用；
  NONE不可用；
  leakage不可用；
  Python local function timing有效；
保护性commit。
```

必须新增反例测试：

```text
target从result中选取→指标无效；
NONE event无实际operation→指标无效；
hard-coded leakage→指标无效；
Provider prohibition在活动authority中不存在。
```

Gate 0 PASS：

```text
状态不再把未执行写成被禁止；
完成度重算；
下一步明确是Live和工具隔离。
```

建议提交：

```text
checkpoint(aold): correct Rev5 evidence and Provider-live baseline
```

---

# 10. Gate A：run-scoped 主代理工具 operation

## 10.1 服务器签发 operation

首个 `surface` 动作：

```text
模型不提供operation_id；
插件根据：
  toolCallId；
  session/run context；
  scope/workspace；
  random nonce或等价唯一源；
签发operation_id。
```

返回：

```text
operation_id；
expires_at；
Atlas状态；
visibleregions/entries。
```

如SDK强制模型提供字段：

```text
该字段只能是上一工具结果返回值；
首次surface必须使用固定空值或省略；
插件仍覆盖并签发真实ID。
```

## 10.2 Operation 绑定

每个operation至少绑定：

```text
runtime session identity；
main run identity；
capture/memory scope；
workspace identity；
Core state；
Atlas policy/fingerprint；
created_at；
last_used_at；
selected entry；
expansion state。
```

后续调用必须来自相同运行范围。

如果SDK无法在execute直接提供run context：

```text
使用toolCallId、after_tool_call、before_agent_run、agent_end等Host事件建立绑定；
或使用服务端不可猜测token并在当前run显式登记；
必须有设计说明和测试。
```

## 10.3 生命周期

删除时机：

```text
NONE；
fatal error；
run完成；
session结束；
Gateway停止；
TTL到期；
成功expanded完成。
```

成功default Recall后可暂时保留用于一次expand。

## 10.4 并发测试

至少：

```text
两个session相同模型建议ID；
两个run并发surface；
run A不能recall run B；
run B不能none run A；
TTL；
64+operations；
Gateway stop；
restart。
```

不得仅依赖高熵而不做作用域校验。

## 10.5 region/entry身份

选择：

```text
删除未使用region_id；
或强制验证(region_id,entry_id)。
```

不得保留无效果参数。

Gate A PASS：

```text
无全局ID碰撞；
无跨run使用；
无operation泄漏；
工具参数和实现一致。
```

建议提交：

```text
fix(openclaw): bind main-agent memory operations to the active run
```

---

# 11. Gate B：Atlas Policy 和 expansion 状态

## 11.1 Policy 绑定

surface operation 保存完整：

```text
ProgressiveAtlasPolicy；
max_regions；
max_prompt_bytes；
max_depth；
Atlas fingerprint；
page fingerprint。
```

recall/expand 使用同一 policy，不得重新采用 Python 默认值。

必须修复反例：

```text
surface max_entries=8
→ recall不再selected entry changed。
```

## 11.2 State freshness

至少验证：

```text
Core state；
Atlas fingerprint；
selected entry；
policy identity。
```

Handle/Statement变化是否需要使主代理operation stale，由Codex依据当前page内容明确决定并测试；不能让报告声称绑定但代码未实现。

## 11.3 Expansion

```text
bridge成功后再设置expanded=true；
bridge失败允许重试；
同一entry最多一次成功扩展；
不能换entry。
```

## 11.4 Surface 计数

报告：

```text
region_count；
selectable_entry_count；
Prompt bytes；
private entry count；
tool-visible entry count。
```

配置名应与真实含义一致：

```text
recall_surface_max_cells若实际限制regions，应改名或明确兼容。
```

Gate B PASS：

```text
所有允许配置可用；
policy不同不产生伪stale；
失败expand可重试。
```

---

# 12. Gate C：Recall-satisfied run 与防止自我回声

## 12.1 Run级标记

退出：

```text
session级 recallSatisfiedSessions。
```

建立：

```text
recallSatisfiedRuns：
  session + run + scope；
```

成功工具 Recall 后：

```text
通过tool execute context或after_tool_call确定当前run；
标记该run已使用admitted memory。
```

Capture/Formation启动时：

```text
只抑制同一个run的assistant answer再形成相同记忆；
不影响下一正常run；
Pending-only context的行为明确；
工具surface但未recall不应抑制。
```

## 12.2 证据

记录：

```text
tool_recall_satisfied；
capture_suppressed_same_run；
next_run_capture_allowed；
suppression reason；
run identity。
```

## 12.3 测试

```text
surface only；
recall success；
recall failure；
NONE；
expand；
same session next run；
concurrent runs；
Gateway restart。
```

Gate C PASS：

```text
主代理使用Recall后的回答不会被重新Admission；
下一轮正常新事实仍可Capture。
```

建议提交：

```text
fix(openclaw): suppress same-run reabsorption after native memory Recall
```

---

# 13. Gate D：发行 Profile 和真实安装

## 13.1 Profile

至少定义并统一：

### shadow-observation

```text
write_mode=shadow；
不Admission；
可用于安装观察；
不得宣称长期记忆已启用。
```

### active-memory

```text
write_mode=statement-store；
durable Capture；
异步Admission；
main-agent Recall；
本任务Live使用。
```

## 13.2 安装与诊断

`install.ps1` 或等价：

```text
明确Profile参数；
active-memory要求workspace；
显示最终write_mode；
不清空旧数据。
```

`diagnose.ps1` 输出：

```text
profile；
write_mode；
Capture enabled；
Absorption enabled；
main-agent tool enabled；
legacy Reader false；
workspace；
Provider/model；
pending count；
last Admission；
active Evidence path。
```

## 13.3 文档一致

同步：

```text
distribution manifest；
plugin manifest；
README；
ACTIVE_PROJECT；
Current Status；
install defaults。
```

不得：

```text
manifest说live；
实际默认shadow；
报告不说明Profile。
```

Gate D PASS：

```text
真实Live明确运行active-memory；
shadow与active证据不混合。
```

---

# 14. Gate E：非自证明确定性规模 Gate

## 14.1 预声明 query 和 target

在执行Recall前定义：

```text
query_id；
query_utf8；
expected target Statement IDs；
allowed supporting IDs；
forbidden unrelated IDs；
expected Locality/entry family；
NONE expectation。
```

目标不能从返回结果中生成。

## 14.2 Entry selection

确定性 fixture分两类：

### Geometry function Gate

```text
给定预定entry；
验证bounded Locality、排序、扩展和性能。
```

不宣称语义查询。

### Semantic simulation Gate

```text
使用独立规则化oracle或Provider main-agent；
根据query选择entry；
再检查预声明target。
```

确定性Python不能用坐标标签直接替代语义选择并声称产品成功。

## 14.3 NONE

必须实际执行：

```text
真实main-agent run；
模型选择none或不调用Recall；
无admitted injection；
最终回答正常。
```

确定性Gate可测试工具`none`状态机，但不能计为语义NONE。

## 14.4 Leakage

根据返回 Statement ID 与预声明集合计算：

```text
unrelated leakage；
wrong Locality；
duplicate；
target miss。
```

不得硬编码。

## 14.5 Timing

分别记录：

```text
Python function；
OpenClaw→bridge；
完整tool roundtrip；
query→visible。
```

名称不得混用。

Gate E PASS：

```text
所有Summary指标可由Evidence重算；
无先看答案再定义target；
无伪造NONE/leakage。
```

建议提交：

```text
test(lab): replace self-referential selectivity with declared targets
```

---

# 15. Gate F：真实 Provider Writer 与 Admission Live

## 15.1 工作区

新建：

```text
nollm-aold-main-agent-native-recall-v8
```

使用：

```text
active-memory profile；
独立Capture spool；
独立run-scoped Evidence；
旧工作区只读保留。
```

## 15.2 自然聊天

最低：

```text
20个Provider-backed durable Statements；
至少12个普通自然聊天turn；
至少3个multi-Statement turn；
至少2个reuse；
至少2个真实revision；
至少2个no-memory/defer；
至少3个independent seeds；
至少3个related growth；
Gateway restart。
```

不得在用户可见消息中使用：

```text
请写入Nollm；
返回JSON；
选择candidate；
调用memory tool；
强制坐标。
```

## 15.3 Writer指标

记录：

```text
first-attempt success；
format repair；
semantic validation retry；
final durable；
quote not found/ambiguous；
resolved reference failure；
provenance reopen；
Provider/model；
calls；
latency；
backlog。
```

最低完成条件：

```text
provider_backed_statement_count >=20；
first-attempt success如实报告，不设永久阈值；
最终durable成功率可复算；
duplicate/orphan=0。
```

## 15.4 Stale Cartography

真实或受控Provider等待期间修改相关Locality：

```text
stale plan零写入；
重新Cartography；
最终可恢复。
```

---

# 16. Gate G：真实主代理工具 Recall

## 16.1 查询矩阵

最低：

```text
10 relevant；
5 relation-entry target-hidden；
5 dense hidden-target；
5 NONE/unrelated；
3 same-entry expand；
2 cold restart；
2 concurrent sessions。
```

所有query预先登记expected target/forbidden IDs。

## 16.2 主代理行为

必须真实观察：

```text
主代理是否调用nollm_memory；
surface；
select one entry；
default Recall；
必要时same-entry expand；
NONE；
最终自然回答。
```

不得通过脚本代替主代理选择entry。

## 16.3 结果

至少报告：

```text
tool invocation rate；
correct entry；
target reach；
forbidden leakage；
NONE precision observation；
default/expanded result count；
single-entry；
child-agent calls=0；
same-run Capture suppression；
query→visible latency；
tool roundtrip latency。
```

## 16.4 工具教学

Codex可以优化：

```text
tool description；
main-agent system hint；
surface result framing。
```

但不得：

```text
Python语义路由；
关键词触发；
query→entry索引；
隐藏Reader恢复；
直接把query作为工具搜索参数。
```

## 16.5 完成条件

```text
至少15个真实main-agent查询；
至少10次正确使用工具或正确NONE；
无跨run operation；
无回答再吸收；
target/forbidden指标可复算；
visible answer自然；
Gateway restart后重复。
```

未达到则保持IN_PROGRESS，不补造。

建议提交：

```text
test(openclaw): validate native main-agent Recall in real Host runs
```

---

# 17. Gate H：回归、证据和交付

## 17.1 回归

执行：

```text
Core；
Snapshot；
Trace；
Access全量；
OpenClaw Python；
OpenClaw Node；
M0 active；
Rev3/Rev4 causal；
Rev5 quote/provenance/stale；
operation scope；
same-run suppression；
semantic scale；
Manifest；
boundaries；
build/compile。
```

完整套件耗时过长时：

```text
允许分组；
必须保存每组结果；
不得只报告未完成的总命令。
```

## 17.2 Evidence

主 Evidence：

```text
validation/aold_main_agent_provider_live_selectivity_20260722.jsonl
validation/aold_main_agent_provider_live_selectivity_summary_20260722.json
```

必须绑定：

```text
natural chats；
Provider Writer raw attempts；
durable Statement/provenance；
tool calls；
run/session/operation；
declared targets；
Recall outcomes；
visible answers；
same-run suppression；
latency；
profile/config；
Provider/model；
workspace SHA。
```

## 17.3 Freeze

```text
停止/旋转live writer；
冻结exact bytes；
line/bytes/SHA；
生成Summary/Report；
Manifest；
从Git blob复算；
commit；
Bundle。
```

## 17.4 主报告

```text
docs/project/AOLD_MAIN_AGENT_PROVIDER_LIVE_SELECTIVITY_REPORT.md
```

报告必须直接回答：

```text
真实Provider Writer是否工作；
主代理是否真正调用tool；
额外hidden child是否为0；
operation是否run-scoped；
是否发生跨run混用；
工具Recall后回答是否被重新吸收；
真实NONE；
真实target reach/leakage；
default/expand；
query→visible；
active-memory profile；
测试与限制。
```

---

# 18. 自动测试矩阵

## OpenClaw Node

```text
server-issued operation；
run/session/scope binding；
operation collision；
TTL/cleanup；
none/fatal/run-end；
region/entry validation；
policy storage；
failed expand retry；
after_tool_call recall-satisfied；
same-run capture suppression；
next-run allowed；
shadow/active profile；
tool registration；
legacy Reader remains false。
```

## OpenClaw Python

```text
non-default policy surface→recall；
page/Atlas identity；
entry uniqueness；
bounded locality；
default/expand；
state mutation stale；
provenance；
Writer v3；
Cartography stale。
```

## Access

```text
declared target fixture；
leakage computation；
Locality ranking；
provenance reopen；
corrupt item；
revision；
independent/related growth。
```

## Lab

```text
old self-proof detector；
real target registry；
NONE actual event verifier；
hard-coded leakage rejection；
Provider Live evidence；
tool roundtrip；
same-run reabsorption；
freeze verifier。
```

---

# 19. 性能和调用边界

保持：

```text
Capture p95目标<=100ms；
Writer common 1 call/batch；
Cartographer one session/batch；
每Prompt<=64KB；
main-agent independent hidden child calls=0；
one final entry；
default Locality<=4 Statements/3000 chars；
one same-entry expand<=8/6000；
Core local V3.9数量级。
```

新增测量：

```text
surface tool roundtrip；
recall tool roundtrip；
expand tool roundtrip；
main-agent Provider total；
query→visible；
same-run suppression overhead。
```

不把一次机器结果写成永久 SLA。

---

# 20. 实际停止条件

只在以下情况停止：

```text
OpenClaw SDK无法将工具调用与run/session建立任何可靠关联；
主代理无法在同一run调用内部工具；
active-memory配置必然破坏旧数据；
真实Provider长期不可用；
Statement/Handle/Core存在不可恢复损坏；
主代理工具必须引入query索引或多入口才能工作。
```

普通Prompt、JSON、tool description、测试、配置、性能和证据问题直接修复继续。

即使停止：

```text
commit；
clean；
完整Bundle；
如实IN_PROGRESS。
```

---

# 21. 完成状态

全部闭合才允许：

```text
REAL_MAIN_AGENT_GEOMETRIC_RECALL_AND_PROVIDER_ADMISSION_VALIDATED_AT_<HEAD>
```

必须同时满足：

```text
Provider-backed Statements>=20；
active-memory profile；
main-agent real tool runs；
server-issued/run-scoped operations；
no cross-run access；
same-run recall answer not reabsorbed；
legacy hidden Reader=0；
independent child-agent calls=0；
real target reach/leakage；
real NONE；
non-default policy；
restart；
visible answer；
full evidence freeze；
Manifest/boundary/clean/Bundle。
```

否则：

```text
AOLD_MAIN_AGENT_PROVIDER_LIVE_IN_PROGRESS_AT_<HEAD>
```

---

# 22. 明确非目标

```text
Core修改；
multi-cell；
多物理层；
Stitch；
多Chart；
持久Lens；
Topic/Entity；
query/fact entry map；
vector/graph/embedding；
multi-entry；
Provider更换；
PB；
正式发布；
产品Audit/History；
外部消息队列或数据库。
```

---

# 23. 建议提交序列

```text
checkpoint(aold): correct Rev5 live and evidence baseline
fix(openclaw): scope native memory operations to one main run
fix(openclaw): bind Recall policy and same-run absorption suppression
fix(distributions): separate shadow and active-memory profiles
test(lab): replace self-referential Recall metrics
test(aold): run Provider admission and native main-agent Recall
docs(aold): record real main-agent memory capability
```

---

# 24. Git Bundle

建议文件名：

```text
nollm_aold_main_agent_provider_live_selectivity_20260722_<shorthead>.bundle
```

仓库外执行：

```powershell
git bundle create ..\nollm_aold_main_agent_provider_live_selectivity_20260722_<shorthead>.bundle --all
git bundle verify ..\nollm_aold_main_agent_provider_live_selectivity_20260722_<shorthead>.bundle
Get-FileHash ..\nollm_aold_main_agent_provider_live_selectivity_20260722_<shorthead>.bundle -Algorithm SHA256
```

---

# 25. 最终回复要求

最终只报告：

```text
branch / HEAD / commits；

Writer Live：
  chats；
  Statements；
  first-attempt/retry；
  durable/provenance；
  profile；

Main-agent Tool：
  operation identity；
  run/session binding；
  tool calls；
  child calls；
  same-run suppression；
  non-default policy；

Recall：
  declared targets；
  target reach；
  leakage；
  NONE；
  default/expand；
  restart；
  query→visible；

Engineering：
  tests；
  Manifest；
  boundaries；
  actual vector；
  completion；
  known limitations；

Bundle：
  filename；
  SHA-256。
```

---

# 26. 最终任务概括

```text
ec83e0c 已经把 Writer、provenance、stale plan 和主代理工具写出来了，
但还没有证明真实主代理会正确使用它。

现有80事实结果只证明：
给定正确入口后，Locality函数有界且较快。

它没有证明：
问题能选对入口；
NONE成立；
无关事实不会泄漏。

本任务不再扩张架构。
先把工具绑定到真正的run/session，
修复回答再吸收和非默认Policy，
然后在active-memory配置下真实运行：

普通聊天形成记忆，
主代理自己调用几何工具，
一个入口找到目标，
无关问题正确NONE，
最终回答自然可见。
```

> **只有真实主代理在真实对话中使用同一个几何工具完成写入后的召回，Rev5 才从“实现存在”变成“产品链路成立”。**
