# Nollm 架构与理念审核：供本地测试和优化使用

日期：2026-11-28（Asia/Hong_Kong）。审核代码基线：`d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d`。
范围：当前 Core、Access、仓库记忆 CLI、便携部署和 OpenClaw memory-slot 的关键活跃链路，以及已有独立试验的证据强度。

执行入口：[完整测试—优化计划](tasks/NOLLM_TEST_OPTIMIZATION_PLAN_20261128.md)；本地 agent 可直接使用[交接任务](tasks/NOLLM_LOCAL_AGENT_HANDOFF_20261128.md)。

## 1. 审核结论

**保留几何原生、证据优先和 LLM/Core 分工；优先补齐入口间的实现接缝、真实发现能力及成本证据。**

仓库记忆 CLI 已形成可以实际读、写、修订、重组和回源的原生工作回路。其主要关系来自几何占用和覆盖，语义判断交由 Host/LLM，原文与解释、当前位置与事实真实性保持分离。这一方向有实际代码和有限独立使用证据支持。

接下来的首要工程问题是：CLI 的较新能力尚未完整进入 OpenClaw memory-slot；几何路径验证与终点回读尚不能替代有限预算内的完整相遇；已有独立回答试验也没有证明整体召回完整性或相对平面记忆的净收益。局部 p8 已完成显式 Lab 执行器，生产 Core 仍为 Q40/96，后续应在同一物理 profile 下检验显式候选合同。

本审核完成的是关键路径静态审查、历史结果重算及小范围现场核对。完整本地测试、优化实施和新独立试验按关联计划执行；本文不把计划列为已经通过的验收。

## 2. 第一性原理如何落到实现

