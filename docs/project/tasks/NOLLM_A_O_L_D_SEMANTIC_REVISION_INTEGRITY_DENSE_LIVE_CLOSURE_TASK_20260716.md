# Nollm A/O/L/D：语义修订完整性、P1 双事实无损修复与真实密集 Locality 闭环任务书

**任务文件名**：`NOLLM_A_O_L_D_SEMANTIC_REVISION_INTEGRITY_DENSE_LIVE_CLOSURE_TASK_20260716.md`
**日期**：2026-07-16
**性质**：V3.9 真实语义 Placement 边界纠偏与 Provider-backed Dense Live 收口；不是 Coverage 方法重开、Stitch、换层语义 Placement、PB 长跑或正式发布任务
**直接修改模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**高风险回归模块**：`C=Core`（仅回归确认，不计划改变公共合同或实现）
**输入 Bundle**：`nollm_caold_write_policy_legal_traversal_p1_dense_live_20260715_f61efd5.bundle`
**输入 Bundle SHA-256**：`e1f9b2d70551266eb40c83213d5949065c6e128a9fdc5b78423b714721055084`
**输入分支**：`codex/caold-write-policy-legal-traversal-p1-dense-live-closure`
**输入 HEAD**：`f61efd5dcb46ffc8c8c79a5ca0ae588562346f8d`
**输入状态 Tag**：`CAOLD_LEGAL_TRAVERSAL_P1_DENSE_LIVE_IN_PROGRESS_AT_f61efd5dcb46ffc8c8c79a5ca0ae588562346f8d`
**补充 Live Evidence**：`nollm_caold_write_policy_legal_traversal_p1_dense_live_v5_20260716.jsonl`
**补充 Evidence SHA-256**：`95bd1ced05207b156cca82bed71ee4f9c3db5a732656da18635ce2052182aa7e`
**建议工作分支**：`codex/aold-semantic-revision-integrity-dense-live-closure`
**主执行环境**：Windows 10/11、PowerShell、Python 3.13、Node 24、当前真实 OpenClaw Provider/模型配置
**交付**：所有真实进展 commit；最终工作树 clean；仓库外单一完整历史 Git Bundle；未完成亦交付 `IN_PROGRESS` Bundle
**插件最终状态**：保持安装和启用
**数据最终状态**：V1～V5、Broad/Dense、V3.8/V3.9 旧工作区和全部 Statement/Evidence/Handle/Core state 保留；不得覆盖源工作区

---

# 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
明确 reuse / revision_current / new_local / expand_surface / defer 的真实语义边界；
对会改变当前 Handle 绑定的 revision_current 增加真实 LLM 的有限确认；
无损修复 V5 中被错误合并的 BX-3917 与 CR-7159 两条不同主体事实；
在修复后的工作区用正常聊天自然形成真实密集 Locality；
证明一个最终 physical entry 可以召回至少三条真实、相互补充的当前事实；
冻结与报告完全一致的 Live Evidence，完成状态、Ledger、Manifest 和 Bundle 收口。

范围变化：
V3.9 的硬物理参数、K=96、min_hit=1、Broad Policy、安全写入半径、Lazy Surface、
state-derived legal_actions、有限纠错、机械单例 physical entry 与单入口 Recall 保持不变；
本任务新增“破坏性语义修订必须确认”的 Access/OpenClaw 合同；
不引入 Python 语义规则、关键词判断、embedding、图、Topic/Source route 或第二套关系索引。
```

## 0.1 各 Gate 向量复述

每个 Gate 开始记录：

```text
当前预计向量：
C 0 | S 0 | T 0 | A +5 | H 0 | U 0 | O +5 | L +5 | D +5

