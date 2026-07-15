# Nollm C/A/O/L/D：广域余量校准、安全物理场与密集局部单入口召回任务书

**任务文件名**：`NOLLM_C_A_O_L_D_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_RECALL_TASK_20260715.md`  
**日期**：2026-07-15  
**性质**：V3.9 能力加固与真实密集场验证；不是 Stitch、换层 Placement、PB 长跑或正式发布任务  
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**输入 Bundle**：`nollm_v39_bounded_approximate_coverage_lazy_surface_20260715_5a45384.bundle`  
**输入 Bundle SHA-256**：`e95f13582e79d24708d14189f1f2d23e7bb80e3126c3d3f9a492f47005f8225f`  
**输入分支**：`codex/caold-bounded-approximate-coverage-lazy-surface`  
**输入 HEAD**：`5a453847747a7f460ce37df044dec50c554b494b`  
**输入能力 Tag**：`FAST_BOUNDED_APPROXIMATE_COVERAGE_SURFACE_VALIDATED_AT_5a453847747a7f460ce37df044dec50c554b494b`  
**建议工作分支**：`codex/caold-broad-residue-safe-field-dense-locality`  
**主执行环境**：Windows 10/11、PowerShell、Python 3.13、Node 24、当前真实 OpenClaw 环境  
**交付要求**：所有真实进展提交；工作树干净；仓库外生成并验证单一完整历史 Git Bundle；未完成也交付 `IN_PROGRESS` Bundle  
**插件最终状态**：保持安装和启用  
**数据最终状态**：旧 V3.8/V3.9 工作区、Statement、HandleBinding、Core canonical state 和插件配置均保留；不得清空或覆盖  

---

# 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +10% | DISTRIBUTIONS +5%

主方向：
扩大 K=96 近似 Coverage 的余量统计校准；
把“存储/传输地址域”与“当前两步 Coverage 可闭合的活动写入场”分开；
修正 relation-threshold、状态权威和占用语义；
在不引入 Stitch、换层 Placement、Cursor 或多入口扇出的前提下，
验证密集 layer-0 Locality 的惰性 Surface、单入口自然传播和真实 OpenClaw Recall。

范围变化：
V3.9 仍为活动架构；
5a45384 保留为快速有界 Coverage 与 Lazy Surface 检查点；
其“96 个 fixture 已足以证明 p99<=2%”和“整个 hex radius 2^31-1 均可正常执行双向 Coverage”
降为有限窗口观察，不再作为全活动域能力；
本任务新增可写场边界、广域 residue 校准和密集 Locality 能力，不改变硬物理参数。
```

## 0.1 Gate 向量复述

每个 Gate 开始时记录：

```text
当前预计向量：
C +5 | S 0 | T 0 | A +5 | H 0 | U 0 | O +5 | L +10 | D +5

当前主方向：
广域校准 → 安全写入场 → 近似核 Policy 选择 → 密集 Locality → 单入口 Live。
```

每个 Gate 结束时记录：

```text
实际受影响模块；
预计与实际偏差；
是否出现超过 5% 的模块偏差；
是否新增 canonical state、Wire 或模块依赖；
是否错误引入 Stitch、换层 Placement、持久 Surface cache 或语义索引。
```

不得静默扩大到 Snapshot、Trace、History、Audit、Stitch、多 Chart 或多物理层语义 Placement。

---

# 1. 可验证结果

本任务的最终可验证链路为：

```text
5a45384 快速 K=96 Coverage
→ 广域 residue-stratified Oracle 校准
→ 选择有证据的 min-hit / relation-threshold Policy
→ 存储地址域与 Coverage-safe 写入场分离
→ 当前 RecallBudget 双向两步传播在写入场内闭合
→ 真实 dense/sparse Core fixtures
→ Lazy Surface 继续满足预算且不重建全部 Orders
→ occupancy_band 不冒充物理 density
→ 单入口 Recall 在密集 Locality 中稳定找到目标事实
→ 多入口仅作为多次独立单入口运行的观察
→ 真实 OpenClaw R1/R2/R3/P1 与密集查询
→ 状态、Ledger、Manifest、Bundle 收口。
```

完整通过必须至少证明：

```text
1. 覆盖校准矩阵不再只有 96 个手选 fixture；
2. Broad calibration 的样本生成、种子、residue 覆盖和指标可复现；
3. relation threshold/min-hit 由 Broad calibration 选择，不由旧任务数字固定；
4. active writable field 对当前 max_layer_delta=2 的双向传播闭合；
5. 合法可写地址不会在当前 Recall/Surface 中因 target 越界而失败；
6. 存储/传输边界以外仍明确拒绝；
7. dense fixture 不依赖 Topic/Source/Entity、Cursor、Anchor、vector 或 Python 语义路由；
8. 一次 Recall Traversal 最终只选择一个 physical entry；
9. 自然多入口不设最低数量、不作为通过条件、不持久化 fact→entries；
10. 当前状态不存在 `<FINAL_DELIVERY_HEAD>`、`保持封板` 或重复活动 Ledger；
11. 所有进展 commit，clean tree，完整历史 Bundle 验证通过。
```

---

# 2. 活动依据与优先级

开始执行前必须按顺序读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_7_ROTATED_MULTI_SCALE_PHYSICAL_MEMORY_FIELD_20260714.md
3. docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_9_BOUNDED_APPROXIMATE_HEX_COVERAGE_20260715.md
4. docs/project/NOLLM_ROUTE_BOOK_V3_7_ROTATED_PHYSICAL_FIELD_SINGLE_ENTRY_RECALL_20260714.md
5. docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md
6. docs/project/ACTIVE_PROJECT.md
7. docs/project/NOLLM_CURRENT_STATUS.md
8. 当前唯一 canonical 模块进度账
9. 本任务书
10. C/A/O/L/D 模块章程
11. 根目录 AGENTS.md
```

