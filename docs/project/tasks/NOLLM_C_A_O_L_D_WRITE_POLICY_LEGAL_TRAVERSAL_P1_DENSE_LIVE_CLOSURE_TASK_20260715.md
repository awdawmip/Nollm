# Nollm C/A/O/L/D：活动写入 Policy、合法 Surface Traversal、P1 与密集 Live 闭环任务书

**任务文件名**：`NOLLM_C_A_O_L_D_WRITE_POLICY_LEGAL_TRAVERSAL_P1_DENSE_LIVE_CLOSURE_TASK_20260715.md`  
**日期**：2026-07-15  
**性质**：V3.9 真实 OpenClaw 主链路收口与状态所有权纠偏；不是 Stitch、换层语义 Placement、PB 长跑、精确 Coverage 或正式发布任务  
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**输入 Bundle**：`nollm_caold_broad_residue_safe_field_dense_locality_in_progress_20260715_2e779764.bundle`  
**输入 Bundle SHA-256**：`2b4b51afa508d00e67e117475798b1ec83f99c2bfcb0a873c63f60eb527e7f35`  
**输入分支**：`codex/caold-broad-residue-safe-field-dense-locality`  
**输入 HEAD**：`2e779764cde6fbb1ef228444edfd55bd157b2b52`  
**输入状态 Tag**：`CAOLD_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_IN_PROGRESS_AT_2e779764cde6fbb1ef228444edfd55bd157b2b52`  
**建议工作分支**：`codex/caold-write-policy-legal-traversal-p1-dense-live-closure`  
**主执行环境**：Windows 10/11、PowerShell、Python 3.13、Node 24、当前真实 OpenClaw 环境  
**交付**：所有真实进展提交；最终工作树干净；仓库外单一完整历史 Git Bundle；未完成亦交付 `IN_PROGRESS` Bundle  
**插件最终状态**：保持安装和启用  
**数据最终状态**：旧 V3.8/V3.9 及 Broad/Dense 工作区、Statement、HandleBinding、Core canonical state、失败 P1 Statement 和 OpenClaw 配置全部保留；不得清空、覆盖或静默删除  

---

# 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
分离 Core canonical 存储域与 Access/OpenClaw 活动语义写入 Policy；
由 Access 生成状态相关的完整合法动作集合；
OpenClaw 只向真实 LLM 展示当前状态确实可执行的动作；
对无效模型动作进行有限、无状态污染的同模型纠错；
在 physical-entry 候选全局唯一时允许机械单例消解，减少无语义选择的模型调用；
复用失败 P1 已形成但未绑定的 Statement，闭合 Placement→Core write→重启→新 Session Recall；
随后完成真实密集主题的自然积累和单入口跨事实 Recall。

范围变化：
V3.9 有界近似 Coverage、Broad calibration、安全半径、Lazy Surface、单入口 Recall 继续作为活动基线；
本任务不改变 Δθ=22.5°、β=2^(1/4)、β²=√2、K=96、min_hit=1；
不进入 Stitch、多物理层语义 Placement、多 Chart、持久 Surface cache、PB 长跑或精确 polygon 生产路径。
```

## 0.1 Gate 向量复述

每个 Gate 开始记录：

```text
当前预计向量：
C +5 | S 0 | T 0 | A +5 | H 0 | U 0 | O +5 | L +5 | D +5