当前主方向：
语义动作边界 → revision 有限确认 → P1 双事实修复 → 真实密集形成 → 单入口跨事实 Recall。
```

每个 Gate 结束记录：

```text
实际受影响模块；
是否新增 canonical state；
是否新增持久入口或语义索引；
是否把真实 LLM 语义责任交给 Python；
是否出现超过 5% 的模块偏差；
是否把单次模型结果写成永久架构不变量；
是否需要更新任务名、向量或活动范围。
```

不得静默把 Core、History、Audit、Stitch、多层 Placement 或 PB 性能加入实现范围。

---

# 1. 本任务的可验证结果

目标链路：

```text
f61efd5 legal-actions / correction / singleton checkpoint
→ 明确语义 Placement 动作定义
→ revision_current 先产生 provisional decision
→ 同一真实 LLM 对“新 Statement + 当前 Statement”进行一次有限 revision confirmation
→ 不满足同主体、同命题槽位、明确替代关系时拒绝 revision，零写入
→ 在 operation 内排除被拒绝的 revision candidate，允许一次重新 Placement 或 defer
→ 复制 V5 到新 V6 工作区
→ 恢复 Alpha V3.9 / BX-3917 的原 current Handle
→ 复用已存在 CR-7159 Statement，作为不同事实重新 Placement
→ BX-3917 与 CR-7159 分属不同 current Handle，均可单独 Recall
→ 正常聊天自然形成 8～12 条同一主题、相互补充的真实 Statement
→ 至少一个 Surface Cell / Locality 出现 truthful truncation
→ 新 Session 从一个 physical entry 召回至少三条真实事实并自然回答
→ R1/R2/R3、跨层 Recall、P1 双事实 Recall 不回退
→ Evidence 冻结、状态/进度账/Manifest/clean tree/Bundle 收口。
```

完整通过至少满足：

```text
1. P1 当前错误修订被确认并无损修复；
2. Alpha项目 V3.9 校验码 BX-3917 仍为 current 可召回事实；
3. CAOLD广域余量验收校验码 CR-7159 成为另一个 current 可召回事实；
4. 两条事实使用不同 Handle/Atom current binding；
5. 对 Alpha code 的查询不返回 CR-7159；
6. 对 CAOLD broad-residue code 的查询不返回 BX-3917；
7. revision_current 只在真实 LLM 确认 same_subject_same_slot_supersedes 后执行；
8. revision confirmation 拒绝时 Statement/Handle/Core 零变化；
9. 被拒绝的 revision candidate 在同一 operation 的重新 Placement 中不可再次选择；
10. exact duplicate 仍可 reuse；
11. 同主体同槽位的新值可以 revision_current；
12. 不同主体但字段形式相同不得 revision_current；
13. 同主体的新增补充事实不得因“相关”自动 revision_current；
14. uncertainty 应 defer，而不是强行 revision；
15. 真实密集主题形成至少 8 条 current Statement；
16. 至少一个真实 Surface projection `truncated=true` 且 `remaining_count>0`；
17. 密集查询最终只选择一个 physical entry；
18. Recall Agent 选择至少三条不同 current Statement；
19. 至少一条被选事实不在最初三条 Surface preview 中，证明 preview 只用于导航；
20. 无 Cursor、select_entries、Topic/Source/Entity route、graph/vector/embedding 或 Python 语义 Placement；
21. Live Evidence 文件冻结后不再追加，报告 line count/SHA 与交付文件完全一致；
22. final Manifest 包含报告、Evidence 和最终状态文件；
23. 工作树 clean，完整历史 Bundle verify 通过。
```

若 Provider 无法闭合密集 Live，必须提交所有真实进展并交付 `IN_PROGRESS` Bundle；不得用 synthetic fixture 替代 Provider-backed Dense Live。

---

# 2. 活动依据与优先级

执行前按顺序读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_7_ROTATED_MULTI_SCALE_PHYSICAL_MEMORY_FIELD_20260714.md
3. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_9_BOUNDED_APPROXIMATE_HEX_COVERAGE_20260715.md
4. docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md
5. docs/project/ACTIVE_PROJECT.md
6. docs/project/NOLLM_CURRENT_STATUS.md
7. docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
8. 本任务书
9. Access/OpenClaw/Lab/Distribution 模块章程
10. 根目录 AGENTS.md
```

冲突顺序：

```text
第一性原理
> V3.7 硬物理、Layer/Order 分离、单入口架构
> V3.9 快速有界 Coverage、Lazy Surface 和合法 Traversal
> 本任务的语义动作边界、revision confirmation、数据修复与 Dense Live 变化量
> 当前状态
> 历史任务、历史报告和历史 Tag。
```

开始时更新根目录 `AGENTS.md`，至少加入：

```text
- Placement action semantics are LLM-owned but must be precisely defined.
- `reuse` means the new Statement is materially the same current fact.
- `revision_current` is destructive to the current Handle binding and is allowed only for the same subject/referent, the same proposition slot, and a new value that supersedes the current value.
- Similar wording, the same field label, the same document type, or the same locality is not enough for revision.
- Different subjects with analogous attributes must remain distinct current facts.
- Additive facts about the same subject use new_local or another non-destructive action, not revision_current.
- Every revision_current decision is provisional until one bounded real-LLM confirmation succeeds.
- Rejected revision confirmation causes zero mutation and excludes that revision target for the operation-local retry.
- Python/Core must not infer subject identity or proposition equality by keywords, hashes, regexes, embeddings, or fixed scores.
- The V5 BX-3917/CR-7159 binding is a known semantic repair target; repair only in a non-destructive V6 copy using public Access operations.
- Dense Live must be formed from normal conversation, not direct Store injection or forced Cell addresses.
- Freeze Live evidence before writing the report; do not append to a hashed evidence file afterward.
- No Stitch, multi-layer semantic Placement, persistent Surface cache, semantic route, graph/vector/embedding, or PB validation.
```

---

# 3. 输入现场与审核基线

## 3.1 Git/Bundle

```text
Bundle SHA-256:
e1f9b2d70551266eb40c83213d5949065c6e128a9fdc5b78423b714721055084

Branch:
codex/caold-write-policy-legal-traversal-p1-dense-live-closure

HEAD:
f61efd5dcb46ffc8c8c79a5ca0ae588562346f8d

Tag:
CAOLD_LEGAL_TRAVERSAL_P1_DENSE_LIVE_IN_PROGRESS_AT_f61efd5dcb46ffc8c8c79a5ca0ae588562346f8d

Working tree:
clean

Bundle:
complete history, verified
```

## 3.2 已复现自动结果

```text
Core:             70 passed
Snapshot:          7 passed
Trace:             3 passed
Access:           87 passed, 8 existing deprecation warnings
OpenClaw Python:  37 passed
Surface legal-action runner: passed
Traversal correction runner: passed
Ownership manifest: 1878 tracked / 1878 rows / 0 unclassified
Production violations: 0
Production cycles: 0
```

