# Nollm CAOLD：字段完整 Atlas、已实现 Junction 与真实 Writer→Field→Reader 因果闭环任务书

**任务文件名**：`NOLLM_C_A_O_L_D_FIELD_COMPLETE_ATLAS_REALIZED_JUNCTION_CAUSAL_WRITER_READER_TASK_20260718.md`  
**日期**：2026-07-18  
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**任务性质**：V3.11 Rev2 因果正确性闭环；不扩张到 multi-cell、多物理层或 Stitch  
**输入 Bundle**：`nollm_caold_lens_causal_true_junction_hierarchical_atlas_20260718_440b7d4.bundle`  
**输入 Bundle SHA-256**：`f6d640f1581e59628e355291827944ad302b007534befaba769d4a0cf5d7b335`  
**输入分支**：`codex/caold-lens-causal-true-junction-hierarchical-atlas`  
**输入 HEAD**：`440b7d43ade67a2c1b8f67aa0fabf24c2b7297ef`  
**输入 Tag**：`CAOLD_LENS_CAUSAL_JUNCTION_GROWTH_IN_PROGRESS_AT_440b7d4`  
**建议分支**：`codex/caold-field-complete-atlas-realized-junction-causal-loop`  
**主环境**：Windows 10/11、PowerShell、Node 24、真实 OpenClaw / LongCat-2.0  
**交付**：大跨度单任务；内部 Gate；普通问题就地修复；所有真实进展 commit；clean tree；仓库外单一完整历史 Git Bundle  
**插件状态**：保持安装并启用  
**数据状态**：旧工作区全部保留；新建 Rev2 工作区  
**能力边界**：只验证 layer-0、one Statement/Atom/Cell；不实现 multi-cell footprint、多物理层、Stitch、Topic/Entity 或语义索引

---

# 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +10% | DISTRIBUTIONS +5%

主方向：
Atlas 从“有限抽样”改为“有限但字段完整”；
Core 只输出真实接触全部关系组的 Junction；
Access 拒绝 partial Junction；
Provider Writer 的 plan 实际写入同一字段；
独立 Reader 从该字段单入口召回；
用因果反事实和真实长分支决定 one-cell 模型是否成立。

范围变化：
V3.11 Rev1 保留；
新增 Atlas coverage certificate 和 realized-junction 硬合同；
不新增 Lens 类型、持久状态或产品模块。
```

## 0.1 Gate 向量复述

每个 Gate 开始：

```text
C +5 | S 0 | T 0 | A +10 | H 0 | U 0 | O +5 | L +10 | D +5
```

每个 Gate 结束：

```text
实际向量；
公共合同变化；
字段覆盖率；
partial Junction 数；
Provider causal cycles；
是否证伪 one-cell 模型。
```

偏差超过5%或新增模块必须更新任务范围。

---

# 1. 输入审核事实

## 1.1 基础现场

```text
Bundle verify：通过；
完整历史：是；
SHA-256：
f6d640f1581e59628e355291827944ad302b007534befaba769d4a0cf5d7b335；

HEAD：
440b7d43ade67a2c1b8f67aa0fabf24c2b7297ef；

branch：
codex/caold-lens-causal-true-junction-hierarchical-atlas；

tag：
CAOLD_LENS_CAUSAL_JUNCTION_GROWTH_IN_PROGRESS_AT_440b7d4；

working tree：
clean。
```

独立复现：

```text
关键 Rev1 tests：
20 passed；

Manifest：
tracked=1952；
rows=1952；
unclassified=0；

