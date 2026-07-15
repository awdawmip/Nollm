# Nollm 架构书 V3.8：平移协变物理 Coverage 与历史数学资产复用

**版本**：V3.8
**日期**：2026-07-14
**性质**：当前活动目标架构；修正 V3.7 中“8 phase 固定权重足以覆盖全平面”的错误假设
**输入检查点**：`ac8ebaa44cda35e1d2f73e0bfc95055bae425a86`
**状态**：活动架构；2026-07-15 声明域内实现与 P1 组合已验证
**配套路线书**：`NOLLM_ROUTE_BOOK_V3_8_TRANSLATION_COVARIANT_COVERAGE_REUSE_20260714.md`

# 0. 架构结论

Nollm 的关系必须来自真实物理几何。

V3.8 保留：

```text
Δθ = 22.5°
β = 2^(1/4)
β² = √2
Physical Memory Layer / Aggregation Order 分离
无 Cursor
query-agnostic Surface Order
真实 LLM 单入口 Scale Scan
Coverage/Lateral/Bridge 有界传播
```

V3.8 修正：

```text
8 个 rotation phase 不能代表全平面 Coverage 权重；
原点 overlap 不能平移复用到所有 q/r；
固定 offset+weight 不能称为 certified physical Coverage；
nearest-cell 或最多双 target 不能称为真实 Surface 聚合；
“Core runtime 不得做 polygon”不能高于物理正确性。
```

# 1. 为什么 8 phase 不足

物理层旋转和尺度为：

```text
theta(L) = L * 22.5° mod 60°
s(L) = s0 * beta^(-L)
```

22.5° 不是六边形格的整格自同构，`beta=2^(1/4)` 也不是 Eisenstein 整数范数尺度。

因此 source Cell 变换到 target lattice 后的 fractional axial residue 会随：

```text
source q；
source r；
source/target layer；
phase policy；
chart translation；
```

变化。

正确结论：

```text
rotation phase 只确定一部分常数；
Coverage candidate 和权重仍必须读取完整 source physical address。
```

# 2. 历史数学资产是架构组成部分

当前仓库的纯几何代码已经实现：

```text
LocalChart；
axial_to_world / world_to_fractional_axial；
正六边形顶点；
凸多边形相交；
Coverage distribution；
finite residual；
translation variation；
bidirectional Coverage。
```

它们的架构地位：

```text
独立 Oracle；
回归真值；
迁移实现的来源；
不是可被忽略的 Legacy。
```

生产模块不得依赖 `reference/`，但新实现必须与其交叉验证。

# 3. 三层数学结构

## 3.1 物理合同层

唯一硬参数：

```text
theta0 = 0°
delta theta = 22.5°
beta = 2^(1/4)
density ratio = sqrt(2)
pointy-top Model T
increasing layer = finer
```

## 3.2 Oracle 层

至少两个独立路径：

```text
Oracle A：
  历史 float64+tolerance polygon engine。

Oracle B：
  独立 Decimal/interval/integer engine。
```

Oracle 只用于验证和生成，不承担产品语义。

## 3.3 Core runtime 层

首个正确版本采用“真值优先”：

```text
完整 source physical address；
预编译的高精度 phase/scale 常数；
确定性 Decimal、区间、整数固定点或有理 polygon overlap；
安全候选窗口；
Q16 权重和显式 residual。
```

允许以后以 translation-residue atlas 或缓存加速，但缓存不能成为正确性来源。

# 4. 地址

## 4.1 GeometryAddress

只表示真实 Physical Cell：

```text
profile_id
chart_id
physical_layer
q
r
phase identity
```

## 4.2 SurfaceAggregateAddress

只表示派生观察 Cell：

```text
field_scope_id
reference_layer
aggregation_order
observation_q
observation_r
observation_phase
coverage_contract_id
```

两者不可互换。

# 5. Coverage 正式合同

Coverage 是函数：

```text
C(profile, source_address, target_layer, direction, chart_state)
```

输出：

```text
target GeometryAddress；
overlap interval；
source_share；
target_share；
propagation_weight_q16；
core/halo/boundary/ambiguous；
residual；
oracle/certification identity。
```

## 5.1 禁止的模板键

以下键不足以决定权重：

```text
profile + direction + layer_mod_8
```

它最多用于：

```text
预编译 trig/scale 常数；
候选半径上界；
粗略 cache partition；
诊断分组。
```

## 5.2 Candidate completeness

候选窗口必须由真实 circumradius 和 target lattice 推导。

运行时可以：

```text
将 source world center 投影到 target fractional axial；
得到 nearest target；
枚举数学证明足够的 disk/ring；
对每个 target 做真实 overlap；
```

不得假定固定七个 target 总是足够或总有权重。

## 5.3 Residual

Residual 必须区分：

```text
finite candidate window outside mass；
threshold truncation；
numeric ambiguity；
unsupported span；
invalid geometry。
```

不能用很小正权重填满零重叠 target 来制造质量守恒。

# 6. 运行时精度策略

第一正确版本不以最快为目标。

允许：

```text
固定 Decimal context；
预编译 sin/cos/beta Decimal 常数；
确定性 convex clipping；
整数固定点与有理交点；
区间上下界。
```

硬要求：

```text
同输入同输出；
无二进制 float 进入 canonical state；
误差和 ambiguous 显式；
Core stdlib only；
Core 不 import Lab/reference。
```