当前 Linux 环境未独立完成：

```text
M0 45 项：执行超过当前审核窗口；Bundle 报告记录 Windows 45 passed；
Node 22 环境缺少 node_modules/@types/node，未复现任务要求的 Node 24 22/22。
```

## 3.3 已验证正确推进

```text
Core storage validity 与 Access active semantic write Policy 分离；
Surface/Physical page legal_actions 由状态生成；
root 不再展示 return_to_parent；
无 continuation 不展示 continue_page；
hard-max 不展示 request_coarser_surface；
无效 Traversal 可在同一 operation/state 上有限纠错；
纠错失败零写入；
physical-entry 全局单例可机械消解；
最终 Manifest 已闭合；
P1 形成、写入、绑定、重启 Recall 的机械链路成立；
Dense synthetic fixture 继续通过。
```

## 3.4 审核发现的语义阻断

V5 P1 输入：

```text
新 Statement:
dream:82b8b33fc8c0cf13220db726e34f67fe781ddaa073d5033c7d739766e3e268d9
“用户要求记忆：CAOLD广域余量验收的发布校验码是 CR-7159。”
```

被选择的 current 事实：

```text
旧 Statement:
dream:91b6c843119549038dd2bbb0a40a8452f82edf5c158cac39c877c691f22280dc
“Alpha项目 V3.9 发布校验码是 BX-3917。”

Handle:
default_dream_v1/default/layer0/q=-13/r=9
local_atom_id=dream:09adbf112797b51f45925c8b429c21a64c6ae6e90ebba9bf2e0e51e8ed1775a1
```

模型动作：

```text
revision_current
candidate_id=placement:existing:0
core_write_count=1
```

审核结论：

```text
两条文字明确指向不同主体：Alpha项目 V3.9 与 CAOLD广域余量验收；
字段形式都叫“发布校验码”不足以建立同一事实身份；
在没有额外 Evidence 证明二者为同一命题更新时，revision_current 不具备语义依据；
机械链路成功，但 current binding 合并了两个应当并存的事实；
P1 不能据此认定为语义正确闭环。
```

## 3.5 Evidence 不一致

报告记录：

```text
V5 evidence = 18 JSONL records
SHA-256 = dfc6134d03f44c3532d4a4e9254278569da8529b3232f8ebf6524162f2cf4880
```

本次上传文件实际：

```text
24 JSONL records
SHA-256 = 95bd1ced05207b156cca82bed71ee4f9c3db5a732656da18635ce2052182aa7e
```

这不证明数据伪造，但说明原 Evidence 在报告后继续追加或上传的并非报告引用的冻结副本。下一任务必须冻结 Evidence 后再生成报告。

## 3.6 仍未完成

```text
真实密集主题未开始；
没有 Provider-backed truncated Locality；
没有新 Session 单入口跨三条真实密集事实 Recall；
当前工作区中的 BX-3917/CR-7159 current binding 未分离；
真实 revision 对比矩阵未验证。
```

---

# 4. 任务开始前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 95% | 高（当前 bounded route） | K=96 Coverage、canonical state、Lazy Surface、单入口 Recall、storage validity | 本任务无 Core 变化；只回归 | 高风险回归，0% |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state-byte 回归 | 版本化、增量 Snapshot | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 独立事件合同 | 长期性能观察 | 否 |
| ACCESS | `IMPLEMENTED` | 90% | 中高 | write Policy、legal_actions、candidate validation、原子编排 | revision 语义边界不足；错误 current 合并 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 90% | 中高 | 真实 Formation、合法 Traversal、有限纠错、单例、R1/R2/R3 | P1 语义错误；Dense Live 未完成 | 是 |
| LAB | `IMPLEMENTED` | 90% | 高（deterministic） | Broad/Safe/Dense runners、legal/correction fixtures | 缺 revision 对比、修复验证、真实密集结果 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 85% | 中高 | plugin 0.12、V3.9 contracts | 缺 revision guard Wire 和最终证据冻结合同 | 是 |

说明：

```text
Access/OpenClaw 低于仓库 Ledger 的 100%/97%，是因为新 Live 证据推翻了“P1 语义正确”的隐含结论；
这不是已有合法动作和性能能力失效，而是当前目标范围恢复后的完成度重算。
```

---

# 5. 任务完成后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 95% | 95% | 0% | 无合同变化；全部回归 | package + Surface/Recall runners | Stitch、换层 Placement、PB |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | package tests | 增量 Snapshot |
| TRACE | 40% | 40% | 0% | 无变化 | package tests | 长期观察 |
| ACCESS | 90% | 95% | +5% | 精确动作语义、provisional revision、无损修复、原子拒绝 | 单元、对比矩阵、V6 state | 多层语义 Placement |
| HISTORY | 10% | 10% | 0% | 无变化 | 章程回归 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 章程回归 | 暂停 |
| OPENCLAW | 90% | 95% | +5% | revision confirmation、重决策、双事实 Recall、Dense Live | 真实模型/重启/新 Session | Provider 长期稳定性 |
| LAB | 90% | 95% | +5% | revision 对比、修复、dense truth runners | JSON/Markdown reports | 自然多入口长期统计 |
| DISTRIBUTIONS | 85% | 90% | +5% | 新 Wire/schema/plugin 配置 | Node/plugin check | 正式发布 |

