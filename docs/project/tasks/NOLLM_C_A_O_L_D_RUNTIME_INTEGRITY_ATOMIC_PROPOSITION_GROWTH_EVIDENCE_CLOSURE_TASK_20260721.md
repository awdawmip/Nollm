# Nollm CAOLD：运行时完整性、原子命题场生长与证据闭环任务书

**任务文件名**：`NOLLM_C_A_O_L_D_RUNTIME_INTEGRITY_ATOMIC_PROPOSITION_GROWTH_EVIDENCE_CLOSURE_TASK_20260721.md`  
**日期**：2026-07-21  
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**任务性质**：冻结 V3.11 Rev3 能力范围，偿还可能造成静默丢数据的可靠性债务，纠正错误验收不变量，并完成真实场生长与证据闭环  
**输入 Bundle**：`nollm_aold_prompt_bounded_lens_cartography_relation_entry_recall_20260718_db2b5b0.bundle`  
**输入 Bundle SHA-256**：`a795bb9941c8765b26dda8373678b66f2ccf62a2a30372f193d2e604a6934a28`  
**输入分支**：`codex/aold-prompt-bounded-lens-cartography-relation-entry-recall`  
**输入 HEAD**：`db2b5b0c25d8d527a249de90c6555aeaf686f618`  
**输入 HEAD Tag**：无  
**外部阶段审核报告**：`Nollm_V311Rev2阶段认证审核报告_2026-07-18.md`  
**外部报告 SHA-256**：`d6a44af6a23dbe85dace51f818095467c87a37137bdacc0376b6367fb1f6a068`  
**建议工作分支**：`codex/caold-runtime-integrity-atomic-proposition-growth-evidence-closure`  
**主环境**：Windows 10/11、PowerShell、Node 24、当前真实 OpenClaw / LongCat-2.0  
**交付方式**：大跨度单任务；内部 Gate；普通问题直接修复；所有真实进展 commit；工作树 clean；仓库外生成并验证单一完整历史 Git Bundle  
**插件最终状态**：保持安装并启用；冻结 Evidence 不得继续作为 live append 目标  
**数据最终状态**：全部历史工作区和 Capture 原文保留；新建独立验证工作区；不得清空、覆盖或回写历史冻结 Evidence  
**能力边界**：本任务不新增多 Cell footprint、多物理层 Placement、Stitch、多 Chart、语义索引、Topic/Entity、multi-entry Recall、外部队列、数据库或 PB 长跑

---

# 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +10% | DISTRIBUTIONS +5%

主方向：
冻结 Rev3 Prompt-bounded Writer/Cartographer、independent seed、realized Junction 和 relation-entry Recall；
先修复 Core 重入和公共 Junction 静默截断；
恢复 Access 事务、回滚、修订与损坏数据回归；
纠正“一轮 Capture 只能形成一个 Statement”的错误 Gate；
以原子命题重新完成 Provider 东京/时间/天气/无关长分支、重启、NONE 和关系入口召回；
将 live Evidence 与冻结 artifact 生命周期彻底分离；
同步治理入口和活动测试。

范围变化：
无新架构能力；
明确：
  one Statement → one Atom → one Cell；
  one Capture/turn → zero、one 或多个独立 Statements；
因此 db2b5b0 的 T0 两条 Statement 不构成 multi-cell 证据，也不授权 multi-cell。
```

## 0.1 Gate 向量复述

每个 Gate 开始必须记录：

```text
C +5 | S 0 | T 0 | A +10 | H 0 | U 0 | O +5 | L +10 | D +5
```

每个 Gate 结束必须记录：

```text
实际受影响模块；
预计/实际向量偏差；
是否修改公共合同；
是否发现静默数据丢失；
是否形成新的架构范围；
是否仍保持 one Statement/Atom/Cell；
是否需要更新任务名称、范围或向量。
```

新增模块或某模块实际偏差超过 5%，必须更新任务书和 canonical Ledger，不得静默扩张。

---

# 1. 输入检查点审核结论

## 1.1 Bundle 基础现场

```text
Bundle verify：通过；
完整历史：是；
HEAD：db2b5b0c25d8d527a249de90c6555aeaf686f618；
branch：codex/aold-prompt-bounded-lens-cartography-relation-entry-recall；
working tree：clean；
exact HEAD tag：无；
tracked files：1981。
```

当前独立复现：

```text
Core：80 passed；
Snapshot：7 passed；
Trace：3 passed；

Access/Rev3 关键测试：
27 passed；

OpenClaw Cartographer：
4 passed；

Rev3 Lab：
9 passed；

Manifest：
1981 tracked / 1981 rows / 0 unclassified；

