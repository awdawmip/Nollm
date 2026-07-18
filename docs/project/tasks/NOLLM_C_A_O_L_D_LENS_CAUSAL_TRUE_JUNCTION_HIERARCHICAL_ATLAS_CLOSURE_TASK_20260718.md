# Nollm CAOLD：Recall Lens 因果绑定、真实 Junction、层级 Atlas 与逆向生长闭环任务书

**任务文件名**：`NOLLM_C_A_O_L_D_LENS_CAUSAL_TRUE_JUNCTION_HIERARCHICAL_ATLAS_CLOSURE_TASK_20260718.md`
**日期**：2026-07-18
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`
**任务性质**：V3.11 原型因果闭环和能力重新验证；不增加持久语义索引，不进入多物理层或 Stitch
**输入 Bundle**：`nollm_caold_llm_recall_lens_junction_growth_20260717_dd95606.bundle`
**输入 Bundle SHA-256**：`032bf5c6b169ae800d21f1307f515454a363441efdb3b7971a62624cdfa83f64`
**输入分支**：`codex/caold-llm-recall-lens-junction-growth`
**输入 HEAD**：`dd95606b36acae753ce137c5c449f6fa16a070b4`
**输入 Tag**：无
**建议分支**：`codex/caold-lens-causal-true-junction-hierarchical-atlas`
**主环境**：Windows 10/11、PowerShell、Node 24、当前真实 OpenClaw / LongCat-2.0
**交付**：大跨度单任务；内部 Gate；真实进展全部 commit；工作树 clean；仓库外单一完整历史 Git Bundle
**插件状态**：保持安装并启用
**数据状态**：旧工作区和 V3.11 v1 工作区全部保留；新建 v2 工作区
**能力边界**：只闭合 layer-0 单 Cell Atom 的 Lens→Geometry 因果链；不做 multi-cell footprint、多物理层、Stitch、多 Chart、PB 长跑或正式发布

---

# 0. 任务推进向量

```text
任务推进向量：
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +15% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +15% | DISTRIBUTIONS +5%

主方向：
撤回“Lens/Junction 已验证”的扩大结论；
将 Lens path 确定性编译为 relation groups；
重写 Core Junction 为真实多关系几何优化；
将 Atlas 从坐标前缀改为有界多尺度层级结构；
用 Writer/Reader/Critic、counterfactual 和长分支场证明因果；
完成 Provider-backed 三方向独立单入口 Recall。

范围变化：
Core 公共几何合同新增 relation-group Junction；
Access 的 Atlas/Lens 编译合同扩大；
Lab 从 synthetic conformance 扩展到真实 LLM 因果验证；
不改变 Core MemoryAtom、Handle、layer-0、Coverage 或单入口 Recall。
```

## 0.1 Gate 向量复述

每个 Gate 开始记录：

```text
C +10 | S 0 | T 0 | A +15 | H 0 | U 0 | O +5 | L +15 | D +5
```

每个 Gate 结束记录：

```text
实际模块偏差；
新增公共合同；
是否出现持久 Lens/Topic/index；
是否证明了因果而非相关；
是否需要更新架构范围。
```

新增模块或偏差超过 5% 必须更新任务书和 Ledger。

---

# 1. 输入 Bundle 审核基线

## 1.1 基础现场

```text
Bundle verify：通过；
完整历史：是；
SHA-256：
032bf5c6b169ae800d21f1307f515454a363441efdb3b7971a62624cdfa83f64；

branch：
codex/caold-llm-recall-lens-junction-growth；

HEAD：
dd95606b36acae753ce137c5c449f6fa16a070b4；

working tree：
clean；

exact HEAD tag：
无。
```

当前独立复现：

```text
Core/Snapshot/Trace/Access/OpenClaw Python/Lab selected：
236 passed，8 warnings；

Manifest：
tracked=1944；
rows=1944；
unclassified=0；

