# Nollm 独立几何 Oracle 与平移协变 Coverage 合同

**版本**：V1
**日期**：2026-07-14
**用途**：为 V3.8 物理 Coverage 提供不可由同源实现替代的数学 Gate。

## 1. 两个独立 Oracle

### Oracle A：历史纯几何实现

固定入口：

```text
reference/python/nollm/dream_geometry/geometry/**
```

数值模式：

```text
float64 + 显式 tolerance
```

作用：

```text
世界坐标和正六边形构造；
候选枚举；
凸多边形真实相交；
Coverage distribution；
residual；
translation variation。
```

不得由生产 Core import。

### Oracle B：新的独立高精度实现

必须满足：

```text
不得 import Oracle A 的 chart/polygon/coverage；
固定 Decimal context >= 72 digits，或使用有理/区间/整数固定点；
独立推导 world transform；
独立实现 polygon clipping/intersection；
输出 overlap interval 或明确误差界。
```

Oracle B 可以位于：

```text
lab/nollm-lab/geometry/oracle_decimal/**
```

不得让生产编译器和 Oracle B 调用同一个 overlap 函数作为唯一证明。

## 2. 平移协变的准确含义

Coverage 是下列完整输入的函数：

```text
profile；
source physical layer；
source q/r；
source chart/phase；
target physical layer；
direction；
target chart/phase。
```

禁止把 Coverage 权重简化为：

```text
direction + layer_mod_8 + fixed offsets。
```

旋转 phase 可以决定预编译常数，但不能消除 source `(q,r)` 产生的 translation residue。

## 3. 最低样本空间

快速 Gate：

```text
physical layer phases：0..7
source q/r：[-4,4] 的 axial disk 或等价不少于 81 个位置
directions：up/down
adjacent layer gap：1
phases：至少 constant-local 的 4 个 phase sample
```

完整 Gate：

```text
q/r 窗口扩展到 [-16,16] 或按磁盘半径定义；
layer gaps：1,2,4,8；
constant-local + layer-drift-control；
边界附近的 residual 样本；
正负层/坐标迁移语义；
随机确定性 seed 样本。
```

## 4. 候选完整性 Gate

对 Oracle A、Oracle B 和生产 runtime：

```text
false_negative_count = 0
```

其中 false negative 是：

```text
Oracle overlap > declared_positive_threshold
但 runtime 未返回该 target。
```

同时：

```text
false_positive_positive_weight_count = 0
```

即 runtime 不得对 Oracle 明确为零重叠的 target 给出正传播权重。

允许保守候选：

```text
返回 target；
weight interval 包含 0；
标记 ambiguous/boundary；
不把它计为已认证正 overlap。
```

## 5. 权重和残差 Gate

必须报告：

```text
source_share error；
target_share error；
Q16 error；
kernel mass；
residual mass；
candidate window boundary mass；
最大误差；
p50/p95/p99；
ambiguous count。
```

不得使用：

```text
intersection_area_lower = 0
```

作为所有项的有效认证下界。

## 6. Up/Down Gate

`CoverageUp` 和 `CoverageDown` 是两个独立方向：

```text
不互为数组反转；
不互为简单矩阵逆；
各自使用真实 source area 归一化；
各自独立验证候选和 residual。
```

## 7. Surface Gate

Surface 只能使用：

```text
所有已认证非零 overlap member；
或包含明确 ambiguous 标记的保守 member。
```

禁止：

```text
nearest target only；
最多两个 target；
固定七邻域必定有权；
在无 overlap 时给 weight=1。
```

## 8. Recall Gate

构造至少一个 fixture：

```text
entry Atom 位于物理层 L；
目标 Atom 位于相邻物理层 L±1；
二者不是同层 lateral；
无 Bridge；
关闭 Coverage 后 Recall 不命中；
开启 Coverage 后从一个入口命中；
报告实际 kernel path。
```

只有该 fixture 通过，才能宣称跨层单入口 Recall。