production boundaries：
0 violations / 0 cycles。
```

当前 Linux 审核环境：

```text
Node 22；
Bundle 未携带 node_modules；
未独立重建报告中的 Node 44；
全 Access 套件含长时 Surface tests，在当前执行窗口未完整跑完。
```

Bundle 报告记录：

```text
Core/Snapshot/Trace/Access/Lab：233 passed；
OpenClaw Python：53 passed；
OpenClaw Node：44 passed；
M0：45 passed。
```

本任务必须在 Windows 主环境重新执行全部活动 Gate。

## 1.2 Rev3 应保留的真实成果

```text
Capture-only Proposition Writer；
Prompt-bounded Progressive Cartographer；
每 Prompt 最大证据约 7.4 KB；
300/1027 Cell Atlas 页面不超过 64 KB；
Atlas coverage certificate；
independent_seed；
production Recall 退出 stable-key first32；
Writer plan 实际 Admission；
target Cell 和 target preview 从 Reader 候选隐藏；
10/10 relation-entry Reader 从非目标 Cell进入；
10/10 target path 非空；
10/10 forced Lens-entry reach；
0/10 unrelated false reach；
one final entry；
Lens/Atlas operation-local；
one Statement/Atom/Cell；
V3.10 durable Capture 和异步 worker 基础。
```

这些成果必须保持。

## 1.3 对外部阶段报告的结论校正

外部报告对 `f9f01f5` 的可靠性、治理和证据纪律审计具有高价值，尤其是：

```text
Core trace 重入可造成静默覆盖；
旧 Junction API 排序前截断；
Access 致命回滚和关键测试缺失；
冻结 Evidence 仍被 live 插件追加；
治理入口和 distributions 事实矛盾。
```

这些问题在 `f9f01f5..db2b5b0` 的 Rev3 提交中基本未被触及，当前仍需处理。

但外部报告将 `f9f01f5` 的 Reader 10/10 解释为：

```text
Writer 改变字段 → Reader 通过几何找回。
```

该结论在严格因果定义下不成立，因为 `f9f01f5` Reader 直接选择 Writer target Cell，target path 为空。

真正满足：

```text
target Cell 被隐藏；
Reader 从 Writer resolved relation entry 进入；
target path 非空；
unrelated 不达；
```

的 10/10 证据来自当前 `db2b5b0`。

后续状态和报告必须区分这两个检查点。

## 1.4 当前 Rev3 报告的错误停止理由

Rev3 Live T0 原话：

```text
2026年7月18日，我计划下午三点开始东京浅草之旅，
并会根据当天降雨情况调整安排。
```

真实 Writer 形成：

```text
Statement A：
用户计划于2026年7月18日下午三点开始东京浅草之旅。

Statement B：
用户会根据2026年7月18日当天的降雨情况，
灵活调整东京浅草的出行安排。
```

这是两个独立、有意义、可分别召回的命题。

当前报告用：

```text
one_statement_atom_cell_achieved = false
```

将其认定为 one-cell 模型失败，并建议下一步研究 multi-cell。

该推论错误。

正确不变量是：

```text
每个 MemoryStatement 只有一个 canonical Atom、一个 Handle、一个 Cell。
```

不是：

```text
每个 Capture、每轮聊天或每段用户文本只能形成一个 Statement。
```

当前两个 Statement 各自拥有一个 Atom、一个 Handle、一个 Cell，仍然符合 one-cell 模型。

multi-cell footprint 讨论的是：

```text
一条 Statement 是否需要同时占据多个 Cell。
```

它与：

```text
一个复合 Capture 形成两条独立 Statements
```

不是同一个问题。

本任务必须撤回该错误完成 Gate，不得据此启动 multi-cell。

## 1.5 当前未闭合的真实 Live 问题

```text
东京 arm、时间 arm、天气 arm、unrelated arm 尚未全部完成；
四条 Capture 在 Provider basis span / outer text / timeout 后仍 pending/processing；
restart、三个 relation-entry query、unrelated negative、NONE 尚未完成；
Provider Writer 单次可超过 120 秒；
T0 使用了“请记住”命令式表达，不是最自然的普通聊天；
冻结脚本将 workspace_frozen 和 Gateway stopped 写成硬编码布尔；
报告与最终 Manifest 数字存在 1961/1962、当前 1981 等漂移。
```

这些是真实下一步，而不是 multi-cell。

---

# 2. 当前能力重新定性

`db2b5b0` 应记录为：

```text
PROMPT_BOUNDED_CARTOGRAPHY_RELATION_ENTRY_CAUSAL_CHECKPOINT_AT_db2b5b0
```

它证明：

```text
Writer/Cartographer/independent seed；
Prompt-bounded complete Atlas；
relation-entry non-empty causal Recall；
大字段 Recall 不再取 first32。
```

它没有证明：

```text
长期运行时完整性；
Core trace callback 安全；
Access 致命回滚状态；
完整 Provider 三臂场；
冻结 Evidence 生命周期；
one-cell 模型被证伪。
```

## 2.1 审核后预计实际推进向量

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +7% |
HISTORY 0% | AUDIT 0% | OPENCLAW +6% |
LAB +8% | DISTRIBUTIONS +4%
```