冲突解释：

```text
第一性原理 > V3.7 硬物理与单入口架构
> V3.9 有界近似 Coverage 修订
> 本任务对校准样本、地址 Policy 和密集场 Gate 的变化量
> 当前状态 > 历史报告和历史任务。
```

必须在 `AGENTS.md` 中保留并强化：

```text
- Δθ=22.5°、β=2^(1/4)、β²=√2 不得改变；
- Production Coverage 可以近似，但必须有独立 Oracle 和误差报告；
- 误差 Gate 由广域校准 Policy 决定，不得只用手选小样本；
- storage/transport radius 与 active writable radius 必须分开；
- 一次 Traversal 一个最终 physical entry；
- 自然多入口是 Observation/Hypothesis，不是 Invariant；
- 不得使用“封板”“100% 永久完成”；
- 审核通过后必须直接生成下一任务书，但任务不得机械继承旧目标。
```

---

# 3. 输入基线与独立审核事实

## 3.1 Git 基线

```text
Bundle SHA-256:
e95f13582e79d24708d14189f1f2d23e7bb80e3126c3d3f9a492f47005f8225f

Branch:
codex/caold-bounded-approximate-coverage-lazy-surface

HEAD:
5a453847747a7f460ce37df044dec50c554b494b

Tag:
FAST_BOUNDED_APPROXIMATE_COVERAGE_SURFACE_VALIDATED_AT_5a453847747a7f460ce37df044dec50c554b494b

Working tree:
clean

Bundle:
complete history, verified
```

## 3.2 已复现工程结果

在外部 Linux 审核环境已复现：

```text
Core + Snapshot + Trace + Access + OpenClaw Python:
191 passed, 8 warnings

V3.9 calibration:
passed

V3.9 benchmark:
small 11 cells ≈ 12.9 ms
217 cells ≈ 524.8 ms

Manifest:
tracked 1835 = rows 1835
unclassified = 0
production violations = 0
production cycles = 0
```

M0 全量在外部 Linux 环境因活动 entrypoint 导入长时间未完成；Bundle 报告记录 Windows 45 passed。该项属于环境复现限制，不得补写为本次外部复现成功。

## 3.3 已验证并应保留

```text
K=96 fixed-point equal-area microtriangle Coverage；
生产路径无 Decimal/polygon/sin/cos；
Δθ、β、β² 保持；
GeometryAddress / SurfaceAggregateAddress 分离；
PhysicalEntryCandidate 与单入口 Wire；
无 Cursor、select_entries、Topic/Source/Entity route；
Lazy Surface Order 逐阶构建；
小场和 217-cell benchmark 大幅加速；
R1/R2/R3/P1 和重启 Recall 报告证据；
Statement/Handle/Core 非破坏迁移；
OpenClaw 只依赖 Access；
旧 exact polygon 保留为 Lab Oracle。
```

## 3.4 新发现、必须修正的事实

### 3.4.1 96 个 hand-picked fixtures 不足以证明广域 p99

独立 512 样本广域抽样：

```text
有效 Coverage 样本：434
因 target 超出活动半径而 unsupported：78

missed_mass p95 ≈ 1.6301%
missed_mass p99 ≈ 2.1371%
missed_mass max ≈ 4.0140%

total_variation p95 ≈ 2.2712%
total_variation p99 ≈ 2.8102%
total_variation max ≈ 4.0140%

dominant-target agreement ≈ 99.08%
false_mass max = 0
fanout max = 7
```

结论：

```text
K=96 方法本身仍表现良好；
但当前 `missed_mass_p99 <= 2%` 结论对更广 residue 分布略微失败；
不得继续把 96 个 fixture 的 p99 当成整个活动域统计结论。
```

### 3.4.2 min-hit 仍是 Policy，不是数学常量

在安全内域的独立抽样中：

```text
min_hit_count = 1：
missed p99 约 1.41%，max 约 1.64%；
TV p95 约 1.86%；fanout max 7；false mass max 0。

min_hit_count = 2：
missed p99 约 2.10%，max 约 2.14%；
TV p95 约 2.17%；fanout max 7；false mass max 0。
```

