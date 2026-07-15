# Nollm C/A/O/L/D：平移归一化 Coverage、物理残差、唯一 Physical Entry 与 P1 闭环任务书

**任务文件名**：`NOLLM_C_A_O_L_D_TRANSLATION_NORMALIZED_COVERAGE_PHYSICAL_RESIDUAL_ENTRY_AND_P1_CLOSURE_TASK_20260715.md`
**日期**：2026-07-15
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`
**任务性质**：V3.8 数学真值和真实写入闭环纠偏；不是新路线，不进入 Stitch、多物理层 Placement 或规模优化
**输入 Bundle**：`nollm_caold_translation_covariant_coverage_reuse_20260715_66684dc5.bundle`
**输入 Bundle SHA-256**：`2a56dad3164d468169d8ff27a4dd7512041956c5eaa6ba0f64ef5c94897213da`
**输入分支**：`codex/caold-translation-covariant-physical-coverage-reuse`
**输入 HEAD**：`66684dc51339544ad4a846614ed31aa52c7ddc24`
**输入状态 Tag**：`CAOLD_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_REUSE_IN_PROGRESS_AT_66684dc5`
**建议工作分支**：`codex/caold-translation-normalized-coverage-physical-entry-p1-closure`
**主执行环境**：Windows 10/11、PowerShell、当前真实 OpenClaw 环境
**交付方式**：所有真实进展提交；最终工作树干净；仓库外生成并验证单一完整历史 Git Bundle
**插件最终状态**：保持安装和启用；不得因任务失败卸载、清空配置或回退到 Cursor/Anchor 路径
**数据最终状态**：旧工作区、Statement、Handle、Core canonical state 和用户数据全部保留
**能力结论边界**：只在数学、Surface、唯一 physical entry 和 P1 均有真实证据时升级能力；否则必须交付 `IN_PROGRESS` Bundle

---

# 0. 可验证结果

```text
绝对世界坐标多边形计算
→ 改为 source-centered / translation-normalized Coverage
→ 明确受支持坐标定义域
→ 原始 overlap mass 与物理 residual 可见
→ Q16 不再掩盖几何错误
→ 大坐标、负坐标、8 phase、双方向数学 Gate
→ Surface native_atom_count 和 Coverage residual 真实
→ LLM 明确选择唯一 physical entry candidate
→ 不再由 Python stable-key 决定最终入口
→ P1 分阶段计时、定位并闭合
→ 新 Statement 经 V3.8 Surface Placement 写入 Core
→ Gateway 重启
→ 单入口 Recall 找回该 Statement
→ 最高原则、架构、路线、AGENTS、状态和 Ledger 一致
→ 最终 Manifest 在最终 HEAD 上通过
→ clean tree
→ 单一完整历史 Bundle。
```

本任务不得以以下结果替代上述目标：

```text
小坐标 [-4,4] 通过；
Q16 权重和强制等于 65536；
两个绝对坐标 Oracle 在小窗口一致；
受控跨层 Recall 成功；
R1/R2/R3 聊天成功；
Formation 已生成但未写入；
最终报告提交前的 Manifest 曾经通过。
```

---

# 1. 任务推进向量

```text
任务推进向量：
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +10% | DISTRIBUTIONS +5%

主方向：
平移归一化数学真值
→ 显式物理 residual
→ 真实 Surface 统计
→ 唯一 physical entry 由 LLM 选择
→ P1 写入和重启 Recall 闭环。

范围变化：
V3.8 主架构方向不变；
补充“支持坐标定义域、数值条件、物理 residual、physical-entry 选择”合同；
不恢复 phase-only template；
不恢复多入口扇出；
不提前进入多物理层语义 Placement、Stitch、density relocation 或 PB 优化。
```

## 1.1 Gate 向量复述

每个 Gate 开始时在任务报告写：

```text
当前预计向量：
C +10 | S 0 | T 0 | A +5 | H 0 | U 0 | O +5 | L +10 | D +5

当前主方向：
translation-normalized Coverage
→ physical residual
→ explicit physical entry
→ P1 closure。
```

每个 Gate 结束时记录：

```text
实际受影响模块；
当前实际推进；
是否新增范围；
是否出现超过 5% 的偏差；
是否必须更新任务名、向量、架构或状态。
```

不得静默把 Snapshot、Trace、History、Audit、Stitch、多物理层语义 Placement 或性能缓存加入任务。

---

# 2. 本任务产生的直接原因

`66684dc5` 已经取得真实进展，但独立审核确认以下事实：

## 2.1 已保留的真实进展

```text
完整 V3.8 权威文档进入 Git；
历史数学资产完成复用清单；
Core Coverage 读取完整 GeometryAddress；
Physical/Surface 地址类型分离；
Surface 使用全部当前 Runtime 返回的 overlap members；
单入口跨层 Recall fixture 成立；
Recall kernel path 可见；
OpenClaw 受控单入口跨层 Recall 成立；
P1 未完成时如实交付 IN_PROGRESS；
旧数据和插件保留。
```

## 2.2 当前 P0 数学阻断

当前 `physical_coverage.py`：

```text
固定 Decimal precision = 80；
先生成巨大绝对 world center；
再加减边长约为 1 的六边形顶点；
再在巨大绝对坐标上裁剪多边形。
```

大坐标下发生数值消减：

```text
q = 10^14 时 raw source-share sum 可达到 1.2；
正确高精度 source-centered 结果应接近 1；
支持集和权重均发生变化；
更大坐标可能 DivisionByZero 或无正 overlap。
```

随后 `_quantize()` 强制把所有正权重归一化为：

```text
sum_weight_q16 = 65536
normalization_residual_q16 = 0
```

从而掩盖物理质量错误。

## 2.3 当前 P1 架构和组合缺口

```text
Coverage 输出缺少 raw mass、numeric bound、candidate residual、threshold residual 和 ambiguity；
Surface coverage_residual_q16 被硬编码为 0；
高 Order native_atom_count 统计的是 source Cell 数，不是 Atom 数；
Order 0 Surface candidate 含多个 physical source Cell 时，Access 使用 min(stable_key) 选入口；
LLM 没有明确选择唯一 physical entry；
chart_id/phase 接口接受但没有真实进入变换；
P1 两次 Formation 后均未进入 placement_apply；
最终 HEAD 1813 个 tracked，Manifest 仅 1812 行；
最高原则仍保留过时 GRF8 调度和旧 Evidence/Core 措辞。
```

本任务必须同时解决上述数学、入口、P1 和文档收口问题，不能只修其中一个后再次宣称完成。

---

# 3. 活动依据与优先级

开始执行前必须按顺序读取：

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/project/NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md
3. docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_8_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_20260714.md
4. docs/project/NOLLM_ROUTE_BOOK_V3_8_TRANSLATION_COVARIANT_COVERAGE_REUSE_20260714.md
5. docs/validation/NOLLM_REUSABLE_GEOMETRY_ASSET_INVENTORY_20260714.md
6. docs/validation/NOLLM_INDEPENDENT_GEOMETRY_ORACLE_CONTRACT_20260714.md
7. docs/project/NOLLM_CURRENT_STATUS.md
8. docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
9. 本任务书
10. C/A/O/L/D 模块章程
11. 根目录 AGENTS.md
```

