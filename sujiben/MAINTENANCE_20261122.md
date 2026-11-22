# 速记本使用与 C4 维护 · 2026-11-22

本轮先使用独立副本回答一个实际任务：在新 checkout 或安装运行时后，如何恢复、使用和维护速记本，完整迁移要保留什么，关系实际保存在哪里。随后把发现的实现变化按固定 C4 提交 `5d27118b1011f7e8817d18c0a052e4f40719170f` 原位维护到正式场。

维护完成后，正式场有 **16 条当前判断、35 个表达版本、14 个 L0 占用格、16 个 atom、2 条原生有向桥**。本记录说明一次真实使用及其限制，不作为概念到入口的路由表。

## 独立副本实际消费

本次由速记本形成者执行独立副本消费，不属于未知语料盲测。入口均从当次 Surface 的已保存正文预览选择；没有使用关键词/find、预先指定地址或 Statement ID、外部概念表进入场。固定 ID 在原生观察之后用于展开正文和来源。

第一轮在 Surface 第三页看到“完整速记本包含几何状态之外的当前绑定与表达正文”，据此选择物理入口。该格也保存 Core 重开理解。Surface 页面展示了这两条预览；物理候选页只展示其中一条，同时报告表达省略及文本截断，选定入口后的 locality 返回两条完整正文。

| 实际观察 | 预算 | 返回及遗漏 |
| --- | --- | --- |
| 第一轮：完整恢复相关入口 | connected；1 步；beam 16；limit 8 | 8 条，包含完整恢复、Core 重开、Stitch、召回、模板、表达版本、绑定、提交。 |
| 保留同一入口扩大范围 | connected；3 步；beam 48；limit 16 | 11 条。navigation 与 sources 经 `coverage_up → lateral → coverage_down` 返回；安装侧仍未返回。 |
| 第二轮：上一轮 recall 结束后，重新从 Surface 第五页选择安装与三者边界的预览 | connected；2 步；beam 32；limit 12 | 11 条。安装、三者边界在入口；Core 重开和完整恢复经 bridge 返回；共同入口实现经 lateral 返回；绑定、表达版本等经 bridge+lateral 返回。 |

三次局部观察都报告 `budget_exhausted=true`。本次使用需要两轮原生观察；没有把第一入口未返回的内容当作已召回，也没有通过外部表补出一个隐藏入口。安装到 Core 的桥有方向，在本次预算中不能反向把 Core 入口自动变成安装入口。

第二轮展示了同格表达的实际作用：旧桥连接安装物理格与 Core 物理格，新增完整恢复判断与 Core 重开同格，因此沿原桥一起返回。Stitch 保存的是物理格联系，正文解释使用条件；返回路径和几何权重不能单独证明语义正确。

## 回源、独立安装与迁移结果

从实际返回的表达读取了完整恢复的 4 个来源，以及安装器、命令分派、运行时替换回归、EM 适配器、current 判断和固定源码展开等来源。旧表达继续按原先保存的 a1c0f5a 等提交读取，新形成的两条边界判断按 beaafab 读取。源码读取是原生观察后的证据核对，未计为原生发现。

之后实际把当时工作树的运行时安装到独立临时目录，再传入独立副本的绝对 `--field`：完整正文可读，两条原生桥可读；把 `--repo` 改为另一份 archive checkout，仍能展开相同 beaafab 的固定 Snapshot 窗口及原行号。副本与正式场的 34 个文件内容一致，这一阶段没有写入场。运行时安装时尚在 C4 发布前；相关代码变化在 C4 固定后又按该提交回读，未把未提交工作树称作固定来源。