这不是最终选择结论，只证明：

```text
现有 `relation_threshold≈2% / min_hit=2` 不应永久固化；
应在更广 matrix 中比较 min_hit=1 与 2，再选择 Policy。
```

### 3.4.3 当前 2^31−1 地址域对 Coverage 不闭合

当前允许构造：

```text
hex radius <= 2^31 - 1
```

但靠近边界的合法 source 执行 `coverage_down` 时会生成超过该半径的 target，导致 `UnsupportedPhysicalCoverage`。

独立随机样本中约 15% 的均匀合法地址发生该边界失败。该比例不代表真实用户分布，但证明：

```text
storage/transport legal domain
≠
current Coverage-safe writable field。
```

### 3.4.4 Fixed-point 与 float prototype 在大坐标存在一采样点级差异

在 20,000 个广域随机 source 中：

```text
有效样本：17,091
boundary unsupported：2,909
production/prototype hit-count mismatch：683（约 4.0%）
```

多数差异为一个采样点在相邻 target 之间移动，属于允许的固定点边界量化现象。不得再要求 production 与 float prototype 全地址逐项相同；应分别对照 Oracle 计算权重误差。

### 3.4.5 文档状态存在不一致

当前仓库同时存在：

```text
ACTIVE_PROJECT: IN_PROGRESS
NOLLM_CURRENT_STATUS: VALIDATED_AT_<FINAL_DELIVERY_HEAD>
canonical ledger 文件仍为 V3.8
另有 V3.9 ledger 副本
V3.9 ledger 多次使用“保持封板”
```

这违反：

```text
活动指针唯一；
状态只记录真实 HEAD；
进度账持续维护；
能力验证不等于 sealed/final。
```

---

# 4. 任务前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 90% | 中高 | K=96 fixed-point Coverage、原子状态、Lazy Surface、单入口 bounded Recall | 广域 p99 证据不足；合法域非 Coverage 闭合；occupancy band 冒充 density | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | state bytes 回归 | 版本与增量 Snapshot | 否，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 状态隔离 | 长期性能观察 | 否，仅回归 |
| ACCESS | `CAPABILITY_VALIDATED` | 90% | 中高 | physical entry、Lazy Surface 编排、原子协调 | 密集 Locality 质量未验证；occupancy 语义需纯化 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `CAPABILITY_VALIDATED` | 90% | 中高 | R1/R2/R3/P1、单入口、隐藏注入 | 密集场真实 Recall 未验证；Provider latency | 是 |
| LAB | `IMPLEMENTED` | 90% | 中高 | exact Oracle、K54/K96 校准、Lazy benchmark | 校准 matrix 过小；无 residue-stratified 广域报告 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 80% | 中高 | v0.10 contracts、迁移 | 缺 safe writable field 和 threshold Policy 版本 | 是 |

说明：

```text
完成度不是撤销 5a45384 的真实能力；
它只是撤销“96 手选 fixture 足以代表广域 p99”和“2^31−1 全域可双向传播”的扩大解释。
```

---

# 5. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 90% | 95% | +5% | Broad-calibrated kernel Policy、safe writable field、纯化 occupancy band | 单元、Broad Oracle、closure fixtures、dense Surface | 多层 Placement、Stitch、持久 cache |
| SNAPSHOT | 50% | 50% | 0% | 无合同变化 | package regression | 增量 Snapshot |
| TRACE | 40% | 40% | 0% | 不新增产品 Trace | package regression | 长期性能观察 |
| ACCESS | 90% | 95% | +5% | 密集 Locality 页面、占用语义纯化、单入口稳定 Recall | dense fixtures、真实 Live | 多层语义 Placement |
| HISTORY | 10% | 10% | 0% | 无变化 | 章程回归 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 章程回归 | 暂停 |
| OPENCLAW | 90% | 95% | +5% | 密集记忆单入口 Recall、R1/R2/R3/P1 保持 | Windows Live | Provider latency、其他模型 |
| LAB | 90% | 95% | +10% | residue-stratified 广域 calibration、safe-domain proof fixtures、dense field report | JSON/Markdown runners | PB 长跑、多 Chart |
| DISTRIBUTIONS | 80% | 85% | +5% | safe writable contract、approximation Policy 版本、插件配置 | plugin check、migration | 正式发布 |

任何模块不得因任务通过宣称 sealed、final 或永久 100%。

---

# 6. 所有权与合同变化

## 6.1 Core

Core 新增并独占：

```text
storage/transport address bound；
active writable field bound；
current Recall closure depth identity；
min-hit / relation-threshold runtime Policy identity；
occupancy_band 的确定性计数语义；
Coverage-safe mutation validation；
广域 residue calibration 所需只读合同字段。
```

Core 不拥有：

```text
Oracle calibration orchestration；
语义密度；
Fact relevance；
Topic/Source/Session；
自然多入口结论；
LLM 决策。
```

## 6.2 Access

Access 新增并独占：

