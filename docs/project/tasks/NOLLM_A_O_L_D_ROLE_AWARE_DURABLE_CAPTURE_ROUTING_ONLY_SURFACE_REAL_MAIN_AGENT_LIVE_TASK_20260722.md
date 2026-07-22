# Nollm AOLD：角色感知持久 Capture、Routing-only Surface 与真实主代理 Live 闭环任务书

**任务文件名**：`NOLLM_A_O_L_D_ROLE_AWARE_DURABLE_CAPTURE_ROUTING_ONLY_SURFACE_REAL_MAIN_AGENT_LIVE_TASK_20260722.md`
**日期**：2026-07-22
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**任务性质**：Rev5 产品闭环纠偏；保持现有记忆架构和 Core 几何不变
**输入 Bundle**：`nollm_aold_main_agent_provider_live_selectivity_20260722_53182a4.bundle`
**输入 Bundle SHA-256**：`f28eb7ae37b84b625e6a3a341c6525ba2ee04c5f392b0808485e36d41ad0de9c`
**输入分支**：`codex/aold-main-agent-tool-scope-provider-live-selectivity`
**输入 HEAD**：`53182a40d7fb443a81d90cf560dc905d96a2e208`
**输入实现检查点**：`9cc0f005cce15e022884ce4a0fb930b17668fe08`
**输入精确 Tag**：无
**建议工作分支**：`codex/aold-role-aware-capture-routing-surface-real-main-agent-live`
**主执行环境**：Windows 10/11、PowerShell、Node 24、真实 OpenClaw、当前 Host Provider/模型
**交付方式**：大跨度单任务；内部 Gate；普通问题直接修复；全部真实进展 commit；工作树 clean；仓库外生成并验证一个完整历史 Git Bundle
**插件最终状态**：保持安装并启用；正式 Live 使用明确的 `active-memory` Profile
**数据最终状态**：全部历史工作区、Capture、Statement、Handle、Core state 和冻结 Evidence 保留；新建独立 Live 工作区；不得覆盖旧冻结工件
**能力边界**：不修改 Core、Coverage、Junction、物理参数、MemoryAtom 或单入口原则；不启动 multi-cell、多物理层、Stitch、多 Chart、Topic/Entity、vector/graph/embedding、query/fact 索引、multi-entry Recall、Provider 更换或 PB 长跑

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +15% | DISTRIBUTIONS +5%

主方向：
始终持久保存用户与主代理的原始可见 turn；
用角色级、可持久复算的吸收指令防止记忆派生回答自我回声，
而不是跳过整个 Capture；
将主代理 Surface 从“多区域完整事实展示”改为
字段完整、Prompt 有界、只用于选路的 routing-only 地图；
将工具作用域绑定到真实 Host scope；
在 active-memory Profile 下运行真实 Provider Writer 和真实主代理工具；
以预声明 target、target-hidden、NONE、expand、restart、并发和可见延迟
闭合产品链路。

范围变化：
无新记忆架构；
Capture 公共合同增加角色来源/吸收资格元数据；
主代理工具 Surface 的可见合同收窄为 routing-only；
Core、one Statement/Atom/Handle/Cell 和 single-entry Recall 保持不变。
```

## 0.1 内部 Gate 向量复述

每个 Gate 开始必须记录：

```text
C 0 | S 0 | T 0 | A +5 | H 0 | U 0 | O +15 | L +15 | D +5
```

每个 Gate 结束必须记录：

```text
实际受影响模块；
预计/实际向量偏差；
是否改变公共合同；
是否修改 Core tree；
是否出现多入口或语义索引；
是否丢失原始 Capture；
是否从 Surface 直接泄露答案；
是否执行真实 Provider/Host；
是否需要更新任务名称、范围或向量。
```

新增 Core 修改或任一模块实际偏差超过 5%，必须先更新任务范围、任务名、向量和 canonical Ledger，不得静默扩张。

---

# 1. 输入 Bundle 审核基线

## 1.1 Bundle 与 Git 现场

```text
Bundle verify：
通过；

完整历史：
是；

Bundle SHA-256：
f28eb7ae37b84b625e6a3a341c6525ba2ee04c5f392b0808485e36d41ad0de9c；

branch：
codex/aold-main-agent-tool-scope-provider-live-selectivity；

HEAD：
53182a40d7fb443a81d90cf560dc905d96a2e208；

working tree：
clean；

exact HEAD tag：
无；

tracked files：
2062。
```

输入区间提交：

```text
438469d checkpoint(aold): correct Rev5 live and evidence baseline
793a01f fix(openclaw): scope native memory operations to one main run
9cc0f00 test(aold): bind profiles and declared-target Recall evidence
53182a4 docs(aold): record run-scoped main-agent closure
```

## 1.2 独立复现

当前审核环境独立完成：

```text
Rev5 closure focused Python：
13 passed；

module boundary：
production violations = 0；
production cycles = 0；
migration diagnostics = 7；

Evidence：
51 JSONL records；
139578 bytes；
SHA-256 =
49c722f4c903da73aa87b7c94a5f216b2001606f101f1c41f8553c746ef1821d；

