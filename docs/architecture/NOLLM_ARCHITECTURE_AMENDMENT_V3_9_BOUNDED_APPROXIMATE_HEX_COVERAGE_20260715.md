# Nollm 架构修订 V3.9：有界近似六边形 Coverage 与快速结构场

**日期**：2026-07-15
**性质**：对 V3.8 的数学与运行时纠偏；保留真实物理参数，撤销生产路径的精确面积义务
**输入检查点**：`871f78203a7ef05584abf893ea0059640c7e2829`

# 0. 架构结论

V3.8 正确恢复了真实旋转、尺度、完整地址、单入口和历史数学 Oracle，但错误地把“几何关系真实”升级成了“生产每次必须高精度求精确六边形相交面积”。

V3.9 采用：

```text
硬物理变换
→ 确定性等面积六边形采样
→ 每个样本映射到唯一 target Cell
→ 小整数计数形成 sparse partition-of-unity
→ 阈值剪枝和 residual
→ 可选 residue atlas
```

生产 Coverage 是**结构核**，不是测量仪器。

# 1. 保留的硬物理合同

```text
Δθ = 22.5°
θL = L × 22.5° mod 60°
β = 2^(1/4)
β² = √2
increasing physical layer = finer
```

这些参数必须进入固定点坐标变换。任何近似只发生在 overlap support 和 weight，不发生在层方向、旋转或尺度。

# 2. Coverage 的新正式定义

对 source Cell `c`，生产 Coverage 返回：

```text
K(c, direction) = {(target_i, weight_i)}
```

满足：

```text
locality；
bounded fanout；
determinism；
approximate partition of unity；
translation covariance within fixed-point quantization；
query/Statement blindness；
deletable cache；
weighted error bounds against Lab Oracle。
```

它不再承诺：

```text
精确 overlap area；
精确非零支持集；
全坐标域测量学认证；
每条边的 reciprocal area identity。
```

# 3. 推荐数学方法：等面积微三角形采样

## 3.1 Canonical source quadrature

把正六边形分成 6 个等边三角形；每个大三角形按边长 `m` 等分为 `m²` 个等面积微三角形，取每个微三角形重心作为采样点。

样本数：

```text
K = 6m²
```

首选：

```text
m = 3 → K = 54
```

备选：

```text
m = 4 → K = 96
```

每个样本质量相同。无需 polygon clipping。

## 3.2 Runtime mapping

对每个 canonical sample：

```text
source-local sample
→ 固定点旋转/尺度映射到 target fractional axial
→ deterministic cube rounding
→ 唯一 target GeometryAddress
```

累计命中数：

```text
weight_i = hit_count_i / K
```

因此：

```text
样本质量天然严格守恒；
没有全局世界坐标消减；
每次运算固定 K；
不存在高精度 Decimal、sin/cos 或 polygon；
实际 fanout 通常 3～7。
```

## 3.3 边界误差

可能遗漏没有覆盖任何采样重心的小 overlap；这是允许的，只要其总真实质量在声明阈值内。

可能的误传播只来自数值舍入和边界 tie；必须在 Oracle Gate 中统计 false mass。

# 4. 可选加速：Translation-residue Atlas

相邻层变换后，Coverage 只依赖：

```text
direction；
layer mod 8；
source center 在 target lattice fundamental domain 中的 residue。
```

可将 residue 量化为 `N×N` bins：

```text
N = 32 或 64
```

每个 bin 存储由同一 quadrature 生成的 sparse stencil。

运行时：

```text
fixed-point affine transform
→ base target cell
→ residue bin
→ sparse stencil lookup
```

Atlas 是派生加速，不是真值源；删除 Atlas 后直接 quadrature 结果仍可重建。

# 5. 误差合同

V3.9 不使用“零错误”Gate。使用：

```text
missed_mass：Oracle 中存在、生产核未赋权的总真实质量；
false_mass：生产核赋权、Oracle 为零的总生产质量；
total_variation = 0.5 × Σ|p_i-q_i|；
partition_mass_error；
dominant_target_agreement；
structural_support_jaccard_above_threshold。
```

初始 Gate：

```text
missed_mass_p99 <= 0.02
false_mass_p99 <= 0.02
total_variation_p95 <= 0.05
dominant_target_agreement >= 0.95
partition_mass_error = 0 after integer normalization
max_fanout <= 8
```

具体阈值是 `POLICY`，可由真实实验调整；不得无证据永久固化。

# 6. Relation threshold

定义：

```text
relation_threshold = 0.02
```

Oracle 中低于该阈值的小边是否出现，不作为结构正确性硬要求。剪枝质量进入 `threshold_residual`。

# 7. 固定点实现

## 7.1 坐标域

活动产品域：

```text
R = max(|q|,|r|,|q+r|) <= 2^31-1
```

单层 Cell 容量约：

```text
1 + 3R(R+1) ≈ 1.38×10^19
```

远超 PB 需求。此范围在 JavaScript `number` 中精确。

## 7.2 Matrix

预编译相邻层 8 phase × 2 directions 的固定点矩阵和 sample offsets。

建议：

```text
Q32.32 或 Q24.40
```

Python 使用 int；未来 C/C++ 使用 int64/int128 中间量。

# 8. Surface

Surface 使用相同 approximate Coverage，不再调用 Decimal/polygon。

规则：

```text
Order 按需构建；
从 Order 0 开始；
满足预算立即停止；
只有下钻访问的下一 Order/页面才构建；
同 operation 复用结果；
mutation 后失效。
```

不要求所有 Order `N(k+1)<N(k)`；只要求在真实 dense fixture 中存在有效粗化，并满足时间预算。

# 9. 当前范围

本修订不启动：

```text
Stitch；
多物理层语义 Placement；
精确 reciprocal Coverage；
PB 长跑；
多 Chart；
持久 Surface cache。
```

当前真实 MemoryAtom 仍按 `POLICY: write_physical_layer=0`。

# 10. 旧资产处理

```text
Decimal polygon Coverage：MOVE_LAB_ORACLE
历史 float polygon：REUSE_AS_ORACLE
source-centered transform：PORT_TO_FIXED_POINT
PhysicalCoverageExpansion residual schema：简化保留
signed-64 closure：退出活动主任务
```

# 11. Broad calibration and writable-field correction

The 96-fixture checkpoint demonstrates the production method but does not establish broad-domain percentiles. Active approximation thresholds and minimum hit count must be versioned from deterministic, residue-stratified exact-Oracle calibration. Production/prototype sample differences are scored independently against the Oracle.

The storage and transport radius identifies serializable cells. A smaller active writable radius must be closed under every Coverage step available to the configured Recall depth. Mutation rejects unsafe source cells before any partial propagation. Occupancy bands describe deterministic atom counts only; they are not physical-density or semantic-density claims.

One traversal still chooses exactly one final physical entry. Reachability from multiple entries is a non-persistent observation and has no minimum count.

# 12. 最终架构概括

> **Nollm 的突破来自几何关系场，而不是相交面积小数点后的真值。只要局部关系、质量、误差和传播稳定，快速近似 Coverage 比生产路径中的高精度 polygon 更符合项目第一性原理。**