Rev3 没有修改 Core，因此 Core 不应再记录 `+5% actual`。

---

# 3. 活动依据

开工前按顺序读取：

```text
1. NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. 当前稳定项目书与 Core Function Priority
3. V3.7 Rotated Physical Memory Field
4. V3.9 Bounded Approximate Coverage
5. V3.10 Durable Capture / Async Absorption
6. V3.11 Rev3 Prompt-bounded Lens Cartography
7. 本任务书
8. CURRENT_STATUS
9. canonical Module Progress Ledger
10. C/A/O/L/D charters
11. 根目录 AGENTS.md
12. 外部阶段审核报告，仅作为审计证据和问题输入
```

冲突优先级：

```text
原始 Evidence 和用户数据不丢失
> 运行时无静默覆盖
> LLM语义/Core几何边界
> Architecture is the Index
> one Statement/Atom/Cell
> 单入口 Recall
> 活动测试与证据真实性
> 历史任务和旧完成度。
```

---

# 4. 给 Codex 的自由与停止边界

## 4.1 Codex 可以自主决定

```text
Core 重入使用 depth guard、callback phase guard或事件外移；
旧 Junction API 是修复、内部化还是删除活动调用；
AccessConsistencyError 的结构化字段；
runtime poison/failed state 的具体名称；
readback unknown 的返回类型或异常类型；
supporting Statement 在 revision 后的明确语义；
Evidence freeze 使用 rename、copy+digest还是run-scoped目录；
Gateway停止探测方式；
长分支主题和普通聊天文本；
是否复用 v4 pending Captures或新建 v5工作区；
测试文件布局；
旧时代测试是更新、迁移还是明确历史隔离。
```

普通工程问题应直接选择最简单正确方案继续，不需停下来确认。

## 4.2 不可协商结果

```text
1. Trace sink 不得在外层 batch 中完成嵌套 mutation并被外层静默覆盖。
2. Trace sink 不得在 operation 中 close Core 后让外层继续提交。
3. 公共 Junction API 不得按与评分无关的 stable-key 静默截断候选。
4. Access 致命回滚失败后不得继续宣称 runtime 可安全使用。
5. 回滚失败诊断不得丢失。
6. confirmed revision replay 不得无说明地绕过状态/Atlas新鲜度。
7. 提交后 readback 失败必须能区分“未提交”和“提交状态未知/需重开验证”。
8. 单个损坏 Statement 不得让整个 Recall 无结果且无诊断。
9. 一个 Capture 可以形成多个独立 Statements。
10. 每条 Statement 仍必须只有一个 Atom/Handle/Cell。
11. 不得因复合 Capture 形成两个 Statements而授权multi-cell。
12. 冻结 Evidence 不得继续作为 live append 目标。
13. freeze 报告中的 Gateway/workspace 状态必须来自机器探测或明确 operator attestation，不能硬编码成事实。
14. Rev3 relation-entry 10/10 因果 Gate不得回退。
15. 完整长分支必须使用普通自然聊天、真实 Provider、单入口和无关负对照。
16. Core/Access/OpenClaw关键旧回归场景必须恢复。
17. 不引入 Topic/Entity、vector/graph/embedding、fact→entries、multi-entry Recall或外部队列。
```

## 4.3 真实停止条件

只在以下情况停止：

```text
最小Core重入保护会破坏Trace隔离或死锁；
Access rollback无法在现有状态合同中判断提交状态；
one Statement/Atom/Cell在原子命题长分支中被真实证伪；
Provider长期不可用且无法取得最低Live证据；
旧工作区或原始Capture存在不可恢复数据损坏。
```

普通 Prompt、JSON、命名、测试、文档和性能问题直接修复继续。

---

# 5. 根目录 `AGENTS.md` 更新

至少加入：

```text
- db2b5b0 is a Prompt-bounded relation-entry causal checkpoint, not a completed growth or reliability baseline.
- One MemoryStatement maps to one Atom, one Handle and one Cell.
- One Capture or chat turn may produce zero, one or multiple independent MemoryStatements.
- Multiple Statements from one Capture do not authorize multi-cell footprints.
- Trace sinks are observational only; reentrant Core mutation, import or close during an operation must not commit.
- Public Junction candidate limits may not silently discard better candidates before scoring.
- Fatal Access rollback failure must preserve diagnostics and poison/close the affected runtime.
- Confirmed revision replay must have an explicit freshness contract.
- Readback failure after commit must be reported as an indeterminate commit state, not an ordinary pre-commit failure.
- A corrupt Statement is an item-level Recall error unless canonical state itself is unreadable.
- Live Evidence always writes to a run-scoped mutable path.
- Freeze seals immutable artifacts and rotates or disables the live writer before any report claims frozen state.
- Machine-detected facts and operator attestations must be distinct.
- Complete the atomic-proposition Tokyo/time/weather/unrelated growth gate before any multi-cell research.
- Do not add new memory architecture in this task.
```