Summary：
与 JSONL summary event 一致；
verifier 可重算 declared target、expand、restart 和 forbidden-ID leakage。
```

完整 Python 总套件在当前 Linux 审核环境两次超过执行窗口：

```text
packages：
执行到约 56% 后超过 5 分钟；

packages + integrations + Lab：
执行到约 20% 后超过 15 分钟。
```

因此当前审核没有独立确认报告中的：

```text
Core/Snapshot/Trace/Access/OpenClaw Python 300 passed；
Lab 43 passed。
```

Bundle 未包含 `node_modules`，当前环境未独立重建：

```text
OpenClaw Node 55 passed。
```

这些项目必须在 Windows 主环境重新执行并冻结分组结果。

## 1.3 已验证并必须保留的成果

```text
Host 签发 operation ID；
operation 绑定 session/run/configured scope/workspace；
跨 run/session Recall 和 NONE 被拒绝；
operation TTL、capacity、session/gateway cleanup；
Surface 与 Recall 重用同一 ProgressiveAtlasPolicy；
region_id + entry_id 校验；
bridge 失败后的 expand 可重试；
同 entry 只允许一次成功扩展；
shadow-observation / active-memory Profile 显式分离；
legacy hidden Reader 活动路径关闭；
独立 hidden child calls 目标为0；
80 Statement fixture 的 target 在 Recall 前声明；
forbidden-ID leakage 按返回 Statement ID 计算；
NONE 被诚实标记为未执行；
Python bounded-locality function timing未冒充工具或端到端延迟；
Core tree相对输入保持不变。
```

这些成果不得回退。

---

# 2. 当前能力重新定性

`53182a4` 应记录为：

```text
RUN_SCOPED_MAIN_AGENT_TOOL_OFFLINE_CHECKPOINT_AT_53182a4
```

或更精确地记录：

```text
implementation checkpoint：
9cc0f005cce15e022884ce4a0fb930b17668fe08；

delivery/documentation HEAD：
53182a40d7fb443a81d90cf560dc905d96a2e208。
```

它证明：

```text
离线工具状态机；
run/session 隔离原型；
Policy reopen；
Profile 配置；
预声明 target 的确定性 Locality fixture。
```

它没有证明：

```text
真实 Provider Writer；
真实 durable Admission；
真实主代理会调用 nollm_memory；
Surface → Recall 工具序列；
真实 semantic NONE；
真实 query 选对 entry；
真实答案质量；
真实 query→visible 延迟；
跨用户/真实 scope 隔离；
Recall turn 的原始 Capture 不丢失；
主代理不会直接从 Surface 预览回答。
```

---

# 3. 审核发现

## 3.1 P0：Recall 成功后整轮原始 Capture 被跳过

当前 `publishCapture()`：

```text
若 recallSatisfiedRuns 包含当前 run
→ 记录 suppressed trace
→ return undefined
→ 不调用 CaptureStore.publish。
```

`message_sent` 和 `agent_end` 都调用该函数。

结果：

```text
主代理成功 Recall
→ 用户原话不进入 immutable Capture；
→ 主代理可见回答也不进入 immutable Capture。
```

这违反 V3.10 的稳定基线：

```text
可见用户和 assistant 原始 bytes
必须先 durable Capture；
Capture 与是否长期 Admission 分离。
```

它还会丢失混合型 turn 中的新信息。

例：

```text
用户：
“我今天改住银座了，顺便告诉我上次东京为什么取消浅草？”

主代理使用旧记忆 Recall 回答。
```

当前实现会因为该 run 使用了 Recall 而跳过整个 Capture：

```text
“今天改住银座”
也永久丢失。
```

### 正确边界

```text
Raw Capture：
始终保存 exact user + exact assistant bytes；

Absorption：
区分 user-originated source
与 memory-derived assistant output；

防回声：
阻止旧记忆派生回答再次形成同一事实，
但不得删除原始对话 Evidence。
```

不得继续使用：

```text
Recall success → skip Capture。
```

## 3.2 P0：Surface 在选入口前泄露多区域完整事实

当前 Python `build_main_agent_surface()` 返回：

```text
regions[].representative_statements[].content_utf8
```

TypeScript `surface` 动作只删除私有 `entries`，但将完整 `regions` 返回给主代理。

独立 80 Statement fixture：

```text
statement_count：
80；

region_count：
27；

Surface 可见 representative statements：
80；