目标值仅表示当前活动范围，不表示永久完成或封版。

---

# 6. 资产分类

## 6.1 KEEP_ACTIVE

```text
V3.9 K=96/min_hit=1 approximate Coverage；
Broad calibration 与 safe writable radius；
Lazy Surface；
Physical/Surface 地址分离；
state-derived legal_actions；
Traversal bounded correction；
mechanical singleton physical entry；
单入口 Core Recall；
StatementStore、HandleStore、Core canonical state；
OpenClaw Formation、hidden Recall、same-run suppression；
R1/R2/R3 和跨层 deterministic fixtures；
旧 V1～V5 工作区与全部 Evidence。
```

## 6.2 PUREFY

```text
Placement prompt 中 reuse/revision/new_local/expand/defer 的定义；
revision_current 从 final decision 改为 provisional decision；
revision confirmation Wire；
Live Evidence 冻结流程；
当前状态与 Ledger 的完成度和能力措辞。
```

## 6.3 REBUILD

```text
P1 V6 非破坏工作区；
BX/CR 双事实 current binding；
真实密集主题工作区和 Live Evidence；
revision semantic contrast runner；
revision repair state runner；
Dense hidden-preview Recall runner/report。
```

## 6.4 DELETE_ACTIVE

```text
“相同字段名称足以 revision”的任何 Prompt 暗示；
未经确认直接执行 revision_current；
把 V5 revision_current 写成“valid semantic revision”的报告措辞；
报告后继续追加同一 Evidence 文件；
Core/Access/Lab 永久 100% 或“封板”措辞。
```

## 6.5 PAUSE

```text
Stitch/Unstitch；
多物理层语义 Placement；
多 Chart；
持久 Surface cache；
PB 长跑；
精确 polygon 生产路径；
History/Audit 产品化；
新的安全或攻击 Gate。
```

---

# 7. Placement 动作语义合同

本节属于 Access/OpenClaw 的活动语义合同，不进入 Core。

## 7.1 `reuse`

仅当：

```text
新 Statement 与当前 Statement 表达实质相同的当前事实；
没有新的值、时间状态或独立命题需要保存；
复用不会丢失新信息。
```

不得因为“主题相同”而 reuse。

## 7.2 `revision_current`

只有以下条件同时成立才允许：

```text
A. same_subject：两个 Statement 指向同一个真实主体/对象/约定；
B. same_slot：两个 Statement 表达同一个命题槽位或当前状态字段；
C. supersedes：新值明确替代旧值，或新的时间状态使旧 current 值不再是当前事实；
D. current-only：系统只应有一个 current 值；
E. evidence-preserved：旧 Statement/Evidence 仍保留，不被删除。
```

以下均不足以 revision：

```text
相同关键词；
相同字段名称；
相同文档类型；
相同 Locality；
都含“发布校验码”；
都与软件项目有关；
句式相似；
模型觉得“相关”。
```

## 7.3 `new_local`

用于：

```text
同一 Locality 中新的独立事实；
同主体但不同槽位的补充事实；
可以与现有 current 事实同时为真；
不同主体但适合进入当前局部的事实。
```

## 7.4 `expand_surface`

用于：

```text
现有 Locality 没有适合位置；
新事实与展示局部没有足够关系；
需要从关系中性 frontier 开始新局部。
```

## 7.5 `defer`

用于：

```text
主体身份或 revision 关系不清楚；
候选上下文不足；
模型不能可靠判断；
达到确认/重决策预算。
```

## 7.6 禁止 Python 语义判断

生产代码不得用：

```text
关键词匹配；
正则主体抽取；
字符串相似度；
hash；
embedding/vector；
固定分数；
Topic/Entity route；
人工 hard-code BX/CR IDs。
```

确定语义关系仍由真实 LLM 完成；Python 只验证 Wire、candidate、预算和状态原子性。

---

# 8. Revision Confirmation Wire

建议新增：

```text
nollm_openclaw_revision_confirmation_v1
```

## 8.1 输入

只包含：

```text
new_statement_id + content；
existing_statement_id + current content；
existing_handle；
provisional placement candidate_id；
上述 revision_current 五项语义定义；
不包含额外 Topic/Entity 索引或历史入口。
```

## 8.2 输出

确认：

```json
{
  "schema_version": "nollm_openclaw_revision_confirmation_v1",
  "outcome": "confirm_revision",
  "relation": "same_subject_same_slot_supersedes"
}
```

拒绝：

```json
{
  "schema_version": "nollm_openclaw_revision_confirmation_v1",
  "outcome": "reject_revision",
  "relation": "different_subject_or_non_superseding"
}
```

不允许输出任意地址、Topic、Entity、reason chain 或新 candidate。

## 8.3 执行规则

```text
1. Placement LLM 返回 revision_current；
2. Access 只做 provisional validation，不写 Statement/Handle/Core；
3. OpenClaw 用同一 Host 模型发起一次 deliver=false confirmation；
4. confirm → 执行原 revision_current；
5. reject → 保持原 Traversal/Statement/Handle/Core 不变；
6. operation-local blacklist 该 existing_handle 的 revision_current；
7. 允许一次重新 Placement；
8. 再次失败或超时 → defer；
9. 不持久化 confirmation 状态；
10. confirmation 仅用于 revision_current，不增加普通 new/reuse 的调用成本。
```