production violations=0；
production cycles=0。
```

Node 依赖未随 Bundle 提供；当前审核环境 Node 22，未独立重建 Node 44 项。Bundle 报告记录 Windows Node 24 通过。

## 1.2 应保留成果

```text
operation-local Lens Wire；
exact Capture basis span；
Lens 文本不持久化；
one Dream Sculptor batch；
LLM 不输出 q/r；
Core 语义盲候选接口；
one Statement / one Atom / one Cell；
即时 Capture和异步吸收基础；
Pending+admitted context；
fast Recall common hidden call <=1；
Provider-backed 6 Statements；
Manifest/boundary clean。
```

## 1.3 审核发现的 P0

### P0-1：Lens 与 Placement 可矛盾

当前校验允许：

```text
Lens locality_candidate_ids = [A]
primary_candidate_id = B
```

只要 A、B 都存在于 Atlas，计划即通过。

因此：

```text
Lens 没有被编译进几何；
它只是 Prompt 解释字段。
```

### P0-2：当前 Junction 不是真实交汇

当前 Core：

```text
只围绕 primary cells 枚举；
排序先 primary_max_distance；
再 contact_max_distance；
contact 不进入候选 universe。
```

独立例：

```text
primary=(0,0)
contact=(4,0)

当前 top candidate=(1,0)
primary distance=1
contact distance=3
```

真正平衡候选 `(2,0)` 不会优先。

### P0-3：Atlas 是坐标前缀

当前：

```text
occupied sorted by stable_key；
取前 candidate_limit；
frontier 仅围绕最前最多8个 occupied。
```

字段增长后，相关 Locality 可能不在 Atlas。

### P0-4：100-case self-play 是自证

脚本：

```text
程序制造 JSON；
程序选择 candidate；
程序从实际落点 Recall；
primary/secondary reach 使用同一个 reached 计数。
```

没有真实 Writer、Reader 或 Critic。

### P0-5：东京三入口 deterministic Observation 是手工星形

后续每条 fact 都程序选择包含 T0 的 candidate，再放到 T0 周边。

最终三个 entry 都是 T0 的直接 lateral 邻居。

这证明：

```text
紧凑簇的任意邻居可达中心
```

没有证明：

```text
东京、日期、天气 Lens 造成了不同生长分支。
```

### P0-6：Live 三入口缺乏反事实

Live 最终仍是中心加五个相邻 Cell。

没有：

```text
unrelated occupied branch；
相同预算负对照；
长路径；
Lens ablation；
contact effect。
```

### P0-7：Live Lens Evidence 是事后恢复摘要

Evidence 只保存：

```text
source_log_line；
raw SHA；
恢复出的部分 plan。
```

Bundle 不含对应原始 Host log/raw output，无法重新验证：

```text
exact basis spans；
contact IDs；
完整 JSON；
恢复过程。
```

## 1.4 P1

```text
一个 batch 多个 revision_current 只确认第一个；
其他 revision_confirmation_required 可能 terminal deferred；
confirmation timeout/invalid 可能退出 Pending；
报告和状态使用 98%/97% 高估；
status 使用 validated；
Layer Atlas representatives <=3，在大场需要层级结构；
Live Capture p95 有1.6秒 outlier，但不是本任务主线。
```

---

# 2. 当前能力重新定性

Gate 0 必须将 `dd95606` 记录为：

```text
LLM_RECALL_LENS_JUNCTION_PROTOTYPE_CHECKPOINT_AT_dd95606
```

它不是失败，也不是已验证终点。

实际推进向量建议回填：

```text
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +5% | DISTRIBUTIONS +5%
```

原因：

```text
Core 有候选原型，但非真实 Junction；
Access 有 Atlas/Lens Wire，但无因果绑定；
OpenClaw 有真实 Sculptor；
Lab 有基础 fixture，但验证方法不成立。
```

---

# 3. 开工依据

按顺序读取：

```text
1. FIRST_PRINCIPLES；
2. PROJECT_BOOK V3.1；
3. CORE_FUNCTION_PRIORITY V3.4；
4. V3.7 physical architecture；
5. V3.9 approximate Coverage；
6. V3.10 durable Capture；
7. V3.11 Rev1 architecture；
8. CURRENT_STATUS；
9. canonical Ledger；
10. 本任务书；
11. C/A/O/L/D charters；
12. 根目录 AGENTS.md。
```

冲突优先级：

```text
Evidence不丢
> LLM语义/Core几何边界
> Lens因果性
> Architecture is the Index
> 单入口Recall
> V3.9性能
> 当前实现便利。
```

---

# 4. `AGENTS.md`

至少加入：

```text
- dd95606 is a prototype checkpoint, not validated Lens-to-geometry causality.
- A resolved Recall Lens must causally constrain the geometry relation groups.
- Do not accept a primary/contact choice unrelated to Lens Atlas paths.
- Core Junction must score all relation groups symmetrically enough to make contacts observable.
- Do not enumerate only around the first group.
- Do not truncate candidate universe before geometry scoring.
- Locality Atlas must be derived from bounded multi-scale Surface, not stable-coordinate prefixes.
- Synthetic hand-built wire tests are conformance tests, not LLM self-play.
- Multi-entry observations require independent single-entry queries and unrelated occupied negative controls.
- The Tokyo/date/weather field must use arms of length at least two, not a center-plus-neighbor star.
- Persist raw validated Sculptor evidence at runtime; do not rely only on post-hoc log recovery.
- Do not add Lens persistence, Topic/Entity indexes, fact-to-entry maps, vectors, graphs or multi-cell Atoms.
```

---

# 5. 全部模块任务前完成度

审核后基线：

| 模块 | 生命周期 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `IMPLEMENTED` | 88% | 中高 | V3.9几何、候选原型 | Junction非多关系交汇 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes | 增量/版本 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 独立合同 | 长期metrics | 否 |
| ACCESS | `IMPLEMENTED` | 85% | 中 | Atlas/Lens/Admission原型 | Lens无因果绑定，Atlas不扩展 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `IMPLEMENTED` | 88% | 中高 | Dream Sculptor/fast Recall | Wire需Rev1，raw evidence | 是 |
| LAB | `IMPLEMENTED` | 82% | 中 | synthetic/live基础 | 自证、无counterfactual | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 90% | 中高 | plugin/policy | Rev1 schema/budgets | 是 |

---

# 6. 任务后目标完成度

| 模块 | 任务前 | 目标 | 增量 | 本任务交付 | 剩余限制 |
|---|---:|---:|---:|---|---|
| CORE | 88% | 96% | +10向量 | relation-group true Junction | multi-cell、多层 |
| SNAPSHOT | 50% | 50% | 0 | 回归 | 增量 |
| TRACE | 40% | 40% | 0 | 回归 | metrics |
| ACCESS | 85% | 96% | +15向量 | hierarchical Atlas、Lens编译 | 长期规模 |
| HISTORY | 10% | 10% | 0 | 无 | 暂停 |
| AUDIT | 10% | 10% | 0 | 无 | 暂停 |
| OPENCLAW | 88% | 93% | +5% | Rev1 Sculptor、raw evidence | multi-provider |
| LAB | 82% | 96% | +15向量 | causal/counterfactual/self-play | 长期统计 |
| DISTRIBUTIONS | 90% | 95% | +5% | schema/budget/version | 发布 |

不写永久100%。

---

# 7. Gate 0：状态纠偏和反例固化

工作：

```text
更新 AGENTS/ACTIVE_PROJECT/STATUS/Ledger；
加入V3.11 Rev1；
将原validated状态降为checkpoint；
把以下反例写成自动测试：
  Lens A / primary B 被拒绝；
  contact改变Junction；
  stable-prefix Atlas被替代；
  star Observation不算growth；
  unrelated occupied negative。