```text
密集 Locality 的有限 Statement 预览；
occupancy_band 的用户不可见投影；
truncated Cell 的下钻提示；
单 physical entry 的候选验证；
活动 write radius 的调用前验证和错误表达。
```

Access 不得：

```text
按关键词拆分密集场；
语义排序预览；
持久化 fact→entries；
恢复 select_entries；
把 occupancy_band 称为 physical density 或 importance。
```

## 6.3 OpenClaw

OpenClaw 保持：

```text
真实 LLM Formation/Placement/Recall；
单入口 Traversal；
隐藏注入；
失败开放；
deliver=false；
模型继承。
```

新增：

```text
密集 Cell truncated 提示；
safe writable field 错误的明确 defer；
Live 中记录初始 Order、页面数、physical entry、kernel path 和 geometry/model timing。
```

## 6.4 Lab

Lab 独占：

```text
Broad residue matrix 生成；
exact polygon Oracle；
生产 fixed-point kernel 对照；
min_hit=1/2 Policy 比较；
统计置信区间和 percentile；
safe writable field closure runner；
dense/sparse field fixtures；
自然多入口 Observation runner。
```

生产模块不得依赖 Lab。

## 6.5 Distributions

只声明：

```text
coverage method version；
min-hit/relation-threshold Policy version；
storage radius；
active writable radius；
current max coverage-down depth；
Surface budget/Wire version。
```

不得实现几何或选择器。

---

# 7. 广域 Residue 校准合同

## 7.1 目的

校准的是：

```text
在当前受支持产品域和真实 residue 分布中，
K=96 fixed-point quadrature 是否保持可接受的结构误差。
```

不是：

```text
证明所有整数坐标的 exact polygon 支持集；
证明 production 与 float prototype 每个 hit_count 相等；
证明 2^31−1 边界全部可写。
```

## 7.2 Fixture 组成

至少包含：

```text
8 个 layer phase；
coverage_up / coverage_down；
正负 layer；
原点与小坐标；
均匀 residue 样本；
大坐标但位于 safe writable field 内的样本；
六个 hex 边界方向；
接近 cube-rounding tie 的样本；
随机种子固定的样本。
```

最低建议：

```text
2048 个 exact-Oracle fixtures；
其中每个 phase × direction 至少 128 个；
另有不少于 20,000 个 production-vs-prototype 快速样本，
该快速矩阵只用于固定点实现差异诊断，不作为 exact error Gate。
```

若 Windows 运行时间过长，可拆为：

```text
Quick Gate：512 exact fixtures；
Full Gate：2048 exact fixtures。
```

最终能力结论必须来自 Full Gate。未完成 Full Gate 时交付 `IN_PROGRESS`。

## 7.3 需要比较的 Policy

固定：

```text
K=96；
硬物理参数不变；
fixed-point matrix 不变，除非发现明确实现错误。
```

比较：

```text
min_hit_count = 1；
min_hit_count = 2；
可选 min_hit_count = 1 + 明确低权重标记，而非删除。
```

不得直接提高 K 到数百点来掩盖 Policy 问题。

## 7.4 指标

必须输出：

```text
missed_mass p50/p95/p99/max；
false_mass p50/p95/p99/max；
total_variation p50/p95/p99/max；
dominant-target agreement；
fanout distribution；
threshold residual distribution；
production mean/p95/max cell time；
按 phase、direction、坐标规模分桶结果；
失败样本地址和 Oracle/production distributions。
```

## 7.5 Policy 选择规则

默认目标仍为：

```text
TV p95 <= 5%；
dominant agreement >= 95%；
false_mass p99 <= 2%；
fanout <= 8；
无长程 target；
Q16 sum = 65536。
```

`missed_mass p99` 不机械固定为 2%。执行者必须根据 Full Gate：

```text
A. 若 min_hit=1 能以相同 fanout/运行时间把 p99 稳定压到 <=2%，采用 min_hit=1；
B. 若 min_hit=1 引入不可接受的结构噪声，保留 min_hit=2，并把有证据的新 p99 阈值版本化；
C. 阈值不得宽于 3%，除非另行更新架构范围和任务向量；
D. max outlier 必须如实报告，但不自动成为失败，除非产生 dominant target 错误或长程边。
```

阈值调整是 `POLICY`，不是修改硬物理合同。

---

# 8. 安全地址域合同

## 8.1 三个不同概念

必须分开：

```text
Mathematical lattice：概念上无限；
Storage/transport radius：JSON/Node/Python 能无损表达的最大 canonical 地址；
Active writable radius：在当前 RecallBudget 和 Coverage 深度下保证传播 target 仍留在存储域的写入范围。
```

## 8.2 当前建议 Policy

保留：

```text
STORAGE_RADIUS = 2^31 - 1
```

新增：

```text
ACTIVE_WRITABLE_RADIUS = 2^30 - 1
CURRENT_MAX_COVERAGE_DOWN_STEPS = 2
```

该值为初始保守 Policy。必须用当前 fixed-point kernel 验证：