production violations=0；
production cycles=0。
```

## 1.2 应保留成果

```text
Lens→relation groups；
自由 primary/contact 字段已退出 V2 Wire；
Core 全 relation-group candidate universe；
Lens exact Capture spans；
operation-local Atlas/Lens；
Synthetic long-arm；
Provider raw evidence；
Evidence SHA/bytes/lines一致；
即时 Capture与异步吸收基础。
```

## 1.3 新 P0

### P0-A：Atlas 不是字段完整层级

当前 300 occupied Cell 实测：

```text
Atlas candidates = 32；
Atlas nodes = 64；
Atlas paths = 32；
candidate geometry exposed cells = 59；
uncovered occupied cells = 241。
```

当前算法：

```text
atlas_order = 0 if occupied<=limit else 1；
读取所有 order1 projections；
even_sample 到32；
每个 projection 再 even_sample 最多4个 source Cells。
```

因此：

```text
既没有选择可容纳全部 projections 的更粗 Order；
也没有覆盖未采样 projections；
parent/leaf path 只属于被抽中的 projections。
```

`final_stable_key_cell_exposed=true` 只是端点被 even sample 选中，不是完整性证明。

### P0-B：partial Junction 被当成真实 Junction

Core 对 groups `(0,0)` 与 `(6,0)`、`contact_radius=2` 返回：

```text
Cell (2,0)
group_distances = (2,4)
groups_within_contact_radius = 1
all_groups_realized = false
```

Access 会直接选择第一候选并写入。

这违反：

```text
resolved Lens必须真实接触。
```

### P0-C：Provider Reader 与 Writer 无因果连接

当前 Lab `_prepare()`：

```text
Writer workspace：
只构建空 Atlas，调用 Writer。

