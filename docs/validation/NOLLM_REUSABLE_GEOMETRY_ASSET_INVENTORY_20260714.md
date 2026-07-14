# Nollm 可复用几何数学资产清单

**日期**：2026-07-14
**输入代码检查点**：`ac8ebaa44cda35e1d2f73e0bfc95055bae425a86`
**目的**：禁止下一任务绕开已有正确数学代码重新搭建简化几何。

## 1. 审核结论

当前仓库已经包含一套比 `ac8ebaa4` 新建的 phase-only 编译器更完整的纯几何实现。

它已经提供：

```text
真实 axial/world 双向变换；
带旋转和尺度的 LocalChart；
正六边形顶点；
凸多边形裁剪和相交面积；
Coverage candidate；
fine_to_coarse / coarse_to_fine 独立 Coverage；
质量守恒和有限窗口 residual；
nearest axial 与有限 target disk；
参数 B：beta=2^(1/4)、delta theta=22.5°；
多 phase；
非原点平移窗口；
旋转—尺度共振诊断；
平移变化 envelope；
双向 Coverage 非逆性；
profile regime 和稀疏覆盖实验。
```

这些文件仍存在于当前工作树，并与历史 `grf1a-math-kernel-coverage-template` 分支逐字一致。

## 2. 资产分类

### 2.1 `REUSE_AS_ORACLE`

以下代码应保持独立，作为真值交叉验证路径，不应由新生产代码 import：

```text
reference/python/nollm/dream_geometry/geometry/chart.py
reference/python/nollm/dream_geometry/geometry/hexgrid.py
reference/python/nollm/dream_geometry/geometry/polygon.py
reference/python/nollm/dream_geometry/geometry/coverage.py
reference/python/nollm/dream_geometry/geometry/schedules.py
reference/python/nollm/dream_geometry/geometry/transform.py
reference/python/nollm/dream_geometry/geometry/metrics.py
```

可复用事实：

```text
chart.py：
  正确的 pointy-top axial/world 变换；
  rotation 和 translation；
  正六边形顶点。

polygon.py：
  Sutherland-Hodgman convex clipping；
  overlap area；
  conservative circumcircle candidate。

coverage.py：
  由真实 polygon overlap 得到 directed kernel；
  finite partition；
  mass/residual；
  K_up 与 K_down 分离。

schedules.py：
  Parameter B 已明确 beta=2^(1/4)、22.5°；
  layer scale/rotation；
  phase schedule。
```

限制：

```text
float64+tolerance；
面向纯数学实验；
不是当前 Core runtime API；
不能直接证明 exact/interval certification；
大窗口验证运行较慢。
```

### 2.2 `PORT_WITH_ADAPTATION`

可迁移到当前 Lab/Core 的数学思想和局部实现：

```text
axial_to_world / world_to_fractional_axial；
nearest_axial；
safe target disk；
hex vertex construction；
convex clipping；
overlap/source_area weight；
partition residual；
bidirectional Coverage；
translation stencil；
phase recurrence；
support/entropy/residual metrics。
```

迁移要求：

```text
不得直接复制为第二套无人维护实现；
保留 provenance 注释；
改用当前 GeometryAddress、Profile 和 Q16/Decimal 类型；
新增独立 Oracle 对照；
生产代码不得依赖 reference package。
```

### 2.3 `REFERENCE_ONLY`

以下资产用于实验设计、样本窗口和历史结论，不直接进入生产：

```text
GVR1 translation radius=1 固定窗口；
GRA1 resonance classification；
GRC1 conditioned coverage labels；
GPR1 profile comparison；
GKD1 gap 4/8/16 窗口；
历史报告中的具体比例与结论。
```

## 3. 必须复用的验证资产

```text
reference/python/tests/fixtures/gvr1/fixture.py
reference/python/tests/fixtures/gra1/fixture.py
reference/python/tests/fixtures/grc1/fixture.py
reference/python/tests/fixtures/gkd1/fixture.py
reference/python/tests/fixtures/gpr1/fixture.py

validation/gvr1/run_gvr1_translation_variation.py
validation/gra1/run_gra1_rotation_scale_resonance.py
validation/grc1/run_grc1_resonance_conditioned_coverage.py
validation/gkd1/run_gkd1_bidirectional_coverage.py
validation/gpr1/run_gpr1_geometry_profile_regime.py
```

下一任务不得只运行原点和 phase=0。

## 4. 历史分支与提交

```text
feature/dg1-v2-geometry-kernel                     97c27ef
feature/dg1-01-core-mathematical-repair            0ff24c9
feature/dg1-02-phase-recurrence-correction          314f0d9
codex/gvr1-finite-translation-variation-validation ffe76e4
codex/gra1-rotation-scale-resonance-validation      1c9b1f0
codex/grc1-resonance-conditioned-coverage-validation 39b673f
codex/gkd1-bidirectional-coverage-validation        f2629ba
codex/gpr1-geometry-profile-regime-validation       a0ffe4e
codex/grf1a-math-kernel-coverage-template           bd05ec5
```

## 5. 已独立复现的快速 Gate

在 `ac8ebaa4` 工作树中运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "$PWD/reference/python"

python -m pytest -q `
  reference/python/tests/test_dg1_hex_coordinates.py `
  reference/python/tests/test_dg1_polygon_overlap.py `
  reference/python/tests/test_dg1_coverage_kernels.py `
  reference/python/tests/test_dg1_anti_resonance_metrics.py
```

实际结果：

```text
46 passed
```

`GVR1` 全窗口计算较重，不能因运行时间长而绕开。应拆为：

```text
fast smoke；
full Windows validation；
缓存后的报告重生成。
```

## 6. 禁止的执行方式

```text
不读上述代码，另写一个 phase-only compiler；
只复制函数名，不复用数学逻辑；
把旧代码全部标为 Legacy 因而忽略；
让新 compiler 和 validator 共用同一个 overlap 函数；
只在 (0,0) 计算权重；
把 nearest-cell 量化称为真实 overlap；
因为 Live 成功跳过 GVR1/GKD1。
```