这些操作支持了本次任务需要的分工：迁移完整 `field`，保留几何状态、当前及支持绑定、所有版本正文和来源；用兼容运行时显式打开这个 field；回源时提供能够读取所引用提交的 Git 仓库。只保存 Core 快照不能恢复完整速记本。[Core document](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/packages/nollm-core/src/nollm_core/state.py#L442-L465)、[Access 绑定](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/packages/nollm-access/src/nollm_access/handle_store.py#L43-L84)、[表达存储](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/packages/nollm-access/src/nollm_access/statement_store.py#L20-L65)与 [Snapshot 委托](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/packages/nollm-snapshot/src/nollm_snapshot/service.py#L7-L24)分别说明这些内容的边界。

## 由实际差异触发的正式维护

独立安装的 `em --help` 已要求 `--field`，安装目录也不再带企业数学 field；旧 installation.v3、adapter.v4 仍描述默认场。预览输出增加了 `text_truncated`，旧 navigation.v2 尚未解释这个字段。因此 C4 固定后，本轮只修订这三条已受影响的当前理解：

| 版本维护 | 决定和固定依据 |
| --- | --- |
| `nollm.navigation.v2 → v3` | 从实际 Surface 选择导航预览，进入局部后原位修订。明确 Access 预览的 256 字符上限，区分 `text_truncated` 文本截断与 `truncated` 省略表达；locality 仍返回完整正文。依据 [Access 预览](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/packages/nollm-access/src/nollm_access/surface_navigation.py#L602-L623)、[候选输出](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/lab/nollm-lab/repository_memory/coverage_cli.py#L176-L196)与[同场观察和决定](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/lab/nollm-lab/repository_memory/project_memory.py#L127-L260)。 |
| `nollm.installation.v3 → v4` | 从实际 Surface 选择安装预览，取得包含两条边界理解的局部后原位修订。安装不再复制企业数学工作场，project/em 均显式指定 field，仓库中的研究场仍继续保存。依据[安装器](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/lab/nollm-lab/repository_memory/install_skill.py#L33-L63)、[EM 别名](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/lab/nollm-lab/repository_memory/enterprise_math/research.py#L1-L14)与[原场重开回归](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/lab/nollm-lab/repository_memory/test_project_memory.py#L98-L138)。 |
| `nollm.adapter.v4 → v5` | 重新从 Surface 选择架构预览，以 connected、1 步、beam 16、limit 5，经既有架构桥读到共同入口实现。在这个局部修订已显示的当前目标，目标物理位置不变。移除 EM 隐式默认场描述，保留共同观察、支持、原位修订和新命题的分工。依据[共享写入](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/lab/nollm-lab/repository_memory/project_memory.py#L28-L64)、[显式 field 参数](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/lab/nollm-lab/repository_memory/project_memory.py#L277-L286)与[Access 执行](https://github.com/awdawmip/Nollm/blob/5d27118b1011f7e8817d18c0a052e4f40719170f/packages/nollm-access/src/nollm_access/runtime.py#L157-L203)。 |

三次写入均使用 `encounter --revise`，每次都先观察当前局部并读取固定 C4 原文，没有绕过现场直接替换 field JSON。共同入口的修订实际发生在原生桥返回的目标格，概念与实现的联系参与了本轮维护。

`nollm.notebook-boundaries.v1` 保留：安装与 field 分离、`--repo` 回源和 current 的含义仍成立；C4 移除捆绑场加强了这种分工，没有使原命题失效。`nollm.notebook-restoration.v1` 也保留：其四处存储与 Snapshot 实现从 beaafab 到 C4 未变。没有为了统一提交号而重写不受影响的表达。

固定 C4 的企业数学 README 尚有默认场、安装复制场的旧文字，本轮回源已经发现；当前[研究入口说明](../lab/nollm-lab/repository_memory/enterprise_math/README.md)已随仓库整理同步修正。这里对安装及 CLI 行为的判断依据真实 `research.py`、`install_skill.py` 和参数实现；未以陈旧说明覆盖代码事实。

## 维护后核对

| 项目 | 维护前 | 维护后 |
| --- | ---: | ---: |
| 当前判断 | 16 | 16 |
| 表达版本 | 32 | 35 |
| L0 占用格 | 14 | 14 |
| atom | 16 | 16 |
| 原生桥 | 2 | 2 |

维护前的 **32 个表达文件逐字保留**，包括 M3 继承的全部 29 个版本。原有物理地址、几何身份、两个桥、三个被修订命题的 handle 均不变；其余绑定不变。`show` 回读确认三个旧版本 `current=false`，三个新版本 `current=true` 且指向各自前版。新版本的 16 个来源窗口全部固定 C4 并可展开，另从每个新版本各用一次 `source --id` 读回保存的窗口。全部维护游标正常结束。

本轮证明了这项具体使用任务以及由代码差异触发的局部维护。它没有证明任意新消费者、任意问题或默认预算下都能作出相同选择；实际入口遗漏、第二次观察和源码辅助都保留在记录中。