Surface 可见 JSON：
约 24736 bytes。
```

也就是说主代理第一次 `surface` 工具调用已经看见全部 80 条事实。

它可以：

```text
不选择一个 entry；
不调用 recall；
直接从多 region preview 回答。
```

这会同时绕过：

```text
single-entry Recall；
default Locality <=4 Statements；
same-entry expand；
successful Recall run 标记；
target-hidden 因果验证。
```

因此当前：

```text
hidden child calls = 0
```

并不等于：

```text
主代理只读取了一个 bounded Locality。
```

### 正确边界

Surface 只能提供：

```text
routing-only region cards；
有限、非权威、不可直接作为完整回答 Evidence 的 anchor；
完整字段覆盖；
Prompt/字符预算；
operation-local IDs。
```

只有 `recall`/`expand` 才能返回完整 Statement 内容和 provenance。

## 3.3 P0：Surface-only 回答与 Recall 回答形成相反错误

当前两条路径：

### Surface-only 回答

```text
主代理从 Surface preview直接回答；
没有 successfulMainAgentRecallCalls；
run不标 recall-satisfied；
整轮会被正常 Capture；
memory-derived assistant回答可能再次形成旧事实。
```

### Recall 回答

```text
主代理调用 recall；
run标 recall-satisfied；
整轮 Capture 被跳过；
用户原话和回答都丢失。
```

因此当前实现不能同时满足：

```text
原始对话不丢；
记忆回答不自我回声。
```

必须改为角色级吸收资格，而不是 run 级 Capture 删除。

## 3.4 P1：报告中的 scope 绑定不是实际 Host scope

`MainAgentRunScope.scopeId` 当前取：

```text
config.capture_scope_id ?? "local-default-user"
```

而 Raw Capture/Pending fallback 的 scope 取：

```text
captureScope(ctx, configuredScope)
```

后者会读取：

```text
accountId；
userId；
senderId；
provider/channel。
```

因此报告所称：

```text
exact Host scope binding
```

目前只绑定了静态配置值，不是实际 Host identity-derived scope。

run/session 隔离是真实的，但 scope 声称过宽。

本任务应选择以下一种明确路线：

```text
A. 真正绑定 captureScope(ctx)；
或
B. active-memory明确为single-scope实例，
   对检测到的其他scope拒绝并诊断。
```

不得继续一边动态分 Capture scope，一边让主代理工具读取共享 memory workspace 而报告“scope-bound”。

## 3.5 P1：真实 Provider/Main-agent Gate仍未执行

报告诚实记录：

```text
provider_backed_statement_count = 0；
semantic NONE unavailable；
query→visible unavailable；
visible answer quality unavailable。
```

任务的核心 Gate 因此未完成。

该未完成不存在新的架构阻断，应在下一执行中直接完成。

## 3.6 P1：完成度和实际向量偏高

Bundle 将：

```text
OPENCLAW = 97%；
LAB = 96%；
DISTRIBUTIONS = 95%；
实际 OPENCLAW +15 / LAB +10 / D +5
```

但：

```text
Provider Live = 0；
真实主代理工具调用 = 0；
semantic NONE = 0；
真实 visible-answer = 0；
active-memory安装验证 = 0；
Surface仍泄露完整多区域事实；
Recall turn Raw Capture会丢失。
```

这些百分比不符合当前实际能力证据，应下调。

## 3.7 P1：最终 HEAD 未进入活动状态身份

最终 Bundle HEAD：

```text
53182a4
```

活动状态仍绑定：

```text
AOLD_MAIN_AGENT_PROVIDER_LIVE_IN_PROGRESS_AT_9cc0f00
```

报告 Delivery 表也只列至 `9cc0f00`，没有记录最终 `53182a4`。

可以保留：

```text
implementation/evidence checkpoint = 9cc0f00
```

但必须同时记录：

```text
delivery HEAD = 53182a4
```

最终状态、Ledger、Bundle回复和能力记录不得让读者误以为 Bundle HEAD 是 `9cc0f00`。

## 3.8 P2：测试执行时长与复现入口

当前全量 Python 在审核环境显著超出此前报告的几十秒级记录。

本任务无需建设 CI，但应：

```text
提供分组 active validation runner；
每组保存命令、环境和结果；
识别长时测试；
报告 wall time；
避免一个总命令超时后只留下部分进度。
```

---

# 4. 审核后的实际推进向量

建议回填：

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW +8% |
LAB +5% | DISTRIBUTIONS +3%
```

理由：

```text
OPENCLAW：
run/session operation、Policy、expand状态和Profile有真实提升，
但未经过真实Host且Capture/Surface存在P0；

LAB：
修复了自证明target和硬编码leakage，
但仍是deterministic oracle，不是产品语义证据；

DISTRIBUTIONS：
Profile事实更清楚，
但active-memory没有真实安装验证。
```

---

# 5. 开工依据

按顺序读取：

```text
1. NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md；
2. 当前稳定项目书；
3. NOLLM_CORE_FUNCTION_PRIORITY_PROJECT_BOOK_V3_4；
4. V3.7 Rotated Physical Memory Field；
5. V3.9 Bounded Approximate Coverage；
6. V3.10 Durable Capture / Async Absorption；
7. V3.11 Rev5；
8. CURRENT_STATUS；
9. canonical Module Progress Ledger；
10. 本任务书；
11. A/O/L/D charters；
12. 根目录 AGENTS.md。
```

冲突优先级：

```text
原始用户/assistant Evidence不丢
> 用户scope隔离
> 真实产品链路
> LLM语义/Core几何边界
> Architecture is the Index
> single-entry
> Prompt有界
> 离线fixture便利。
```

---

# 6. `AGENTS.md` 更新要求

至少加入：