```text
六个边界方向；
全部 layer phase；
两次连续 coverage_down；
所有 retained target 均满足 STORAGE_RADIUS；
单步 coverage_up/down 均无部分传播。
```

如果执行者提出更大写入半径，必须由机器 runner 计算和验证，不得凭估计写入合同。

## 8.3 Mutation 行为

对于 `default_dream_v1` 活动 Placement：

```text
put/move/new_local/expand_surface 目标必须在 ACTIVE_WRITABLE_RADIUS；
超出时在 mutation 前明确拒绝；
不得先写入，再在 Surface/Recall 时失败；
旧工作区若存在超范围数据，不删除，标为 preserved_unsupported 并停止静默迁移。
```

直接 Core 研究调用是否允许写入 storage-only 区域，可作为私有/unsupported 研究合同，但不能进入活动 OpenClaw 组合。

## 8.4 Coverage 行为

```text
source 合法但 target 越界时，整次 expansion 明确 Unsupported；
不得返回部分 retained members；
不得 silently clamp；
不得归一化剩余 target 后继续；
错误必须携带 source、direction、required radius 和 contract id。
```

---

# 9. Occupancy 与密集 Locality 合同

## 9.1 删除错误语义

当前：

```text
count < 8 → normal
8..31 → dense
>=32 → overloaded
```

它只是计数 Policy，不是物理 density。

处理方式二选一：

```text
A. 重命名为 occupancy_band，并从几何真值字段中移除；
B. 若当前 Placement Prompt 不需要，直接删除该字段。
```

禁止继续向 LLM 表述为：

```text
physical density；
importance；
confidence；
semantic crowding。
```

## 9.2 Dense fixture

至少建立：

```text
Sparse fixture：若干隔离 Cell；
Dense-local fixture：不少于 300 occupied Cell；
Dense-atom fixture：同一 Locality 不少于 1000 MemoryAtom，分布于多个 Cell；
Boundary fixture：Locality 邻近但不跨 safe writable radius；
Unrelated locality fixture：两个无 Bridge 的隔离区域。
```

这些 fixture 可以使用确定性测试 Atom，不模拟语义 Placement。

## 9.3 Dense Surface 验收

必须记录：

```text
N0...Nk；
selected order；
overflow；
冷启动时间；
继续分页时间；
每个 Order aggregate mass；
truncated Cell 数；
最终 physical entry page 大小；
cache clear/reopen identity。
```

最低性能 Gate：

```text
300-cell fixture cold begin <= 5s；
1000-atom dense Locality cold begin <= 10s；
页面继续 <= 1s；
mutation 后结果正确失效并重建。
```

这些是当前 Python/Windows 阶段 Gate，不是永久架构上限。

---

# 10. 单入口密集 Recall 与自然多入口 Observation

## 10.1 单入口硬约束

始终：

```text
一次 Traversal 最终一个 physical entry；
AccessRecallRequest 的活动 entry_cells 长度为 1；
无 select_entries；
无 per-entry merge；
无持久 entry hints。
```

## 10.2 Dense Recall fixture

建立确定性 fixture：

```text
目标 Handle 位于密集 Locality；
入口 A 通过 Coverage/Lateral 可达；
干扰事实数量显著高于现有 Alpha/Office 小样本；
无 Topic/Source 路由；
关闭相关 kernel 后目标不可达；
开启有界 kernel 后目标可达；
结果去重只处理单入口内多路径。
```

## 10.3 自然多入口只作观察

可以运行：

```text
从入口 A 单独 Recall；
从入口 B 单独 Recall；
观察同一 Handle 是否分别可达。
```

必须记录：

```text
入口、路径、预算、是否依赖 Bridge、Locality 密度和结果。
```

不得：

```text
要求至少两个入口；
一次提交 A+B；
为制造多入口复制事实；
持久化 fact→entries；
把没有多入口认定为失败。
```

---

# 11. OpenClaw 真实验收

## 11.1 保留 Gates

必须回归：

```text
R1 Alpha；
R2 Office；
R3 NONE；
P1 Formation→Placement→Core write；
Gateway restart；
新 Session Recall P1；
插件保持 enabled；
旧工作区保留。
```

## 11.2 新密集场 Live

在独立新工作区或 V3.9 工作区的非破坏副本中：

```text
增加一组同一主题但相互独立的 MemoryStatement；
Statement 数量以能形成明显 truncated Locality 为准，建议 12～24 条；
真实 LLM 仍负责 Formation/Placement；
不要求一次完成全部，可分多轮自然对话积累；
每轮进展均允许 commit/记录；
最终用一个新 Session 单入口 Recall 回答跨多条事实的问题。
```

由于真实模型成本较高，本 Live 不要求数百条；大规模结构由 Lab fixture 验证。

## 11.3 Timing

至少记录：

```text
surface_build_ms；
surface_order_count；
surface_projection_count；
surface_page_count；
physical_entry_resolution_ms；
recall_core_ms；
recall_agent_ms；
formation_ms；
placement_subagent_ms；
placement_apply_ms；
total_operation_ms。
```