当前主方向：
状态所有权纠偏 → 合法动作合同 → 有限纠错 → 单例机械消解 → P1 恢复 → 密集 Live。
```

每个 Gate 结束记录：

```text
实际受影响模块；
预计与实际偏差；
是否出现超过 5% 的模块偏差；
是否新增 canonical state、持久入口或跨模块依赖；
是否把模型行为结果错误升级为架构不变量；
是否误入 Stitch、换层语义 Placement、语义索引或外围治理。
```

不得静默扩大任务范围。

---

# 1. 本任务的可验证结果

最终目标链路：

```text
2e779764 Broad/Dense IN_PROGRESS checkpoint
→ 修复最终 Manifest 和当前状态锚点
→ Core 只拥有 canonical 存储地址合法性
→ Access/OpenClaw 独占当前活动语义写入 Policy
→ Surface/Physical page 提供状态相关 legal_actions
→ Prompt 只列出当前合法动作
→ 无效 LLM 动作有限纠错且不改变 Traversal/Statement/Handle/Core
→ 单一 physical entry 自动机械消解；多候选仍由真实 LLM 选择一个
→ 复用既有失败 P1 Statement 或重新形成唯一新 Statement
→ Placement 成功写入并绑定
→ Gateway 重启
→ 新 Session 单入口 Recall P1
→ 真实密集主题形成 truncated Locality
→ 新 Session 单入口回答跨多条事实问题
→ R1/R2/R3 不回退
→ clean tree + 完整历史 Bundle。
```

完整通过至少满足：

```text
1. 最终 HEAD ownership manifest 与全部 tracked files 一致；
2. `validation/caold_openclaw_live_validation.json` 不再遗漏；
3. Core mutation 不再承担 Access 的当前语义写入层/半径 Policy；
4. Access/OpenClaw 当前语义写入只允许 default_dream_v1/default/layer0/phase=null 且在 active writable radius 内；
5. storage-only 旧状态继续可重开，研究性 Core fixture 可在 storage contract 内使用非 layer0；
6. root Surface Prompt 不出现 return_to_parent；
7. 无 continuation 时不出现 continue_page；
8. hard-max Order 不出现 request_coarser_surface；
9. Order 0 才出现 open_physical_entries；
10. physical-entry page 只列当前合法动作；
11. 无效 action/candidate/JSON 经有限纠错后可继续，且失败时零写入；
12. total physical entry count 恰为 1 时不再调用一次无语义选择的 LLM；
13. 多 physical entry 时仍由真实 LLM 从已展示 candidate_id 中选择恰好一个；
14. P1 写入、绑定、重启和新 Session Recall 闭合；
15. 密集主题真实 Statement 数达到能产生 truncated Locality 的程度，并完成新 Session 单入口跨事实 Recall；
16. 无 Cursor、select_entries、Topic/Source/Entity route、graph/vector/embedding 或 Python 语义 Placement；
17. 所有真实进展 commit，工作树 clean，完整历史 Bundle 验证通过。
```

若 Provider 无法完成密集 Live，但 P1 已闭合，允许交付 `IN_PROGRESS`，不得补造密集结果。

---

# 2. 活动依据与优先级

执行前按顺序读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_7_ROTATED_MULTI_SCALE_PHYSICAL_MEMORY_FIELD_20260714.md
3. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_9_BOUNDED_APPROXIMATE_HEX_COVERAGE_20260715.md
4. docs/project/NOLLM_ROUTE_BOOK_V3_7_ROTATED_PHYSICAL_FIELD_SINGLE_ENTRY_RECALL_20260714.md
5. docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md
6. docs/project/ACTIVE_PROJECT.md
7. docs/project/NOLLM_CURRENT_STATUS.md
8. docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
9. 本任务书
10. C/A/O/L/D 模块章程
11. 根目录 AGENTS.md
```

冲突顺序：

```text
第一性原理
> V3.7 硬物理、Layer/Order 分离与单入口架构
> V3.9 有界近似 Coverage、Lazy Surface 和误差 Policy
> 本任务的状态所有权、合法动作、纠错和 Live 变化量
> 当前状态
> 历史任务、历史报告和历史 Tag。
```

开始执行时必须更新根目录 `AGENTS.md`，至少加入：

```text
- Core storage validity and Access/OpenClaw active semantic write policy are different contracts.
- Active semantic Placement remains default_dream_v1/default/layer0/phase=null and active writable radius only.
- Surface prompts must be generated from state-derived legal_actions; never advertise impossible actions.
- Invalid model navigation is recoverable only through a bounded operation-local correction loop with zero state mutation.
- Mechanical singleton physical-entry resolution is allowed only when the total visible candidate universe contains exactly one entry; otherwise the LLM selects one visible candidate.
- Existing failed P1 Statement/Evidence must be reused when valid; do not create duplicate facts merely to retry Placement.
- Provider latency and model failures must be reported separately from Surface/Core timing.
- No Stitch, multi-layer semantic Placement, Cursor, semantic route, graph/vector/embedding, exact polygon production path, or persistent traversal state.
- Final delivery commit must be included in the ownership manifest before bundle creation.
```

---

# 3. 输入基线与独立审核事实

## 3.1 Git 基线

```text
Bundle SHA-256:
2b4b51afa508d00e67e117475798b1ec83f99c2bfcb0a873c63f60eb527e7f35

Branch:
codex/caold-broad-residue-safe-field-dense-locality

HEAD:
2e779764cde6fbb1ef228444edfd55bd157b2b52

Tag:
CAOLD_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_IN_PROGRESS_AT_2e779764cde6fbb1ef228444edfd55bd157b2b52

Working tree:
clean

Bundle:
complete history, verified
```

## 3.2 已独立复现的工程结果

```text
Core + Snapshot + Trace + Access + OpenClaw Python:
199 passed, 8 warnings

Safe writable field runner:
passed

Dense Surface runner:
passed

Dense single-entry Recall runner:
passed

Natural multi-entry observation runner:
passed
```

独立 Broad Oracle 复核，使用两个不同于仓库正式矩阵的种子，各 384 exact fixtures：

```text
seed 0x12345678:
missed p99 ≈ 1.1604%
TV p95 ≈ 2.0185%
TV p99 ≈ 2.8323%
dominant agreement ≈ 99.48%
false max = 0
fanout max = 7

seed 0xDEADBEEF:
missed p99 ≈ 1.2129%
TV p95 ≈ 2.1077%
TV p99 ≈ 2.7229%
dominant agreement ≈ 98.44%
false max = 0
fanout max = 7
```