“运行时无 polygon”降为未来优化目标，不再是硬架构条件。

## 6.1 Translation-normalized numeric contract

The active default profile supports:

```text
q/r: signed 64-bit integers
physical layer: -64 through 64
chart_id: default
phase: null
adjacent Coverage span only
```

Non-default chart and non-null phase are explicitly unsupported in this stage
and must be rejected before geometry work. The default Coverage path constructs
source and target polygons in a source-side-normalized local frame. The target
center is derived from bounded fractional target-lattice residue; it does not
add unit-scale vertices to a large absolute world center.

Raw overlap partition mass is validated before Q16 conversion. Physical output
separately reports candidate-window residual, threshold residual, numeric error
bound and ambiguity, raw partition residual, and Q16 quantization residual.
Q16 conversion must not normalize invalid raw physical mass to 65536.

# 7. 可丢弃加速

允许：

```text
source-address Coverage cache；
translation-residue bucket；
compiled candidate envelope；
Surface materialization。
```

必须：

```text
derived=true；
包含 profile/contract/version；
删除后结果不变；
失败不污染 canonical state；
未命中时回到真值路径。
```

禁止持久：

```text
query→Cell；
fact→entries；
session→entry；
Topic/Source/Entity route。
```

# 8. Surface

Surface 必须通过相同的 Coverage 真值路径构建。

Order k 的每个 source member：

```text
投影到所有正 overlap 或 ambiguous target；
按 overlap 分配质量；
按 target Surface address 聚合；
保留 source member provenance；
```

禁止 nearest-only 和最多双 target。

Occupied count 是否下降是 `OBSERVATION`；观察面积增长是 `PHYSICAL_CONTRACT`。

# 9. Recall

一次 OpenClaw Traversal 只选择一个物理 entry。

Core Recall：

```text
单一 entry
→ CoverageUp/Down
→ Lateral
→ Bridge
→ 有界传播
→ Handle 去重。
```

必须保存可审查的 kernel path，至少供 Lab/报告使用。

只有“关闭 Coverage 不命中、打开 Coverage 命中”的跨层 fixture，才能证明物理 Coverage 进入主路径。

# 10. 模块所有权

## Core

```text
物理地址；
确定性 runtime overlap；
Coverage expansion；
Surface 派生；
有界 Recall；
canonical state。
```

## Lab

```text
Oracle A/B；
高精度常数生成；
全平移验证；
误差认证；
资产复用清单；
性能研究。
```

## Access

```text
固定预算；
Surface View；
单入口候选验证；
Statement/Handle 映射；
原子协调。
```

## OpenClaw

```text
真实 LLM Traversal；
单入口选择；
Recall Agent；
隐藏注入。
```

## Distribution

```text
profile/coverage/wire/version；
默认预算；
插件组合。
```

# 11. 能力名称

只有下列 Gate 均通过后才能使用：

```text
TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_VALIDATED
```

Gate：

```text
两个独立 Oracle；
全平移候选完整；
零重叠无正权；
权重误差有界；
Surface 使用真实 members；
单入口跨层 Recall；
真实数据和插件保留；
完整文档进入 Git。
```

在此之前只能使用：

```text
IN_PROGRESS；
ADDRESS_SEPARATION_VALIDATED；
SINGLE_ENTRY_WIRE_VALIDATED；
CURSOR_FREE_TRAVERSAL_VALIDATED。
```

# 12. 最终架构概括

> **rotation phase 不是 translation residue；固定模板不是全平面物理关系；历史数学 Oracle 必须复用；正确性路径先成立，缓存和模板优化后置。**

# 13. 2026-07-15 平移归一化闭合合同

活动 `default_dream_v1` 的公开支持域是：

```text
q/r: signed 64-bit
physical layer: -64..64
chart_id: default
phase: null
span: one adjacent physical layer per Coverage expansion
```

超出域必须显式拒绝。活动 Runtime 在 source-centered 局部坐标中构造
source polygon，并仅用 target candidate 相对 source center 的有界坐标做
裁剪；不得先构造两个巨大 absolute-world polygon 再相减。Decimal 精度
由输入幅度和 layer 推导，至少 Decimal96，并保留 guard digits。

物理质量必须先于 Q16。每次 expansion 分别公开：

```text
raw_source_share_sum
raw_partition_residual
candidate_window_residual
threshold_residual
numeric_error_bound / numeric_ambiguity
q16_sum / q16_rounding_residual
candidate strategy and contract identities
```

原始 partition mass 未落在声明误差界内时，不得进入 Q16 强制归一化或
Recall propagation。几何零 overlap 不得以正权成员出现。

Surface 的 `native_atom_count` 来自真实 source Cell occupancy，不是 source
Cell 数。Coverage residual 和 ambiguity/invalid count 从 Core expansion
确定性投影，不允许常量零。

OpenClaw/Access 入口流程是：

```text
finite Surface page
-> Order 0 Surface candidate
-> finite physical-entry page
-> Host selects exactly one visible physical-entry candidate_id
-> finite PlacementDecision or RecallDecision
```

operation-local candidate ID 不持久化；重开时从当前 Core/Access truth 重建。
`select_entries`、stable-key final-entry fallback、Cursor、entry hint 和
fact-to-entry map 均不属于活动合同。