```text
- 53182a4 is an offline run-scoped tool checkpoint, not Provider or semantic product validation.
- Every visible user/assistant turn is durably Captured even when Nollm Recall was used.
- Recall use changes role-level absorption eligibility; it never deletes Raw Capture.
- User-originated text remains eligible in mixed Recall/new-fact turns.
- Memory-derived assistant text may be context-only or ineligible as a new proposition source.
- Capture eligibility metadata is durable and hook-order independent.
- A Surface is routing-only. It must not expose complete Statement bodies from multiple Localities.
- Full Statement content is returned only after one entry is selected by Recall or same-entry expansion.
- Surface-only model answers are invalid product evidence.
- Target-hidden tests must verify that target content is absent from routing cards.
- Main-agent operation scope uses the actual Host-derived scope or an explicitly enforced single-scope profile.
- Real Provider Writer and real main-agent Host execution are mandatory in this task.
- Deterministic geometry fixtures remain conformance, not semantic product evidence.
- Do not modify Core or add a new memory architecture.
```

---

# 7. 全部模块任务前完成度

审核后基线：

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 93% | 中高 | V3.9几何、realized Junction、runtime完整性 | 本任务仅回归 | 否 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes | 增量/version | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | sink隔离 | metrics | 否 |
| ACCESS | `IMPLEMENTED` | 95% | 中高 | provenance、stale plan、bounded Locality | routing Surface投影合同 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 90% | 中 | run-scoped工具状态机、Profile | Raw Capture回退、Surface泄露、无Live | 是 |
| LAB | `IMPLEMENTED` | 89% | 中 | predeclared deterministic fixture | 无真实语义选择、NONE、visible answer | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 92% | 中 | shadow/active配置 | active-memory未实装验证 | 是 |

---

# 8. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付 | 剩余限制 |
|---|---:|---:|---:|---|---|
| CORE | 93% | 93% | 0% | 完整回归 | 多层、Stitch |
| SNAPSHOT | 50% | 50% | 0% | 回归 | 增量 |
| TRACE | 40% | 40% | 0% | 回归 | metrics |
| ACCESS | 95% | 98% | +5%向量 | routing-only投影、role-aware来源合同 | 长期规模 |
| HISTORY | 10% | 10% | 0% | 无 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无 | 暂停 |
| OPENCLAW | 90% | 97% | +15%向量 | durable turn、真实tool/Provider闭环 | 多Host |
| LAB | 89% | 97% | +15%向量 | 真实语义target/NONE/echo证据 | 长期统计 |
| DISTRIBUTIONS | 92% | 96% | +5% | active-memory实装Profile | 正式发行 |

不得写永久 100%。

---

# 9. Gate 0：状态和反例固化

工作：

```text
核验Bundle/HEAD/clean；
更新AGENTS/ACTIVE_PROJECT/CURRENT_STATUS/Ledger；
记录implementation checkpoint与delivery HEAD；
将53182a4重定性为offline checkpoint；
将OpenClaw/Lab/Distribution完成度下调；
加入以下自动反例：
  Recall成功→Raw Capture数量0；
  mixed new fact + Recall→新用户事实丢失；
  80 Statement Surface可见80条完整事实；
  Surface-only回答不产生recall-satisfied；
  configured scope与Host-derived scope不一致；
保护性commit。
```

Gate 0 PASS：

```text
状态不再宣称Provider或真实semantic closure；
P0反例在旧实现上稳定失败；
任务范围仍不包含Core。
```

建议提交：

```text
checkpoint(aold): record durable-turn and routing-surface blockers
```

---

# 10. Gate A：始终持久化 Raw Turn

## 10.1 不可协商合同

每个成功可见 assistant delivery：

```text
exact user bytes；
exact assistant bytes；
session/run/scope/workspace身份；
时间；
Provider/model；
visible endpoint；
```

都必须进入 immutable Capture。

以下情况也不能跳过：

```text
主代理使用Recall；
主代理只查看Surface；
主代理执行expand；
主代理选择NONE；
Pending context存在；
回答包含旧记忆；
回答同时包含用户新事实。
```

## 10.2 删除整轮 Capture suppression

活动路径不得再执行：

```text
recallSatisfiedRuns
→ publishCapture return undefined。
```

`recallSatisfiedRuns` 可以改为：

```text
runMemoryUseState
```

只用于生成 durable absorption directive。

## 10.3 角色级吸收资格

为 Capture 增加版本化、可重开合同，例如：

```text
CaptureAbsorptionDirective：
  capture_id；
  run identity；
  user_role_mode：
    source；
  assistant_role_mode：
    source | context_only | memory_derived；
  memory_tool_actions：
    surface | recall | expand | none；
  selected entry ID digest；
  recalled Statement IDs；
  directive_epoch_ms；
  finalized；
  schema_version。
```

Codex可选择：

```text
append-only sidecar；
Capture state event v2；
独立run directive；
等价可复算结构。
```

要求：

```text
Raw Capture本体仍不可变；
directive可幂等发布；
hook顺序不影响最终结果；
restart后worker可读取；
directive缺失时采用安全、文档化的默认；
不在Core持久化。
```