结论：

```text
min_hit=1 Broad Policy 具有真实、可复现的独立支持；
本任务不重开 Coverage 方法选择；
Exact Oracle 继续只属于 Lab。
```

## 3.3 Safe field 独立复核

对 active writable radius 外缘附近 20,000 个随机地址执行两步 `coverage_down`：

```text
最大 target radius = 1,692,586,957
storage margin = 454,896,690
失败数 = 0
```

但发现层维度合同不完整：

```text
layer -64 可以写入，但 coverage_up unsupported；
layer  64 可以写入，但 coverage_down unsupported；
当前 active semantic Placement 实际始终为 layer 0。
```

因此，本任务不为尚未启用的多层语义写入建设复杂闭合域；应明确：

```text
Core canonical storage layer domain = [-64,64]；
Access/OpenClaw active semantic write layer Policy = 0；
Coverage 对边界层按请求方向明确 Unsupported；
不得把 Access 当前 Policy 强塞为 Core 通用 mutation 限制。
```

## 3.4 已验证并应保留

```text
Δθ=22.5°、β=2^(1/4)、β²=√2；
K=96 Q40 bounded approximate Coverage；
min_hit=1 Broad Policy；
生产无 Decimal/polygon/sin/cos；
storage radius 与 active writable radius 分离；
Lazy Surface；
GeometryAddress / SurfaceAggregateAddress 分离；
physical-entry 候选页；
单入口 Recall；
无 Cursor/select_entries/semantic route；
300-cell、1000-atom structural fixtures；
R1 Alpha、R2 Office、R3 NONE；
插件 0.11.0 和工作区非破坏保留。
```

## 3.5 必须修正的事实

### 3.5.1 Manifest 再次遗漏最终 Live 文件

最终 HEAD 实际：

```text
Git tracked files = 1854
Manifest rows     = 1853
Missing:
validation/caold_openclaw_live_validation.json
```

因此输入报告中的最终治理通过不能在 HEAD `2e779764` 上复现。

### 3.5.2 P1 失败来自 Prompt 广告了非法动作

真实 P1 Placement 在 root Surface 返回：

```text
action = return_to_parent
error  = Surface traversal has no parent
result = invalid_surface_traversal
Core writes = 0
```

当前 `_traversal_prompt()` 无论当前是否存在 parent，都列出：

```text
return_to_parent
```

这是系统向模型提供了非法选择，不应把责任归为模型质量。

### 3.5.3 无效导航被当成终局失败

当前行为：

```text
无效 action/candidate
→ bridge error
→ 本次 Placement/Recall 直接 defer/结束
```

正确行为应是：

```text
无状态 mutation 的校验失败
→ 同一 page/state 生成一次精确纠错 Prompt
→ 只列 legal_actions
→ 有限重试
→ 超限后 defer/zero-write。
```

### 3.5.4 physical-entry 单例仍消耗一次模型调用

若 physical-entry 全部候选总数恰为 1：

```text
不存在语义选择；
继续调用 LLM 只增加延迟和失败面。
```

允许机械单例消解并不等于 Python 语义 Placement，因为系统没有在多个语义候选中做选择。

### 3.5.5 Dense Live 与新 P1 未闭合

```text
新 P1 Formation 已形成 Statement dream:b93c...5745；
Placement 因 root 非法 return_to_parent 失败；
P1 retry Provider timeout；
restart Recall 选错 Alpha Locality；
dense coral Live 未形成 Statement 或可见回答。
```

失败证据必须保留并用于恢复，不能重新开始时丢弃。

---

# 4. 任务开始前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 当前主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 90% | 高（有限域） | 快速 Coverage、safe radius、Lazy Surface、canonical state | Access Policy 混入 Core mutation；边界层合同不清 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes 回归 | 版本迁移、增量 Snapshot | 否，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 状态隔离 | 长期性能观察 | 否，仅回归 |
| ACCESS | `CAPABILITY_VALIDATED` | 90% | 中高 | Surface、physical entry、单入口 Recall、原子协调 | legal_actions 未成为单一权威；活动写 Policy 归属不纯 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `CAPABILITY_VALIDATED` | 90% | 中高 | R1/R2/R3、隐藏注入、真实模型 | 非法动作被 Prompt 广告；无纠错；P1/dense Live 未闭合 | 是 |
| LAB | `IMPLEMENTED` | 95% | 高（结构 Gate） | Broad/safe/dense runners | 缺 Traversal 状态机和恢复矩阵 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 85% | 高 | 插件 0.11、Policy/schema | legal-action/singleton/retry contract 未版本化 | 是 |

说明：

```text
完成度相对当前活动章程；
不是永久完成度；
本轮不因 Broad Policy 已通过而继续提高 LAB 数字；
主要推进对象是主链路正确性和可用性。
```

---