冲突处理：

```text
第一性原理
> V3.1 模块所有权
> V3.8 架构书
> V3.8 路线书
> 当前状态和模块进度账
> 本任务变化量
> 历史任务、报告和 Tag。
```

本任务必须更新但不得重复定义：

```text
第一性原理：删除或显式历史化过时调度/所有权措辞；
V3.8 架构书：补充数值定义域、translation-normalized runtime、physical residual 和 physical-entry 选择；
V3.8 路线书：增加大坐标数学 Gate 和最终 Manifest 顺序；
AGENTS.md：加入本任务执行硬约束；
CURRENT_STATUS / Ledger：以 66684dc5 审核值重算。
```

任务书不得重新定义完整 Nollm 架构；上述长期合同只在对应权威文档中更新。

---

# 4. 输入代码锚点与已验证基线

## 4.1 Git 基线

```text
Bundle:
  nollm_caold_translation_covariant_coverage_reuse_20260715_66684dc5.bundle

SHA-256:
  2a56dad3164d468169d8ff27a4dd7512041956c5eaa6ba0f64ef5c94897213da

Branch:
  codex/caold-translation-covariant-physical-coverage-reuse

HEAD:
  66684dc51339544ad4a846614ed31aa52c7ddc24

Tag:
  CAOLD_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_REUSE_IN_PROGRESS_AT_66684dc5

Working tree:
  clean
```

开工时必须重新执行：

```powershell
git bundle verify <bundle>
git fsck --full
git rev-parse HEAD
git status --short
git log --oneline -15
Get-FileHash <bundle> -Algorithm SHA256
```

## 4.2 当前可复现工程事实

当前审核已复现：

```text
Core              52 passed
Snapshot           7 passed
Trace              3 passed
Access            76 passed（存在既有 warnings）
新增关键测试      11 passed
OpenClaw 关键测试  9 passed
工作树 clean
Bundle 完整历史
```

当前最终 HEAD 的治理事实：

```text
Git tracked files = 1813
Manifest rows     = 1812
Manifest stale    = true
```

## 4.3 当前应保留能力

```text
22.5°、beta、sqrt(2) Profile 常量；
Physical/Surface 地址分离；
Order 0..8 Surface API；
无 Cursor/cluster/new_cluster；
query-agnostic Active Surface；
历史数学资产复用机制；
完整地址参与 Coverage；
单入口 Recall Wire；
跨层 kernel path；
受控跨层 Recall；
原子 Core/Handle/Statement 回滚；
OpenClaw 隐藏注入和失败开放；
插件和旧工作区保留。
```

## 4.4 当前不能继续使用的能力表述

```text
arbitrary q/r Coverage；
all-plane certified Coverage；
explicit complete physical residual；
Core 90% 高置信；
Lab 95% 高置信；
Gate 7 governance passed；
P1 Placement closure；
最终 physical entry 已由 LLM 选择。
```

---

# 5. 任务开始前模块完成度

以下为 `66684dc5` 审核后的活动基线：

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务是否影响 |
|---|---|---:|---|---|---|---|
| CORE | `IMPLEMENTED` | 85% | 中高 | canonical state、完整地址 Coverage、Surface、跨层 Recall path | 大坐标数值消减；physical residual 不真实；chart/phase 边界 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 7 tests、state bytes | 版本迁移、增量 Snapshot | 否，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 状态隔离、最小 path | 产品化 Trace 暂停 | 否；仅 operation-local timing，不改公共 Trace |
| ACCESS | `IMPLEMENTED` | 85% | 中高 | Surface/单入口编排、原子协调 | physical entry 由 stable-key 选择；Surface residual/统计错误 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | `CAPABILITY_VALIDATED` | 85% | 中高 | R1/R2/R3、受控跨层 Recall、隐藏注入 | P1 未进入 placement_apply；未显式选 physical entry | 是 |
| LAB | `IMPLEMENTED` | 90% | 中高 | 历史资产、两个 Oracle、小窗口验证 | 共享绝对坐标弱点；无大坐标/partition mass Gate | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 75% | 中高 | v0.8.0、V3.8 wire/profile | 数值定义域和 residual schema 未声明；最终 Manifest 陈旧 | 是 |

说明：

```text
完成度基线恢复不是否定已有真实代码；
降低来自独立审核推翻了“任意 q/r、全平面认证、最终 Gate 已闭合”的结论。
```

---

# 6. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 85% | 95% | +10% | translation-normalized Coverage、明确定义域、physical residual、真实 Surface residual | 大坐标 Gate、Oracle、partition mass、Core tests | 多层语义 Placement、PB 性能 |
| SNAPSHOT | 50% | 50% | 0% | 无合同变化 | package tests | 版本迁移 |
| TRACE | 40% | 40% | 0% | 不扩展公共 Trace | 状态回归 | 产品 Trace |
| ACCESS | 85% | 90% | +5% | LLM 明确选择唯一 physical entry、真实 Surface 统计 | Access tests、跨模块、Live | 大规模候选体验 |
| HISTORY | 10% | 10% | 0% | 无变化 | 章程 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 章程 | 暂停 |
| OPENCLAW | 85% | 90% | +5% | physical-entry Wire、P1 写入、重启 Recall | Windows Live P1 | 长期成本、其他模型 |
| LAB | 90% | 100% | +10% | source-centered Oracle、大坐标压力、mass/residual 认证 | 数学报告和 fixtures | PB 性能研究；100% 仅当前章程 |
| DISTRIBUTIONS | 75% | 80% | +5% | coordinate/residual/wire 版本、Manifest 最终闭合 | plugin check、manifest、bundle | 正式发布 |

`LAB 100%` 仅表示本轮当前数学验证章程能力，不表示数学体系封版。