---

# 6. 全部模块任务前完成度

审核后基线：

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `IMPLEMENTED` | 88% | 中 | V3.9几何、realized Junction、单入口Recall | trace重入静默覆盖、旧Junction截断、若干边界债 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes、structural diff | 增量/版本化 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | sink合同与状态隔离 | 本任务不扩展Trace产品 | 否 |
| ACCESS | `IMPLEMENTED` | 88% | 中 | Cartography、Admission、revision确认 | fatal rollback、测试缺失、readback/stale/corrupt语义 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 92% | 中高 | Capture、Writer/Cartographer、relation-entry Reader | 长分支、Provider retry、freeze生命周期 | 是 |
| LAB | `IMPLEMENTED` | 90% | 中高 | 10/10 relation-entry causal Gate | 错误one-turn Gate、未完成growth/restart、可靠性反例 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 90% | 中 | Rev3 wires/config | live activation与文档事实不一致 | 是 |

完成度下降来自发现真实可靠性缺口和目标重算，不表示 Rev3 功能消失。

---

# 7. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付 | 剩余限制 |
|---|---:|---:|---:|---|---|
| CORE | 88% | 93% | +5% | reentrancy-safe runtime、正确candidate limit | 多进程协调、长期规模 |
| SNAPSHOT | 50% | 50% | 0% | 回归 | 增量Snapshot |
| TRACE | 40% | 40% | 0% | 不扩展产品 | metrics |
| ACCESS | 88% | 96% | +10% | fatal rollback、freshness、readback、corrupt fallback、tests | 长期并发 |
| HISTORY | 10% | 10% | 0% | 无变化 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 暂停 |
| OPENCLAW | 92% | 96% | +5% | atomic growth、retry、evidence lifecycle | 多Provider |
| LAB | 90% | 96% | +10% |可靠性反例、完整long arms、freeze verifier | 长期统计 |
| DISTRIBUTIONS | 90% | 95% | +5% | 活动事实与配置一致 | 正式发布 |

不得写永久 100%。

---

# 8. Gate 0：活动状态、完成度和错误不变量纠正

工作：

```text
核验Bundle/HEAD/clean；
提交外部报告副本或登记其hash和结论；
更新ACTIVE_PROJECT/CURRENT_STATUS/Ledger；
将db2b5b0重命名为checkpoint；
删除或改写：
  one_statement_atom_cell_achieved（turn-level）；
替换为：
  per_statement_single_atom_cell；
  capture_statement_count；
  statement_placement_count；
修正“下一步必须multi-cell”的报告和状态；
记录f9与db2b5b0因果证据区别；
保护性commit。
```

机器验证：

```text
复合Capture→2 Statements：
  两条Statement均独立；
  每条1 Atom/1 Handle/1 Cell；
  不是multi-cell失败。

原子Capture→1 Statement：
  1 Atom/1 Handle/1 Cell。
```

Gate 0 PASS：

```text
活动依据不再授权multi-cell；
完成度和实际向量重算；
外部报告可靠性发现进入任务基线；
Rev3因果Gate保留。
```

建议提交：

```text
checkpoint(caold): correct atomic-statement and reliability baseline
```

---

# 9. Gate A：Core 运行时完整性

## 9.1 Trace 重入

当前已独立复现：

```text
单次nested put：
  内层put返回成功；
  随后被外层旧cells副本静默覆盖；
  最终仅外层Atom存在。

trace sink在core.batch.begin调用close：
  outer put仍成功并写盘；
  runtime状态为CLOSED；
  第二个runtime可立即claim同一workspace。
```

必须修复。

Codex可选择：

```text
operation depth / callback depth guard；
trace event在状态提交后、锁外发送；
不可变event queue；
等价最小方案。
```

要求：

```text
trace sink中的mutating public operation拒绝；
close/import_state等生命周期/状态替换拒绝；
只读操作是否允许由Codex明确决定并测试；
外层operation结果不被trace改变；
trace异常仍不改变主结果；
无死锁；
默认trace=None无额外复杂度。
```

必须新增：

```text
single-fire nested put；
nested apply_batch；
close-from-sink；
import_state-from-sink；
trace exception；
outer rollback；
second runtime claim。
```

不得依赖无限递归触发 `RecursionError`。