模型延迟与几何延迟必须分开，不得因 Provider 慢否定几何能力，也不得用 Provider 慢掩盖几何回退。

---

# 12. 文档与状态收口

必须修改：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
根 AGENTS.md
V3.9 架构修订（仅新增 broad calibration / safe field 合同）
V3.9 路线书（仅调整下一阶段和防复发 Gate）
任务报告
```

必须处理：

```text
删除 `<FINAL_DELIVERY_HEAD>` 占位符；
canonical Ledger 更新为本任务最新实际值；
V3.8/V3.9 副本 Ledger 标为 HISTORICAL 或删除活动指针；
删除“保持封板”；
LAB 不轻率写 100%；
Tag/状态只证明实际能力；
ACTIVE_PROJECT 只指向一个活动任务。
```

第一性原理第 9 节和第 10 节增加明确解释：

```text
第 9 节的 exact support 检查适用于 Oracle 和方法校准；
Production Approximate Coverage 按第 10 节的 weighted-error Gate 评价；
二者不冲突，不得恢复生产 polygon，也不得取消独立 Oracle。
```

---

# 13. 资产分类

## 13.1 KEEP_ACTIVE

```text
K=96 fixed-point quadrature；
source-local sample offsets；
Q24.40 transforms；
deterministic cube rounding；
Q16 normalization；
Physical/Surface address separation；
Lazy Surface；
PhysicalEntryCandidate；
单入口 Wire；
R1/R2/R3/P1；
历史 polygon Oracle；
无 Cursor/Anchor route。
```

## 13.2 PUREFY

```text
relation_threshold/min_hit Policy；
coordinate domain contract；
density_state → occupancy_band 或删除；
current status/ledger；
第一性原理第 9/10 节关系；
能力 Tag 名称。
```

## 13.3 ADD

```text
Broad calibration runner；
residue-stratified fixture generator；
safe writable field constants；
Coverage closure runner；
dense Locality fixtures；
natural multi-entry observation runner；
dense OpenClaw report。
```

## 13.4 PAUSE

```text
Stitch/Unstitch；
多物理层语义 Placement；
多 Chart；
持久 Surface cache；
PB 长跑；
History/Audit 产品；
正式发布。
```

---

# 14. 内部 Gate 与实施工作流

## Gate 0：活动依据与状态纠偏

工作：

```text
核验 Bundle/HEAD/Tag/clean tree；
更新 AGENTS；
激活本任务；
将 5a45384 记录为检查点而非永久封板；
合并 canonical Ledger；
记录独立审核 broad-sample 事实；
形成 checkpoint commit。
```

建议提交：

```text
checkpoint(caold): activate broad calibration and dense locality route
```

PASS：

```text
活动任务唯一；
无 placeholder；
无“保持封板”；
V3.9 硬物理和近似路线不回退。
```

## Gate 1：Broad Residue Calibration

工作：

```text
实现 deterministic residue fixture generator；
2048 exact fixtures；
20k fast production/prototype diagnostics；
比较 min_hit=1/2；
输出分桶指标、worst cases 和运行成本；
选择并版本化 Policy。
```

建议提交：

```text
test(lab): calibrate broad residue coverage policy
```

PASS：

```text
Full Gate 完成；
指标来自 exact Oracle；
production/prototype 差异不被误写成数学失败；
Policy 选择有数据支持；
TV/dominant/fanout/locality Gates 通过；
missed p99 阈值不超过任务允许范围。
```

若失败：

```text
允许保持 K=96 并交付 IN_PROGRESS；
不得直接恢复生产 Decimal；
不得提高 K 数百点；
不得放宽 p99 超过 3% 而不更新架构范围。
```

## Gate 2：Coverage-safe Writable Field

工作：

```text
定义 storage radius / writable radius / max down steps；
实现边界验证；
所有活动 Placement 在 mutation 前检查；
运行六方向 × phase × 双步 closure；
迁移盘点旧数据。
```

建议提交：

```text
feat(core): separate storage and coverage-safe writable domains
```

PASS：

```text
合法活动写入不会在当前 Recall/Surface 因 target 越界失败；
无部分传播；
旧数据不清空；
Node/Python 表示一致。
```

## Gate 3：Occupancy 纯化与 Dense Fixtures

工作：

```text
density_state 重命名/删除；
实现 sparse/dense/dense-atom/unrelated fixtures；
运行 Lazy Surface 和 cache identity；
记录 N0...Nk、时间和截断统计。
```

建议提交：

```text
feat(access): expose truthful occupancy bands for dense locality