---

# 7. 现有资产分类

## 7.1 KEEP_ACTIVE

```text
packages/nollm-core/src/nollm_core/geometry.py
packages/nollm-core/src/nollm_core/profiles.py
packages/nollm-core/src/nollm_core/state.py
packages/nollm-core/src/nollm_core/recall.py
packages/nollm-core/src/nollm_core/surface.py
packages/nollm-access/src/nollm_access/surface_navigation.py
packages/nollm-access/src/nollm_access/memory_loop.py
integrations/openclaw/formation-loop/**
reference/python/nollm/dream_geometry/geometry/**
validation/gvr1/**
validation/gra1/**
validation/grc1/**
validation/gkd1/**
validation/gpr1/**
```

保留能力：

```text
历史 world/hex/polygon/Coverage Oracle；
完整地址 API；
Surface/Physical 类型分离；
单入口 Wire；
跨层 path；
原子协调；
真实 Host 集成。
```

## 7.2 PUREFY

```text
physical_coverage.py：从 absolute world 改为 source-centered / residue-centered；
PhysicalCoverageExpansion：补充 raw physical mass 和 residual；
surface.py：修正 native_atom_count 和 coverage residual；
surface_navigation.py：删除 stable-key physical-entry fallback；
OpenClaw Wire：显式 physical-entry 选择；
First Principles：清除旧调度/所有权冲突；
Manifest 最终顺序。
```

## 7.3 REBUILD

只允许重建以下受阻部分：

```text
translation-normalized candidate coordinate；
坐标定义域和动态精度/固定点策略；
physical residual schema；
physical-entry candidate page；
P1 operation-local timing 和闭环报告。
```

禁止重建已有：

```text
世界坐标基础定义；
正六边形构造；
凸多边形裁剪；
历史 GVR/GRA/GRC/GKD/GPR 验证；
Statement/Handle/Core 原子协调；
OpenClaw Dream/Recall 主流程。
```

## 7.4 DELETE_ACTIVE

```text
absolute-world polygon 作为默认大坐标计算路径；
固定 precision=80 即宣称 arbitrary q/r；
raw mass 未校验即 Q16 强制归一化；
normalization_residual_q16=0 作为物理正确证据；
Surface coverage_residual_q16=0 硬编码；
Order>0 native_atom_count=len(source_cells)；
min(stable_key) 作为生产 physical-entry 选择；
硬编码 two_independent_oracles=true；
最终报告后再新增 tracked file；
最高原则中的活动 GRF8 调度措辞。
```

## 7.5 PAUSE

```text
多物理层语义 Placement；
Stitch/Unstitch；
Bridge endpoint 最终纯化；
density relocation；
持久 Surface cache；
PB scale；
History/Audit 产品；
安全攻击 Gate；
正式发布。
```

---

# 8. 模块所有权变化

## 8.1 Core

Core 新增并独占：

```text
受支持 coordinate-domain 验证；
translation-normalized physical Coverage；
raw physical mass 和 residual；
numeric ambiguity / unsupported coordinate 结果；
Q16 量化前的物理合法性检查；
Surface residual 聚合；
真实 native Atom 统计。
```

Core 不读取：

```text
query；
Statement 文本；
Topic/Source/Entity/Session；
LLM 输出；
历史命中；
用户。
```

## 8.2 Lab

Lab 负责：

```text
source-centered 高精度 Oracle；
历史 Oracle A 的受支持范围声明；
大坐标和负坐标压力；
partition mass=1；
候选窗口完整性；
误差上界；
坐标域认证；
metamorphic/translation normalization 验证。
```

生产模块不得依赖 Lab 或 reference。

## 8.3 Access

Access 负责：

```text
Surface candidate 展示；
Surface Cell 内有限 physical-entry candidate 展示；
physical candidate_id 验证；
只允许一个最终 physical entry；
不做语义排序；
不以 stable-key 代替 LLM 选择。
```

## 8.4 OpenClaw

OpenClaw 负责：

```text
真实 LLM 从可见 physical-entry candidate 中选择一个；
P1 operation-local 阶段编排；
隐藏 Recall 注入；
失败开放；
模型和认证继承。
```

## 8.5 Distributions

Distributions 只声明：

```text
geometry contract version；
coordinate-domain version；
physical residual schema version；
Surface/physical-entry Wire version；
预算配置；
插件版本和组合依赖。
```

---

# 9. 坐标定义域与数值合同

本任务必须在 Gate 1 做出并提交一个明确选择。

## 9.1 首选合同：平移归一化、坐标幅度无关

首选实现必须避免生成巨大绝对 world polygon。

给定 source layer `Ls`、target layer `Lt` 和 source axial vector `v=(q,r)`：

```text
u_t = M(Ls→Lt) · v
```

其中 `u_t` 是 source center 在 target axial basis 中的坐标。

实现必须把：

```text
u_t = n + f
```

拆为：

```text
n：候选 target 中心附近的整数 axial 基点；
f：限制在 target 基本平行四边形内的 fractional residue。
```

随后：

```text
source polygon 以 source center = (0,0) 构造；
target candidate polygon 只用 (candidate - u_t) 的局部相对中心构造；
所有裁剪坐标保持在与 Cell 尺度同量级的有界范围内。
```

禁止：

```text
先计算 B_s·v 的巨大 absolute world center；
再计算 B_t·candidate；
最后用两个巨大数相减得到局部差。
```

## 9.2 可接受替代：明确有限坐标域

若执行中无法证明坐标幅度无关，可选择明确有限域，但必须同时满足：

```text
Core 明确公开 supported_coordinate_bits；
至少支持 signed 64-bit q/r；
超出范围抛出明确 UnsupportedCoordinateMagnitude；
不得静默计算；
不得继续写 arbitrary q/r；
架构书、路线书、Profile、Wire 和状态同步更新；
需要记录为何暂不支持更大坐标和恢复条件。
```

未经更新架构范围，不得选择低于 signed 64-bit 的支持域。

## 9.3 动态精度

若使用 Decimal：

```text
precision 不得固定为与坐标位数无关的常数；
必须由坐标 bit length、目标误差和运算条件推导；
source-centered 后仍需保留 guard digits；
误差界必须输出；
不得只凭两次运行一致声明正确。
```

若使用代数数、区间或固定点：

```text
必须记录表示、舍入方向、误差界和 unsupported 条件；
不得把近似值命名为 exact。
```

---

# 10. Physical Coverage 与 Residual 合同