## 9.2 Junction 候选限制

当前 `JunctionRequest`：

```text
先stable-key取前64；
后按primary/contact距离评分。
```

必须选择：

```text
完整候选评分后截limit；
或candidate universe超限显式失败；
或将旧API内部化并证明活动调用仅使用安全半径。
```

禁止静默丢弃更优候选。

必须测试：

```text
max_radius=8；
多个primary；
最佳候选stable-key靠后；
前后顺序不影响；
independent_seed radius1不回退。
```

同时统一：

```text
active_hex_radius = (1<<30)-1；
fanout 7/8合同；
不可达断言和明显常量债。
```

只修复与当前正确性直接相关的低成本项，不展开全面Core清理。

Gate A PASS：

```text
无静默嵌套覆盖；
无operation中close后继续commit；
候选limit语义真实；
Core 80+ tests和新对抗测试通过。
```

建议提交：

```text
fix(core): restore operation integrity and deterministic junction limits
```

---

# 10. Gate B：Access 事务和状态完整性

## 10.1 恢复关键回归场景

按当前新锁模型重写并恢复以下能力测试，不要求恢复旧文件原样：

```text
所有Access action异常原子性；
fatal rollback failure；
事务串行化；
Access与直接Core竞争的支持边界；
workspace一对一state owner；
revision/current/supporting binding；
损坏Statement Recall；
confirmed revision freshness；
post-commit readback failure。
```

至少覆盖外部报告指出被净删除的四个测试场景。

## 10.2 Fatal rollback

当前：

```text
rollback中Core或Handle恢复失败
→ AccessConsistencyError只保存一句话
→ runtime仍可继续调用。
```

要求：

```text
保留original error；
保留每个rollback failure；
错误类型或字段可机器读取；
受影响AccessRuntime进入FAILED/CLOSED等不可继续写状态；
后续mutation拒绝；
重开新runtime从文件判断实际状态；
不得宣称已回滚。
```

Codex可选择是否将 StatementStore纳入同一恢复记录。

## 10.3 `_atomic` 异常边界

Codex必须明确：

```text
KeyboardInterrupt/SystemExit/BaseException期间是否尝试回滚；
何种异常保证rollback；
何种异常只记录indeterminate。
```

不得保持无文档的偶然行为。

## 10.4 Confirmed revision freshness

当前 confirmed revision replay 可绕过 Atlas重开。

要求：

```text
恢复必要的Core/Handle/current Statement新鲜度校验；
或用更窄的revision proof明确证明不依赖Atlas；
必须有并发/状态漂移测试；
不得无注释旁路。
```

## 10.5 Readback 语义

当前 durable readback 在提交后失败时，调用方收到普通异常，但状态可能已经提交。

必须区分：

```text
pre_commit_failure；
rolled_back_failure；
commit_state_unknown；
committed_but_readback_unavailable；
reopen_verified。
```

Codex可选择：

```text
结构化结果；
专用异常；
重开确认后返回。
```

用户数据和worker重试不得因误判造成重复Admission。

## 10.6 Recall 损坏项

一个 Statement 文件损坏：

```text
不应中止整个Recall；
该item返回evidence_corrupt或等价诊断；
其他items继续；
canonical Store整体无法解析时才失败。
```

## 10.7 Revision supporting 语义裁决

`revise_current` 当前删除旧 binding 及 supporting IDs。

Codex必须先在模块章程中明确：

```text
supporting_statement_ids表示：
  对当前命题的等价支持；
还是历史旧值支持；
还是仅reuse别名。
```

然后：

```text
按明确语义保留、迁移、退役或拒绝；
不得静默丢失；
补测试。
```

不启动History产品。

Gate B PASS：

```text
fatal rollback后不可继续写；
诊断完整；
旧四类测试恢复；
readback不会导致重复写；
corrupt item隔离；
revision freshness明确；
Access package完整通过。
```

建议提交：

```text
fix(access): restore transactional integrity and explicit commit outcomes
```

---

# 11. Gate C：Evidence 生命周期和可复现交付

## 11.1 Mutable 与 frozen 分离

建立：

```text
run-scoped mutable evidence：
  validation/live/<run_id>/events.jsonl

frozen delivery artifact：
  validation/frozen/<task_id>/evidence.jsonl
```

或等价结构。

冻结时：

```text
停止/切换live writer；
复制或atomic rename exact bytes；
计算SHA；
冻结文件只读；
插件立即改写新run path或debug_trace=false。
```

禁止：

```text
冻结artifact继续作为evidence_path；
交付后live hook继续append同一文件。
```

## 11.2 Freeze 真值

不得硬编码：

```text
workspace_frozen=true；
gateway_listener_present_at_freeze=false。
```

机器探测：

```text
port/listener；
plugin config；
writer path；
文件mtime/size stability；
Gateway process。
```

