# Nollm 路线书 V3.9：快速结构几何与有界近似 Coverage

**日期**：2026-07-15
**性质**：当前活动路线；替代 V3.8 的生产精确 Coverage 路线

# 0. 一句话路线

```text
精确几何留在 Lab 校准；
生产几何使用有界近似稀疏核；
Surface 惰性构建；
先让几何场工作得快，再研究 Stitch 和换层。
```

# 1. 重新定性 V3.8

V3.8 的正确成果：

```text
硬物理参数；
Physical/Surface 地址分离；
完整 source address；
source-centered 数值思想；
单入口 physical entry；
P1 闭环；
历史 Oracle 复用。
```

V3.8 的过度要求：

```text
生产逐 Cell Decimal polygon；
零 false negative / zero false positive；
全坐标域精确闭合；
复杂 physical residual 先于使用效果；
数学 Gate 规模远超过当前产品阶段。
```

# 2. 新增防漂移教训

## 2.1 从伪精确漂移到过度精确

纠正固定 offset 后，项目把“真实几何”误解成“每次运行都精确面积相交”。这导致 11 个 Cell 也需要数十秒到数分钟。

以后规则：

```text
生产关系核只需结构正确；
精确面积只作离线 Oracle；
先用误差指标判断是否影响 Recall/Surface；
不得用数值完美阻止核心链路。
```

## 2.2 把数学无限域当成产品需求

signed-64 全闭包和 arbitrary q/r 对当前 PB 目标没有现实必要。

以后规则：产品坐标域按容量和跨语言成本确定；数学无限域只保留为理论扩展。

## 2.3 用边数量而不是权重衡量误差

小 overlap 是否漏掉并不等于架构失败。以后只对 missed/false mass、TV、locality 和 dominant target 设 Gate。

# 3. 路线阶段

## R0：撤回过度精确任务

- 将 `LOSSLESS_INTEGER_ADDRESS_AND_LAZY_SURFACE_RUNTIME` 降为历史草案。
- V3.9 成为活动架构和路线。
- `871f7820` 保留为精确路径检查点，不作为长期 runtime 方案。

## R1：近似方法校准

- 复用历史 polygon Oracle。
- 实现 54 点等面积微三角形 quadrature。
- 对 8 phase、两个方向、平移窗口比较误差。
- 在 54 点不满足 Gate 时测试 96 点，不允许直接回到生产 Decimal。

## R2：生产固定点 Coverage

- 预编译 sample offsets 和相邻层矩阵。
- 整数 nearest axial。
- hit count → Q16。
- 阈值剪枝和 residual。
- 保留 Decimal path 仅 Lab。

## R3：惰性 Surface

- Order 逐阶构建。
- 满足预算立即停止。
- page/descent 不重建全部 orders。
- LRU 仅缓存派生 Coverage/Surface。

## R4：真实组合回归

- R1/R2/R3。
- P1 Formation→Placement→restart Recall。
- 单入口和无 Cursor 保持。
- 记录几何时间、模型时间和总时间。

## R5：可选 residue atlas

仅当直接 quadrature 仍无法满足预算时：

- 建立 32×32 atlas；
- 误差仍以 quadrature/Oracle 为准；
- Atlas 删除后正确性不变。

## R6：后续能力

V3.9 通过后才重新判断：

```text
多物理层 Placement；
Stitch；
长期 Surface cache；
PB 性能。
```

## R7: Broad residue, safe field, and dense locality

- Run at least 2,048 deterministic exact-Oracle fixtures across phase, direction, residue, sign, and boundary buckets.
- Run 20,000 production/prototype diagnostics and score each kernel against the Oracle instead of requiring hit-count identity.
- Compare minimum hit counts 1 and 2 while keeping K=96, then version the selected policy from evidence.
- Separate transport radius from a two-step Coverage-closed writable radius.
- Validate truthful occupancy on at least 300 occupied cells and dense locality on at least 1,000 atoms.
- Preserve exactly one final physical entry per Recall traversal. Natural multi-entry reachability remains observation-only.

# 4. 进入后续阶段的条件

```text
approximate Coverage p95 TV <= 5%；
p99 missed/false mass <= 2%；
11-Cell Surface geometry <= 1 second target，hard ceiling 5 seconds；
217-Cell dense fixture <= 5 seconds target，hard ceiling 15 seconds；
R1/R2/R3/P1 不回退；
生产无 Decimal/polygon；
clean tree + full-history Bundle。
```