```

PASS：

```text
旧实现上的反例能够失败；
新状态不夸大；
保护性commit。
```

---

# 8. Gate A：Lens 因果 Plan 合同

## 8.1 Wire Rev1

建议：

```text
nollm_openclaw_dream_sculptor_v2
```

每条 plan：

```text
Statement；
source_capture_ids；
ordered lenses；
action；
existing_handle（reuse/revision）；
reason。
```

删除或弃用自由：

```text
primary_candidate_id；
contact_candidate_ids。
```

Lens 中提供：

```text
atlas_path_ids；
leaf_locality_candidate_ids；
unresolved。
```

## 8.2 Access 编译

```text
ordered resolved Lenses
→ ordered relation_groups。
```

必须验证：

```text
path连续；
leaf属于path；
candidate存在；
basis exact；
groups非空；
reuse/revision Handle出现在group；
Atlas fingerprint未变。
```

## 8.3 兼容

旧 v1 Wire：

```text
仅作历史读取；
不得继续作为活动Provider输出；
迁移测试清楚。
```

PASS：

```text
Lens和Placement不再可分离；
mismatch必拒绝；
Lens删改会改变relation_groups。
```

---

# 9. Gate B：Core 真实 Junction

## 9.1 新合同

建议：

```text
RelationGroupJunctionRequest
RelationGroupJunctionCandidate
```

Codex可选择命名。

## 9.2 数学

实现V3.11 Rev1的：

```text
group distance；
all-group candidate universe；
完整评分后截断；
realized group证据；
no bounded junction。
```

## 9.3 必测

```text
primary(0,0)+contact(4,0)
→ 平衡候选优于(1,0)；