## 10.1 PhysicalCoverageMember

最低字段：

```text
target: GeometryAddress
intersection_area_lower
intersection_area_upper
source_share_lower
source_share_upper
target_share_lower
target_share_upper
weight_q16
q16_rounding_residual
classification: core | halo | boundary | ambiguous
numeric_ambiguity
```

第一版若暂不提供区间上下界，必须改为：

```text
intersection_area
source_share
target_share
numeric_error_bound
ambiguous
```

不得同时省略误差界和 ambiguous。

## 10.2 PhysicalCoverageExpansion

最低字段：

```text
source
direction
members
raw_source_share_sum
raw_partition_residual
candidate_window_residual
threshold_residual
numeric_error_bound
q16_sum
q16_rounding_residual
candidate_radius / candidate_strategy
coordinate_contract_id
oracle_contract_id
```

Residual 必须分开，禁止把所有误差合并为一个始终为零的字段。

## 10.3 Partition mass 不变量

对于完整相邻层六边形铺砌：

```text
所有 target overlap 的 source_share 总和应为 1。
```

合法条件：

```text
1 必须落在 raw_source_share_sum 的认证区间内；
或 abs(raw_source_share_sum - 1) <= declared_numeric_bound。
```

若不满足：

```text
不得进入 Q16 强制归一化；
返回 ambiguous/invalid；
Core Recall 不得传播错误物理权重；
报告记录 source address、方向、残差和坐标域。
```

## 10.4 Q16 量化

只有在物理质量 Gate 通过后才允许 Q16：

```text
raw physical shares
→ 明确舍入
→ Q16 sum 调整
→ 保留 q16 rounding residual。
```

Q16 sum 等于 65536 只证明离散权重归一，不证明物理 Coverage 正确。

## 10.5 零重叠和阈值

必须满足：

```text
几何零 overlap → weight_q16 = 0 且不进入 members；
正 overlap 低于阈值 → 计入 threshold_residual；
不得用 min weight=1 填充零重叠；
不得因 Q16 正权重要求扩大支持集。
```

---

# 11. 独立数学 Oracle 与历史资产复用

## 11.1 Oracle A：历史纯几何实现

保留不改：

```text
reference/python/nollm/dream_geometry/geometry/**
```

用途：

```text
小坐标和中等坐标 float64/tolerance 对照；
世界坐标、polygon、Coverage distribution 历史行为；
回归和趋势检测。
```

限制：

```text
不得把 Oracle A 单独用于大坐标真值；
必须记录其数值稳定窗口；
不因其历史标签宣称全平面正确。
```

## 11.2 Oracle B：source-centered 高精度实现

必须独立于生产 Core：

```text
不能 import nollm_core.physical_coverage；
不能调用生产 polygon clipping；
不能复用生产 candidate enumeration 作为唯一候选；
使用 source-centered / translation-normalized coordinates；
精度高于生产实现；
输出 raw mass 和误差界。
```

## 11.3 Oracle C：不变量和变形验证

至少建立以下非同源验证：

```text
partition mass = 1；
up/down reciprocal overlap area；
candidate radius R 与 R+2 结果一致；
source-centered 与高精度 absolute reference 在安全小窗口一致；
符号翻转/层方向/负坐标一致；
缓存清除结果不变；
动态精度提高后结果收敛。
```

不得将：

```python
"two_independent_oracles": True
```

作为独立性证明。独立性必须由脚本扫描 import/call graph 和报告人工代码锚点共同证明。

---

# 12. 数学压力矩阵

## 12.1 坐标数量级

若采用 signed 64-bit 支持域，至少测试：

```text
0
±1
±10^4
±10^8
±10^10
±10^12
±10^14
±10^16
±(2^31-1)
±(2^53-1)
±(2^63-1)
```

组合必须覆盖：

```text
q 大、r 小；
r 大、q 小；
q 与 r 同号；
q 与 r 异号；
q + r 接近 0；
负坐标；
八个 layer phase；
coverage_up；
coverage_down。
```

若采用无界动态精度，额外测试：

```text
128-bit、256-bit 整数样本；
运行时间和 precision 增长；
结果收敛；
不得静默超时或返回错误权重。
```

## 12.2 硬验收

在声明支持域内：

```text
false negative = 0；
positive weight on zero overlap = 0；
partition mass residual <= declared bound；
Core 与 Oracle B 支持集一致；
Core 权重误差 <= declared bound；
R 与 R+2 candidate window 一致；
重复运行一致；
缓存删除一致；
不存在 DivisionByZero；
不存在无正 overlap 的合法 adjacent-layer Cell。
```

任何样本失败：

```text
数学 Gate 失败；
不得进入 OpenClaw P1；
提交 IN_PROGRESS Bundle。
```

---

# 13. Surface 修正合同

## 13.1 native_atom_count

定义：

```text
该 Surface projection 直接包含的原生 MemoryAtom 数量。
```

禁止：

```text
Order > 0 时使用 len(source_cells)；
用 source Cell 数冒充 Atom 数；
用 Handle 数冒充 Atom 数但不说明。
```

必须从实际 Core Cell occupancy 计算。

## 13.2 aggregate mass

必须来自：

```text
全部有效 physical Coverage members；
认证 source shares / Q16 weights；
确定性去重；
明确的 mass 单位。
```

## 13.3 coverage residual

`SurfaceOrderInfo` 和 `SurfaceCellProjection` 必须聚合：

```text
raw physical residual；
candidate residual；
threshold residual；
numeric ambiguity；
Q16 rounding residual。
```

不能继续硬编码为 0。

第一版可以暴露：

```text
coverage_residual_q16
coverage_ambiguous_count
coverage_invalid_count
```

但必须有真实来源。

## 13.4 Ambiguous/unsupported

Surface 构建遇到：

```text
unsupported coordinate；
invalid physical mass；
ambiguous overlap；
未认证 chart/phase；
```

必须：

```text
明确失败或标 overflow/unsupported；
不得静默丢失原生 Atom；
不得用 nearest cell fallback；
不得转向语义索引。
```

---

# 14. 唯一 Physical Entry 选择

## 14.1 当前问题

当前 Order 0 Surface candidate 可能对应多个 physical source cells。

当前生产路径：

```text
LLM 选择一个 Surface candidate_id
→ Access 从 source cells 中取 min(stable_key)
→ 作为最终 entry。
```

这把最终入口语义交给了 Python 字典序。

## 14.2 新合同