无法机器证明的内容记录：

```text
operator_attestation：
  value；
  operator；
  timestamp；
  evidence。
```

不得冒充自动验证事实。

## 11.3 Provider identity

从真实 Host/session envelope 提取：

```text
resolved_provider；
resolved_model；
resolved_model_ref。
```

不得在summary硬编码 `meituan/LongCat-2.0`。

## 11.4 Freeze verifier

必须从最终 Git blob复算：

```text
line count；
bytes；
SHA；
record type counts；
summary metrics；
report metadata；
Manifest classification。
```

冻结后任何追加必须使 Gate失败。

Gate C PASS：

```text
旧f9污染案例有回归测试；
Rev3新Evidence不会被live追加；
机器事实/attestation分离；
final artifact可从Git blob复现。
```

建议提交：

```text
fix(openclaw): separate live evidence streams from frozen delivery artifacts
```

---

# 12. Gate D：原子命题场生长

## 12.1 不变量

正式写入：

```text
one MemoryStatement
→ one Statement file
→ one current Handle
→ one Core Atom
→ one physical Cell。
```

允许：

```text
one Capture
→ zero Statements；
one Capture
→ one Statement；
one Capture
→ multiple independent Statements。
```

禁止：

```text
用turn-level statement_count判断one-cell模型；
把两条Statement写成一个multi-cell Atom；
为完成Gate强迫Writer合并独立命题。
```

## 12.2 新验证工作区

新建：

```text
nollm-caold-atomic-proposition-growth-v5
```

V4保持不变。

如果V4 pending Captures可安全恢复：

```text
可以作为worker recovery回归；
不得修改已冻结Evidence；
结果写入新run evidence。
```

## 12.3 使用原子自然表达

不得使用：

```text
“请记住”；
“请写入Nollm”；
坐标/动作命令；
一个句子故意塞入多个独立命题再要求只生成一条。
```

建议自然对话事实：

```text
T0：
2026年7月21日东京下雨了。

东京arm 1：
我今天在东京取消了浅草行程。

东京arm 2：
取消浅草后我改去了东京站。

时间arm 1：
2026年7月21日我还参加了一个线上会议。

时间arm 2：
那天晚上我整理了会议记录。

天气arm 1：
大阪同一天是晴天。

天气arm 2：
东京的雨在傍晚停了。

unrelated arm 1：
审计日志保留三十天。

unrelated arm 2：
服务器备份窗口是凌晨两点。
```

Codex可改写为更自然场景，但每条 Capture应只含一个主要独立命题。

## 12.4 Writer 输出验证

每个原子 Capture：

```text
目标是1条Statement；
若模型形成0条或多条，如实记录；
不得Python强行合并；
检查是否是Prompt/assistant污染、命题确实复合或模型错误。
```

只将：

```text
一条命题被拆成重复/重叠Statements
```

视为Writer问题。

## 12.5 Field Growth

全部通过正常：

```text
Capture；
Proposition Writer；
Cartographer；
independent_seed或related_growth；
Access/Core Admission；
reopen。
```

不得：

```text
direct Core.put semantic seed；
脚本强制region；
强制坐标；
复制Atom；
multi-cell。
```

## 12.6 长分支

要求：

```text
T0；
东京arm长度>=2；
时间arm长度>=2；
天气arm长度>=2；
unrelated arm长度>=2。
```

“长度”按真实单入口Core路径测量，不按命名声明。

## 12.7 Recall

至少：

```text
东京关系入口→T0，path>=2；
时间关系入口→T0，path>=2；
天气关系入口→T0，path>=2；
三个entry不同；
每次一个entry；
同一T0 Handle；
unrelated同预算不达；
target Cell/preview隐藏；
Gateway restart后重复；
NONE。
```

如果关系场在 one-cell 模型下无法形成：

```text
记录真实 Writer计划、Junction、Field和Recall反例；
提交IN_PROGRESS；
只有下一份独立任务才能研究multi-cell。
```

不得本任务中静默实现。

Gate D PASS：

```text
复合Capture多Statement不再误判；
原子Capture场完整；
三relation entry非空路径；
unrelated负对照；
restart/NONE；
Rev3 10/10 causal Gate不回退。
```

建议提交：

```text
test(aold): validate atomic proposition growth and three relation arms
```

---

# 13. Gate E：Provider retry、积压和运行闭环

当前 V4 中存在：

```text
basis span mismatch；
fenced/outer JSON；
Provider timeout；
attempt 6 processing；
captured/processing backlog。
```

要求：

```text
bounded correction只修改格式，不改Statement文本；
exact span失败保留raw并retry；
timeout回到retryable，不永久processing；
stale processing可恢复；
worker无需新聊天自动继续；
同batch identity和provenance保持；
不重复Admission；
失败Capture继续Pending；
diagnose输出next retry和oldest age。
```