Reader workspace：
脚本直接 apply target Statement；
脚本直接 apply unrelated Statement；
再调用 Reader。
```

Writer raw plan 没有被 apply 到 Reader workspace。

因此：

```text
Reader 10/10 与 Writer Lens/Junction 无关。
```

### P0-D：Provider long-arm 未执行

现有 long-arm：

```text
provider_backed=false；
脚本 direct Core.put target/unrelated seed；
脚本按预定 anchor选择 candidate。
```

仍是合成合同，不是 Provider逆向生长。

### P1

```text
Critic 9/10 fenced JSON被判无效；
Writer平均112秒；
Provider harness保留两次失败尝试并追加同一Evidence；
Live main agent产生一个普通OpenClaw memory文件；
当前报告完成度偏高；
Core API仍会返回部分超max_radius的非首候选。
```

---

# 2. 当前能力重新定性

记录：

```text
LENS_RELATION_GROUP_AND_JUNCTION_PROTOTYPE_CHECKPOINT_AT_440b7d4
```

建议实际推进：

```text
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +7% |
HISTORY 0% | AUDIT 0% | OPENCLAW +3% |
LAB +5% | DISTRIBUTIONS +3%
```

建议完成度：

| 模块 | 当前 |
|---|---:|
| CORE | 90% |
| SNAPSHOT | 50% |
| TRACE | 40% |
| ACCESS | 88% |
| HISTORY | 10% |
| AUDIT | 10% |
| OPENCLAW | 90% |
| LAB | 85% |
| DISTRIBUTIONS | 92% |

---

# 3. 开工依据

按顺序读取：

```text
FIRST_PRINCIPLES；
PROJECT_BOOK V3.1；
CORE_FUNCTION_PRIORITY V3.4；
V3.7 physical architecture；
V3.9 approximate Coverage；
V3.10 Capture；
V3.11 Rev2；
CURRENT_STATUS；
canonical Ledger；
本任务书；
C/A/O/L/D charters；
AGENTS。
```

---

# 4. `AGENTS.md`

至少加入：

```text
- An Atlas is active only when its coverage certificate shows zero uncovered occupied Cells.
- Never even-sample or stable-key-sample Surface projections and call the result field-complete.
- Choose the finest Surface Order whose entire non-empty projection set fits the Atlas budget.
- If no supported Order fits, return explicit Atlas overflow and defer; do not sample.
- A resolved Lens is not geometrically realized until the selected Junction is within contact_radius of every relation group.
- Access must never apply an all_groups_realized=false Junction.
- Core must not expose active candidates outside max_radius.
- Provider Writer/Reader validation must use one causal workspace: apply Writer, reopen, then Reader.
- Do not preseed the Reader target independently of Writer.
- Counterfactual and Reader must use the same final field and RecallBudget.
- Synthetic direct seeds are conformance only, not Provider long-arm evidence.
- Preserve one Statement/Atom/Cell and operation-local Lens.
```

---

# 5. 全部模块任务前完成度

| 模块 | 生命周期 | 当前完成度 | 置信度 | 主要缺口 | 影响 |
|---|---|---:|---|---|---|
| CORE | IMPLEMENTED | 90% | 中高 | partial Junction可写 | 是 |
| SNAPSHOT | IMPLEMENTED | 50% | 中高 | 增量 | 否 |
| TRACE | IMPLEMENTED | 40% | 中 | metrics | 否 |
| ACCESS | IMPLEMENTED | 88% | 中 | Atlas不完整、partial apply | 是 |
| HISTORY | PROPOSED | 10% | 低 | 暂停 | 否 |
| AUDIT | PROPOSED | 10% | 低 | 暂停 | 否 |
| OPENCLAW | IMPLEMENTED | 90% | 中高 | causal Provider loop未连通 | 是 |
| LAB | IMPLEMENTED | 85% | 中 | Writer/Reader解耦、无Provider long-arm | 是 |
| DISTRIBUTIONS | IMPLEMENTED | 92% | 中高 | Rev2 schema/policy | 是 |

---

# 6. 任务后目标完成度

| 模块 | 前 | 目标 | 交付 |
|---|---:|---:|---|
| CORE | 90 | 95 | realized-only Junction |
| SNAPSHOT | 50 | 50 | 回归 |
| TRACE | 40 | 40 | 回归 |
| ACCESS | 88 | 96 | field-complete Atlas、拒绝partial |
| HISTORY | 10 | 10 | 无 |
| AUDIT | 10 | 10 | 无 |
| OPENCLAW | 90 | 94 | causal Writer/Reader runtime evidence |
| LAB | 85 | 95 | end-to-end causal and long-arm |
| DISTRIBUTIONS | 92 | 96 | Rev2 contracts |

不写永久100%。

---

# 7. Gate 0：状态与反例

新增自动反例：

```text
300 Cells Atlas uncovered=241；
groups distance(0,6) partial candidate；
Writer plan未apply却Reader成功；
same-field Reader/counterfactual identity。
```

更新：

```text
AGENTS；
ACTIVE_PROJECT；
STATUS；
Ledger；
Rev2 architecture；
checkpoint commit。
```

---

# 8. Gate A：字段完整 Atlas

## 8.1 Order选择

实现：

```text
从Order0开始；
计算完整non-empty projection count；
选择第一个<=node_budget的Order；
包含该Order全部projections。
```

不得 even_sample projections。

## 8.2 overflow

最大支持Order仍超预算：

```text
status=atlas_overflow；
记录counts；
Dream Sculptor defer/retry；
不生成抽样Atlas。
```

## 8.3 coverage certificate

Atlas映射必须包含：

```text
occupied_field_cell_count；
covered_field_cell_count；
uncovered_field_cell_count；
selected_order；
region_count；
overflow。
```

必须机器验证 source-cell union。

## 8.4 region support

每region：

```text
完整source_cell_count；
有限support cells；
support method/version；
representatives从完整region选择。
```

不得把support当完整leaf。

## 8.5 大场

```text
300 Cells /1000 Atoms；
uncovered=0；
相关Cell放在任意位置仍属于某region；
Core state不变；
<=5秒。
```

---

# 9. Gate B：realized-only Junction

## 9.1 Core

过滤：

```text
max_group_distance<=max_radius；
多组 all_groups_realized=true；
单组 distance<=contact_radius。
```

允许诊断partial，但活动候选分开。

## 9.2 Access

```text
只apply realized candidate；
无realized candidate→lens_geometry_unrealized；
一次correction或retry；
零写入。
```

## 9.3 测试

```text
(0,0)+(6,0),contact2→无可写Junction；
(0,0)+(4,0),contact2→平衡Cell；
删除group→结果变；
替换无关group→defer；
所有返回candidate预算合法。
```

---

# 10. Gate C：Provider causal Writer→Field→Reader

## 10.1 场景流程

每case：

```text
初始背景字段；
Capture；
Writer Atlas；
Provider Writer；
validate；
apply Writer plans；
durable reopen；
Reader prompt来自该字段；
独立Provider Reader；
Core Recall；
same Writer target Handle。
```

## 10.2 无关分支

在Writer之前或通过独立正常Capture形成：

```text
unrelated branch。
```

不得在Reader阶段脚本直接放 target。

## 10.3 Evidence

每case冻结：

```text
initial state SHA；
Atlas certificate；
Writer raw/validated；
Junction realized evidence；
durable target Handle；
final state SHA；
Reader raw/entry/path；
counterfactual entry/path；
Lens ablation。
```

## 10.4 Minimum

至少10 cases：

```text
10 valid Writer durable；
10 Reader target reach；
10 unrelated false reach=0；
>=5 multi-group realized；
>=3 atlas unresolved/geometry unrealized诚实defer；
Provider failures分开。
```

Critic不是硬正确性来源。

---

# 11. Gate D：Provider causal long arms

## 11.1 工作区

新建：

```text
nollm-caold-field-complete-atlas-realized-junction-v3
```

## 11.2 全部事实走正常链

禁止：

```text
direct Core.put semantic seed；
脚本选择relation candidate；
复制Statement。
```

允许只用公共Host/Capture/worker/Access。

## 11.3 场

```text
T0；
东京>=2；
时间>=2；
天气>=2；
unrelated>=2。
```

## 11.4 Recall

```text
三个外端；
一个entry；
path>=2；
同一T0；
unrelated不达；
restart后重复；
NONE。
```

## 11.5 one-cell证伪

在限定尝试内真实Writer无法形成分支：

```text
保持IN_PROGRESS；
记录为什么；
下一任务才讨论multi-cell footprint。
```

---

# 12. Gate E：V3.10/V3.11回归

必须保持：

```text
Capture快速；
scope安全；
turn幂等；
worker drain/retry；
provenance/partial；
revision确认；
Pending+geometry；
hidden recall<=1；
Lens不持久化；
one Atom/Cell；
single-entry。
```

多revision timeout必须retryable。

---

# 13. Gate F：证据和交付

主报告：

```text
docs/project/CAOLD_FIELD_COMPLETE_ATLAS_REALIZED_JUNCTION_CAUSAL_LOOP_REPORT.md
```

Evidence：

```text
validation/caold_field_complete_atlas_causal_loop_20260718.jsonl
validation/caold_field_complete_atlas_causal_loop_summary_20260718.json
```

冻结：

```text
结束Live；
冻结raw；
计算line/bytes/SHA；
报告；
Manifest；
Git blob复算；
commit；
Bundle。
```

---

# 14. 完成 Gate

全部满足：

```text
Atlas uncovered=0；
无projection sampling；
overflow诚实；
partial Junction不可写；
Writer真正改变Reader字段；
Reader目标来自Writer Handle；
counterfactual同字段不达；
Lens ablation改变几何或结果；
Provider long arms；
unrelated负对照；
restart；
Core/Access/OpenClaw/Lab/Node/M0回归；
Manifest/boundary/clean/Bundle。
```

完成状态：

```text
FIELD_COMPLETE_ATLAS_REALIZED_JUNCTION_CAUSAL_WRITER_READER_VALIDATED_AT_<HEAD>
```

否则：

```text
CAOLD_FIELD_COMPLETE_ATLAS_CAUSAL_LOOP_IN_PROGRESS_AT_<HEAD>
```

---

# 15. 非目标

```text
multi-cell footprint；
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
正式发布。
```

---

# 16. Git与Bundle

建议提交：

```text
checkpoint(caold): adopt field-complete causal-loop rev2
fix(access): build coverage-complete locality atlas
fix(core): expose realized junction candidates only
fix(access): reject unrealized lens geometry
test(lab): connect provider writer field reader causally
test(caold): grow provider-backed long arms
docs(caold): record field-complete causal capability
```

最终Bundle：

```text
nollm_caold_field_complete_atlas_realized_junction_causal_loop_20260718_<shorthead>.bundle
```

最终回复：

```text
branch/HEAD；
Atlas coverage；
Junction realized；
Writer→Field→Reader；
counterfactual；
long arms；
one-cell结论；
calls/performance；
tests/manifest/boundary；
actual vector/completion；
limitations；
Bundle/SHA。
```
