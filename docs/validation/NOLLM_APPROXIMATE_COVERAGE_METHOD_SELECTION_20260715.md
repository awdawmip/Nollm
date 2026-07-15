# Nollm 近似 Coverage 方法选择记录

**日期**：2026-07-15
**输入 HEAD**：`871f7820`

# 1. 现有生产路径成本

在当前 Python Core 中，对 10 个不同地址清空缓存后测量：

```text
coverage_up   ≈ 0.121 秒 / Cell
coverage_down ≈ 0.124 秒 / Cell
```

该成本来自 Decimal 高精度三角函数、六边形构造、候选窗口和多边形裁剪。

# 2. 原型：规则网格采样近似

私有审计原型使用 source hex 内确定性采样点，每个点映射到 nearest target Cell 并累计质量。与当前 Decimal polygon 路径比较 30 个随机地址、正负层和两个方向：

| 采样数 | up 平均 TV | down 平均 TV | up 平均 missed mass | down 平均 missed mass |
|---:|---:|---:|---:|---:|
| 19 | 5.5% | 6.7% | 0.6% | 1.9% |
| 41 | 3.3% | 4.6% | 0.1% | 0.2% |
| 65 | 2.1% | 2.9% | 0.1% | 0.1% |
| 131 | 1.1% | 1.7% | <0.1% | 0.1% |

65 点 Python 原型运行约：

```text
97 微秒 / Cell
```

相对当前约：

```text
1200 倍加速
```

该原型不是仓库能力结论，只用于证明“固定采样近似”值得进入正式任务。

# 3. 推荐

首选 54 点等面积微三角形 quadrature；如果 p95 TV 超过 5%，升级为 96 点。

理由：

```text
固定运算量；
质量天然守恒；
每个样本只属于一个 target Cell；
几乎不产生长程 false edge；
误差主要集中于低质量边界 overlap；
易于固定点和 C/C++ 实现；
可进一步编译 residue atlas。
```

不推荐作为生产主路径：

```text
Decimal polygon；
interval polygon；
每地址 exact certification；
nearest-center 单点；
无误差 Gate 的 phase-only 固定模板。
```