## 10.4 Writer来源规则

如果 assistant 由 admitted memory Recall 产生：

```text
assistant文本可作为理解当前对话的context；
不得单独作为新Statement的唯一source；
不得把召回旧事实的改写重新Admission。
```

user文本：

```text
始终保留为可能source；
是否形成Statement仍由Writer决定。
```

混合turn：

```text
新用户事实必须可Formation；
旧记忆回答不重复Formation。
```

不得用关键词或文本hash判断语义重复。

## 10.5 Hook顺序

必须验证：

```text
after_tool_call → message_sent → agent_end；
message_sent → after_tool_call → agent_end；
after_tool_call缺失；
message_sent缺失、只有agent_end；
重复message_sent/agent_end；
Gateway在directive finalization前停止。
```

worker只在 directive达到可处理状态后吸收，或采用可证明安全的默认。

## 10.6 Pending fallback

Raw Capture进入Pending后：

```text
仍可read-your-recent-writes；
memory-derived assistant部分必须标注来源；
不得让Pending fallback把旧记忆回答再次作为新事实证据。
```

Gate A PASS：

```text
Recall run的Raw Capture=1；
mixed user new fact可Admission；
memory-derived assistant重复Admission=0；
hook顺序和restart一致；
Capture前台0 Provider/bridge/Core。
```

建议提交：

```text
fix(openclaw): preserve every visible turn and mark role-level absorption origin
```

---

# 11. Gate B：Routing-only Surface

## 11.1 Surface内容分层

内部 private Surface 可以持有：

```text
完整 region/entry/Cell/Statement映射；
用于后续校验。
```

主代理可见 Surface 只返回 routing cards：

```text
operation_id；
region_id；
entry_id；
routing_anchor_utf8；
source_cell_count；
native_atom_count；
has_children；
routing_only=true；
answer_from_surface=false。
```

禁止直接返回：

```text
完整 representative_statements 数组；
完整 support-entry Statement数组；
Statement provenance；
一个region的全部事实；
多个region的完整答案材料。
```

## 11.2 Routing anchor

Routing anchor 必须：

```text
operation-local；
由现有Statement/几何确定性导出；
不持久化；
每region最多一个；
字符严格受限；
只用于区分Locality；
不宣称事实证据。
```

初始建议预算：

```text
每anchor <= 96字符；
每page routing text <= 3000字符；
可见JSON <= 8192 bytes；
regions <=32；
Prompt-bounded完整覆盖。
```

Codex可实测调整，但必须显著低于当前：

```text
80完整Statement / 24736 bytes。
```

## 11.3 字段完整

不得为了缩小Surface：

```text
stable-key截前N；
语义抽样；
embedding/query过滤；
遗漏top-level region。
```

如果一页无法容纳：

```text
使用更粗Surface order；
或progressive open_region；
每页包含当前parent全部children；
explicit overflow。
```

## 11.4 选择入口

Surface只允许：

```text
选择一个region/entry；
继续打开一个region；
NONE。
```

完整 Statement 内容只由：

```text
recall；
same-entry expand。
```

返回。

## 11.5 Target-hidden

产品因果测试必须证明：

```text
expected target Statement content
不在任何routing anchor中；
主代理Surface后不能直接回答；
执行recall后才获得target；
path非空；
一个entry。
```

## 11.6 Surface-only行为

如果主代理只执行Surface便回答：

```text
该样本判定为invalid_memory_use；
不计Recall成功；
Raw Capture仍保存；
assistant标routing-preview-derived或未知；
不得将其作为产品能力证据。
```

工具description和Host提示必须明确：

```text
Surface是选路地图，不是答案；
要使用记忆必须recall或none。
```

Gate B PASS：

```text
80事实Surface可见完整Statement=0；
routing anchor总字符/bytes达标；
target内容隐藏；
default Recall仍<=4/3000；
single-entry不回退。
```

建议提交：

```text
fix(access): project complete Atlas into routing-only main-agent cards
```

---

# 12. Gate C：真实 Host Scope 与 operation 真值

## 12.1 Scope身份

`before_tool_call` 必须使用与 Capture/Pending 相同的：

```text
captureScope(ctx, configuredScope)
```

或等价统一resolver。

Operation绑定：

```text
session；
run；
actual scope；
workspace；
toolCall；
Profile；
Atlas/Core identity。
```

trace和Evidence也使用相同scope identity。

## 12.2 当前部署模式

Codex必须明确选择并实现：

### 单scope模式

```text
active-memory配置一个allowed scope；
检测到其他scope：
  tool unavailable；
  Capture仍独立保存；
  明确诊断；
  不读取共享memory。
```

### scope分区模式

```text
由scope确定独立memory workspace；
不同scope不得共享Statement/Handle/Core；
安装/诊断可复算。
```

本任务不要求建设通用多租户系统；可以选择单scope模式完成，但不能继续声称动态scope隔离而实际共享字段。

## 12.3 Tool binding真实Host验证

冻结真实事件：