交换group顺序：
→ 几何等价结果稳定；

删除contact：
→ 结果变化；

远contact：
→ no_bounded_junction或unrealized，不冒充实现；

多cell group：
→ 取min distance；

负坐标/active radius/budget；
stdlib only；
无semantic字段。
```

PASS：

```text
contact对候选有真实影响；
候选不是primary邻接器换名。
```

---

# 10. Gate C：层级 Locality Atlas

## 10.1 来源

复用：

```text
PhysicalFieldScope；
Surface Order 0～N；
真实occupancy；
Coverage-derived projection。
```

不得重复造新语义索引。

## 10.2 结构

实现有界：

```text
AtlasNode；
AtlasPath；
leaf Locality；
fingerprint。
```

小场可扁平。

## 10.3 大场 fixture

至少：

```text
300 occupied Cells；
1000 Atoms；
相关 Locality 位于stable-key排序后半部；
Atlas仍通过层级path暴露；
初始Atlas不读取Capture语义。
```

注意：

```text
Atlas初始结构选择query-agnostic；
LLM在Prompt中根据Capture语义选择path。
```

## 10.4 性能

```text
300-cell Atlas target <=2s；
1000-atom target <=5s；
不得恢复逐页Provider导航。
```

PASS：

```text
相关区域不依赖坐标前缀；
一次Prompt可选择完整path。
```

---

# 11. Gate D：Dream Sculptor 与多Revision

工作：

```text
Prompt教Writer：
  未来Reader视角；
  ordered Lens；
  Atlas path；
  unresolved诚实；

