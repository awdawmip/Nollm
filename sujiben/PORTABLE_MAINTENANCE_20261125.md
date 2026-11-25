# 便携部署与条件写恢复的原生维护

日期：2026-11-25。引用的固定实现提交：
`a30dafca126b2b533ee86868cab10d1bc7e5e51a`。

本次沿已有 Surface 观察并原位修订五条受影响判断：运行时安装与工作场导出
分别选择；固定原文可以通过便携 snapshot 回源；条件写在提交状态不明时
保留新原文和恢复记录。实现与48项针对性测试见
[固定实现说明](https://github.com/awdawmip/Nollm/blob/a30dafca126b2b533ee86868cab10d1bc7e5e51a/docs/project/NOLLM_PORTABLE_DEPLOYMENT_20261125.md)。

## 实际相遇和修订

从“运行时可替换，工作场与源码各自保留。”选择 `L−2(2,1)`，沿已显示的
`L−1(3,0)` 下降，读取中层与安装、资料边界的详细判断。三个版本通过同一次
`--reorganize` 原位修订：

| 原版本 | 当前版本 | 物理格 |
|---|---|---|
| `nollm.formed.-1.runtime-field.v1` | `nollm.formed.-1.runtime-field.v2` | L−1(3,0) |
| `nollm.installation.v4` | `nollm.installation.v5` | L0(4,−1) |
| `nollm.notebook-boundaries.v1` | `nollm.notebook-boundaries.v2` | L0(4,−1) |

从“正文、绑定、几何一起恢复；版本可回溯。”选择 `L−2(0,0)`，沿实际候选
`L−1(0,1)` 下降，读取版本提交和 Core/Access 恢复判断。第二次局部批次修订：

| 原版本 | 当前版本 | 物理格 |
|---|---|---|
| `nollm.formed.-1.versions-commit.v2` | `nollm.formed.-1.versions-commit.v3` | L−1(0,1) |
| `nollm.core-commit.v3` | `nollm.core-commit.v4` | L0(1,0) |

两个相遇各自保持原 physical entry。计划为每条新判断声明从原入口到原格的
实际相邻路径，提交返回 `committed` 并读回完整新正文。安装、来源、运行时
和回归测试共七份固定源码的八个引用窗口已经按 Git blob 字节身份及行号核对。

## 保留与回读

| 项目 | 结果 |
|---|---:|
| 版本文件 | 81 → 86 |
| 维护前81份表达的原字节 | 全部保留 |
| 当前物理 handle | 43 |
| 占用格 | 41 |
| 桥 | 2，原文件保持 |
| L−2 | 8条，401 UTF-8字节 |
| L−1 | 12条，2,397 UTF-8字节 |
| L0 | 23条，22,367 UTF-8字节 |
| 重新逐层返回 | 全部43条当前判断，包含23条详情 |

旧版本继续可读且不再为 current。所有改变都是已有 slot 中的原位修订，
入口、容量配置与桥文件未变。记录见
[维护结果](../lab/nollm-lab/repository_memory/results/portable_maintenance_20261125.json)。

本记录只描述项目自身理解的维护。另一个知识库的完整原文、语义内容和读者
测试资料不进入 Nollm 代码仓库。便携测试场使用其独立场副本和固定来源，
不替换本速记本，也不把显式 Lab 局部p8改为 Core 默认几何。