一次 Recall 仍只能选择一个最终入口，但必须分两步：

```text
LLM 选择 Order 0 Surface Cell
→ Access 展示该 Cell 内有限 physical-entry candidates
→ LLM 选择一个 physical_entry_candidate_id
→ Access 验证并返回一个 GeometryAddress
→ Core single-entry Recall。
```

如果 Order 0 Surface Cell 只有一个合法 physical entry：

```text
允许直接确认；
仍需报告 resolved_singleton=true；
不得伪装为模型做了多候选判断。
```

如果候选超过预算：

```text
分页；
或继续下钻/细化；
或 defer；
不得 stable-key 自动截取为最终 entry。
```

## 14.3 PhysicalEntryCandidateView

最低字段：

```text
candidate_id
GeometryAddress
native_atom_count
current_statement_preview
truncated
coverage_share / membership weight
source_surface_candidate_id
```

禁止：

```text
Topic；
Source route；
Session；
持久 anchor；
fact→entry；
Python 语义分数。
```

## 14.4 Placement

Placement 的 Locality 最终 physical target 也必须使用同一候选验证思想：

```text
LLM 选择已展示 physical target candidate；
Access 验证；
Core 写入。
```

不要求本任务实现多物理层语义选择；当前仍可：

```text
POLICY: write_physical_layer = 0
```

但 layer 0 内具体 physical Cell 不能由隐藏 stable-key fallback 决定。

---

# 15. OpenClaw Wire 修订

建议 Wire：

```text
nollm_openclaw_translation_normalized_surface_traversal_v1
nollm_openclaw_single_physical_entry_recall_v1
nollm_openclaw_translation_normalized_placement_v1
```

允许动作：

```text
continue_page
open_surface_cell
open_physical_entries
select_entry
return_to_parent
request_coarser_surface
none
defer
```

`select_entry` 的 candidate 必须是 physical-entry candidate，而不是可能包含多个 source Cell 的 Surface candidate。

禁止：

```text
select_entries；
candidate_ids 数组；
LLM 生成 GeometryAddress；
Python stable-key fallback；
持久保存 physical entry；
跨 Session 复用 candidate_id。
```

模型调用上限保持有界。达到上限：

```text
Recall → NONE/available=false；
Placement → defer；
主聊天继续；
不污染状态。
```

---

# 16. P1 写入闭环与阶段计时

## 16.1 当前阻断

`66684dc5`：

```text
P1 Formation completed twice；
两次均未在 5 分钟内到达 placement_apply；
无 HandleBinding；
无 Core placement；
无完成证据补造。
```

## 16.2 Operation-local timing

不扩展 Trace 产品，只在本次后台 operation 记录：

```text
formation_ms
statement_persist_ms
surface_build_ms
surface_order_count
surface_projection_count
surface_page_count
placement_prompt_build_ms
placement_subagent_ms
placement_json_repair_ms
physical_entry_resolution_ms
decision_validation_ms
placement_apply_ms
handle_bind_ms
total_operation_ms
timeout_stage
```

要求：

```text
仅 operation-local 或写入任务报告；
不进入 Core canonical state；
不建立长期 Audit/Trace 产品；
不得记录隐藏推理全文；
足以定位卡在哪一阶段。
```

## 16.3 P1 自然记忆

使用普通聊天形成一条与 Alpha Locality 相关的新记忆，例如：

```text
Alpha 发布前的最终确认还需要由某负责人在某时间前完成。
```

具体内容可根据真实环境自然生成，不硬编码模型答案。

必须完成：

```text
真实 Formation；
Statement 持久化；
Surface Placement；
真实 LLM 选择 Locality/physical target；
Access 原子 apply；
HandleBinding；
Core placement；
Gateway restart；
新 Session 单入口 Recall 找回；
主代理自然使用。
```

## 16.4 超时处理

若 P1 再次超时：

```text
必须给出 timeout_stage 和各阶段时间；
提交所有真实进展；
工作树 clean；
交付 IN_PROGRESS Bundle；
不得通过扩大超时无限等待掩盖算法复杂度；
不得跳过 Surface 直接写入。
```

---

# 17. 第一性原理、架构、路线与 AGENTS 更新

## 17.1 第一性原理

必须直接修订旧冲突，不得只在文件末尾追加新段落。

处理：

```text
将“GRF8 已在执行，不中途打断”和其后旧调度标为 HISTORICAL_STAGE_RECORD 或移除；
将“Core 保存 Evidence”修正为系统 Evidence-first、Access/EvidenceStore 持有原文、Core 语义盲；
将“是否形成新簇”改为现行 Locality/expand_surface/Stitch 边界；
保留 Architecture is the Index、真实 LLM 语义和禁止索引原则；
新增数值真值不能被归一化掩盖；
新增支持域必须显式，越界必须拒绝。
```

## 17.2 V3.8 架构书

补充：

```text
source-centered / translation-normalized Coverage；
支持 coordinate domain；
动态精度/固定点条件；
raw partition mass；
physical residual 分类；
Q16 前置合法性；
physical-entry candidate 选择；
chart/phase 当前支持边界。
```

## 17.3 V3.8 路线书

新增阶段 Gate：

```text
大坐标压力先于 Live；
partition mass 先于 Q16；
physical-entry 明确选择先于 P1；
最终报告必须先生成，再生成 Manifest，再提交；
任何最终 tracked file 变化后必须重跑 Manifest。
```

## 17.4 AGENTS.md

根目录至少加入：

```text
- Do not compute physical overlap from large absolute world polygons when a source-centered local frame is available.
- Q16 normalization cannot be used to prove physical mass conservation.
- Validate raw partition mass before quantization.
- The supported coordinate domain must be explicit and enforced.
- An Order-0 Surface candidate is not necessarily a physical entry; the LLM must select one visible physical entry candidate.
- Do not use stable-key fallback as a semantic entry decision.
- Do not start P1 until large-coordinate and physical-residual Gates pass.
- Generate final reports before the final ownership manifest; no tracked files may be added after the final manifest check without regenerating it.
```

不得把项目书和架构书全文复制进 `AGENTS.md`。

---

# 18. Chart 与 phase 当前边界

当前 runtime 实际只支持：

```text
chart_id = default
phase = null
```

本任务必须二选一：

## 18.1 首选

真正实现 Profile/Chart translation 和 phase 对 Coverage 的作用，并纳入 Oracle。

## 18.2 当前阶段最小正确边界

若不实现多 Chart/phase：