```text
before_tool_call；
tool execute；
after_tool_call；
message_sent；
agent_end；
operation cleanup。
```

确认SDK真实hook顺序和context字段，不仅依赖模拟测试。

## 12.4 状态泄漏

处理：

```text
after_tool_call缺失时binding TTL；
successful call set清理；
agent_end/session_end/gateway_stop；
tool异常；
run取消。
```

Gate C PASS：

```text
scope事实与Capture一致；
跨scope读取被拒；
operation无长期泄漏；
真实Host hook链可复算。
```

---

# 13. Gate D：Profile 与真实 Active-memory 安装

## 13.1 新工作区

创建：

```text
nollm-aold-routing-only-real-main-agent-v9
```

旧工作区全部保留。

## 13.2 安装

使用明确命令：

```powershell
.\scripts\install.ps1 `
  -Profile active-memory `
  -StatementWorkspace <v9_workspace> `
  -MemoryWorkspace <v9_workspace>
```

记录：

```text
最终OpenClaw config；
Profile；
write_mode；
workspace；
capture spool；
Provider/model；
tool allowlist；
legacy Reader；
Evidence path；
Gateway状态。
```

## 13.3 Diagnose

必须输出：

```text
profile=active-memory；
write_mode=statement-store；
plugin loaded；
Capture enabled；
worker enabled/alive；
main-agent tool enabled；
legacy_reader=false；
actual scope mode；
workspace；
pending；
last admitted；
Evidence mutable path；
operation TTL；
routing Surface budgets。
```

## 13.4 回退

验证：

```text
切换shadow不删除已有数据；
重新active后可reopen；
可关闭插件；
旧OpenClaw原始数据不变。
```

Gate D PASS：

```text
active-memory真实安装；
不是只修改manifest；
Gateway重启后诊断一致。
```

建议提交：

```text
test(distributions): validate active-memory installation and scope profile
```

---

# 14. Gate E：真实 Provider Writer 与 durable Admission

## 14.1 普通自然聊天

至少完成：

```text
20条 Provider-backed durable Statements；
至少12个普通自然对话turn；
至少3个multi-Statement turn；
至少2个reuse；
至少2个revision_current确认；
至少2个no_memory或defer；
至少3个independent_seed；
至少5个related_growth；
至少3个混合“新用户事实 + 旧记忆问题”turn；
Gateway restart。
```

不得在用户可见消息中使用：

```text
请输出JSON；
选择candidate；
写入Nollm；
指定坐标；
调用nollm_memory；
返回某action。
```

“请记住”可作为单独显式记忆场景，但不得冒充普通聊天。

## 14.2 Capture证据

每个turn必须冻结：

```text
Raw Capture exact user/assistant bytes；
absorption directive；
user/assistant role mode；
tool usage；
Provider/model；
Capture publish latency；
state events；
Statement/provenance；
Handle/Atom；
reopen。
```

## 14.3 Writer指标

记录：

```text
first-attempt；
format repair；
semantic retry；
quote not found/ambiguous；
resolved reference；
final outcome；
calls；
Provider latency；
backlog；
duplicate/orphan。
```

不设伪精确永久阈值，但所有数字必须可复算。

## 14.4 混合turn硬Gate

至少三个样本：

```text
用户陈述一个新事实
+
询问一个旧记忆。
```

要求：

```text
Raw Capture存在；
新用户事实可Admission；
旧记忆回答不重复Admission；
same-run directive正确；
next run仍可Capture。
```

Gate E PASS：

```text
Provider-backed Statement >=20；
Raw Capture丢失=0；
memory echo duplicate=0；
provenance reopen；
worker backlog收敛或诚实IN_PROGRESS。
```

---

# 15. Gate F：真实主代理 Routing→Recall

## 15.1 预声明查询矩阵

在运行前登记：

```text
query_id；
自然query；
expected target Statement IDs；
allowed supporting IDs；
forbidden IDs；
target-hidden要求；
expected NONE；
是否需要expand；
预期scope/session。
```

不得从Recall结果中选择target。

最低：

```text
10 relevant；
5 relation-entry target-hidden；
5 dense hidden-target；
5 NONE/unrelated；
3 same-entry expand；
3 mixed new-fact+Recall；
2 cold restart；
2 concurrent sessions。
```

## 15.2 工具序列

真实观察主代理：

```text
surface；
可选open region；
recall one entry；
可选same-entry expand；
或none；
最终自然回答。
```

必须记录：

```text
toolCallId；
operation；
run/session/scope；
routing cards；
selected region/entry；
default/expanded locality；
visible answer。
```

## 15.3 不允许

```text
脚本替主代理选择entry；
直接把正确entry注入；
从Surface preview回答并计成功；
恢复hidden Reader；
Python语义路由；
多入口合并。
```

## 15.4 结果指标

可复算：

```text
correct entry；
target reach；
forbidden leakage；
NONE；
target-hidden reach；
default result count/chars；
expanded reach；
single-entry；
surface-only invalid count；
hidden child calls；
query→first tool；
tool roundtrip；
query→visible answer；
visible answer correctness。
```

## 15.5 Capture闭环

每个Recall run同时检查：

```text
Raw Capture存在；
assistant role标memory-derived；
用户新事实不丢；
assistant echo不Admission。
```

Gate F PASS：

```text
真实main-agent query >=15；
真实Recall/正确NONE >=10；
Surface-only答案不计成功；
target-hidden内容不在routing card；
hidden child calls=0；
single-entry=100%；
restart后重复。
```

建议提交：

```text
test(openclaw): validate routing-only native Recall in real main-agent runs
```

---

# 16. Gate G：规模与选择性

## 16.1 确定性压力场

继续使用60～100 Statement fixture，但重新测量：

```text
Surface routing card count；
routing chars/bytes；
完整Statement泄露数；
default Locality；
expand；
forbidden leakage；
restart；
Python function latency。
```

硬Gate：

```text
Surface完整Statement泄露 = 0；
routing text <= active budget；
default p95 <=4或5；
default chars p95 <=3000；
single-entry=100%。
```

## 16.2 Provider-backed规模子集

在真实v9字段至少形成：

```text
20+ Statements；
多个Localities；
dense Locality；
unrelated seeds；
三种关系方向。
```

真实主代理完成预声明query。

## 16.3 解释边界

分开报告：

```text
Geometry function conformance；
Routing Surface conformance；
Provider Writer；
Main-agent semantic selection；
Visible answer。
```

不得将任何一层的成功冒充另一层。

---

# 17. Gate H：回归、Evidence 与交付

## 17.1 回归分组

至少：

```text
Group 1：
Core/Snapshot/Trace；

