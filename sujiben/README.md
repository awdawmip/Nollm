# 速记本

速记本是主开发分支中持续使用的 Nollm 开发工作场。LLM 在这里保存读过证据后形成的概念、实现行为和成立条件，并在后续开发中继续支持、修订或补充这些理解。活跃内容位于 `sujiben/field`；已停用的代码和旧实验另行归档。

概念与代码理解共用这个原生场。一条判断可以连接多份源码，也可以说明某个实现尚未满足的概念边界。物理关系来自实际占用、邻接、多目标 Coverage 和 Host 提出的 Stitch；语义判断由 LLM 作出。目录和文件名只负责存放材料，本文也不提供概念到物理入口的路由表。项目依据见[第一性原理](../docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md)。

## 打开并继续使用

在仓库根目录运行：

```bash
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field sujiben/field encounter \
  --cursor-file /tmp/nollm-sujiben.json
```

阅读返回的已保存正文预览。在同一命令的 `encounter` 后加入本次实际显示的候选 ID；需要下一页时加入 `next`。单物理成员候选显示 `physical_cell`，选择后直接进入 `locality`；多成员继续逐步选择。局部默认读取完整当前正文、固定来源和实际下降候选。准备新增或搬移时，先在同一会话执行 `--prepare-write` 观察写格；需要支撑建议时再显式 `--pressure`。预览的 `text_truncated` 表示正文被截短，`truncated` 表示该候选还有表达未展示。`project` 与 `em` 命令都需要显式指定 `--field`。

当前场已形成三层：L−2 保存8条完整短判断，共401 UTF-8字节；L−1 保存12条条件和使用关系，共2,278字节；L0 保留23条详细判断，共22,318字节。默认入口只展示 L−2，选择一个物理入口后先展开相邻 L−1，再按实际显示的 `descent_candidates` 选择下一观察位置。下面的 `CELL_ID` 必须替换为本次实际显示的格 ID：

```bash
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field sujiben/field encounter \
  --cursor-file /tmp/nollm-sujiben.json --descend CELL_ID
```

`--ascend` 沿当前观察路径返回一层。整个相遇的 `entry` 保持为最初选定的物理入口，`focus` 随下降或返回而改变；多个上层可覆盖同一份下层正文。入口层和局部可写层分别由 `--surface-layers`、`--layers` 控制，本场默认值在 `field/access/encounter.json` 中保存。当前默认 `steps=1, via=downward`；`steps=0` 可严格只读当前格，直到显式下降。

在这个现场判断下一步：已有理解足够时 `--recall`；同一命题的新支持用 `--reuse`；原判断需要改变时用 `--revise`；不同命题用 `--new`，可以选择已显示的空格或已占用格。写入需要新的表达 ID、LLM 写的正文和实际读过的固定源码窗口。`--none` 与 `--defer` 可以结束观察。完整工作约定见[原生使用说明](../lab/nollm-lab/repository_memory/skills/nollm-repository-memory/SKILL.md)；在上述命令末尾使用 `--help` 查看具体参数。

若当前范围不足，先不作终态决定，用同一个游标重新打开并显式调整 `--steps`、`--beam`、`--limit` 或 `--via`。`--via connected` 才允许经过原生桥。预算不足表示本轮观察的边界；几何可达也不保证在本轮预算内返回。游标是临时导航状态，成功结束后删除，不属于速记本的持久知识。

默认 `compact=true` 保留完整正文、选择 ID、几何路径、一个固定来源及来源总数；`show` 可以打开全部来源。需要完整压力诊断与来源列表时使用 `--pressure --full-details`，恢复简洁观察时使用 `--compact`；`--read-only` 停止写格与压力准备。

## 写入时保持分层容量

本场的 `field/access/content_budget.json` 在写入前检查当前物理正文：L−2 每格最多2条、128字节，整层最多16个占用格及2 KiB；L−1 每格2条、512字节；L0 每格2条、8192字节。这些是当前速记本的配置，层号和数值可以按真实使用调整。

`revision_current` 同样检查替换后的正文，`move` 按实际载荷检查目标位置；`reuse` 增加支持 Evidence，不增加当前物理正文。容量超限时，根据返回的具体指标重新提炼、整理已有判断，或沿已观察的下层保存细节。支撑压力继续给建议，容量约束控制实际体量。第一层保存有意义的短判断；条件和证据按相邻覆盖逐层展开。

后继模型可以在同一相遇中用 `--reorganize PLAN_JSON` 一起提炼、修订、搬移或退出占用。
容量按最终布局检查；改变的当前表达与指定旧入口路径须能实际向下读回。
新粗层、入口配置与预算也可一起调整。计划格式见
[局部重组与存放](../lab/nollm-lab/repository_memory/skills/nollm-repository-memory/references/local-reorganization.md)。

本场的 Core 与绑定已显式迁移到宽度64的物理分页，继续沿原场路径打开。
`project --field sujiben/field storage` 可只读查看布局。已知物理格避开远处页正文，
同页内容仍有读写成本；只给表达ID寻找位置仍会盘点绑定，完整快照仍是全量操作。

## 正文、绑定和固定源码

`show` 打开一个确定版本的完整表达；`source` 按它保存的提交和行号回到原文。将下面的 `STATEMENT_ID` 替换为刚观察到的版本 ID：

```bash
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field sujiben/field show STATEMENT_ID

python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field sujiben/field source --id STATEMENT_ID --number 1 --repo .
```