```text
Core 明确拒绝非 default chart；
Core 明确拒绝非 null phase；
Profile/Distributions/Schema 声明 unsupported；
测试覆盖；
不得接受后静默按零平移处理。
```

本任务不要求建设完整 Atlas/Gluing。

---

# 19. 真实数据和工作区保护

不得清空：

```text
旧 StatementStore；
旧 HandleStore；
旧 Core state；
旧 Bridge；
旧 V3.7/V3.8 工作区；
OpenClaw 配置和认证；
插件安装状态。
```

建议新工作区：

```text
nollm-caold-translation-normalized-v1
```

迁移前后记录：

```text
Statement count/SHA；
Handle count/SHA；
Core state SHA；
physical layer distribution；
Cell/Atom count；
Bridge count；
Profile/Schema/Wire version；
旧工作区仍存在。
```

若旧数据存在非 default chart、非 null phase 或超出支持坐标域：

```text
不得静默迁移；
保留旧工作区；
记录阻断；
交付 IN_PROGRESS。
```

---

# 20. Gate 0：活动依据、审核回填与保护性 Checkpoint

### 开始向量

```text
C +10 | S 0 | T 0 | A +5 | H 0 | U 0 | O +5 | L +10 | D +5
```

### 工作

```text
核验 Bundle/HEAD/Tag/clean tree；
把本任务书加入 docs/project/tasks；
更新 ACTIVE_PROJECT 指向本任务 IN_PROGRESS；
把 66684dc5 重新定性为保留检查点；
CURRENT_STATUS 和 Ledger 按审核值重算；
更新根 AGENTS.md；
盘点真实工作区 coordinate/chart/phase；
形成备份摘要；
commit。
```

建议提交：

```text
checkpoint(caold): activate translation-normalized coverage closure
```

### Gate 结束

```text
活动指针唯一；
状态不是 COMPLETED；
没有删除旧数据；
预计向量无新增模块；
AGENTS 已禁止绝对坐标消减和 Q16 掩盖。
```

---

# 21. Gate 1：数值定义域与历史资产再确认

### 开始向量

```text
L +10 为当前主推进；C +10 等待数学合同。
```

### 工作

```text
重新运行历史资产 SHA 校验；
复现 q=10^14 失败样本；
确认 80 位 absolute-world 消减；
选择 source-centered 无幅度合同或 signed-64 明确支持域；
更新架构书和路线书；
建立 source-centered Oracle B；
建立不变量 Oracle C；
commit。
```

建议提交：

```text
feat(lab): define translation-normalized coordinate contract
```

### Gate 结束硬条件

```text
支持域明确；
旧 arbitrary q/r 表述删除；
Oracle B 不调用 Core overlap；
Oracle C 不依赖同一 polygon engine 作为唯一证明；
q=10^14 样本在 Oracle B 中 raw mass≈1；
历史资产继续复用；
未新增重复世界/hex/polygon体系。
```

失败：提交 IN_PROGRESS，不进入 Core 改造。

---

# 22. Gate 2：Core 平移归一化 Coverage 与物理 Residual

### 开始向量

```text
C +10 | L +10 为当前主推进。
```

### 工作

```text
改造 physical_coverage.py；
使用 source-centered / residue-centered local polygons；
或实现明确的 coordinate-domain guard；
补充 PhysicalCoverageMember/Expansion residual 字段；
物理 mass Gate 先于 Q16；
零重叠不进入 members；
chart/phase unsupported 明确拒绝；
缓存结果保持可删除；
commit。
```

建议提交：

```text
feat(core): add translation-normalized physical coverage residuals
```

### 内部 Gate

```text
G2.1 local-frame transform
G2.2 candidate completeness
G2.3 raw partition mass
G2.4 numeric/error bound
G2.5 Q16 truthfulness
G2.6 coordinate-domain rejection
G2.7 cache/reopen identity
```

### Gate 结束硬条件

在声明支持域内：

```text
大坐标压力全部通过；
partition mass 在误差界内包含 1；
false negative=0；
zero-overlap positive-weight=0；
无 DivisionByZero；
Core 与 Oracle B 支持集一致；
错误 mass 不会被 Q16 掩盖；
unsupported 输入明确失败。
```

失败：不得进入 Surface/OpenClaw。

---

# 23. Gate 3：Surface 物理统计与 Residual 真值

### 开始向量

```text
C +10 主推进；A +5 开始适配。
```

### 工作

```text
修正 native_atom_count；
聚合 raw/threshold/numeric/Q16 residual；
Surface 遇到 ambiguous/unsupported 时明确处理；
保留全部有效 overlap members；
重算 dense/sparse fixtures；
预算只使用真实 Surface infos；
commit。
```

建议提交：

```text
feat(core): propagate physical residuals through surface projections
```

### Gate 结束

```text
native Atom 统计可由 Cell occupancy 复核；
coverage residual 不再恒零；
Surface 删除/重开一致；
真实 dense 至少一次粗化；
sparse 不被强制下降；
selected_within_budget 与 overflow 分开；
无 nearest/stable-key 物理替代。
```

---

# 24. Gate 4：唯一 Physical Entry 候选与 LLM 选择

### 开始向量

```text
A +5 | O +5 为当前主推进。
```

### 工作

```text
新增 PhysicalEntryCandidateView；
Surface Cell 内 physical candidates 分页；
删除 Access min(stable_key) 生产 fallback；
更新 Traversal State；
更新 Python Wire；
更新 Node/plugin schema；
更新 Prompt；
候选只在 operation 内有效；
commit。
```

建议提交：

```text
feat(access): require one explicit physical entry selection
feat(openclaw): add single physical entry traversal wire
```

### Gate 结束

```text
一次 Recall 最终一个 GeometryAddress；
多个 physical candidates 时 LLM 必须选择；
单一候选时明确 singleton resolution；
不能选择未展示 candidate；
无 stable-key 语义 fallback；
无 select_entries；
无持久 entry hint；
OpenClaw 不 import Core。
```

---

# 25. Gate 5：单入口跨层 Recall 再验证

### 开始向量

```text
C/A/O/L 组合验证；D 等待 Wire 收口。
```

### Fixture

```text
entry 与 target 位于相邻 physical layers；
无同层 lateral 替代；
无 Bridge；
Order 0 Surface candidate 含至少两个 physical candidates 的附加场景；
LLM/受控 decision 选择正确一个；
关闭 Coverage 不命中；
开启 Coverage 命中；
path 含 coverage_up 或 coverage_down；
错误 candidate 不命中；
大坐标 fixture 在支持域内重复一组。
```