每batch一次common Sculptor；
raw输出和validated plan实时写Evidence；
多个revision_current逐个确认；
timeout/invalid为retry并保留Pending；
partial成功不重放。
```

PASS：

```text
多revision fixture；
raw evidence可从Bundle重验；
Provider call预算不恶化。
```

---

# 12. Gate E：Synthetic Conformance

重命名：

```text
run_deterministic_self_play
→ run_synthetic_lens_contract_conformance
```

或保留旧入口做compat，但报告不得称LLM self-play。

验证：

```text
schema；
basis；
path；
relation-group编译；
Junction数学；
durable state；
Lens不持久化。
```

不输出：

```text
semantic accuracy；
wrong-locality rate；
LLM reach rate。
```

---

# 13. Gate F：真实 Writer/Reader/Critic

## 13.1 Writer

真实Host LLM：

```text
Capture+Atlas
→ Statement+Lens paths。
```

## 13.2 Reader

独立session，不见Writer plan：

```text
query+field
→ one entry
→ Core Recall。
```

## 13.3 Critic

独立session：

```text
检查Lens/geometry/Reader因果；
比较counterfactual；
输出Lab-only结论。
```

最低：

```text
30 Provider-backed cycles；
10类场景；
至少10个短期完整事实；
至少5个unresolved；
至少5个多relation group；
至少5个no bounded junction。
```

报告：

```text
Lens-plan consistency；
Reader single-entry success；
counterfactual sensitivity；
unrelated false reach；
Provider failures。
```

---

# 14. Gate G：东京—时间—天气长分支场

新工作区：

```text
nollm-caold-lens-causal-junction-growth-v2
```

## 14.1 正常聊天

不得命令坐标或动作。

形成：

```text
T0东京下雨；
东京arm >=2；
时间arm >=2；
天气arm >=2；
unrelated arm >=2。
```

## 14.2 真实放置

每条事实：

```text
Provider Writer；
层级Atlas；
Lens relation groups；
Core true Junction；
durable Admission；
restart。
```

## 14.3 Recall

三次独立新Session：

```text
从三个arm外端；
path length>=2；
一个entry；
同一T0 Handle。
```

负对照：

```text
unrelated arm外端；
同预算不达T0。
```

如果字段过小导致广播：

```text
扩大arm；
降低验证budget；
不得放宽为任意可达。
```

## 14.4 NONE

无关问题返回NONE或不注入目标。

---

# 15. Gate H：回归和交付

执行：

```text
Core；
Snapshot；
Trace；
Access；
OpenClaw Python；
OpenClaw Node；
M0；
V3.9；
V3.10；
revision；
dense；
Manifest；
boundaries；
compile/build；
Git diff/status。
```

最终报告：

```text
docs/project/CAOLD_LENS_CAUSAL_TRUE_JUNCTION_HIERARCHICAL_ATLAS_REPORT.md
```

Evidence：

```text
validation/caold_lens_causal_true_junction_20260718.jsonl
validation/caold_lens_causal_true_junction_summary_20260718.json
```

Freeze：

```text
raw Writer/Reader/Critic outputs；
hash；
line/bytes/SHA；
Report；
Manifest；
Git blob复算。
```

---

# 16. 独立验收标准

必须同时满足：

```text
Lens A / Placement B不能通过；
contact relation改变Core结果；
真实Junction平衡多组；
Atlas不再是stable-key前缀；
大场相关Locality可见；
synthetic不冒充self-play；
真实Writer/Reader/Critic；
长分支三入口；
unrelated branch负对照；
one Statement/Atom/Cell；
Lens不持久化；
single-entry；
隐藏Recall<=1；
Capture/worker不回退；
多revision正确；
Manifest/boundary/clean/Bundle。
```

---

# 17. 停止条件

只有：

```text
真实关系组无法在不向Core传语义的情况下表达；
层级Atlas必须引入语义索引才能暴露Locality；
one-cell模型无法产生任何可区分分支；
现有Surface无法形成有界层级Atlas；
数据会丢失或旧workspace会损坏。
```

才停止。

普通Prompt、JSON、测试、性能、命名问题直接修复继续。

如one-cell模型确实被证伪：

```text
提交IN_PROGRESS Bundle；
用证据建议下一任务研究multi-cell footprint；
本任务不得静默实现multi-cell。
```

---

# 18. 完成状态

全部通过：

```text
LLM_RECALL_LENS_CAUSALLY_COMPILED_TRUE_JUNCTION_GROWTH_VALIDATED_AT_<HEAD>
```

否则：

```text
CAOLD_LENS_CAUSAL_JUNCTION_GROWTH_IN_PROGRESS_AT_<HEAD>
```

无论完成与否：

```text
commit；
clean；
完整历史Bundle；
不补造。
```

---

# 19. 明确非目标

```text
multi-cell footprint；
多物理层Placement；
Stitch/Bridge重构；
多Chart；
持久Lens；
Topic/Entity；
query route；
fact-to-entry；
vector/graph/embedding；
multi-entry Recall；
PB；
正式发布；
更换Provider。
```

---

# 20. Git Bundle

建议：

```text
nollm_caold_lens_causal_true_junction_hierarchical_atlas_20260718_<shorthead>.bundle
```

最终回复只报告：

```text
branch/HEAD；
Lens causal contract；
true Junction；
hierarchical Atlas；
Writer/Reader/Critic；
Tokyo/date/weather long arms；
negative control；
calls/performance；
tests/manifest/boundary；
actual vector/completion；
limitations；
Bundle/SHA。
```