Group 2：
Access；

Group 3：
OpenClaw Python；

Group 4：
OpenClaw Node/build/plugin check；

Group 5：
Lab active；

Group 6：
M0/Manifest/boundary。
```

每组记录：

```text
命令；
环境；
pass/fail；
duration；
warnings；
timeout。
```

不得只运行一个超时总命令后宣称全量通过。

## 17.2 主 Evidence

```text
validation/aold_routing_only_real_main_agent_live_20260722.jsonl
validation/aold_routing_only_real_main_agent_live_summary_20260722.json
```

必须绑定：

```text
active-memory config；
Host/version；
Provider/model；
natural chats；
Raw Captures；
absorption directives；
Writer/Cartographer raw attempts；
durable outcomes；
routing Surface；
tool sequence；
declared targets；
Recall results；
visible answers；
latency；
restart；
scope；
freeze。
```

## 17.3 Freeze

```text
停止或旋转live writer；
确认mutable文件稳定；
冻结exact bytes；
line/bytes/SHA；
Summary；
Report；
Manifest；
Git blob复算；
commit；
Bundle。
```

## 17.4 主报告

```text
docs/project/AOLD_ROUTING_ONLY_REAL_MAIN_AGENT_LIVE_REPORT.md
```

必须直接回答：

```text
Raw Capture是否每turn存在；
如何防assistant memory echo；
Surface暴露多少routing信息；
完整Statement泄露是否为0；
真实scope；
Provider Writer；
主代理工具；
target/NONE/leakage；
混合turn；
可见延迟；
active-memory配置；
测试；
实际向量；
限制。
```

## 17.5 HEAD绑定

最终文档至少分别记录：

```text
implementation/evidence checkpoint；
delivery HEAD；
Bundle HEAD；
Bundle SHA。
```

如果报告无法自引用自己的commit：

```text
使用精确tag；
或在final reply和status中登记delivery HEAD；
不得只留下parent实现HEAD而不说明。
```

---

# 18. 自动测试矩阵

## 18.1 Capture/OpenClaw Node

```text
Recall run仍生成Raw Capture；
Surface-only run生成Raw Capture；
mixed user fact + Recall；
assistant memory-derived directive；
hook order permutations；
duplicate hooks；
restart directive；
same-run与next-run；
concurrent run；
scope mismatch；
before/after tool真实字段；
TTL/cleanup。
```

## 18.2 Writer/Worker

```text
user source eligible；
assistant source；
assistant context-only；
assistant memory-derived；
old answer not re-admitted；
new user fact admitted；
multi-Statement；
revision/reuse；
Pending；
retry；
directive missing/corrupt；
idempotency。
```

## 18.3 Routing Surface

```text
80 Statement field；
complete region coverage；
zero full Statement bodies；
one routing anchor/region；
bytes/chars；
target-hidden；
open region；
entry uniqueness；
stale Policy；
overflow；
one final entry。
```

## 18.4 Main-agent Live

```text
surface→recall；
surface→none；
surface→expand；
surface-only invalid；
target-hidden；
dense；
NONE；
mixed new fact；
restart；
concurrent sessions；
visible answer；
no hidden child。
```

## 18.5 Regression

```text
Core runtime/Junction；
Access rollback/provenance/cartography；
Rev3/Rev4 relation growth；
Rev5 quote/stale/locality；
Manifest/boundary；
active profiles。
```

---

# 19. 性能与调用边界

保持：

```text
Capture前台：
0 Provider；
0 bridge；
0 Core；
p95目标<=100ms；

Writer：
common 1 call/batch；
格式修复有界；