### Gate 结束

```text
单入口成立；
physical entry 明确；
Coverage 真正参与；
Surface residual 合法；
重开一致；
缓存删除一致；
没有 Host 多入口扇出。
```

建议提交：

```text
test(caold): validate normalized single-entry cross-layer recall
```

---

# 26. Gate 6：P1 性能定位与真实写入闭环

### 前置

Gate 1～5 全部通过。

### 开始向量

```text
O +5 主推进；A/C/D 配合。
```

### 工作

```text
加入 operation-local timing；
新建/迁移受控工作区；
安装并启用新 Wire 版本；
Gateway restart；
运行 P1；
根据 timing 就地修复非架构阻断；
成功后重启；
新 Session 单入口 Recall；
R1/R2/R3 回归；
插件和旧数据保留；
commit。
```

建议提交：

```text
feat(openclaw): close timed normalized surface placement loop
```

### P1 PASS

必须同时有：

```text
Formation output；
Statement ID；
Surface path；
physical entry/target candidate；
PlacementDecision；
placement_apply；
HandleBinding；
Core AtomHandle；
Gateway restart；
新 Session Recall；
主代理可见回答；
Cursor/entry hint 不存在。
```

P1 未通过：

```text
记录 timeout_stage；
提交进展；
clean tree；
IN_PROGRESS Bundle；
不补造。
```

---

# 27. Gate 7：权威文档、状态、Manifest 与最终 HEAD 收口

### 开始向量

```text
按实际结果复算全部模块。
```

### 严格顺序

必须按以下顺序执行：

```text
1. 完成所有代码、测试和 Live；
2. 写最终任务报告；
3. 更新 First Principles、Architecture、Route、AGENTS；
4. 更新 ACTIVE_PROJECT、CURRENT_STATUS、Ledger；
5. 更新 README/配置/版本；
6. 确认不再新增任何 tracked 文件；
7. 生成 ownership manifest；
8. 运行 manifest --check 和 validator；
9. 运行 boundary 和全部回归；
10. 提交最终文档、Manifest 和代码；
11. 再次运行 git ls-files 与 Manifest 行数一致性；
12. 若最终提交改变任何 tracked 文件，重新生成并检查 Manifest；
13. 确认 clean tree。
```

禁止：

```text
生成 Manifest 后再新增最终报告；
在最终 commit 后不重跑 Manifest；
引用前一个 HEAD 的 tracked count；
把“曾经通过”写成最终 HEAD 通过。
```

建议提交：

```text
docs(caold): record normalized coverage and placement checkpoint
```

---

# 28. 自动测试矩阵

## 28.1 Core

至少新增：

```text
source-centered coordinates remain bounded；
q/r magnitude stress；
signed 64-bit boundary or dynamic precision；
unsupported coordinate rejection；
partition mass includes 1；
raw residual visible；
Q16 cannot hide invalid mass；
zero overlap absent；
threshold residual；
numeric ambiguity；
chart/phase rejection；
cache clear identity；
reopen identity；
coverage_up/down；
negative layers；
Surface native_atom_count；
Surface coverage residual；
Surface unsupported propagation。
```

## 28.2 Lab

```text
historical asset SHA；
Oracle A bounded-domain report；
Oracle B source-centered；
Oracle C partition/reciprocal/window invariants；
large-coordinate stress；
precision convergence；
R vs R+2 candidate completeness；
8 phase；
双方向；
负坐标；
大层号边界；
支持域报告。
```

## 28.3 Access

```text
Surface candidate with one physical entry；
Surface candidate with multiple physical entries；
physical candidate pagination；
invalid candidate；
expired candidate；
no stable-key fallback；
only one final entry；
Surface residual projection；
unsupported/ambiguous handling；
Placement physical target validation。
```

## 28.4 OpenClaw Python

```text
new Wire schema；
open_physical_entries；
select_entry uses physical candidate；
select_entries absent；
invalid JSON repair；
invalid candidate fail-open；
operation-local timing；
timeout_stage；
P1 zero pollution；
hidden injection；
OpenClaw no direct Core import。
```

## 28.5 OpenClaw Node

```text
plugin schema includes coordinate/residual/wire versions；
no multi-entry fields；
Hook fast return；
subagent deliver=false；
timing fields bounded；
plugin import check；
Node 24 声明环境复现。
```

## 28.6 项目回归

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

python -m pytest packages/nollm-core/tests -q
python -m pytest packages/nollm-snapshot/tests -q
python -m pytest packages/nollm-trace/tests -q
python -m pytest packages/nollm-access/tests -q
python -m pytest integrations/openclaw/formation-loop/tests -q
python -m pytest reference/python/tests/m0 -q

python -m pytest -q `
  reference/python/tests/test_dg1_hex_coordinates.py `
  reference/python/tests/test_dg1_polygon_overlap.py `
  reference/python/tests/test_dg1_coverage_kernels.py `
  reference/python/tests/test_dg1_anti_resonance_metrics.py

python validation/gvr1/run_gvr1_translation_variation.py --output <path>
python validation/gra1/run_gra1_rotation_scale_resonance.py --output <path>
python validation/grc1/run_grc1_resonance_conditioned_coverage.py --output <path>
python validation/gkd1/run_gkd1_bidirectional_coverage.py --output <path>
python validation/gpr1/run_gpr1_geometry_profile_regime.py --output <path>

python tools/verify_reusable_geometry_assets.py
python tools/check_v38_authority.py
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

若命令名称与仓库实际脚本不一致，按 `--help` 调整并记录真实命令，不得虚构结果。

---

# 29. 机器边界 Gate

最终 HEAD 必须满足：

```text
Git tracked count = Manifest rows；
unclassified = 0；
production violations = 0；
production cycles = []；
OpenClaw direct nollm_core imports = 0；
生产 Cursor = 0；
生产 cluster_anchor = 0；
生产 select_entries = 0；
生产 stable-key physical-entry fallback = 0；
absolute-world default Coverage path = 0 或只保留明确 legacy/reference；
最终报告在 Manifest 内；
工作树 clean。
```

历史文档中的字符串允许存在，但必须被分类为 historical。

---

# 30. 单一任务报告

只新增或更新一个活动报告：

```text
docs/project/CAOLD_TRANSLATION_NORMALIZED_COVERAGE_PHYSICAL_ENTRY_P1_REPORT.md
```

最低记录：