测试：

```text
Gateway在processing中停止；
restart自动恢复；
Provider返回后、状态写前停止；
一条成功、一条失败；
成功项不重跑；
duplicate/orphan=0。
```

Provider latency不作为完成硬Gate，但积压必须最终收敛或诚实保持IN_PROGRESS。

---

# 14. Gate F：活动测试和治理事实收口

## 14.1 关键测试

恢复或重写外部报告指出被删除的四类回归：

```text
fatal rollback；
transaction serialization；
Access vs direct Core supported boundary；
workspace one-to-one binding。
```

## 14.2 时代测试

当前8个旧时代测试不得继续作为模糊失败项。

逐项：

```text
若仍是活动合同：
  更新到当前V3合同并通过；

若已历史化：
  移至明确historical/legacy目录；
  从活动Gate移除；
  文件头标状态和替代证据；

不得简单删除历史价值。
```

## 14.3 活动文档

修正：

```text
ACTIVE_PROJECT指向Historical V3.4；
AGENTS Authority落后；
README引用不存在run_tests.py；
0字节EVIDENCE.md；
distributions matrix/JSON/manifest/README live_activation三方矛盾；
M0 baseline过期；
evidenceFilenameContract与实际run/freeze策略。
```

原则：

```text
只保留一个活动入口；
不重写大量历史任务；
历史文件明确HISTORICAL；
当前能力名绑定具体HEAD。
```

## 14.4 最小活动 Gate runner

Codex可选择建立一个：

```text
tools/run_active_validation.py
```

或 PowerShell等价入口，统一运行：

```text
packages；
OpenClaw Python；
Node；
M0 active；
Rev3 causal；
runtime integrity；
Manifest；
boundaries。
```

不要求建设远程CI或GitHub workflow。

Gate F PASS：

```text
活动测试全绿；
历史失败已分类；
治理三角一致；
最终Manifest在报告后生成。
```

---

# 15. 自动测试矩阵

## 15.1 Core

```text
trace single nested mutation；
trace nested batch；
trace close；
trace import；
trace exception；
outer commit/rollback；
second runtime ownership；
Junction rank-before-limit或overflow；
active radius；
relation-group regression；
Surface/Coverage/Recall。
```

## 15.2 Access

```text
all action atomicity；
fatal rollback poison；
diagnostic preservation；
serialization；
direct Core boundary；
workspace identity；
readback states；
corrupt Statement item；
revision stale Atlas；
supporting semantics；
Cartography/independent seed/relation entry。
```

## 15.3 OpenClaw

```text
Capture；
worker retry；
Writer/Cartographer；
bounded correction；
Pending+admitted；
evidence rotation；
freeze path；
provider identity；
single hidden Recall；
restart。
```

## 15.4 Lab

```text
f9 direct-target not causal；
db2b5b0 relation-entry causal；
compound Capture multiple Statements valid；
atomic Capture one Statement；
three arms；
unrelated negative；
Evidence freeze；
reentrancy probes；
governance checks。
```

---

# 16. 性能边界

本任务主要是正确性，不重写性能架构。

保持：

```text
Capture p95目标<=100ms；
Writer common calls=1/batch；
Cartographer one session/batch；
Prompt<=64KB；
Recall common hidden calls<=1；
Core local V3.9数量级。
```

新增可靠性保护开销：

```text
Core无trace时近零；
Trace guard本地p95增加<=5%或<=1ms；
Access新验证不得增加Provider调用；
Freeze不在用户前台。
```

Provider Writer很慢是已知限制，不在本任务更换模型。

---

# 17. Evidence 与主报告

主 Evidence：

```text
validation/caold_runtime_integrity_atomic_growth_20260721.jsonl
validation/caold_runtime_integrity_atomic_growth_summary_20260721.json
```

主报告：

```text
docs/project/CAOLD_RUNTIME_INTEGRITY_ATOMIC_PROPOSITION_GROWTH_REPORT.md
```

报告必须直接回答：

```text
Core重入是否仍能静默丢数据；
Junction候选是否静默截断；
Access fatal rollback后状态；
readback未知如何表达；
复合Capture为何允许多Statement；
每条Statement是否1 Atom/Cell；
东京/时间/天气长分支；
relation-entry paths；
unrelated/restart/NONE；
worker backlog/retry；
frozen Evidence是否与live writer分离；
活动测试与治理；
实际向量；
Bundle。
```

Freeze顺序：

```text
结束正式Live；
切换/关闭live evidence writer；
验证原mutable文件稳定；
生成frozen artifact；
SHA/line/bytes；
Summary/Report；
Manifest；
Git blob复算；
commit；
Bundle。
```

---

