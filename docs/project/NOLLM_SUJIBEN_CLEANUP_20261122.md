# 速记本与旧实现归档

Date: 2026-11-22

速记本是持续开发 Nollm 的活跃工作场，保留在正常开发代码中。
本轮归档已经停用的旧实验实现，并把原自举工作场完整归并到 `sujiben/field`。
当前交付沿用 [PR #7](https://github.com/awdawmip/Nollm/pull/7) 的
`experiment/enterprise-math-memory-20261120` 分支；这份记录不声称 PR 已合并到 `main`。

## 活跃的速记本

[速记本入口](../../sujiben/README.md)继续使用同一套原生运行时：Surface 观察，
Host 选择一个物理入口，Core 展开 Coverage、邻接及已有桥，Access 返回当前表达和固定来源。
概念、代码行为和成立条件同在一个场中；没有另建关键词表、文件到入口路由或概念索引。

本轮在 M3 的基础上原位修订架构理解，新增“速记本、运行时、源码仓库的边界”
和“完整恢复需要 Core 与 Access 状态”的理解；后两条分别与安装和 Core 重开理解同格。
新增架构到共同入口实现的有向桥，并实际沿桥召回及修订适配器。
形成及使用过程见[形成记录](../../sujiben/FORMATION_20261122.md)和
[C4 维护记录](../../sujiben/MAINTENANCE_20261122.md)。

最终场有 **16 条当前判断、35 个表达版本、14 个 L0 占用格、16 个 atom、2 条原生桥**。
M3 原有 29 个表达文件逐字保留，14 个原地址和 handle、支持表达及旧桥保留。
原 `self_bootstrap/field` 的 31 个文件从活跃树中归并到速记本；新增理解和原位修订
由真实 encounter 完成，保留所有历史正文与固定来源。旧场快照也可从下述归档恢复。

## 自举产生的代码修正

代码提交为 [C4 5d27118](https://github.com/awdawmip/Nollm/commit/5d27118b1011f7e8817d18c0a052e4f40719170f)。

- 开发者从 M3 的 Surface 选择入口，经 lateral 读到导航理解，再回读固定源码，
  复现 415 字正文只展示 256 字而 `truncated=false` 的情况。
  Access 和 CLI 现在用 `text_truncated` 报告正文截短，原 `truncated` 继续表示
  省略其他表达；locality 仍返回全文，`walk` 只显示标题时也标记截短。
- 安装器只复制运行时代码。`project` 和 `em` 都要求显式 `--field`，现用 EM
  研究场继续保留在仓库原路径。安装运行时与维护工作记忆的生命周期分开。
- 活跃资产规则明确保留速记本及仍在使用的研究场；LLM 作者身份不作为归档依据。
  同时修正旧检查器要求清空 `AGENTS.md` 的矛盾，保留当前项目入口与链接检查。

固定 C4 后，正式场通过 encounter 原位更新 navigation.v3、installation.v4、adapter.v5，
16 个新来源窗口全部可展开。其他判断按实际差分核查后保留。
开发者自己的副本也完成了修订，并从原始 Surface 路径重新召回新导航版本。
这个问题已在项目入口列出，因此本轮属于记忆引导的真实工程修正，不属于盲评新发现。

## 已归档的旧实验

[archive/legacy-code-20261122](https://github.com/awdawmip/Nollm/tree/archive/legacy-code-20261122)
已建立并回读确认，固定在 `beaafabfe8dec4ba1c154ecd324954fa81417489`。
以下路径均相对于 `lab/nollm-lab/repository_memory/`：

| 旧资产组 | 数量 | 处理与依据 |
| --- | ---: | --- |
| `examples/` 三份旧清单及 `evaluate_reads.py` | 4 | 固定旧提交的六题读取实验，无当前运行时或现行测试依赖。 |
| `comparison/` 七个旧实验脚本及两份旧报告正文 | 9 | 旧任务、复放、评分和计时流程整体归档；`README.md` 同路径改写为仍在使用的两个通用工具入口。 |
| `self_study/aoci/` | 6 | 固定旧源码的 AOCI 卷、元数据、开启脚本和说明归档。 |
| `self_study/fair_trial/` | 11 | 配套旧六题材料、网关、复放及评分整体归档。 |
| `self_study/` 的旧 atlas、full-field、拟合、评估、题目与两项专用测试 | 7 | 只服务上述固定旧场，当前路径没有消费者。 |

合计 **37 项旧资产**：删除 36 个旧路径，重写 1 个仍需要的 README。
这与原工作场的 31 个文件迁移是两项不同的处理。
归档保留完整旧树及其依赖，当前说明的历史引用指向固定提交。

继续保留速记本、EM 工作场与当前证据、运行时及安装 skill、现行测试、显式辅助和基线工具，
以及独立的几何探针、宿主发现检查、Access 计时工具。
OpenClaw、Oracle、迁移实现和仍受当前 gate 保护的资产保持原职责。
清理依据是实际使用和依赖，不是目录年龄或名称。

## 验证范围

清理后运行当前仓库记忆目录的全部顶层测试：

```sh
PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src \
  python -m unittest discover -s lab/nollm-lab/repository_memory -p 'test_*.py' -v
```

**70 tests passed，24.087 秒**。覆盖原生 encounter、预览截断、版本/支持表达、固定回源、
显式项目/EM 工作场、安装重开，以及继续保留的辅助和基线工具。
此前 13 项聚焦测试、开发者的 5 项测试包含在这 70 项中，不累加计数。
未运行无关的全仓历史或 Provider Live 矩阵。

依赖审查读取了旧实验脚本及保留工具，并检查 135 个当时已物化的保留 Python 文件，
未发现对退役模块的现行 import。已生成的所有权元数据从当前索引更新；
未物化且未变的 Python 源码沿用原有导入元数据。

速记本的实际消费者运行使用独立副本，由形成者执行，不是未知语料盲测。
第一次入口在扩大预算后仍未取回安装侧；结束后重新从 Surface 选择安装入口，
才经已有桥返回 Core 和完整恢复理解。实际更换安装运行时、显式打开原副本，
并用另一份 checkout 回读固定来源，均成功。过程保留预算耗尽和未命中的事实。

本轮没有改变 Coverage 公式、几何权重、默认 beam 或物理布局，也没有证明召回质量优于
Source/Flat。C3 已记录的 mixed / beam 16 漏召回仍是后续问题。