# 5. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 90% | 95% | +5% | canonical storage 与 active semantic write Policy 分离；边界层行为如实 | Core/Access 独立 tests | 多层语义 Placement |
| SNAPSHOT | 50% | 50% | 0% | 无合同变化 | package regression | 增量 Snapshot |
| TRACE | 40% | 40% | 0% | 不建设 Trace 产品 | package regression | 长期观察 |
| ACCESS | 90% | 95% | +5% | state-derived legal_actions、active write Policy、singleton resolution contract | Access state-machine tests | 更复杂多层候选 |
| HISTORY | 10% | 10% | 0% | 无变化 | 章程 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 章程 | 暂停 |
| OPENCLAW | 90% | 95% | +5% | legal Prompt、bounded correction、P1/dense Live | Node/Python/Windows Live | Provider latency |
| LAB | 95% | 95% | +5%（能力深化，不抬高数字） | Traversal/recovery/dense live harness | deterministic runners | 长期模型统计 |
| DISTRIBUTIONS | 85% | 90% | +5% | Wire/Policy/schema/diagnose 更新 | plugin check | 正式发布 |

目标值仅为预测；Bundle 审核后必须回填实际值和实际推进向量。

---

# 6. 所有权与合同纠偏

## 6.1 Core canonical storage 合同

Core 继续负责：

```text
GeometryAddress 的 profile/chart/phase/layer/radius 基本合法性；
canonical Cell/Atom/Bridge state；
原子 mutation；
Coverage 对不支持 layer/direction/target 的明确失败；
不产生部分传播结果。
```

Core 不应继续拥有：

```text
当前 OpenClaw 语义 Placement 只能写 layer 0；
当前产品 active writable radius Policy；
当前 Host 是否允许 expand_surface；
当前插件的写入组合策略。
```

执行要求：

```text
从 Core mutation 通用路径移除 Access-specific active semantic write Policy；
Core 仍拒绝 GeometryAddress storage contract 以外的地址；
旧 storage-only state 继续可读、可重开；
研究性 Core fixture 可以在 storage contract 和支持 layer 内构造非 layer0 Atom；
不得因此开放 OpenClaw 多层语义 Placement。
```

## 6.2 Access 活动语义写入 Policy

Access 新增单一权威对象，建议：

```text
ActiveSemanticWritePolicy
```

至少包括：

```text
policy_id；
profile_id=default_dream_v1；
chart_id=default；
phase=null；
write_physical_layer=0；
active_writable_hex_radius=2^30-1；
max_coverage_down_steps=2。
```

Access 在以下入口统一验证：

```text
new/new_local；
move；
expand_surface；
revision 发生 move 时；
OpenClaw Placement candidate apply；
任何目标 Cell 写入决定。
```

禁止各路径复制不同校验逻辑。

## 6.3 Distribution 声明

插件 schema/manifest 明确声明：

```text
storage contract；
active semantic write policy；
write_physical_layer=0；
active writable radius；
Coverage method/Policy；
Traversal legal-action contract；
singleton physical-entry Policy；
invalid-decision retry limit。
```

Distribution 只声明，不实现逻辑。

---

# 7. Access 状态感知 legal_actions 合同

## 7.1 单一来源

合法动作集合必须由 Access 根据真实 page/state 生成，OpenClaw 不自行推断或硬编码完整集合。

建议新增：

```text
SurfaceTraversalCapabilities
PhysicalEntryTraversalCapabilities
```

或在 page mapping 中加入：

```text
legal_actions
```

每个动作可以包含：

```text
action name；
requires_candidate；
candidate_kind；
reason/availability flags（可选，非语义）。
```

## 7.2 Surface page 动作规则

只有满足条件才允许：

```text
continue_page：page.has_more=true；
open_surface_cell：order>0 且当前页至少一个 has_deeper_locality candidate；
open_physical_entries：order==0 且当前页至少一个可打开 candidate；
request_coarser_surface：order<hard_max_order；
return_to_parent：stack 非空；
none：Recall 始终允许；
defer：Placement/Recall 均允许。
```

不得把当前不可执行动作放进 Prompt。

## 7.3 Physical-entry page 动作规则

```text
continue_page：has_more=true；
return_to_parent：始终可以返回所属 Surface page；
select_entry：当前页至少一个 candidate；
none/defer：允许；
其他 Surface action 禁止。
```

## 7.4 Candidate 校验

LLM 只能选择：

```text
当前 page 已展示 candidate_id；
与 legal action 所要求 candidate_kind 一致；
未过期 operation/page state。
```

无效选择不得改变 Traversal state。

---

# 8. OpenClaw Prompt 与有限纠错

## 8.1 Prompt 生成

Prompt 的 Allowed responses 必须从 Access 返回的 `legal_actions` 生成。

禁止：

```text
固定列出 return_to_parent；
固定列出 continue_page；
固定列出 request_coarser_surface；
由 Node/Python 两处分别维护不同动作表。
```

Python bridge 可以负责把结构化 legal_actions 渲染为 Prompt；Node 只负责调用。