## 8.4 原子性

至少验证：

```text
confirmation timeout → zero write；
invalid JSON → 一次有限 JSON修复或 defer，zero write；
reject → zero write；
retry new_local → exactly one Statement persistence + one Core write + one Handle binding；
confirm revision → exactly one current Handle update；
任何路径旧 current state 可重开。
```

---

# 9. V5 P1 双事实无损修复

## 9.1 工作区

保留：

```text
nollm-caold-write-policy-legal-traversal-p1-dense-live-v5
```

新建：

```text
nollm-caold-semantic-revision-dense-live-v6
```

只能复制，不得覆盖 V5。

## 9.2 修复前盘点

必须记录：

```text
Statement count/tree SHA；
HandleBinding count/SHA；
Core state SHA；
occupied Cell/Atom/Bridge count；
old BX Statement 是否存在；
new CR Statement 是否存在；
current handle 指向哪个 Statement；
原 local_atom_id 和 Cell；
旧 V1～V5 工作区存在性。
```

## 9.3 修复动作

修复属于一次性数据纠偏，不是生产语义算法。

要求：

```text
1. 通过公开 AccessRuntime/AccessDecision 执行，不直接编辑 JSON；
2. 将原 Handle current 恢复为 BX-3917 Statement；
3. CR-7159 Statement 文件继续保留；
4. 通过新的真实 Placement + revision guard 将 CR-7159 作为独立 current 事实写入；
5. 不允许再次 revision BX Handle；
6. CR 可选择 new_local 或 expand_surface；
7. 不规定具体 q/r；
8. 失败时 V6 回滚，V5 不变；
9. 修复脚本必须 dry-run、before/after receipt 和幂等检查。
```

## 9.4 修复验收

```text
BX 与 CR current Statement 均存在；
Handle 不同；
Atom 不同；
旧 Evidence 均保留；
查询“Alpha项目 V3.9 发布校验码”只注入 BX-3917；
查询“CAOLD广域余量验收发布校验码”只注入 CR-7159；
两个查询均为单入口；
重启后仍成立。
```

---

# 10. Semantic Contrast 验证矩阵

## 10.1 Scripted Wire/Atomic Tests

脚本模型仅验证 Wire 和状态，不冒充语义质量：

```text
confirm_revision → apply once；
reject_revision → zero write；
reject then new_local → one write；
invalid confirmation JSON → bounded repair/defer；
confirmation timeout → zero write；
operation-local blacklist 防止同一 revision target 重选；
无持久 confirmation/candidate 状态。
```

## 10.2 Real LLM Contrast Set

用当前真实 Host 模型、有限候选、无写入 sandbox 运行：

### C1 Exact duplicate

```text
old: Alpha发布负责人是Priya。
new: Alpha发布负责人是Priya。
期望：reuse。
```

### C2 Same subject, same slot, new current value

```text
old: Alpha发布校验码是 BX-3917。
new: Alpha发布校验码已更新为 BX-4021。
期望：revision_current + confirmation。
```

### C3 Different subject, analogous slot

```text
old: Alpha项目 V3.9 发布校验码是 BX-3917。
new: CAOLD广域余量验收发布校验码是 CR-7159。
禁止：revision_current。
允许：new_local / expand_surface / defer。
```

### C4 Same subject, additive fact

```text
old: Alpha发布校验码是 BX-3917。
new: Alpha回滚负责人是Ken。
禁止：revision_current。
允许：new_local。
```

### C5 Ambiguous reference

```text
old: Alpha发布校验码是 BX-3917。
new: 发布校验码改成 CX-1。（未说明主体）
期望：defer 或拒绝 revision。
```

规则：

```text
不能把期望动作写入生产 Python；
Contrast 结果属于模型能力证据；
C3/C4 若错误 revision，任务不得进入 Dense Live；
模型不稳定时如实交付 IN_PROGRESS。
```

---

# 11. 真实密集 Locality 场景

## 11.1 原则

```text
通过正常聊天形成；
不直接调用 StatementStore；
不注入 GeometryAddress；
不强制同 Cell；
不要求自然多入口；
不把 truncation 写成普遍不变量；
Provider 失败如实记录。
```

## 11.2 建议主题

使用一个与 Alpha、Office、CAOLD code 不混淆的新主题，例如：

```text
“青岚发布计划”
```

四至六个正常对话回合，共形成 8～12 条独立 current Statement，例如：

```text
周一16:00变更冻结，由Priya主持；
周二10:00风险评审，由林岚负责；
周三15:00预发布演练，由Ken负责；
周四14:00正式发布，由Maya批准；
回滚包存放在 release/rollback/qinglan；
发布前必须完成数据库只读演练；
监控看板由Owen值守；
异常升级电话由Nora维护；
最终确认需要林岚与Maya共同签字；
发布说明必须先列破坏性变更。
```

具体事实可以调整，但必须：

```text
主体一致；
事实相互补充；
不存在故意互相修订；
至少三个事实可共同回答一个自然问题；
不复用 Alpha/Office 数据。
```

## 11.3 Dense 形成 Gate

达到：

```text
current Statement >= 8；
current HandleBinding 与 Core Atom 一一一致；
至少一个 Surface Cell truncated=true；
remaining_count > 0；
没有 Python/脚本强制 Cell；
没有错误 revision；
无孤立 Statement。
```