test(lab): validate dense locality surface behavior
```

PASS：

```text
无虚假 physical density；
性能 Gate 通过；
两个 unrelated locality 不串扰；
没有语义索引。
```

## Gate 4：单入口 Dense Recall

工作：

```text
建立 deterministic dense Recall fixture；
验证 kernel on/off；
验证单入口路径去重；
运行自然多入口 observation，但不设通过数量。
```

建议提交：

```text
test(caold): validate single-entry dense locality recall
```

PASS：

```text
一次一个入口；
目标事实可达；
干扰受预算控制；
无 Host fanout；
自然多入口报告不冒充约束。
```

## Gate 5：Windows/OpenClaw Live

工作：

```text
迁移/复制非破坏工作区；
R1/R2/R3/P1；
密集主题自然对话积累；
新 Session 单入口综合 Recall；
Gateway restart；
插件和数据状态确认。
```

建议提交：

```text
feat(openclaw): validate dense single-entry memory locality
```

PASS：

```text
R1/R2/R3/P1 不回退；
密集查询正确；
无 Cursor/select_entries；
几何和模型 timing 分开；
失败证据保留。
```

## Gate 6：完整回归、状态回填与 Bundle

工作：

```text
运行完整 package/M0/Node/Manifest/boundary；
更新任务报告、CURRENT_STATUS、canonical Ledger；
复算实际向量和完成度；
所有修改 commit；
clean tree；
仓库外完整历史 Bundle；
verify + SHA-256。
```

完成 Tag 建议：

```text
BROAD_CALIBRATED_SAFE_FIELD_DENSE_SINGLE_ENTRY_RECALL_VALIDATED_AT_<HEAD>
```

未完成 Tag：

```text
CAOLD_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_IN_PROGRESS_AT_<HEAD>
```

---

# 15. 自动测试矩阵

## 15.1 Core

```text
K=96 deterministic repeat；
min_hit Policy identity；
Q16 sum=65536；
fanout<=8；
no long-range edge；
storage radius validation；
writable radius validation；
two-step coverage-down closure；
all six boundary directions；
layer boundary behavior；
no partial expansion；
mutation rejects outside writable field；
old unsupported data preserved；
Surface mutation/reopen/cache identity；
Core stdlib only。
```

## 15.2 Lab

```text
2048 exact fixtures；
phase/direction buckets；
min_hit=1/2 comparison；
wide-coordinate residue coverage；
worst-case reports；
20k production/prototype diagnostic；
safe field closure；
300-cell Surface；
1000-atom dense Locality；
natural multi-entry observation；
no result count minimum。
```

## 15.3 Access

```text
occupancy_band truthful；
no physical density wording；
truncated preview behavior；
one physical entry；
invalid/out-of-write-field candidate rejected；
dense page pagination；
unrelated locality isolation；
no persistent traversal。
```

## 15.4 OpenClaw Python/Node

```text
single-entry Wire only；
coordinate contract version；
writable-field contract version；
no select_entries；
no Cursor；
no direct Core import；
dense truncated prompt；
invalid candidate fail-open；
R3 NONE；
P1 rollback；
plugin schema and diagnose。
```

## 15.5 项目级

建议命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

python -m pytest packages/nollm-core/tests -q
python -m pytest packages/nollm-snapshot/tests -q
python -m pytest packages/nollm-trace/tests -q
python -m pytest packages/nollm-access/tests -q
python -m pytest integrations/openclaw/formation-loop/tests -q
python -m pytest reference/python/tests/m0 -q
python -m pytest reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py -q

python lab/nollm-lab/geometry/run_broad_residue_coverage_calibration.py --output <path>
python lab/nollm-lab/geometry/run_coverage_safe_field_validation.py --output <path>
python lab/nollm-lab/geometry/run_dense_locality_surface_validation.py --output <path>
python lab/nollm-lab/geometry/run_natural_multi_entry_observation.py --output <path>

python tools/generate_module_ownership_manifest.py
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

脚本名可按仓库风格微调，但功能和证据不可省略。

---

# 16. 机器边界 Gate

最终必须：

```text
Manifest tracked = Git tracked；
unclassified = 0；
production violations = 0；
production cycles = []；
OpenClaw direct nollm_core imports = 0；
production Decimal/polygon calls = 0；
production select_entries = 0；
production Cursor = 0；
Topic/Source/Entity→Cell route = 0；
placeholder FINAL_DELIVERY_HEAD = 0；
active “保持封板” = 0。
```

历史文件中的字符串允许存在，但必须标记为历史，不得作为活动状态。

---

# 17. 单一任务报告

生成：

```text
docs/project/CAOLD_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_REPORT.md
```

最低内容：

```text
输入 Bundle/HEAD/Tag；
分支和最终 HEAD；
预计与实际向量；
全部模块实际完成度；
Broad calibration fixture 构成；
随机种子；
min_hit Policy 对比；
最终误差分布；
worst cases；
production/prototype diagnostics；
storage/writable radius；
two-step closure；
迁移盘点；
occupancy 语义修正；
dense Surface N0...Nk 和 timing；
dense single-entry Recall；
natural multi-entry observation（非 Gate）；
R1/R2/R3/P1/dense Live；
插件和数据状态；
package/M0/Node/Manifest/boundary；
known limitations；
Bundle filename/SHA。
```

不得把：

```text
某个样本发生多入口；
某个 Order Cell 数下降；
模型选择某条路径；
```

写成永久架构不变量。

---

# 18. 明确非目标

本任务不做：

```text
Stitch/Unstitch；
Bridge endpoint 最终纯化；
多物理层语义 Placement；
LLM 自动选择物理层；
多 Chart/Atlas/Gluing；
持久 Surface cache；
PB 长跑；
C/C++ 迁移；
History/Audit 产品；
新的安全/攻击 Gate；
正式发布；
vector/graph/embedding；
Topic/Source/Entity 索引；
持久 fact→entries；
多入口查询扇出。
```

---

# 19. 停止条件

只在以下情况停止主流程：

```text
1. Broad Full Gate 显示 K=96 在合理 Policy 下仍无法满足 TV/dominant/locality 基本约束；
2. 当前写入场无法在不改变硬物理参数的情况下实现双步 Coverage closure；
3. 单入口 dense Recall 必须恢复语义索引或 Host 多入口扇出才能工作；
4. 修改导致 Statement/Handle/Core 数据不可恢复；
5. production 重新依赖 Decimal/polygon；
6. 模块边界出现无法消除的生产循环；
7. 活动插件必须清空或卸载才能继续。
```

不要因以下事项停止：

```text
某个 worst-case missed mass 超过 p99；
production/prototype 一采样点差异；
自然多入口没有出现；
Provider 模型慢；
非关键文档格式；
M0 在非 Windows 环境运行过慢；
部分 Live 未完成。
```

上述情况如实记录并继续交付真实进展。

---

# 20. Git 与 Bundle

## 20.1 Checkpoint

每个大 Gate 至少一个提交。不得长时间积累未提交实现。

## 20.2 最终工作树

```powershell
git status --short
```

必须无输出。

## 20.3 Bundle

建议：

```text
nollm_caold_broad_residue_safe_field_dense_locality_20260715_<shorthead>.bundle
```

仓库外生成：

```powershell
git bundle create ..\nollm_caold_broad_residue_safe_field_dense_locality_20260715_<shorthead>.bundle --all
git bundle verify ..\nollm_caold_broad_residue_safe_field_dense_locality_20260715_<shorthead>.bundle
Get-FileHash ..\nollm_caold_broad_residue_safe_field_dense_locality_20260715_<shorthead>.bundle -Algorithm SHA256
```

必须包含完整历史。

---

# 21. 完整验收条件

全部满足才允许使用：

```text
BROAD_CALIBRATED_SAFE_FIELD_DENSE_SINGLE_ENTRY_RECALL_VALIDATED_AT_<HEAD>
```

条件：

```text
V3.9 硬物理参数未改变；
生产仍为 K=96 fixed-point approximate Coverage；
Full Broad calibration 完成；
min_hit/relation threshold 有证据选择；
TV/dominant/fanout/locality Gate 通过；
统计阈值与实际 Full Gate 一致；
storage radius 与 writable radius 分离；
当前双步 Coverage 在 writable field 内闭合；
活动 Placement 不写入 unsafe boundary；
无部分传播；
occupancy 不冒充 physical density；
300-cell 和 1000-atom dense fixtures 通过；
一次 Traversal 一个 physical entry；
dense Recall 不依赖语义索引；
自然多入口只作 Observation；
R1/R2/R3/P1 不回退；
密集主题 Live 新 Session Recall 通过或模型限制如实标记；
无 Cursor/select_entries/vector/graph/embedding；
插件启用，旧数据保留；
canonical CURRENT_STATUS 和 Ledger 一致；
无 placeholder/封板措辞；
测试和机器边界通过；
clean tree；
完整历史 Bundle verify 通过。
```

---

# 22. 未完成时合法交付

即使 Full calibration、dense Live 或 OpenClaw 模型结果未全部完成，也必须：

```text
提交所有真实代码、测试和文档；
工作树 clean；
生成完整历史 Bundle；
状态写 IN_PROGRESS；
保留插件和数据；
准确列出已完成与未完成；
不补造 Broad percentile；
不把 Quick Gate 冒充 Full Gate；
不因自然多入口未出现认定失败。
```

合法状态：

```text
CAOLD_BROAD_RESIDUE_SAFE_FIELD_DENSE_LOCALITY_IN_PROGRESS_AT_<HEAD>
```

---

# 23. 下一候选能力

本任务通过后，再基于真实结果重新评估：

```text
A. layer-0 Locality growth 与 capacity Policy；
B. 多物理层 Placement；
C. 内部几何 endpoint Stitch；
D. 更大规模 Surface partition/cache；
E. Provider 调用压缩。
```

不得预先指定哪一项必然成为下一任务。下一任务必须重新生成：

```text
任务名称；
推进向量；
全部模块完成度；
真实代码锚点；
最新 Broad/dense/OpenClaw 证据。
```

---

# 24. 最终一句话

> **V3.9 已经证明快速近似几何可行；下一步不是恢复精确多边形，也不是急于 Stitch，而是用更广的余量统计确认误差 Policy、把实际可写场边界做真实，并验证大量事实堆积后仍能从一个入口自然重建局部。**