## 8.2 有限纠错合同

以下错误属于可纠正模型输出：

```text
非法 action；
当前状态不可用 action；
缺失/额外字段；
未展示 candidate_id；
错误 candidate kind；
可修复 JSON 外壳后仍不合规。
```

处理：

```text
保持同一 operation、同一 page、同一 Traversal state；
不递增几何下钻深度；
不写 Statement/Handle/Core；
生成 correction prompt：说明上次输出不可执行，并重新列出 legal_actions；
调用同一 Host 模型；
最多 2 次 correction；
超过上限后 Recall complete_none/defer，Placement defer；
主聊天继续。
```

不得：

```text
Python 替模型选择一个语义 candidate；
把非法 return_to_parent 自动改成某个 open action；
无限重试；
跨 Session 保存失败动作；
把 correction 做成持久治理系统。
```

## 8.3 Provider timeout

Provider timeout 与非法动作必须分开统计：

```text
invalid_decision_count；
correction_attempt_count；
correction_success；
provider_timeout_stage；
model_call_count；
model_time_ms。
```

Provider timeout 不得伪装为 Surface/Core 性能问题。

---

# 9. 单例 physical-entry 机械消解

## 9.1 允许条件

仅当同时满足：

```text
physical_entry_total_count == 1；
当前页面包含该唯一 candidate；
has_more == false；
candidate 仍在当前 operation/state 中有效；
没有其他物理入口可供语义选择。
```

系统可以机械选择该唯一 entry，并标记：

```text
resolved_singleton = true；
resolution_policy_id = mechanical_singleton_physical_entry_v1；
physical_entry_model_call_skipped = true。
```

## 9.2 禁止范围

若 total count > 1：

```text
真实 LLM 必须从已展示 physical candidate_id 中选择一个；
不得 stable-key min；
不得最高权重自动选；
不得一次选择多个；
不得保存上次选择。
```

## 9.3 为什么不属于 Python 语义 Placement

```text
候选宇宙只有一个；
不存在语义比较；
系统只是消除无选择意义的模型调用；
上层 Surface Cell 仍由 LLM 语义导航选择。
```

该规则必须标记为 `POLICY`，不是几何不变量。

---

# 10. P1 失败资产恢复与闭环

## 10.1 先盘点，禁止重复制造

在新工作区副本中记录：

```text
失败 P1 Statement ID；
Statement 文件 SHA；
是否存在 HandleBinding；
是否存在对应 Core Atom；
是否存在重复语义 Statement；
当前 Statement/Handle/Core count。
```

已知候选：

```text
dream:b93c2e97cba5e002236190b205742368f1008cca452abaca023b663619545745
```

若该 Statement 存在且未绑定：

```text
优先复用该 Statement 执行 Placement；
不得为了重试重新 Formation 同一事实；
成功后形成唯一 HandleBinding 和 Core Atom。
```

若不存在或内容不适合当前 P1：

```text
如实记录；
再通过正常聊天 Formation 一条新的唯一 P1；
避免重复旧事实。
```

## 10.2 P1 验收

必须记录：

```text
Formation/已有 Statement；
Surface pages；
legal_actions；
模型原始动作；
纠错动作（如有）；
singleton resolution（如有）；
Placement decision；
Core write count；
HandleBinding；
Gateway restart；
新 Session Recall entry/path/selected Statement；
主代理可见回答。
```

通过条件：

```text
恰好一个有效 P1 当前 Statement；
恰好一个当前 HandleBinding；
Core write 成功；
重启后新 Session 单入口 Recall 正确；
无 Cursor/entry hint；
失败尝试没有产生孤立 Atom 或重复绑定。
```

---

# 11. 真实密集主题 Live

## 11.1 目标

验证真实 MemoryStatement 密集而非仅结构 Atom 密集：

```text
同一主题 12～24 条独立、有意义、可回到 Evidence 的 Statement；
通过正常聊天和真实 LLM Formation/Placement 逐步积累；
形成至少一个 truncated Surface/physical-entry Locality；
新 Session 从单入口回答需要组合多条事实的问题。
```

主题可以继续使用 coral archive，也可以选择稳定、易区分的新主题；一旦开始不得中途更换以规避模型结果。

## 11.2 执行节奏

```text
每轮自然对话只增加少量独立事实；
复用已成功形成的 Statement，不清空重来；
每轮记录 Statement/Handle/Core 增量；
普通失败继续下一轮；
达到 truncated Locality 后停止无意义加量；
不要求一次调用生成 12～24 条。
```

## 11.3 Recall 验收

新 Session 提出一个需要组合至少 3 条事实的问题。

必须：

```text
从 query-agnostic Active Surface 开始；
一次 Traversal 最终一个 physical entry；
Recall 结果来自该 entry 的有界几何传播；
Recall Agent 选择多条相关 Statement；
主代理回答正确且不暴露 Nollm；
无 Topic/Source/Entity route；
无人工多入口扇出。
```