一条表达可以引用多个窗口，`--number` 逐一展开。`current` 只说明当前绑定；它不表示该理解已经对最新源码复核。支持表达有自己的正文和来源，历史版本也继续可读。源码变更后，先回到受影响的局部理解和真实源码，再决定维持、支持、原位修订或新增；不要仅因为仓库 HEAD 改变就重写全部理解。

速记本的 `field`、执行命令的运行时、保存固定提交的源码仓库分别承担不同职责。更换运行时可以继续打开原场。搬迁速记本时保留整个 `field`，同时保留可以读取来源提交的 Git 仓库；Core 快照本身不包含 Access 的绑定和全部版本正文。这一边界的实现依据是 [Core 状态](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/packages/nollm-core/src/nollm_core/state.py#L442-L465)、[Access 绑定](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/packages/nollm-access/src/nollm_access/handle_store.py#L43-L84)、[表达存储](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/packages/nollm-access/src/nollm_access/statement_store.py#L20-L65)和 [Snapshot 委托](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/packages/nollm-snapshot/src/nollm_snapshot/service.py#L7-L24)。

[形成记录](FORMATION_20261122.md)说明速记本的继承起点与补充理解；[使用与 C4 维护记录](MAINTENANCE_20261122.md)说明两轮实际消费、独立安装与换源码仓库的结果，以及受影响版本的原位修订。这些记录解释具体形成和维护依据，日常使用仍从原生场开始。

[支撑压力与几何维护记录](SUPPORT_GEOMETRY_MAINTENANCE_20261122.md)记录显式多层写入、建议压力和 Lab 变形实现之后的局部理解更新及回读；固定源码与实际测试范围见[实现说明](../docs/project/NOLLM_SUPPORT_PRESSURE_AND_DEFORMATION_IMPLEMENTATION_20261122.md)。

[残差算法维护记录](EM_RESIDUAL_MAINTENANCE_20261122.md)记录吸收进取数论研究后的覆盖、平移和压力计算优化，以及相对坐标 v2 的局部修订；它保留原有版本，说明成立条件与本次完整实测范围。

[有理数化维护记录](RATIONAL_GEOMETRY_MAINTENANCE_20261122.md)记录新 Lab 有理几何合同、共同变换消去和整数计算核的原生理解；它保留既有 Core 与 float Lab 判断，并说明精确采样、末端投影和分母增长的边界。

[覆盖精度维护记录](PRECISION_MAINTENANCE_20261122.md)记录固定精度的全域边界、有限扫描与局部误差证书的区别，以及 16 位起步并按边界不确定性升精度的实现依据。

[自适应有理几何维护记录](ADAPTIVE_RATIONAL_MAINTENANCE_20261122.md)记录实际逐步整数区间执行、边界未决点精确回退，以及精度预算和有理几何两条判断的原位修订与原生读回。

[量化结构维护记录](QUANTIZED_STRUCTURE_MAINTENANCE_20261123.md)记录接受有限精度缺项的独立判断、12 位默认与 8 位速度档的实测取舍，以及新增表达的原生放置与同入口回读。

[相邻层 8 位与容量维护记录](ADJACENT_P8_CAPACITY_MAINTENANCE_20261123.md)记录用户选定局部 8 位与 96 点、共同尺度探针和局部读写扩容方案，以及量化结构的原位修订、容量判断的新增与同入口回读。

[Surface 存放方式维护记录](STORED_SURFACE_FORMATION_MAINTENANCE_20261123.md)记录用户要求表层本身保存短缩影的纠正、实际原生分层试验，以及容量判断缩短为33字符的原位修订。[分层形成与实际使用记录](STORED_SURFACE_IMPLEMENTATION_MAINTENANCE_20261123.md)记录8/12/23条分层形成、写入容量、同入口下降、真实读者反馈和原版本保留。物理分页与局部重组已由下列2026-11-24维护应用；自动巡查共享上层仍是后续工作。

[向下巡查与重新组织记录](TOP_DOWN_MAINTENANCE_20261123.md)保存该轮计算/写入代价比较、后继 Host 改概括与移动候选的复制场结果，以及活跃中层 `entry-traversal.v2` 的同入口原位修订。维护可主要沿表层向下展开，按需反查保留为局部加速；分类可以调整，重组时应回读新旧相关路径。该轮中层正文为2,026字节，完整版本文件69份，表层398字节。

[固定测试版与精度维护记录](TEST_BASELINE_MAINTENANCE_20261123.md)保存 `nollm-test-20261123.1` 的固定提交，以及中层 `precision-contracts.v2` 的原位修订。该轮明确区分Core Q40/96、旧Lab量化p12/显式p8和待实现的局部p8/96，形成70份版本、中层2,095字节、表层398字节。固定测试分支保持原始场，main继续维护。

[局部重组与分页维护记录](LOCAL_REORGANIZATION_MAINTENANCE_20261124.md)记录固定源码
`211ed1f`之后的9项原位修订和实际重新打开回读。原70份表达全部保留，现有79份；
43个物理handle、41个占用格与两条桥保持，34项未改当前绑定保持。
它也记录安装品的独立会话试用及来源窗口纠正，不将副本试用混入活跃场。

[局部p8执行器维护记录](LOCAL_P8_MAINTENANCE_20261124.md)将已观察的中层精度判断及详细量化判断分别原位修订到v3，引用固定实现 `4dcc953f7f9631f715f1cfe9761abf1f5ad00365`。新局部p8的单位、规范锚、完整地址与测量结果由原入口读回；原79份表达保留，现有81份，43个handle、41个占用格、两条桥和其余41项当前绑定保持。当前速记本仍用Core Q40/96。
