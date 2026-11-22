# 速记本形成记录 · 2026-11-22

本次把已有自举理解接成继续开发使用的速记本。依照本轮用户指令，活跃场保留在主开发分支的 `sujiben/field`，名称为“速记本”。旧实现和停用实验的归档由仓库整理另行处理。

## 起点与本轮范围

起点是提交 `beaafabfe8dec4ba1c154ecd324954fa81417489` 中已有的 M3 自举场：14 条当前判断、29 个表达版本、14 个 L0 占用格、14 个 atom、1 条原生有向桥。本轮复制完整场后维护新副本，旧实验场原件未改写。最初放置的工作目录随用户澄清迁至 `sujiben/field`；迁移前未结束的观察以 `defer` 终结，随后在新路径重新观察。

本轮运行时与新表达的源码基线均固定于上述提交。旧表达保留各自历史提交；没有把历史来源统一改成最新提交。这里记录的是这一轮知识形成，后续运行时修正及独立消费者试用由后续维护记录说明。

## 实际观察和选择

首先从 Surface 当前正文预览选到架构所在物理格，以 2 步、beam 32、最多 10 条观察同一局部。实际返回架构、几何、Surface、导航四条理解，其中导航通过 `coverage_up → coverage_down` 返回。现有场已明确区分物理层与观察阶，也已解释旋转缩放的多目标覆盖，因此没有按照预设概念名单再生成同义条目。

| 本轮表达变化 | 实际语义选择 |
| --- | --- |
| `nollm.architecture.v1 → nollm.architecture.v2` | 原位修订同一命题，补明概念与代码理解共用有来源的表达和几何现场；将 Host/Core/Access 的分工连到真实 `encounter/decide` 行为。保留旧正文与旧来源。 |
| 新增 `nollm.notebook-boundaries.v1` | 区分速记本、运行时、固定源码仓库，以及源码存在、运行时已更新、表达仍为 current 三件事。作为不同命题放在本次已显示的安装实现占用格，与安装理解同格。 |
| 新增 `nollm.notebook-restoration.v1` | 固定源码显示 Core document、Access bindings 与 Statement 文件分别保存不同内容；SnapshotService 仅委托传入 port。完整速记本的恢复边界因而需要单独理解。作为不同命题放在本次已显示的 Core 重开占用格。 |

第二个现场来自安装相关的已保存正文预览。在所选单一物理入口使用 `connected`，2 步、beam 32、最多 10 条，原有 `installation-reopens-state` 桥实际带回 Core 重开理解，并继续返回绑定、表达版本和提交等邻近理解。读完整正文后，再显式展开实际源码窗口。第三个现场从 Core 重开预览选择进入，用 1 步、beam 16、最多 10 条读取当前局部，然后作新增判断。源码展开是已观察理解后的证据补充，未计作原生召回。

完整恢复边界也曾出现在此前独立试用的未合入副本中。本轮对固定源码重新核对，并经当前场的实际观察放置；没有把它记为本轮首次发现。

## 原生关系及回读

修订后的架构正文解释了为什么共同入口实现是相关证据。在读过两端当前正文后，新增有向桥 `architecture-realized-by-encounter`，由架构物理格连接共同入口实现物理格。桥保存的是格之间的原生联系；成立条件在表达正文中，几何权重不充作语义证明。没有另建概念关系索引、关键词表或源码到入口的外部路由。

随后从 Surface 重新观察架构预览，选到同一个物理入口，以 `connected`、1 步、beam 16、最多 5 条召回。结果中的 `nollm.adapter.v4` 路径为 `bridge`，最后通过 `--recall` 返回它并结束游标。这证明新增关系已经参与实际执行；本轮预算仍报告 exhausted，不据此宣称遍历了整个场。

## 保留与核对结果

| 项目 | M3 起点 | 本轮结束 |
| --- | ---: | ---: |
| 当前判断 | 14 | 16 |
| 表达版本 | 29 | 32 |
| L0 占用格 | 14 | 14 |
| atom | 14 | 16 |
| 原生有向桥 | 1 | 2 |

核对确认：原有 29 个表达文件字节不变；原有物理格地址和原桥不变；除架构原位修订外，既有绑定保留；新表达的 12 个固定来源窗口均可从原提交展开。两个新增命题与相关旧判断同格，使表达数量增加而物理格数量不变。形成过程有一次误把 `choose` 当作 CLI 子命令的调用，CLI 拒绝不可用候选；随后按帮助使用显示的候选 ID，完成原生选择，未绕过现场决定。

本轮验证了这些具体正文、来源、历史保留和桥的回读，没有据此证明任意问题都能在默认预算中找到最佳入口，也没有把短预览视为完整语义。后续代码变化应由新的实际使用和回源决定受影响理解的修订范围。

## 新表达的固定依据

全部新来源固定于 `beaafabfe8dec4ba1c154ecd324954fa81417489`。架构修订依据[第一性原理](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md#L11-L147)和[共同入口实现](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/project_memory.py#L173-L257)；速记本边界依据[表达保存与源码展开](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/project_memory.py#L28-L98)、[运行时安装](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/install_skill.py#L33-L64)与[运行时替换回归](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/test_project_memory.py#L98-L138)。完整恢复边界的四处实现依据列于[速记本说明](README.md#正文绑定和固定源码)，各表达自身也保存了这些精确窗口。