Provider 失败允许 `IN_PROGRESS`，但必须保留真实已形成数据和失败证据。

---

# 12. Timing 与运行证据

继续记录：

```text
surface_build_ms；
surface_order_count；
surface_projection_count；
surface_page_count；
physical_entry_resolution_ms；
physical_entry_model_call_skipped；
recall_core_ms；
formation_ms；
placement_subagent_ms；
placement_apply_ms；
recall_agent_ms；
model_call_count；
invalid_decision_count；
correction_attempt_count；
correction_success；
provider_timeout_stage；
total_operation_ms。
```

这些字段是当前主链路诊断，不建设新的 Trace 产品，也不成为用户功能。

---

# 13. 内部 Gate 与工作流

## Gate 0：活动依据、状态和 Manifest 起点

### 工作

```text
核验 Bundle/HEAD/Tag/clean tree；
读取活动依据和 AGENTS；
将本任务加入仓库；
ACTIVE_PROJECT 指向本任务 IN_PROGRESS；
CURRENT_STATUS 和 Ledger 记录输入 HEAD 2e779764 与审核纠正；
修复 ownership manifest，纳入 validation/caold_openclaw_live_validation.json；
Checkpoint commit。
```

### PASS

```text
活动路线唯一；
当前任务唯一；
tracked == manifest rows；
unclassified=0；
状态不写完成 Tag；
无历史 Ledger 重新成为活动权威。
```

建议提交：

```text
checkpoint(caold): activate legal traversal and live closure route
```

---

## Gate 1：Core 存储域与 Access 活动写入 Policy 分离

### 工作

```text
Core 保留 storage GeometryAddress 验证；
移除 CoreRuntime 通用 mutation 对 Access active semantic Policy 的直接依赖；
Access 建立 ActiveSemanticWritePolicy；
活动 Placement 统一验证 profile/chart/phase/layer0/radius；
旧 storage-only state 可重开；
Core 研究 fixture 可使用合法非 layer0；
Coverage 边界层 unsupported 如实测试。
```

### PASS

```text
Core 不理解 OpenClaw 写入 Policy；
Access/OpenClaw 不能写非 layer0 或超 active radius；
旧数据不丢；
非 layer0 deterministic Core fixture 仍可构造；
无新模块循环。
```

建议提交：

```text
refactor(core-access): separate storage validity from active semantic write policy
```

---

## Gate 2：状态相关 legal_actions

### 工作

```text
Access page 输出 legal_actions；
Surface/physical page 分别计算；
Prompt 只渲染 legal_actions；
删除固定完整动作列表；
加入 root/no-more/hard-max/order0/physical page tests。
```

### PASS

```text
root 无 return_to_parent；
无 continuation 无 continue_page；
hard max 无 request_coarser；
order0 只允许 open_physical_entries；
动作集合与实际方法调用一致；
Python/Node 不存在两套漂移动作表。
```

建议提交：

```text
feat(access): expose state-derived surface legal actions
```

---

## Gate 3：有限纠错和单例机械消解

### 工作

```text
实现 invalid-decision correction Prompt；
最多 2 次 operation-local correction；
保证失败零 mutation；
实现 mechanical singleton physical-entry Policy；
多候选保持 LLM 单选；
加入 timing/counter。
```

### PASS

```text
非法 root return 可纠错；
无效 candidate 可纠错；
超限 defer/none；
无状态污染；
单例跳过模型调用；
多候选无自动选择；
无 select_entries。
```

建议提交：

```text
feat(openclaw): recover invalid traversal and resolve singleton entries
```

---

## Gate 4：P1 资产恢复与真实闭环

### 工作

```text
复制工作区；
盘点失败 P1 Statement；
优先复用未绑定 Statement；
执行 Placement；
核验 Core/Handle；
Gateway restart；
新 Session Recall；
记录完整 timing 和纠错证据。
```

### PASS

```text
P1 恰好一次有效写入；
无重复 Statement/Binding/Atom；
重启后正确单入口 Recall；
主代理回答正确；
插件保持 enabled；
旧工作区保留。
```

建议提交：

```text
test(openclaw): close recovered p1 placement and restart recall
```

---

## Gate 5：真实密集主题积累和 Recall

### 工作

```text
自然聊天逐轮积累 12～24 条独立 Statement；
达到 truncated Locality；
新 Session 单入口跨事实 Recall；
记录 Provider/model/geometry timing；
失败不清空。
```

### PASS

```text
真实 Statement/Handle/Core 均存在；
至少一个 truncated Locality；
单入口恢复至少 3 条相关事实；
无 semantic route；
可见回答正确。
```

模型/Provider 未闭合时：

```text
记录 IN_PROGRESS；
保留已形成数据；
不补造回答；
继续 Gate 6 交付。
```

建议提交：

```text
test(openclaw): validate dense single-entry live locality
```

---