若 8 条后尚无 truncation，可继续到 12 条；12 条后仍无 truncation则记录真实自然分布并交付 IN_PROGRESS，不得改写坐标强制通过。

## 11.4 Hidden-preview Query

从真实 truncated Cell 中：

```text
识别至少一条不在首屏三条 preview 中、但属于该主题的 current Statement；
构造自然查询，同时需要：
  一条可见主题锚点事实；
  一条首屏未展示事实；
  第三条相关事实。
```

要求：

```text
LLM 通过主题 preview 选择该 Locality；
最终一个 physical entry；
Core Recall 包含隐藏事实；
Recall Agent 选择至少三条不同 Statement；
主代理自然回答全部三项；
不暴露 Nollm。
```

---

# 12. Evidence 冻结合同

## 12.1 文件

新增不可追加的交付 Evidence：

```text
validation/caold_semantic_revision_dense_live_20260716.jsonl
validation/caold_semantic_revision_dense_live_summary_20260716.json
```

## 12.2 冻结顺序

```text
1. 完成最后一次 Live；
2. 停止向交付 Evidence 文件追加；
3. 复制到仓库 validation 路径；
4. 记录 line count、size、SHA-256；
5. 报告引用该确切文件；
6. Evidence 冻结后不再运行会写入该文件的操作；
7. 后续额外运行使用新文件名；
8. 最终 Manifest 包含冻结文件和报告。
```

## 12.3 Summary 最低字段

```text
Bundle input/HEAD；
workspace before/after identity；
BX/CR Statement/Handle/Cell；
revision contrast outcomes；
revision confirmation count；
rejected revision zero-write evidence；
dense Statement/Handle/Atom counts；
truncated cell/remaining count；
final entry；
selected Statement IDs；
visible answer excerpt/SHA；
R1/R2/R3/P1 regressions；
Provider/model；
geometry vs model timing；
Evidence line count/SHA。
```

不要求完整隐藏推理或完整主聊天。

---

# 13. 所有权与公共合同变化

## 13.1 Core

无公共合同变化。

Core 继续只负责：

```text
canonical physical state；
确定性 Geometry/Coverage/Surface；
有界 Recall；
原子 mutation；
state bytes。
```

不得增加：

```text
subject identity；
revision semantic validation；
关键词/实体解析；
LLM；
confirmation state。
```

## 13.2 Access

新增/纯化：

```text
Placement action semantic contract；
ProvisionalRevisionDecision；
RevisionConfirmationResult；
operation-local rejected revision target set；
confirmation 后原子 apply；
一次性 P1 repair orchestration；
Dense Live state validation。
```

Access 只验证结构，不判断语义内容。

## 13.3 OpenClaw

负责：

```text
真实 Placement LLM；
revision confirmation LLM；
拒绝后的有限重新 Placement；
Provider timeout 分层报告；
Dense normal-chat Formation；
单入口 Dense Recall；
隐藏注入。
```

## 13.4 Lab

负责：

```text
scripted atomic fixtures；
real-model contrast runner/report；
P1 repair before/after validator；
Dense state validator；
Evidence freeze validator。
```

生产模块不得依赖 Lab。

## 13.5 Distributions

只声明：

```text
revision confirmation Wire version；
max confirmation calls=1；
max post-rejection redecision calls=1；
plugin version；
Evidence filename contract。
```

---

# 14. Wire 与配置建议

建议新增：

```text
revision_confirmation_schema_version = nollm_openclaw_revision_confirmation_v1
revision_confirmation_max_calls = 1
revision_redecision_max_calls = 1
revision_confirmation_model_mode = inherit
```

配置不得包含：

```text
subject keywords；
entity lists；
similarity threshold；
embedding model；
Topic route；
revision hard-coded IDs。
```

插件版本建议：

```text
0.13.0
```

版本号可按仓库实际调整，但 Wire identity 必须显式。

---

# 15. Failure 与回滚

至少覆盖：

```text
revision confirmation invalid JSON；
confirmation timeout；
confirmation reject；
redecision 仍选择被 blacklist target；
redecision timeout；
repair source Statement 缺失；
repair old Handle 不匹配；
repair Core write 失败；
repair Handle write 失败；
Dense Formation invalid；
Dense Placement defer；
Provider timeout；
Evidence freeze 后误追加；
Gateway restart failure。
```

要求：

```text
旧 V5 永不改变；
V6 修复失败可删除重建；
任何 revision reject/timeout 零 mutation；
Statement 不成为孤立数据；
旧 Evidence 不删除；
插件保持 enabled；
主聊天失败开放；
下一正常聊天继续。
```

---

# 16. 内部 Gate 与实施工作流

## Gate 0：活动依据与输入保护

工作：

```text
核验 Bundle/HEAD/Tag/clean tree；
读取活动依据和 AGENTS；
加入本任务书；
ACTIVE_PROJECT 切换为本任务 IN_PROGRESS；
重算模块完成度；
登记上传 JSONL 的 24 行/实际 SHA 与报告 18 行/SHA 不一致；
复制 V5 前记录全部 hashes；
形成 checkpoint commit。
```

建议提交：

```text
checkpoint(aold): activate semantic revision integrity and dense live closure
```

PASS：