依据：[README 的 Project understanding](../../README.md#project-understanding)、[第一性原理](../architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md)、[当前入口](ACTIVE_PROJECT.md)。第一性原理第 10 节明确允许经过校准的近似 Coverage；96 点采样与连续面积真值分别评价。

| 原则 | 当前实现证据 | 测试应观察什么 |
|---|---|---|
| Evidence 是事实源 | Statement 保留正文、版本和固定来源；SourceSnapshot/Git 返回对应原文窗口 | 来源能否支持当前断言；版本是否正确；缺失原文是否真实报告 |
| LLM 决定语义，Core 执行几何 | CLI 的选择动作由 Host 提供；Core recall 不读正文作语义排序 | 形成、新增、支持、修订、暂缓来自真实模型；脚本只执行与校验 |
| 关系来自几何场 | Core 返回 handle 后，Access 才解析对应绑定/正文 | 移除派生缓存后结果保持；不能靠题号、关键词或来源表找入口 |
| 非树形上下覆盖 | 多个上层可覆盖同一详情；桥为显式、有向、可撤销的几何连接 | 共享详情、桥开关、跨层关系与边界都保持实际语义 |
| 一个相遇保留一个根入口 | `project_memory.encounter` 固定 entry，focus 沿实际 coverage_down 移动 | 完整 root/focus/path 与预算；重开入口应另计一次相遇 |
| Surface 存实际短判断 | 当前场在上层存正文；物理层和聚合阶分别配置 | 第一页读取真实上层正文，截断和未显示项分别报告 |
| 文件优先、可恢复 | Core 分页日志、Access 局部撤销记录、版本文件和公开状态接口 | 普通失败后的恢复、未知提交的核对、原文与旧版本保存 |

代码依据：`project_memory.py:296–625`、`nollm_core/recall.py:74–141`、`nollm_access/runtime.py:383–408`、`nollm_core/paged_storage.py:181–235`。这些路径均位于上述固定基线。显式 `aux` / `baseline` 工具的存在不等于原生路径使用了外部语义路由。

对象文件的最小物理定位、由坐标计算的页、局部占用及可丢弃缓存属于允许的工程机制。审核按其实际作用判断，不能仅因名称含 lookup/index 就删除，也不能把决定召回关系的外部路由包装成缓存。

## 3. 主要发现与处置

### A1 — 仓库记忆 CLI 与 memory-slot 的能力尚未接齐

**类型：已确认的集成缺口。优先处理。**

当前两条路径并非同一完整相遇服务的两个展示适配器：

| 环节 | 仓库记忆 CLI / 独立部署 | V3.14 memory-slot 活动 .js → bridge |
|---|---|---|
| Surface 范围 | 使用场的 surface_layers，当前使用上层存放的完整短判断 | FIELD_SCOPE 固定 physical_layers=[0] |
| 物理观察 | root 固定，支持相邻 descend/ascend、focus_path | region→locality；工具 action 未暴露物理 descend/ascend |
| 读取准备 | 默认读取，prepare-write 与 pressure 按需 | 旧 FieldEncounterEngine 进入 locality 时构造 facts 与 vacancies |
| 数据读取 | 已知 handle 的局部绑定/正文读取 | 旧 progressive atlas 导出完整 Core 状态并盘点占用 |
| 摘要展示 | 上层有真实物理正文，显示截断单独标识 | 旧 atlas 使用 64 字符 routing preview |
| 自动形成 | 仓库 CLI 接受 Host 已作出的语义决定 | 发布包明确提示 Formation Loop writer 尚未迁入 |

直接证据：

- [memory-tools.js](https://github.com/awdawmip/Nollm/blob/d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d/integrations/openclaw/nollm-memory-provider/src/memory-tools.js)：第 3–18、33–40、174–187 行。
- [bridge-runtime.js](https://github.com/awdawmip/Nollm/blob/d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d/integrations/openclaw/nollm-memory-provider/src/bridge-runtime.js)：第 75–98 行进入 Formation Python bridge。
- [memory_loop.py](https://github.com/awdawmip/Nollm/blob/d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d/packages/nollm-access/src/nollm_access/memory_loop.py)：第 564–568、1090–1097 行。
- [field_encounter.py](https://github.com/awdawmip/Nollm/blob/d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d/packages/nollm-access/src/nollm_access/field_encounter.py)：第 419–505、717–759 行；其中 advertised `expand_same_entry` 还需与真实可调用动作对齐。
- [provider.js](https://github.com/awdawmip/Nollm/blob/d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d/integrations/openclaw/nollm-memory-provider/src/provider.js)：第 31–35 行的 autoCapture 状态。

处置：先用同一复制场和同一语义决定序列做两个 adapter 的差分测试，再把成熟相遇能力收敛到合适的 Access 公共服务。保留 thin adapter；生产包经公共接口消费能力。当前 [Lab charter](../architecture/modules/NOLLM_LAB_CHARTER.md) 不允许生产模块导入 Lab，因此直接 import `project_memory.py` 不能作为集成完成。

build.mjs 只复制 `src/*.js`；历史 .ts 路径不应误计为活动实现。查询接口接通、自动 Capture/Formation、干净安装与真实 Windows/Host 验收是分别可核对的工作。

### A2 — 重组的结构回读与原入口实际可发现性需要分开

**类型：已确认的验收范围差异。**

[local_reorganization.py](https://github.com/awdawmip/Nollm/blob/d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d/lab/nollm-lab/repository_memory/local_reorganization.py) 第 227–267 行检查真实相邻下行边、提交重组，再检查路径，并直接从终点格以 steps=0 回读正文。这确实验证了结构路径和终点当前内容。

后续需另外验证：从原 root 按给定 beam/result/step 预算逐层回放，以及真实 Host 是否能根据更新后的上层判断找到目标。显式列出的旧入口也要用实际相遇回放。全场无孤儿、几何存在一条路径和 show(ID) 成功均不足以替代这些观察。

提交后回读失败属于已提交后的结果，恢复者要先核对状态再决定后续动作。不能将其当作未提交而重复新增。

### A3 — 部分质量缺口发生在回答组合，而非几何传播

**类型：历史独立试验中的已确认现象；具体未取回原因尚需分解。**

2026-11-25 私有独立试验保留 23 题：8 full、13 partial、2 justified_unconfirmed；114 个事实单元为 84 covered、14 partial、16 omitted、0 contradicted。部分遗漏事实未进入读者实际窗口，另一些已经读到却未写入答案。评分细则还含部分超出简短字面问题的补充事实。

因此优化要沿事实链定位：原文存在 → 已形成 → 入口与几何可达 → 本轮预算内返回 → 实际原文窗口 → 答案表达。只有观察支持时才能归因到某一阶段。正确保持现况未知与漏掉已知历史可以同时发生。

该试验来自三个连续读者上下文，同模型且组内复用已读内容；现已作为开发回归。新的泛化结论需要候选冻结后的新题和独立作答。详细方法见计划的质量评测部分。

### A4 — 分页改善局部正文读写，但部分发现与初始化仍需较广扫描

**类型：代码可见的复杂度边界；实际瓶颈待测量。**

| 路径 | 较广操作 | 当前代码 |
|---|---|---|
| 首次 Surface / 聚合缓存 miss | 盘点声明 scope 中的 occupancy 并排序 | `state.py:477–495` |
| 仅 Statement ID / 旧 atom ID 定位 | 读取绑定盘点；已知 handle 路径可局部化 | `handle_store.py:181–208,282–293` |
| 一个物理页的修改 | 读写并日志化同页内容 | `paged_storage.py:255–273` |
| Core 启动 | 打开完整 bridges 文件 | `state.py:123–127` |
| 显式条件写 | 按现有合同计算完整状态 identity | `runtime.py:329–334` |
| SourceSnapshot 构造 | 读取整个来源 manifest；正文缓存在实例内 | `source_snapshot.py:44–82` |
| OpenClaw 旧 atlas | 完整状态导出与盘点 | `memory_loop.py:564–568` |

源码位于 `packages/nollm-core/src/nollm_core/`、`packages/nollm-access/src/nollm_access/` 及 `lab/nollm-lab/repository_memory/`。已有局部存储 probe 计量的是 Python 文件 API payload bytes，未包含真实设备 I/O、目录/stat、fsync/rename、建场费用或模型耗时。它使用固定小 Surface、远处 L0 增长且不含桥。

处置：区分上层固定/同步增长、远处多页/同页密集、已知 handle/仅 ID/历史、bridge 数量、source manifest 体积及冷暖进程。先定位实际热点，再优化重复读取、已观察 handle 传递、纯几何缓存或分页。以关系不变的对照检验优化，不建立来源或主题到入口的持久语义路由。

### A5 — 局部 p8 已完成；生产候选需同一物理 profile 下的显式合同

**类型：已确认的数值合同边界。**

当前 Core 为 `parity_preserving_q40_residual_mask_kernel_v2`，保留 96 个样本的全部命中、Q16 归一化和既有地址域。现有掩码实现已减少逐点重复计算。

Lab `local_quantized` 使用显式源格局部长度、源格扭转前的仿射中心锚、偶数整数目标锚与完整地址分离。表示重锚和共同世界尺度/平移在其声明合同内保持结果。纯仿射路径仍走精确整数仿射求值；p8 主要作用于剩余非线性递推。[实现与固定输入结果](NOLLM_LOCAL_P8_EXECUTOR_20261124.md)已保存独立 Fraction 复算和旧反例。

处置：旧规范锚执行器不需要重做。若推进生产 p8，先定义同一默认物理 profile、同一 96 点采样下的显式候选；保持完整系数与整数地址，只改变声明的局部余量算术。分别比较候选自身独立复算、相对 Q40 的采样关系变化、相对物理 Oracle 的加权误差、实际操作成本与现有场的读取影响。

有理 Lab 的耗时不能与不同几何的 Core 耗时直接归为精度收益。`depth=1/2/3/5` 表示同一相邻层对中的扭转段数。p8 不限制地址范围、材料数量或正文容量。

### A6 — 恢复合同已改善；一个场的写入所有权仍是进程内边界

**类型：支持范围已确认；未发现新破坏性见证。**

Access 条件写遇到 unknown commit 时保留 Evidence 的修复已存在，相关回归见 `test_reorganization.py:256–312`。Core 分页日志和 Access 局部撤销记录覆盖了已声明的普通写入失败及部分进程中断恢复。

`workspace_owner.py` 与 `workspace_lock.py` 使用进程内字典和 RLock。此次临时探针在父进程仍持有 Core 时，子进程也成功打开同一临时场。这证实所有权作用域，未尝试并发破坏性写入。独立评测使用各自的复制场，同一场串行写入；若实际 Host 要支持多进程共同写，再以该需求为对象扩展与验证。

当前 `--read-only` 表示停止写候选/压力准备；新场初始化或待恢复记录有自己的行为。它不是通用只读文件系统打开模式。Bridge stitch/unstitch 与局部多动作重组也有不同提交路径，不能借重组测试宣称桥已包含在同一事务中。

### A7 — 测试资产的名称不能替代其真实执行合同

**类型：已确认的历史工具适用性问题。**

- `reference/python/nollm/grf/grf8_quality_benchmark.py` 的 N1/N2/N3 排序使用 category/topic/partition 元数据；vector_like 使用 ID SHA 距离；faithfulness 仅检查非空 source_ref；update_latency 测 tuple 重建。它可用于原历史 fixture，不能证明当前原生召回、实际 embedding、来源支持或持久化修订性能。
- `run_core_translation_covariant_validation.py` 仍读取旧精确类型字段并使用超出当前域的地址，要求精确支持集相同。它不适合作为当前采样核的全量门禁。
- `probe_top_down_reorganization.py` 固定历史正文、ID 和坐标，使用其文档声明的旧场才是原实验重放。
- `run_nollm_test_matrix.py` 的 reference pytest 矩阵不等于 packages+Lab 全覆盖；unittest discover 也会漏掉 pytest 函数测试。
- 当前几何改动应使用 `run_broad_residue_coverage_calibration.py`、`ACTIVE_APPROXIMATION_POLICY` 与适用的独立 Oracle。缩小规模的 smoke 不等于通过完整校准条件。

计划给出当前命令、需要新增的薄执行器和选择测试的依据。不会要求为无关改动修复全部历史测试。

### A8 — 当前绑定、固定依据与最新事实是三种状态

**类型：持续使用中的必测语义边界。**

`current` 表示当前绑定；固定来源 commit 表示该判断的形成依据。更新运行时不会自动重审全部理解，也不会自动把冻结快照变成最新现实。原始树完整捕获与本地文件物化、语义形成数量分别记录。

便携 build_deployment 的 runtime_commit 是调用者提供的版本声明，不是自动验证工作树身份的凭据。构建者应在实际固定源码上构建并记录已有 Git 版本；读取固定来源时继续使用已有字节和行窗口校验。测试要覆盖换工作目录、缺失来源、已修改来源、来源变更后的支持/修订和后续使用，不增加第二套审计或凭证体系。

## 4. 已有证据可支持到哪里

| 证据 | 可支持的结论 | 后续需要补的对象 |
|---|---|---|
| 2026-11-23 固定测试包 | 固定 Q40/96 场与功能回归；保留旧问题见证 | 当前候选的受影响回归 |
| 2026-11-24 local p8 比较 | 声明有理合同的单位/锚不变性、标签与压力变化 | 默认 Core 物理 profile 的候选与迁移 |
| 2026-11-24 分页与重组 | 局部正文 I/O、最终布局容量、恢复和结构读回 | 全路径发现、同页/桥/元数据规模 |
| 2026-11-25 私有独立试验 | 118 条已形成判断可使用并追源；有限独立维护 | 新题、同内容对照、长期形成维护净成本 |
| 已有 provider .js 单测 | 工具/桥协议及模拟请求行为 | 真实 JS→Python→Access→Core、当前 Host/Windows |

私有试验固定于 `fddcc1e6c3f5f24a2c0815cd93bbba0e33bc3822` 的 `experiments/nollm/20261125/`。原始来源 commit 为 `134f99935f04876c9c8a3a2e6596c4cefc2aeec5`；12,994 blobs / 188,639,573 bytes 是原始树，49 份本地物化文件、32 份被判断引用，118 条是语义形成范围。83/83 详情结构可读不等于全库语义覆盖。

首轮答案运行于 Nollm `a30dafca126b2b533ee86868cab10d1bc7e5e51a`，对应初始部署 `97f5354a3bd0cdc3ffbb7f5cd2f17d9727a9ec96`；最终包携带 `d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d` 的修复运行时，修复后复验不倒灌首轮成绩。

原读者累计 150 次 CLI（含 3 help 和 3 失败），36 次 source 成功，子进程累计 41.630085 秒。该耗时不含模型和编排，不作用户总时延或相对优势。导航修复后的聚焦复测与原回答成绩分别保留。

## 5. 文档纠偏与本轮实际核对

本 PR 仅作两处与审核直接相关的现行文档澄清：ACTIVE_PROJECT 的 phase-kernel v1 段标为 PR #4 历史推导并指向现用 residual v2；OpenClaw charter 的旧 memory-provider ownership 禁令按已完成 V3.14 memory-slot 范围更新。Core 私有接口边界、语义归属与原始历史记录继续保留。继承 V3.13 的空 AGENTS 要求不覆盖现有稳定入口。

本轮实际核对包括：固定 main 的关键源码/入口阅读、原评分 JSON 和 CLI 日志统计重算、现用速记本的只读相遇、复制场从 root `[-2,2,1]` 下降至 focus `[-1,3,0]` 并 recall `nollm.installation.v5`、两个现有脚本的 --help，以及临时跨进程打开范围探针。主读路径保持根入口，未准备写格或压力。完整产品套件、性能基准、新语义盲测、OpenClaw 安装及 Windows Live 留待本地运行。

## 6. 证据入口

- [当前便携部署实现与验证](NOLLM_PORTABLE_DEPLOYMENT_20261125.md)
- [已修复的旧页导航与参数问题](NOLLM_SURFACE_NAVIGATION_FIX_20261125.md)
- [当前局部重组与物理分页](NOLLM_LOCAL_REORGANIZATION_AND_STORAGE_20261124.md)
- [已有 Source / Flat / Native 开发试验](../../lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/REPORT.md)
- [私有独立部署总报告](https://github.com/awdawmip/chatgpt-global-knowledge/blob/fddcc1e6c3f5f24a2c0815cd93bbba0e33bc3822/experiments/nollm/20261125/REPORT.md)
- [私有逐题评分](https://github.com/awdawmip/chatgpt-global-knowledge/blob/fddcc1e6c3f5f24a2c0815cd93bbba0e33bc3822/experiments/nollm/20261125/evaluation/independent_grading.md)

私有题目、原文、答案和完整运行转录沿原仓库权限保存；本文只记录工程发现、汇总和固定引用。