Cartographer：
one session/batch；
Prompt<=64KB；

Main-agent Recall：
独立hidden child calls=0；
one final entry；
default<=4 Statements/3000 chars；
same-entry expand<=8/6000。
```

新增目标：

```text
Surface routing JSON <=8192 bytes；
routing text <=3000 chars；
完整Statement泄露=0。
```

测量：

```text
Capture publish；
surface tool roundtrip；
recall tool roundtrip；
expand tool roundtrip；
main-agent Provider；
query→visible；
worker backlog。
```

这些是当前环境观察，不写永久 SLA。

---

# 20. 实际停止条件

只有以下情况停止：

```text
OpenClaw SDK不能提供任何可用的tool/run lifecycle；
Raw Capture与role directive无法在不破坏旧Capture的情况下并存；
routing-only Surface完全无法让主代理选择入口；
active-memory会损坏旧OpenClaw/Nollm数据；
真实Provider长期不可用；
Statement/Handle/Core出现不可恢复损坏；
产品成功必须依赖query索引、多入口或第二Reader模型。
```

普通 Prompt、tool description、JSON、hook顺序、测试、性能和Evidence问题直接修复继续。

即使停止：

```text
提交真实进展；
clean；
完整Bundle；
状态IN_PROGRESS；
不补造。
```

---

# 21. 完成状态

只有全部闭合才允许：

```text
DURABLE_TURN_ROUTING_ONLY_REAL_MAIN_AGENT_MEMORY_VALIDATED_AT_<HEAD>
```

必须同时满足：

```text
每个可见turn Raw Capture存在；
Recall mixed turn用户事实不丢；
memory-derived assistant重复Admission=0；
Surface完整Statement泄露=0；
routing budget达标；
实际scope隔离；
active-memory真实安装；
Provider-backed Statements>=20；
真实main-agent工具序列；
真实target-hidden；
真实NONE；
真实leakage；
真实expand；
restart；
concurrent sessions；
hidden child calls=0；
single-entry=100%；
visible answer；
分组测试；
Manifest/boundary；
clean；
完整Bundle。
```

否则：

```text
AOLD_ROUTING_ONLY_REAL_MAIN_AGENT_LIVE_IN_PROGRESS_AT_<HEAD>
```

---

# 22. 明确非目标

```text
Core修改；
Coverage/Junction调整；
multi-cell；
多物理层；
Stitch；
多Chart；
持久Lens；
Topic/Entity；
query/fact entry map；
vector/graph/embedding；
multi-entry Recall；
Provider更换；
PB；
正式发布；
History/Audit产品；
外部消息队列或数据库。
```

---

# 23. 建议提交序列

```text
checkpoint(aold): record durable-turn and routing-surface blockers
fix(openclaw): preserve every visible turn with role-level absorption origin
fix(access): expose routing-only complete Atlas cards
fix(openclaw): bind native operations to actual Host scope
test(distributions): validate active-memory installation
test(aold): run Provider Writer and routing-only main-agent Recall
docs(aold): record durable real main-agent memory capability
```

---

# 24. Git Bundle

建议文件名：

```text
nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_<shorthead>.bundle
```

仓库外执行：

```powershell
git bundle create ..\nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_<shorthead>.bundle --all
git bundle verify ..\nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_<shorthead>.bundle
Get-FileHash ..\nollm_aold_role_aware_capture_routing_only_main_agent_live_20260722_<shorthead>.bundle -Algorithm SHA256
```

---

# 25. 最终回复要求

最终只报告：

```text
branch / implementation HEAD / delivery HEAD；

Capture：
  visible turns；
  Raw Capture count；
  role directives；
  mixed-turn user facts；
  echo duplicates；

Surface：
  regions；
  routing cards；
  visible bytes/chars；
  full Statement leakage；
  target-hidden；

Provider Writer：
  natural turns；
  Statements；
  retry；
  durable/provenance；
  backlog；

Main-agent Recall：
  tool sequences；
  scope；
  target reach；
  leakage；
  NONE；
  default/expand；
  restart/concurrency；
  hidden children；
  visible latency；

Engineering：
  test groups；
  Manifest；
  boundaries；
  actual vector/completion；
  limitations；

Bundle：
  filename；
  SHA-256。
```

---

# 26. 最终任务概括

```text
53182a4 已经把主代理工具的离线状态机做得更可靠，
但尚未运行真实主代理和Provider。

更重要的是，当前防回声方法会删除整轮Raw Capture，
而当前Surface又把多区域完整事实提前交给主代理。

这导致两种都不可接受的行为：

真正调用Recall：
  用户原话也被丢掉；

只看Surface回答：
  绕过单入口并把旧答案再次吸收。

本任务不再扩张几何。
先保证每轮原始对话永远保存，
再用角色级吸收指令防回声；
把Surface收窄成routing-only地图，
只有选定一个entry后才返回完整事实；
最后在active-memory和真实OpenClaw中完成真正的用户链路。
```

> **原始对话必须永远保留；几何地图只能帮助选路；完整记忆只能从一个选定入口读取。**