```text
活动指针唯一；
V5 不变；
未启动 Dense Live；
向量无新增模块。
```

## Gate 1：Placement 语义动作边界

工作：

```text
更新 V3.9 架构/路线的 Placement action 定义；
更新 AGENTS；
纯化 Placement Prompt；
增加 Contrast fixtures；
删除“相关即可 revision”的模糊措辞。
```

建议提交：

```text
feat(access): define strict semantic placement action boundaries
```

PASS：

```text
无 Python 语义规则；
C1～C5 结构测试存在；
C3/C4 的 production Prompt 明确禁止错误 revision。
```

## Gate 2：Destructive Revision Confirmation

工作：

```text
实现 provisional revision；
实现 confirmation Wire；
实现 reject zero-write；
实现 operation-local blacklist；
实现一次 redecision/defer；
记录 timing/counters；
Node/Python tests。
```

建议提交：

```text
feat(openclaw): confirm destructive revisions before current binding changes
```

PASS：

```text
confirm/reject/timeout 原子性通过；
普通 new/reuse 不增加模型调用；
无持久 confirmation state；
OpenClaw 不直接 import Core。
```

## Gate 3：P1 双事实无损修复

工作：

```text
建立 V6 copy；
运行 dry-run inventory；
恢复 BX current；
真实 LLM 重新 Placement CR；
revision guard 拒绝错误合并；
形成两个不同 Handle；
重启；
两个独立新 Session Recall。
```

建议提交：

```text
test(aold): repair p1 semantic split and validate dual current recall
```

PASS：

```text
BX/CR 同时可召回；
无交叉污染；
V5 unchanged；
所有修复使用 public APIs；
无直接文件修改。
```

## Gate 4：真实密集 Locality 形成

工作：

```text
用正常聊天形成青岚或等价主题；
逐轮记录 Formation/Placement；
检查 Statement/Handle/Core 一致；
达到 8～12 current Statements；
观察自然 Locality 和 truncation；
不得强制坐标。
```

建议提交：

```text
test(openclaw): accumulate provider-backed dense locality without forced placement
```

PASS 或 IN_PROGRESS：

```text
通过：>=8 current Statements 且出现真实 truncation；
IN_PROGRESS：Provider/模型未达成，但所有进展真实提交；
禁止 synthetic 结果替代。
```

## Gate 5：单入口 Hidden-preview 跨事实 Recall

工作：

```text
选择真实 truncated Locality；
构造包含 hidden preview 事实的自然查询；
Gateway restart；
新 Session Recall；
一个 physical entry；
至少三条 current Statement；
自然回答。
```

建议提交：

```text
test(openclaw): validate single-entry recall across truncated dense facts
```

PASS：

```text
hidden fact 被召回；
一个 entry；
无 select_entries；
无持久入口；
无 Nollm 暴露。
```

## Gate 6：完整回归、Evidence 冻结与 Bundle

工作：

```text
运行全部 package/Node/M0/runners；
冻结 Evidence；
写单一报告；
更新状态/Ledger/actual vector；
生成 Manifest；
提交报告和 Evidence；
再次生成/验证 Manifest并提交；
clean tree；
生成并验证完整历史 Bundle。
```

完成 Tag：

```text
SEMANTIC_REVISION_INTEGRITY_DENSE_LIVE_VALIDATED_AT_<HEAD>
```

未完成 Tag：

```text
AOLD_SEMANTIC_REVISION_DENSE_LIVE_IN_PROGRESS_AT_<HEAD>
```

不得使用 sealed/final/100%-permanent 描述。

---

# 17. 自动测试矩阵

## 17.1 Access

```text
revision provisional 不写入；
confirmation confirm 执行一次；
confirmation reject 零写入；
reject 后 blacklist；
redecision new_local 一次写入；
reuse 不触发 confirmation；
new_local 不触发 confirmation；
defer 零写入；
repair old current；
repair idempotent；
BX/CR distinct bindings；
active write Policy 保持。
```

## 17.2 OpenClaw Python

```text
revision confirmation Prompt 完整；
JSON strict envelope；
invalid JSON bounded repair；
Provider timeout defer；
reject redecision；
max calls；
不输出 hidden reasoning；
Formation/Placement/Recall 不回退；
Evidence timing counters。
```

## 17.3 OpenClaw Node

```text
plugin schema 0.13；
revision confirmation config constants；
只有 provisional revision 调 confirmation；
reject retry operation-local；
transcript cleanup；
no direct Core import；
plugin:check。
```

## 17.4 Lab

```text
semantic contrast Wire fixture；
real-model contrast report；
P1 repair before/after；
V5 unchanged；
Dense current state；
truncated hidden-preview query；
Evidence freeze line/SHA；
Manifest final inclusion。
```

## 17.5 回归命令

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

python lab/nollm-lab/geometry/run_surface_legal_action_validation.py --output validation/caold_surface_legal_action_validation.json
python lab/nollm-lab/geometry/run_traversal_correction_validation.py --output validation/caold_traversal_correction_validation.json
python lab/nollm-lab/geometry/run_revision_semantic_contrast_validation.py --output validation/caold_revision_semantic_contrast_validation.json
python lab/nollm-lab/geometry/run_p1_dual_fact_repair_validation.py --workspace <V6> --output validation/caold_p1_dual_fact_repair_validation.json
python lab/nollm-lab/geometry/run_dense_live_state_validation.py --workspace <V6> --output validation/caold_dense_live_state_validation.json
python lab/nollm-lab/geometry/run_live_evidence_freeze_validation.py --evidence validation/caold_semantic_revision_dense_live_20260716.jsonl --summary validation/caold_semantic_revision_dense_live_summary_20260716.json

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