```text
输入 Bundle/HEAD/SHA；
分支和最终 HEAD；
预计/实际向量；
全部模块实际完成度；
坐标支持域；
source-centered 算法；
Oracle A/B/C 独立性；
大坐标压力结果；
raw partition mass；
residual 分类；
Q16 结果；
Surface native Atom 和 residual；
physical-entry 选择流程；
跨层 Recall path；
P1 timing；
P1 写入和重启 Recall；
插件和旧数据状态；
测试命令与结果；
Manifest 最终 HEAD 结果；
known limitations；
Bundle 文件名/SHA。
```

不要求：

```text
隐藏推理；
完整聊天；
安全攻击矩阵；
外围 Receipt/Merkle；
PB 性能。
```

---

# 31. 状态与进度账回填

必须更新：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
```

记录：

```text
最终 HEAD；
最终合法 Tag；
实际推进向量；
全部模块实际完成度；
预计/实际偏差；
支持 coordinate domain；
P1 状态；
Manifest 最终结果；
下一候选能力。
```

不得继续写：

```text
arbitrary q/r（若未证明）；
all-plane certified（若未证明）；
physical residual complete（若字段未实现）；
P1 completed（若无 Handle/Core 写入）；
Governance passed（若最终 HEAD Manifest 陈旧）。
```

---

# 32. Git 与 Bundle 交付

## 32.1 Checkpoint Policy

每个大 Gate 至少一个提交。普通问题就地修复，不因非架构问题停止。

建议提交：

```text
checkpoint(caold): activate translation-normalized coverage closure
feat(lab): define translation-normalized coordinate contract
feat(core): add translation-normalized physical coverage residuals
feat(core): propagate physical residuals through surface projections
feat(access): require one explicit physical entry selection
feat(openclaw): add single physical entry traversal wire
feat(openclaw): close timed normalized surface placement loop
test(caold): validate normalized coverage and P1 closure
docs(caold): record normalized coverage checkpoint
```

## 32.2 最终工作树

```powershell
git status --short
```

必须无输出。

## 32.3 Bundle

建议：

```text
nollm_caold_translation_normalized_coverage_physical_entry_p1_20260715_<shorthead>.bundle
```

生成：

```powershell
git bundle create ..\nollm_caold_translation_normalized_coverage_physical_entry_p1_20260715_<shorthead>.bundle --all
git bundle verify ..\nollm_caold_translation_normalized_coverage_physical_entry_p1_20260715_<shorthead>.bundle
Get-FileHash ..\nollm_caold_translation_normalized_coverage_physical_entry_p1_20260715_<shorthead>.bundle -Algorithm SHA256
```

Bundle 必须包含完整历史。

---

# 33. 完成条件

只有全部满足才允许：

```text
TRANSLATION_NORMALIZED_PHYSICAL_COVERAGE_SINGLE_ENTRY_P1_VALIDATED_AT_<HEAD>
```

条件：

```text
第一性原理旧冲突已直接修正；
V3.8 架构/路线包含数值和 physical-entry 合同；
AGENTS 更新；
支持坐标域明确；
source-centered / residue-centered Coverage；
大坐标压力通过；
partition mass 合法；
Q16 不掩盖物理错误；
zero-overlap 不传播；
residual 显式；
Surface native_atom_count 正确；
Surface residual 非硬编码；
LLM 明确选择唯一 physical entry；
无 stable-key fallback；
单入口跨层 Recall；
P1 Formation→Placement→Handle→Core→Restart→Recall 全闭环；
插件启用；
旧数据保留；
最终 HEAD Manifest 与 tracked 一致；
边界和测试通过；
工作树 clean；
完整历史 Bundle 验证通过。
```

---

# 34. 未完成时的合法交付

任何以下情况存在时，必须使用：

```text
CAOLD_TRANSLATION_NORMALIZED_COVERAGE_PHYSICAL_ENTRY_P1_IN_PROGRESS_AT_<HEAD>
```

包括：

```text
坐标支持域未确定；
大坐标样本失败；
physical mass residual 超界；
Oracle 不独立；
Surface residual 未贯通；
physical entry 仍由 Python fallback；
P1 超时；
Node 24 环境未复现；
最终 Manifest 陈旧；
Live 环境不可用。
```

即使未完成，也必须：

```text
提交全部真实进展；
工作树 clean；
生成完整历史 Bundle；
保留插件和数据；
如实记录未完成；
不得补造证据；
不得因缺少完美报告拒绝交付。
```

---

# 35. 真实停止条件

只在以下情况停止并标记架构阻断：

```text
1. 目标 22.5° / beta 几何在声明支持域内无法稳定计算；
2. source-centered 方案仍无法保持 partition mass；
3. 必须恢复 graph/vector/embedding 或外置入口才能正确 Recall；
4. 必须让 Python 做语义选择才能确定 physical entry；
5. 真实 P1 必须绕过 Surface 才能写入；
6. 历史数学资产与目标物理合同发生不可调和冲突；
7. Core/Access 拆分必须形成生产循环；
8. 数据迁移会不可恢复地损坏旧用户数据。
```

不要因以下事项停止：

```text
命名调整；
文档修正；
测试数量变化；
性能较慢；
operation timing 增加；
候选页数调整；
Node 环境安装；
Manifest 重新生成；
模型一次选择不理想。
```

---

# 36. 明确非目标

本任务不做：

```text
多物理层语义 Placement；
自动 density relocation；
真实 Stitch/Unstitch；
Bridge endpoint 最终架构；
自然多入口数量研究；
PB scale；
持久 Surface cache；
History/Audit 产品化；
安全攻击矩阵；
正式发布；
跨 Provider 质量矩阵；
删除旧工作区或用户数据。
```

---

# 37. 下一候选能力

本任务通过后，重新审核实际结果，再选择：

```text
候选 A：多物理层 Placement 与物理密度局部生长；
候选 B：关系中性 frontier 和跨局部隔离；
候选 C：内部 canonical endpoint Stitch；
候选 D：正确架构上的增量 Surface 和长期性能。
```

下一任务必须重新生成：

```text
任务名；
推进向量；
全部模块完成度；
代码锚点；
真实数学和 P1 证据；
剩余限制。
```

不得机械沿用旧任务或旧完成度。

---

# 38. 最终一句话

> **先在有界局部坐标中证明真实物理 Coverage，再量化；先让 LLM 明确选择唯一物理入口，再召回；先完成真实写入和最终 HEAD 治理，再声明能力。任何归一化、默认排序或旧报告都不能代替几何真值。**