## Gate 6：完整回归、状态回填和 Bundle

### 工作

```text
运行全部 package/OpenClaw/M0/governance tests；
运行 Broad/safe/dense runners；
更新唯一 task report；
更新 ACTIVE_PROJECT、CURRENT_STATUS、canonical Ledger；
记录实际向量和偏差；
生成 Manifest；
提交最终报告；
再次生成并 check Manifest，确保最终报告在清单内；
clean tree；
生成、验证完整历史 Bundle。
```

### Tag

仅当 P1 与密集 Live 均通过：

```text
LEGAL_SURFACE_TRAVERSAL_P1_DENSE_LIVE_VALIDATED_AT_<HEAD>
```

否则：

```text
CAOLD_LEGAL_TRAVERSAL_P1_DENSE_LIVE_IN_PROGRESS_AT_<HEAD>
```

建议提交：

```text
docs(caold): record legal traversal and dense live checkpoint
```

---

# 14. 自动测试矩阵

## 14.1 Core

```text
storage-valid layer/radius mutation；
Access Policy 不进入 Core public mutation；
Coverage layer -64/+64 方向边界明确 unsupported；
旧 state reopen；
Coverage/Lazy Surface 不回退；
Q16 partition/fanout/Policy 回归。
```

## 14.2 Access

```text
ActiveSemanticWritePolicy：
  profile/chart/phase/layer/radius；
new/move/expand/revision-move 统一校验；

legal_actions：
  root；
  descended page；
  no continuation；
  hard max；
  order0；
  physical page；

candidate validation；
singleton total count；
multi-candidate no automatic choice；
单入口 Recall 回归。
```

## 14.3 OpenClaw Python

```text
Prompt 只列 legal_actions；
root 不列 return_to_parent；
非法动作 correction；
无效 candidate correction；
JSON 字段 correction；
max correction defer；
zero-write；
singleton skip；
多候选真实选择；
P1 recovery bridge；
隐藏注入和 NONE。
```

## 14.4 OpenClaw Node

```text
legal action mapping；
correction loop limit；
operation state 不跨 Session；
provider timeout 与 invalid decision 分离；
singleton model-call skip；
timing fields；
Hook 快速返回；
deliver=false；
plugin schema/diagnose。
```

## 14.5 Lab

新增 runner 建议：

```text
run_surface_legal_action_validation.py
run_traversal_correction_validation.py
run_p1_recovery_state_validation.py
```

验证：

```text
每个状态的动作集合；
非法动作不改变状态 bytes；
单例/多候选分支；
失败 P1 数据盘点与无重复；
现有 Broad/safe/dense runners 回归。
```

## 14.6 项目级命令

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

python lab/nollm-lab/geometry/run_broad_residue_coverage_calibration.py `
  --output validation/caold_broad_residue_coverage_calibration.json
python lab/nollm-lab/geometry/run_safe_writable_field_validation.py `
  --output validation/caold_safe_writable_field_validation.json
python lab/nollm-lab/geometry/run_dense_locality_surface_validation.py `
  --output validation/caold_dense_locality_surface_validation.json
python lab/nollm-lab/geometry/run_dense_single_entry_recall_validation.py `
  --output validation/caold_dense_single_entry_recall_validation.json
python lab/nollm-lab/geometry/run_natural_multi_entry_observation.py `
  --input validation/caold_dense_single_entry_recall_validation.json `
  --output validation/caold_natural_multi_entry_observation.json

python tools/generate_module_ownership_manifest.py --write
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py

git diff --check

git status --short

Push-Location integrations/openclaw/formation-loop
npm test
npm run plugin:check
Pop-Location
```

最终报告提交后，必须再次执行：

```powershell
python tools/generate_module_ownership_manifest.py --write
# 若 manifest 因最终报告发生变化，提交 manifest 更新
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
git status --short
```

---

# 15. 机器边界 Gate

最终必须：

```text
Manifest tracked == Git tracked；
unclassified = 0；
production violations = 0；
production cycles = []；
OpenClaw direct nollm_core imports = 0；
MemoryCursor = 0；
select_entries = 0；
Topic/Source/Entity→Cell route = 0；
graph/vector/embedding production path = 0；
production Decimal/polygon = 0；
active `<FINAL_DELIVERY_HEAD>` = 0；
active `保持封板` = 0。
```

历史文档中的字符串可存在，但必须为历史分类。

---

# 16. 单一任务报告

只新增：

```text
docs/project/CAOLD_WRITE_POLICY_LEGAL_TRAVERSAL_P1_DENSE_LIVE_REPORT.md
```

至少记录：

```text
输入 Bundle/HEAD/Tag；
预计/实际向量；
全部模块实际完成度；
Manifest 起点遗漏和修复；
Core storage / Access active write Policy 分离；
legal_actions 状态矩阵；
correction 规则和实际次数；
singleton resolution；
P1 失败资产盘点；
P1 write/binding/restart recall；
真实密集主题 Statement/Handle/Core 数；
truncated Locality；
密集 Recall entry/path/selected statements/visible answer；
R1/R2/R3；
Provider/model/geometry timing；
插件和工作区状态；
测试结果；
known limitations；
Bundle 文件名和 SHA。
```

不要求：

```text
隐藏推理；
完整私密聊天；
外围攻击矩阵；
完美 Prompt 哈希历史；
PB 性能报告。
```

---

# 17. 状态与 Ledger 回填

必须更新：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
```