# 18. 内部 Gate 与建议提交

## Gate 0
状态、错误不变量、外部报告对账。

```text
checkpoint(caold): correct reliability and atomic-statement baseline
```

## Gate A
Core重入和Junction。

```text
fix(core): reject reentrant state mutation and score junctions before limiting
```

## Gate B
Access事务完整性。

```text
fix(access): restore rollback diagnostics and explicit commit state
```

## Gate C
Evidence生命周期。

```text
fix(openclaw): rotate live evidence before immutable freeze
```

## Gate D
原子命题长分支。

```text
test(aold): complete provider atomic-proposition relation growth
```

## Gate E
worker retry/restart。

```text
fix(openclaw): converge retryable absorption without duplicate admission
```

## Gate F
测试和治理。

```text
docs(caold): reconcile active gates governance and final evidence
```

普通问题直接修复继续，不新拆任务。

---

# 19. 最终 Gate

必须同时满足：

```text
Core single-fire reentrant mutation不能静默成功；
Core close-from-trace不能让外层继续提交；
旧Junction API无评分前静默截断；
Access fatal rollback诊断完整并不可继续写；
readback提交状态明确；
corrupt Statement不阻断其他Recall items；
revision freshness和supporting语义明确；
复合Capture→多个Statement被接受；
每条Statement仍1 Atom/Handle/Cell；
atomic T0+三arms+unrelated；
三个relation-entry paths>=2；
unrelated不达；
restart/NONE；
Provider backlog可恢复；
frozen Evidence不再live append；
provider identity真实；
关键删除测试恢复；
时代测试已活动化或历史化；
README/ACTIVE_PROJECT/AGENTS/distributions一致；
Core/Access/OpenClaw/Node/M0/Rev3回归；
Manifest tracked=rows；
0 unclassified；
0 production violations/cycles；
clean tree；
完整历史Bundle verify。
```

---

# 20. 完成状态

全部完成：

```text
RUNTIME_INTEGRITY_AND_ATOMIC_PROPOSITION_GROWTH_VALIDATED_AT_<HEAD>
```

若Provider或长分支未闭合，但可靠性修复完成：

```text
CAOLD_RUNTIME_INTEGRITY_ATOMIC_GROWTH_IN_PROGRESS_AT_<HEAD>
```

如果one-cell模型被原子命题场真实证伪：

```text
仍使用IN_PROGRESS；
提交完整反例；
下一任务再决定是否研究multi-cell；
本任务不实现multi-cell。
```

任何状态都必须：

```text
commit；
clean；
单一完整Bundle；
不补造证据；
旧数据保留。
```

---

# 21. 明确非目标

```text
multi-cell footprint；
多物理层Placement；
Stitch/Bridge重构；
多Chart；
持久Lens；
Topic/Entity；
query/fact entry map；
vector/graph/embedding；
multi-entry Recall；
Provider更换；
PB；
正式发布；
外部消息队列；
数据库；
完整History/Audit产品；
大规模文档重写。
```

---

# 22. Git Bundle

建议文件名：

```text
nollm_caold_runtime_integrity_atomic_proposition_growth_20260721_<shorthead>.bundle
```

仓库外执行：

```powershell
git bundle create ..\nollm_caold_runtime_integrity_atomic_proposition_growth_20260721_<shorthead>.bundle --all
git bundle verify ..\nollm_caold_runtime_integrity_atomic_proposition_growth_20260721_<shorthead>.bundle
Get-FileHash ..\nollm_caold_runtime_integrity_atomic_proposition_growth_20260721_<shorthead>.bundle -Algorithm SHA256
```

---

# 23. 最终回复要求

最终只报告：

```text
branch / HEAD / commits；
Core reentrancy和Junction；
Access rollback/readback/revision/corrupt item；
compound Capture和per-Statement invariant；
三relation arms/unrelated/restart/NONE；
worker retry/backlog；
Evidence freeze；
tests/Manifest/boundary；
实际向量和完成度；
known limitations；
Bundle filename/SHA。
```

---

# 24. 最终任务概括

```text
Rev3 已经证明：
Writer选择的关系入口能够通过非空几何路径找到新事实。

下一步不是继续发明新几何，
也不是因为一轮聊天形成两条命题就跳到multi-cell。

下一步先保证：
Core和Access不会在回调、回滚和readback中静默丢数据；
Evidence真正冻结；
活动测试和文档说同一件事。

然后用每条只表达一个主要命题的普通聊天，
完成东京、时间、天气和无关四条真实分支。

一轮聊天可以形成多条Statement；
但每一条Statement仍然只存一次、只占一个Cell。
```

> **先把现有 Architecture-is-the-Index 变成可靠、可复现、不会静默损坏的工作基线，再讨论扩大一个事实的几何 footprint。**
