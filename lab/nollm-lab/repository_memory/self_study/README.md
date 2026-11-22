# 原生几何探针与既有源码研究

当前 Nollm 开发理解在[速记本](../../../../sujiben/README.md)中维护。
这里保留可独立复算的原生几何和 Surface 探针；基于 `691590d…` 源码的旧 AOCI 卷、
903 对象建场器、布局拟合与固定题目试验已归档。

## 两种上下关系

物理 Coverage 从一个物理格出发，按方向和几何核形成有界传播。旋转缩放后的蜂巢
允许多目标、相互重叠的上下关系；出发格换了，权重的分母和采样现场也随之变化。
这些关系由 Core 计算，语义放置由 Host 决定。

Surface 保存已有占用对观察窗口的实际贡献及成员。宿主逐页选择，直到选择一个物理
入口后再召回。物理层号描述记忆所在位置，聚合阶数描述观察尺度。要枚举窗口已登记
的成员，应使用 Surface；原生 Coverage 的反向采样不能代替这一枚举。

这些区分及其实现依据见[第一性原理](../../../../docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md)、
[物理覆盖](../../../../packages/nollm-core/src/nollm_core/physical_coverage.py)、
[Surface](../../../../packages/nollm-core/src/nollm_core/surface.py)和
[Access 导航](../../../../packages/nollm-access/src/nollm_access/surface_navigation.py)。

## 留在开发树中的探针

| 工具 | 当前作用 |
| --- | --- |
| [directional_probe.py](directional_probe.py) 与 [回归](test_directional_probe.py) | 对比定向物理传播与重新打开的 Surface 成员；可加入独立理想面积包络。 |
| [surface_walk.py](surface_walk.py) 与 [回归](test_surface_walk.py) | 在调用方指定的原生场中按给定候选序号复现遍历；可在同一最终入口比较传播并枚举观察窗口。 |
| [essence_20261119](essence_20261119/README.md) | 复算多目标覆盖、空层中继与同层原生读回，保留原固定来源和几何实验范围。 |

从仓库根复算方向探针：

```sh
python3 lab/nollm-lab/repository_memory/self_study/directional_probe.py --certify
```

`surface_walk.py` 是按序号复放的研究工具，未提供的序号补零；其输出应按实际选择规则解释。
日常语义发现使用速记本的 `project --field sujiben/field encounter`，由 Host 读取当前页后作选择。
以上探针直接复用 Core/Access，不需要已归档的 AOCI 卷或旧 atlas 构建器。

## 固定研究的完整归档

`archive/legacy-code-20261122` 固定于
`beaafabfe8dec4ba1c154ecd324954fa81417489`。原研究的正文、源码版本、布局意图、
原始结果、失败和复现命令均保留在该快照：

- [完整源码自研究报告](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/self_study/README.md)
- [AOCI 卷、来源与回开方法](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/self_study/aoci/README.md)
- [全仓建场与回读](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/self_study/full_field.py)
- [六道新题等预算试验](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/self_study/fair_trial/README.md)

旧材料证明或暴露的能力仍按当时源码、任务与预算解释。持续开发的概念和代码理解留在
速记本，沿实际改动维护；现有[架构研究](../PROJECT_MINIATURE_DESIGN.md)和
[C1–C3 自举记录](../self_bootstrap/README.md)连接这些前后阶段。