若 M0 或 Provider 超时，记录真实命令、已完成项和环境限制，不得补造。

---

# 18. 机器边界 Gate

最终必须：

```text
Manifest tracked = Git tracked；
unclassified = 0；
production violations = 0；
production cycles = []；
OpenClaw direct nollm_core import = 0；
MemoryCursor = 0；
select_entries = 0；
Topic/Source/Entity route = 0；
production embedding/vector/graph = 0；
production Python semantic revision rule = 0；
persistent revision confirmation state = 0。
```

历史文档可保留字符串，但必须明确 HISTORICAL。

---

# 19. 单一任务报告

新增：

```text
docs/project/AOLD_SEMANTIC_REVISION_INTEGRITY_DENSE_LIVE_REPORT.md
```

最低记录：

```text
输入 Bundle/SHA/HEAD；
分支和最终 implementation/evidence HEAD；
预计/实际推进向量；
全部模块实际完成度；
V5 before inventory；
BX/CR 语义错误说明；
revision confirmation Wire；
contrast matrix；
V6 repair before/after；
BX/CR distinct Handle/Recall；
Dense normal-chat turns；
Statement/Handle/Atom counts；
truncated Cell；
hidden-preview fact；
最终 single entry；
selected statements；
visible answer excerpt/SHA；
R1/R2/R3/P1 regression；
Provider/model/timing；
冻结 Evidence path/line count/SHA；
测试结果；
Manifest/boundary；
插件和旧工作区状态；
known limitations；
Bundle filename/SHA（外部交付信息可在最终回复给出）。
```

不得把 deterministic dense fixture 写成真实 Dense Live。

---

# 20. 状态与进度账回填

更新：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
```

必须：

```text
只保留一个 canonical Ledger；
不写永久 100%；
区分 mechanical P1、semantic P1 和 Dense Live；
记录 V5 语义错误及 V6 修复；
记录实际向量和偏差；
绑定具体 implementation/evidence HEAD；
未完成则保持 IN_PROGRESS。
```

---

# 21. Git 与 Bundle

## 21.1 Checkpoint

每个大 Gate 至少一个 commit。

## 21.2 最终提交顺序

为避免 Manifest 再次遗漏：

```text
1. 提交代码、测试、Live Evidence、报告和状态；
2. 生成 Manifest；
3. 提交 Manifest；
4. 运行 Manifest --check、validator、boundary；
5. 不再新增 tracked 文件；
6. 确认 clean tree；
7. 创建 Tag；
8. 仓库外生成完整历史 Bundle；
9. verify Bundle 和 SHA-256。
```

建议 Bundle：

```text
nollm_aold_semantic_revision_integrity_dense_live_20260716_<shorthead>.bundle
```

---

# 22. 完整验收条件

只有同时满足才允许完成 Tag：

```text
Placement 动作语义合同进入活动权威；
revision_current 需要真实 LLM confirmation；
reject/timeout 零写入；
C1～C5 contrast 通过，尤其 C3/C4 不错误 revision；
V5 保留不变；
V6 中 BX/CR 分离；
两个查询分别正确 Recall；
真实 Dense Live current Statements >=8；
出现真实 truncation；
单入口跨至少三事实 Recall；
包含 hidden-preview 事实；
R1/R2/R3 和跨层 Recall 不回退；
无语义索引、Cursor、多入口或 Python 语义判断；
Evidence 冻结并与报告一致；
全部测试或环境限制如实；
Manifest/boundary通过；
clean tree；
完整历史 Bundle verify。
```

---

# 23. 未完成时合法交付

任何以下情况均允许 `IN_PROGRESS`：

```text
真实模型 C3/C4 仍错误 revision；
Provider 无法完成 Dense formation；
8～12 Statement 后未自然出现 truncation；
Dense query 未选中 hidden fact；
Node 24 环境不可用；
M0 超出执行窗口。
```

但必须：

```text
提交所有真实代码和测试；
保留 V5/V6/旧数据；
clean tree；
完整历史 Bundle；
明确已完成和未完成；
不补造 Live；
不因未闭环拒绝阶段性交付。
```

---

# 24. 明确非目标

本任务不做：

```text
Coverage 方法重新选择；
K/min_hit 重校准；
精确 polygon 生产路径；
Stitch/Unstitch；
多物理层语义 Placement；
多 Chart；
PB/长期性能；
持久 Surface cache；
History/Audit 产品；
新的安全治理系统；
Topic/Source/Entity 索引；
vector/graph/embedding；
删除旧用户数据。
```

---

# 25. 下一候选能力

本任务通过后，才重新评估：

```text
1. 真实密集 Locality 的长期自然生长；
2. 多物理层 Placement 的语义粒度；
3. 内部几何端点 Stitch；
4. 可丢弃 Surface 增量缓存；
5. 工作得久与规模性能。
```

下一任务必须基于实际 Bundle 重新生成任务名、推进向量、全部模块完成度和代码锚点，不得机械沿用本任务预测。