必须记录：

```text
最终 HEAD；
最终 Tag/IN_PROGRESS Tag；
实际推进向量；
全部模块实际完成度；
P1 和 dense Live 实际状态；
Provider 环境依赖；
下一候选能力。
```

不得：

```text
继续只写 input HEAD 而不写当前验证 HEAD；
出现多个 canonical Ledger；
使用 sealed/final/保持封板；
把 Provider timeout 写成几何失败；
把未通过 dense Live 写为完成。
```

---

# 18. Git 与 Bundle

每个大 Gate 至少一个提交。

最终：

```text
所有真实修改 commit；
工作树 clean；
仓库外生成一个完整历史 Bundle；
Bundle verify；
计算 SHA-256；
只交一个 Bundle。
```

建议：

```text
nollm_caold_write_policy_legal_traversal_p1_dense_live_20260715_<shorthead>.bundle
```

PowerShell：

```powershell
git bundle create ..\nollm_caold_write_policy_legal_traversal_p1_dense_live_20260715_<shorthead>.bundle --all
git bundle verify ..\nollm_caold_write_policy_legal_traversal_p1_dense_live_20260715_<shorthead>.bundle
Get-FileHash ..\nollm_caold_write_policy_legal_traversal_p1_dense_live_20260715_<shorthead>.bundle -Algorithm SHA256
```

---

# 19. 完整通过条件

只有全部满足才可使用完成 Tag：

```text
Manifest 最终闭合；
Core storage 与 Access active semantic write Policy 分离；
活动语义写入仍限 layer0/safe radius；
legal_actions 由 Access 状态生成；
Prompt 不广告非法动作；
无效模型动作有限纠错、零污染；
单例 physical entry 机械消解；
多候选 LLM 单选；
P1 唯一写入、绑定、重启 Recall；
密集主题形成真实 truncated Locality；
新 Session 单入口跨至少 3 条事实回答；
R1/R2/R3 不回退；
无 Cursor/select_entries/semantic route；
Broad/safe/dense runners 回归；
全部 package/Node/governance tests 通过或环境限制如实；
插件 enabled；
旧数据保留；
工作树 clean；
完整历史 Bundle 验证通过。
```

---

# 20. 未完成时合法交付

任何以下情形均不得拒绝交付：

```text
Provider timeout；
密集主题未积累到目标数量；
模型连续输出非法动作但纠错证据完整；
P1 成功但 dense Live 未完成；
Node 24 环境不可用；
部分 Live 窗口不足。
```

必须：

```text
commit 真实进展；
clean tree；
完整历史 Bundle；
IN_PROGRESS Tag；
如实区分代码通过、确定性 fixture、真实 Live 和环境依赖；
插件和数据不清空。
```

---

# 21. 明确非目标

本任务不做：

```text
Stitch/Unstitch；
Bridge 公共端点最终纯化；
多物理层语义 Placement；
物理层自动选择；
多 Chart/Atlas；
PB 长跑；
持久 Surface cache；
Exact Decimal/polygon 生产 Coverage；
新的 Coverage 方法选择；
自然多入口数量 Gate；
History/Audit 产品；
安全攻击矩阵；
正式发布。
```

---

# 22. 真实停止条件

只在以下情况停止：

```text
1. legal_actions 无法由 Access 状态唯一确定；
2. bounded correction 必须引入持久状态或 Python 语义选择；
3. P1 恢复会破坏或重复旧 Evidence/Statement/Handle/Core；
4. Core/Access Policy 分离导致 canonical state 不可恢复；
5. 单例机械消解会在候选总数大于 1 时误触发；
6. 主链路必须恢复 Cursor、semantic index、select_entries 或 graph/vector/embedding 才能工作；
7. production dependency cycle 无法消除。
```

不要因以下事项停止：

```text
Prompt 文案调整；
测试名称变化；
Provider 单次超时；
密集 Live 部分轮次失败；
文档、Manifest 或 schema 普通问题；
旧失败 P1 Statement 需要重新绑定；
非关键 timing 波动。
```

---

# 23. 下一候选能力

本任务通过后，下一步优先评估：

```text
真实 Formation/Placement 吞吐与长期局部生长
```

而不是立即进入 Stitch 或换层 Placement。

下一任务必须基于：

```text
最终 HEAD；
实际 P1/dense Live 结果；
实际模型调用和纠错次数；
实际模块完成度；
实际推进向量。
```

不得机械继承本任务的目标或百分比。
