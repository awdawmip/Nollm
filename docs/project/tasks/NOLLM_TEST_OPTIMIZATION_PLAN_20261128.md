# Nollm 本地测试—优化—复验计划

日期：2026-11-28（Asia/Hong_Kong）。输入审核：[架构与理念审核](../NOLLM_ARCHITECTURE_REVIEW_20261128.md)。
本计划由用户要求写入 PR，交本地 agent 运行。本文提供目标、可用输入、工程依赖、测试方法和验收条件；具体实现方法、实验规模及工作拆分由执行者按实际证据调整。

## 1. 目标、交付与当前边界

目标是完成一轮可复查的闭环：建立实际基线，定位功能/发现/成本缺口，实施有依据的改进，在相同输入上复验，再用新的独立任务检查泛化。成果包括候选源码、必要回归、真实运行记录和清楚的取舍。

本地执行范围覆盖 Core、Access、仓库记忆 CLI、便携部署以及隔离的 OpenClaw adapter/Host 试验。用户选定的相邻层局部 p8/96 方向继续研究，现用 Q40/96 为对照。真实全局内容继续在私有复制场独立测试。

**用户要求的全局知识库现有方案和入口保持不变。** 原实验、冻结输入和原始失败保留；候选场、来源更新试验和私有模型转录放在独立实验位置。Nollm PR 接收通用源码、测试和汇总，私有正文沿已有权限保存。当前 PR 是计划与文档澄清，产品代码与整轮执行尚未在本 PR 完成。

## 2. 固定输入与版本识别

| 对象 | 固定参考 | 用途 |
|---|---|---|
| 审核时 Nollm main | `d6e5e5c54a6c542bf66345b6f8f72bb9f3151e3d` | 本轮受审功能基线；不要用包版本 0.1.0 代替实现身份 |
| 旧固定测试包 | `c4b6b922b993732e008e8d1b95951b47bec823df`，`test/nollm-20261123-1` | 历史控制与原问题见证 |
| 旧包引擎和场 | `f37667bf232360d0c26d37de0639285084230ddc` | 重放当时状态 |
| 局部 p8 实现 | `4dcc953f7f9631f715f1cfe9761abf1f5ad00365` | 现有规范单位/锚执行器 |
| 私有最终部署 | 全局仓库 `fddcc1e6c3f5f24a2c0815cd93bbba0e33bc3822`，`experiments/nollm/20261125/` | 独立内容、原始试验和修复后的运行时 |
| 私有初始部署 | `97f5354a3bd0cdc3ffbb7f5cd2f17d9727a9ec96` | 原读者试验使用的部署 |
| 原读者代码 | Nollm `a30dafca126b2b533ee86868cab10d1bc7e5e51a` | 保留修复前失败，避免把旧答案记在新代码名下 |
| 私有固定来源 | `134f99935f04876c9c8a3a2e6596c4cefc2aeec5` | 原文真值的时间和版本边界 |
| 开发工作场 | `sujiben/field`，审核时 43 current / 86 versions | 开发理解与后续维护；实验使用副本 |

私有材料的[稳定入口](https://github.com/awdawmip/chatgpt-global-knowledge/tree/fddcc1e6c3f5f24a2c0815cd93bbba0e33bc3822/experiments/nollm/20261125)包含 REPORT.md、field、runtime、snapshot、formation 和 evaluation。有权限的本地 agent 从固定 ref 取得所需文件；不要求用户另行下载或搬运附件。工程/合成测试可在未取得私有材料时独立推进，私有验收则如实标记缺少的输入。

开始执行时记录实际 PR head、工作树差异、解释器、OS、CPU/内存和可用 Host/模型版本。如 main 已前进，保留上述控制，明确候选基于哪个较新提交及相关差异。沿用用户已有环境；需要隔离时使用普通 worktree、虚拟环境和场副本，保护已有未提交工作。

每个并行写执行者使用自己的场副本，同一场串行写入。这对应当前进程内 ownership 合同，不构成新增并发服务要求。建场、迁移和拷贝在无活动写入的明确时点进行。

## 3. 工作包与依赖

| 工作包 | 产出 | 可以开始的依据 | 完成时检查 |
|---|---|---|---|
| B 基线和真实测试入口 | 当前结果、失败分类、可运行命令 | 固定代码/场/来源可读 | 历史证据与本轮运行分开，实际失败可复现 |
| F 读写、维护、来源与恢复 | 有限预算完整相遇和生命周期用例 | B；可与测量并行 | 写成功、同入口返回、相关旧读法、原文历史分别成立 |
| I 共享相遇与 Host 接缝 | 同一 Access 能力的 CLI/provider 适配与真实 bridge 测试 | B；以现有 CLI 行为为可执行参照 | 上层配置、完整短判断、root/focus、按需写准备、终态和来源合同对齐 |
| Q 真实语义质量 | 已知回归归因、同内容比较、新独立题 | B；新题在候选/场冻结后执行 | 必需事实、正确未知、来源支持与成本清楚 |
| P 成本与增长 | 实际热点、同输入前后数据 | B；覆盖 F/I 的真实路径 | 区分元数据/正文/来源/进程/模型，改善可解释 |
| G 局部 p8 生产候选 | 同物理 profile 的显式候选、误差与迁移结果 | 复用现有 Lab 资产；独立于 Q40 功能改进 | 自身算术、Q40 差异、物理 Oracle、完整操作成本与场路径分别核对 |
| R 集成复验与交付 | 候选提交、复验汇总、适用 Host 记录、未完项 | 已选改进完成 | 用户目标和边界保持，已测/未测准确，可继续或回退 |

这些是依赖关系，不是要求所有工作串行。无需等待 p8 成为生产核才修复读取或回答缺口。几何发生改变时，适用数学校准先于对应候选的 Live 结论；沿用已验证 Q40 的集成工作可复用其未改变的数学依据。

## 4. B：建立可复查的基线

### 4.1 输入口径

分别记录原文已捕获范围、本地物化范围、被实际阅读的来源、已形成判断、当前占用与历史版本。2026-11-25 的 12,994 blobs 是原始树规模，118 条是形成范围；这些数值不能互相替代。

从当前 Surface 实际观察并由 Host 选择入口。工程审计可用源码搜索，但报告标明其辅助作用。来源清单、归因表与答案 rubric 不进入原生 runtime 的入口选择。

### 4.2 基线测试范围

以第 11 节的现有命令覆盖将要修改的接口、恢复与几何。若基线失败，先确定是环境、旧测试合同、当前缺陷还是输入版本不匹配。保存原失败，再建立候选。已有充分且未受影响的证据可复用；组合运行重复覆盖的 test case 不重复计数。

本轮不能以只跑 unittest discover 宣称全部 Python 包通过，也不能把 reference 的旧全矩阵当作当前 packages+Lab 的全集。新增测试针对具体未覆盖行为；不为文档改动执行完整产品套件。

## 5. F：读、写、重组、来源和恢复

### 5.1 场景与验收

| 场景 | 真实动作/输入 | 观察与验收 |
|---|---|---|
| 存放的 Surface | 打开实际上层，翻页，回选已见候选 | 正文来自存放的短判断；旧页候选重新核对；累计预算不重置 |
| 单入口逐层发现 | 选一个 root，下降/返回，多上层共享详情 | entry 保持，focus/path 对应实际相邻边；截断与预算耗尽如实返回 |
| 只读工作流 | 已完成恢复的场上 encounter、recall、show、source | 不准备写格和压力；持久知识内容保持；游标另存。缺失场/待恢复场单独测试 |
| 新增 | Host 选择本次显示的当前/真实下行格 | 实际保存、相同入口读回、来源可打开；上行支撑但无下读路径见证仍被正确处理 |
| 支持与修订 | 同命题支持、同槽位更正、相似但不同表达 | Host 语义决定明确；reuse 不增加当前物理正文；revision 保留旧版本及各自来源 |
| 移动与重组 | 同一已观察局部提交最终布局；涉及共享详情 | 容量按最终布局；新路径与声明要保留的旧路径均以完整相遇复验 |
| 预算导致的漏读 | 弱权重目标、密集同页、result/beam 截断 | 几何可达、预算内返回、Host 是否找到分别记录；扩大预算计入资源 |
| 桥 | 默认向下、显式 connected、stitch/unstitch | 有向、可撤销，同格其他表达影响如实可见；桥与普通重组的提交范围分别测试 |
| 固定来源 | 多来源、中文/CRLF、缺失文件、变更字节、错误 commit/行号 | 只把实际可验证窗口称为固定原文；错误引用在现有边界报错 |
| 来源更新 | 在来源副本加入真实新版本，再维护判断 | 旧依据保持可读；current 绑定不被当作“最新事实已核对”；受影响新旧读法验证 |
| 便携与重开 | 新目录构建，移走原工作目录，从不同 cwd 调用 | runtime/field/source 各自有效；来源物化范围准确；重开后当前与历史一致 |
| 普通失败及未知提交 | 在实际写入边界模拟已有故障模型 | pre_commit、已回滚、未知、已提交但回读不可用分别处理；重开核对后再决定重试 |

“只读”一行检验的是完成恢复后的实际工作流。现 `--read-only` 参数仅关闭写准备/压力，不等于通用文件系统只读模式。无需为本轮发明新的读权限模型。

### 5.2 三层维护证据

每次维护至少分清以下实际结果：持久提交结果；显式结构路径和终点正文；原根入口按同一预算重走的结果。需要评价可发现性时，再由未见坐标/答案的 Host 选择路径。

旧有 `readback_scope=changed_current_and_explicit_paths` 按其实际范围使用。未声明旧入口仍可能失去可发现性。对确实需要保留的读法，把它们列为该次维护输入，而不是扫描全场后以 orphan=0 代替。

已修复的 unknown-commit Evidence 清理、旧页选择和 downward NEW 见证作为回归复用。触及桥持久化时补对应中断/重开用例；不把普通重组测试扩称桥的复合事务。当前所有权未提供跨进程写隔离；只有实际 Host 需要此能力时，才扩展其合同与测试。

## 6. I：收敛共享相遇能力，验证真实 Host 链路

### 6.1 明确要统一的行为

用同一场副本、配置、来源和预先明确的 Host 决定序列，经 CLI 与 provider adapter 调用，比较其核心结果。允许展示格式不同；应一致的是：

- 真实 surface_layers 和 physical_layers、上层完整正文及截断信息；
- 一个 root、相邻 focus/path 和真实候选；Surface 累计调用预算、每次 locality 的 RecallBudget 与整个交互成本分别记录；
- read-first、显式写准备/压力、NONE/defer 和预算调整后的继续；
- 几何 handle 对应当前正文、版本与固定来源；
- 写入动作、条件提交状态、重开恢复与回读；
- adapter 声明的每个可调用动作都存在真实执行路径。

首先为 A1 的现有差异建立失败或差分用例。公共 orchestration 放在适当 Access 服务，生产 adapter 调公开接口，Lab CLI 作为消费者；Core 继续只处理几何和确定性状态。可按消费者需要渐进抽取，不要求为抽象统一改写所有历史实现。

### 6.2 离线集成与实际运行分层

现 provider npm test 只运行 `tests/v314-*.test.mjs`。先在独立工作目录运行真实 JS→Python→Access→Core 链路，用真实多层小场验证协议、UTF-8、空结果、预算、分页、来源和持久化重开。已有模拟测试继续保留，各自标明证据层次。

自动 Capture/Formation 的迁移作为独立工作项：接入后观察真实可见轮次原文、可恢复暂缓、模型作出的形成/放置、重复 hook 的实际行为和后续查询。Capture 成功、形成成功、Admission 成功、可召回分别记录。可见轮次采集 hook 的前台只等待本地 Capture；后台 Formation/Admission 不阻塞该 hook。查询本身仍按需要执行前台几何工具调用。已有更正确认与来源规则按当前适用合同复用。

Windows/PowerShell 是项目的目标环境之一；记录实际版本并在该环境测试路径、中文、启动/终止和便携重开。真实 Host 测试使用用户已有授权的测试实例或隔离配置，不修改全局知识的普通入口。没有相应环境时记录具体 NOT_RUN，继续可执行的离线工作。

干净安装、更新、卸载、packaged runtime 与实际 OpenClaw 兼容性按其真实交付范围验证。旧 Live 报告保留历史日期；当前 npm 单测、Linux 进程测试和旧 Windows 结果分别报告。

## 7. Q：真实内容、同内容比较与独立新题

### 7.1 已知回归与缺口归因

原 23 题与既有公开题现在是开发回归。保留原答案和 rubric，候选结果另存；不修改历史分数。候选失败发生后，用可核对的事实表定位：

| 原文事实 | 已形成？ | 对所选入口结构可达？ | 实际预算内返回？ | 原文窗口读到？ | 回答准确表达？ |
|---|---|---|---|---|---|
| 固定来源与必要条件 | yes/no/unknown | yes/no/unknown | 由实际调用判断 | 精确窗口 | covered/partial/omitted/contradicted |

该表是答卷冻结后的诊断材料。仅有一次 source 调用不能证明读到了目标事实；未取回也不能直接推出未形成。已读未答优先修正 Host 的任务相关完整性，未形成则补足源事实理解，实际入口/预算问题再调整场或工具。

新评分在出题时区分必需事实、补充事实、合理未知和不应断言项。允许来自等价且实际读过的证据，不按答案长短奖励。旧题仍保留原口径。

### 7.2 两层公平比较

**第一层：冻结内容，比较组织和读取。**

| 臂 | 可用内容 | 实际读取方式 |
|---|---|---|
| S / Source | 同一固定原文范围 | 正常目录/源码搜索和精确窗口；全部读量与重试计入 |
| F / Flat | 与 N 完全相同的当前判断文字、版本、来源 | 明确声明的平面列表/字面读取，不附加 N 所没有的解释 |
| N / Native | 同样判断和来源，原生几何布局 | 实际 stored Surface，Host 选择入口，几何展开，按遇到的引用回源 |

F/N 控制正文与来源一致，S 控制底层原文一致。此层检验组织/导航价值。辅助 find、词项或来源路由若要比较，列为明确额外比较臂，不混入 N 的成绩。原生读者可如实结束不足；后续源码搜索单列为辅助补救。

**第二层：从相同来源增量出发，比较形成—维护—使用。**

让各方案真实吸收、提炼、修订并完成后续工作，计入形成、放置、更新、失败恢复和重复使用成本。此层允许产生不同记忆正文，正文差异是实验结果的一部分。不要把它写成纯几何效果。

旧场没有完整历史形成成本时，只报告固定内容读取与今后实际增量成本；不补造历史耗时。随真实任务序列分别列累计形成/维护费用和每次读取费用，观察何时产生收益。

### 7.3 新独立题的执行条件

候选代码、场和形成记录冻结后，由未参与该形成过程的出题上下文从固定来源产生新任务及来源支持的判据；读者只见任务，不见答案/rubric或已知坐标。覆盖实际使用的名称定位、条件迁移、多来源综合、版本冲突、未覆盖问题和“历史可知、现况未知”的情形。题量按覆盖和实际资源确定，不设人为配额。

成对比较使用相同任务、实际模型版本和可用工具预算；各臂使用独立上下文，避免前一臂答案泄露给后一臂。新会话任务与连续工作序列分别报告，不能把每题新游标称为模型上下文独立。只有真实使用了不同模型才称跨模型；本地只提供一个模型时先完成同模型独立上下文试验。

答案冻结后，由未参与本轮形成及作答的上下文依据原文评分，具体争议再复核。新题一旦用于调整场、提示或代码，就转为开发集；下一轮泛化声明使用新的独立材料。无需为此建立新的后台平台或审计链。

### 7.4 度量与结论

报告任务完整/部分/合理未知/无依据结果，以及事实 covered/partial/omitted/contradicted 的原始数量和分母。事实遗漏、来源错误、条件反转与无依据现况断言分别描述；不把 partial 任意折半成准确率。

每项回答关联实际展示的判断与实际来源窗口，同时保留失败、重启、预算耗尽、辅助搜索及重复调用。模型 token/费用使用可取得的真实 usage/回执；字符和 UTF-8 字节按原单位报告。CLI 子进程时间、编排时间、模型等待和用户端到端时间分别计量。

成对结果按任务/独立上下文报告。观察量不足以支持百分位或统计推断时，展示原始观测及离散程度，不把三组连续读者当成 23 个独立样本。新增无依据断言、错源或关键条件反转需要定位处理，不能被平均成本下降抵消。

## 8. P：真实成本与增长测试

### 8.1 分开扩大的轴

- 上层占用固定、远处下层分区增长；上层 Surface 自身增长。
- 同一物理页变密/变大，以及不同物理页变多。
- 当前判断与历史版本分别增长；已知 handle、仅 ID、历史 continuation 分别调用。
- 桥数量增长；默认下行和 connected 分开。
- source manifest 记录数与选中文件长度分别增长。
- 一次读取、连续下降、回选旧页、写准备、压力、普通写入、重组、source、重开和显式条件写分别测量。

规模由实际负载和瓶颈信息决定，逐步扩大到可解释的资源边界。合成场只证明工程性质，不能替代语义形成质量。场的位置和增长输入按明确几何生成规则构造；预知坐标的脚本只测可达性。

### 8.2 计量方法

复用 `probe_local_storage_cost.py`，按需要增加最小测量维度或薄执行器。它原本计 Python 文件 API payload bytes，不是物理磁盘流量或端到端性能测试。新增测量应注明是否包含目录/stat、序列化、进程启动、Core 初始化、manifest、正文、source、模型等待和形成成本。

新 CLI 进程、同运行时暖缓存、OS 文件页缓存、LLM 上下文/服务商缓存是不同条件。记录可实际控制的部分；不把新 Python 进程等同于磁盘冷启动，不为实验清除共享系统缓存。现有产品形态若每次开 CLI，先测其真实成本；持久进程仅作为有明确消费者的候选另测。

保留基线与候选相同数据、顺序或明确的配对顺序、预算、缓存条件。性能重跑以分离噪声和实际成本为目的，不预设加速百分比或百万规模“通过”。

### 8.3 优化选择

优先处理已观测到的热点，例如已观察 handle 却重新 exact-ID 盘点、重复初始化、重复 source manifest 解析、旧 atlas 全量状态导出、同页更新放大。使用现有 public port 和恰当的函数边界；条件提交或回源身份校验有具体语义时保留。

缓存应可丢弃且失效后结果一致；按物理坐标分页和传递已知 handle 不承担语义关系选择。需要改变预算或输出量的候选在质量/成本表里一起比较，不能只报告命中增加。没有实际收益的候选保留其诊断结果，继续采用有效基线或选择更有价值的方向。

## 9. G：局部 p8/96 的生产候选

### 9.1 复用现有成果

局部 p8 的单位、规范锚与完整地址分离已有实现；旧表示换锚见证、固定输入、独立 Fraction oracle、标签/份额/压力报告是回归资产。当前 pure-affine local-p8 仍使用精确整数求值，不能据 p8 名字假设默认 Core 已降精度。

`reference/auto/adaptive` 在同一声明有理几何内检查采样标签与份额保持；`local_quantized` 检查其自身舍入合同、单位/表示不变性及允许的关系变化。共同变换与真实相对几何变化分开。

### 9.2 同 profile 候选的必要定义

若实现 Core 低精度候选，明确：

1. 默认 22.5°/四次根尺度的物理 profile 与 96 点采样保持；使用同一几何输入。
2. p8 作用的量、单位、锚、舍入和边界 tie 被明确写出；完整整数地址及系数乘大地址不先截成 8 位。
3. 邻接物理层语义、Q16 总和、全命中、存储/可写域继续可核对。
4. 变更输出使用可区分的合同/registry/state 语义；已存场通过显式复制或迁移试验打开，不靠更改默认数字隐式改写关系。

### 9.3 三种对照

| 对照 | 回答的问题 |
|---|---|
| 独立候选算术实现 | 单位/锚/舍入/大地址是否按候选声明执行 |
| 现用 Q40 的同一采样 | 改精度引起哪些标签、目标、份额、压力和候选选择变化 |
| 独立物理 Oracle | 连续物理重叠中的 missed/false mass、TV、主导目标、空间局部性与质量误差 |

按当前第一性原理和 ACTIVE_APPROXIMATION_POLICY 使用加权误差。对标签等价的优化要求样本结果保持；对用户允许关系变化的量化候选按明确误差和工作效果评价，不强制所有非零真实边逐一命中。独立 Oracle 不与候选共用核心分类/归一化逻辑自证。

默认 Core 的测试覆盖正负地址、边界 tie、当前存储域内大地址、写域边界、上下方向及不同物理层的旋转相位。这里的旋转相位不同于 GeometryAddress.phase；当前默认核的地址 phase 仍为 null。共同尺度/平移/表示重锚与真实相对变形，在现有 Lab 合同或候选明确提供的低层表示接口测试，不假定现有 Core 公共 API 已支持可变世界映射或扭转。压力另测缺失材料需求与大整数材料守恒；超出公共 GeometryAddress 域的低层整数探针按低层范围单列。

测完整 native 覆盖/压力/读取操作的冷与复用成本，再判断是否适合接入。复制真实场后比较新旧入口、共享详情、预算内读回、正文/来源/历史和回退到原合同。当前全局入口不随该试验切换。若候选没有净收益，报告具体差异与代价，保留 Q40 为当前实现，不把研究完成写成部署完成。

## 10. 优化与复验的接受方式

每个候选对应一个实际问题或测量热点，提交说明写清基线行为、改动目的、结果及影响。修复先重放原失败，再验证相关读写/维护回路；采样不变的优化还要核对缓存清空后的输出。

候选进入最终交付需满足其适用条件：

- Evidence、版本、来源、单入口和实际预算语义保持；需要改变的行为明确记入合同和测试。
- 重要旧读法及新增路径在实际复制场返回；提交失败/未知状态能按声明恢复。
- 新 API 在实际消费者上能调用，产品模块依赖符合边界。
- 正确性/质量或成本有观察支持；质量损失与资源节省同时呈现，不能隐藏。
- 几何变更通过同合同与独立 Oracle 的适用校准，真实场影响有据可查。
- 新题在冻结候选后执行；所有未执行域准确标记。

完整校准只用于涉及它的数值改变；完整 Host Live 只用于对应交付主张。没有必要把无关历史 Gate、所有模型、所有 OS 或无限地址闭包作为当前局部改进前置条件。

## 11. 已有可执行命令与环境前提

以下命令均从 Nollm 仓库根运行。`python` 指本地实际选定的 Python 3.11+ 解释器；POSIX 若使用 `python3` 可等价替换。脚本通过 sys.executable 启动子进程时继续使用该解释器。运行前确认现有环境，缺少依赖才在选定虚拟环境安装：

```text
python -m pip install pytest -e packages/nollm-core -e packages/nollm-access -e packages/nollm-snapshot
```

这不是全仓依赖安装命令。需要运行特定历史验证器时，再读取其实际依赖；requirements-validation.txt 仅声明 zstandard。PowerShell 中原生命令后立即核对 `$LASTEXITCODE`；`$ErrorActionPreference` 不替代该检查。跨平台运行不要把 Bash 的 PYTHONPATH 分隔符直接复制到 Windows。

### 11.1 核心读取、写入和恢复

```text
python lab/nollm-lab/repository_memory/run_stored_surface_tests.py
python lab/nollm-lab/repository_memory/test_portable_deployment.py

python -m pytest -q packages/nollm-core/tests/test_core_commands.py packages/nollm-core/tests/test_core_recall.py packages/nollm-core/tests/test_paged_state.py packages/nollm-core/tests/test_core_workspace_single_owner_lifecycle.py

python -m pytest -q packages/nollm-access/tests/test_access_runtime.py packages/nollm-access/tests/test_access_exception_atomicity.py packages/nollm-access/tests/test_reorganization.py packages/nollm-access/tests/test_paged_handle_store.py packages/nollm-access/tests/test_content_budget.py packages/nollm-access/tests/test_workspace_coordinator_single_state_owner.py

python -m pytest -q packages/nollm-snapshot/tests
```

Lab 附加测试需要两个 Lab import roots。下面一行使用解释器内的路径设置，可在 PowerShell 或 POSIX shell 调用；与上述已有包安装配合：

```text
python -c "import sys,pytest; sys.path[:0]=['lab/nollm-lab','lab/nollm-lab/repository_memory']; raise SystemExit(pytest.main(sys.argv[1:]))" -q lab/nollm-lab/repository_memory/test_encounter_page_history.py lab/nollm-lab/repository_memory/test_encounter_local_cost.py lab/nollm-lab/repository_memory/test_local_reorganization_review.py lab/nollm-lab/repository_memory/test_project_storage_and_placement.py lab/nollm-lab/repository_memory/test_skill_install.py lab/nollm-lab/repository_memory/test_coverage_install.py
```

以上是按风险可选的测试组，不要求每次小修改重复运行其并集。Snapshot 模块测试证明 Core state 的范围；完整工作场包含 Access 正文/绑定/配置，需要便携与重组用例补充。

### 11.2 几何与成本

将下列 `OUTPUT_*.json` 替换为新建本地结果路径，保留原固定结果。参数字面量不是验收指标：

```text
python lab/nollm-lab/geometry/run_support_deformation_tests.py
python -m pytest -q packages/nollm-core/tests/test_residual_mask_coverage.py
python lab/nollm-lab/geometry/run_broad_residue_coverage_calibration.py --output OUTPUT_Q40.json
python lab/nollm-lab/geometry/benchmark_local_p8.py --input lab/nollm-lab/geometry/results/quantized_structure_benchmark_20261123.json --output OUTPUT_P8.json
python lab/nollm-lab/repository_memory/probe_local_storage_cost.py --output OUTPUT_STORAGE.json
```

`benchmark_local_p8.py` 的原默认重复数及暖进程计时沿其脚本说明解释；不当作冷 CLI。`probe_local_storage_cost.py` 支持 `--remote-count`、`--body-bytes`，其 byte 参数至少 128、count 为正，这是现脚本输入合同。参数选择反映待测负载。

`run_broad_residue_coverage_calibration.py` 按活动 policy 执行既有校准。减小固定抽样参数仅能作为诊断，不能绕过完整校准条件。旧 `run_core_translation_covariant_validation.py` 不在当前默认列表。

### 11.3 provider 入口

活动 provider package 声明 Node >=22.19.0；Formation Loop package 声明 Node >=24。使用本地实际支持环境，避免把一个包的 engine 条件当全部项目条件。现有 provider 的 .js build/test 可从根执行：

```text
npm --prefix integrations/openclaw/nollm-memory-provider test
```

只有修改或接入 Formation Loop 时，再在其锁文件/实际依赖环境下执行：

```text
npm --prefix integrations/openclaw/formation-loop test
```

包测试仍需搭配本轮新增的真实 bridge 和多层场用例。检查实际本地 OpenClaw 版本再选择既有 plugin check/安装流程；不直接运行历史 companion 安装脚本去接管普通实例。必要的安装/升级试验使用隔离测试配置并记录结果。

### 11.4 本轮明确需要补充的执行能力

现有仓库未提供等同于本计划的一键全链路 runner。以下属于本地实施工作，不是已存在的可执行命令：

| 待补能力 | 建议落点与最小职责 |
|---|---|
| CLI/provider 多层合同差分及真实 bridge | 对应 Access/adapter 测试：同一输入决定序列，经真实消费者核对行为 |
| 当前场的完整 root 回放与维护 | repository_memory 现有测试/小 harness：使用实际观察候选，输出新旧路径结果 |
| 私有 S/F/N 与独立题执行记录 | 复用现有 commands.jsonl/answers/评分结构，调用真实工具，记失败/输出/耗时；语义评分由实际读者/评审完成 |
| 多维增长与冷 CLI 成本 | 扩展现有 probe 或小脚本，分开计量 metadata/body/source/startup，不新增监控平台 |
| 默认 Core profile 的 p8 候选 | Lab 中显式候选、独立 Oracle 测试及完整操作比较，达标后再设计受控集成/迁移 |

实际文件名由执行者决定。新增薄脚本只做执行和计量；不会按题号、关键词或预知坐标生成“原生语义命中”。

## 12. 回传到本 PR 的内容

在同一个 PR 保持一个清楚的继续入口，提交候选代码与必要测试，更新简洁执行报告：

- 实际 baseline/candidate commit、场和来源版本、环境及真实模型身份。
- 发现的问题、改动及必要行为差异；原失败与修复结果分别保存。
- 按 B/F/I/Q/P/G 列出 PASS、FAIL、NOT_RUN 或具体部分完成范围；不以空测试或模拟调用记作完成。
- 同输入前后质量与成本；已知回归与新独立题分别报告。
- 私有原始记录的稳定引用、源窗口/版本核对以及新旧入口读回结果。
- 当前有证据的收益、代价、剩余问题和直接可执行的下一步。

完整日志默认留实际本地结果目录；需要持久接续的私有数据继续存既有私有实验位置，工程 PR 保留汇总与固定引用。保留失败记录，不用候选重跑覆盖原始答卷。

源码、解释和字段行为有变化后，通过正常原生相遇修订受影响的速记本判断，引用实际提交并读回；维护自身也列出当前与历史结果。全局知识的普通方案、入口与既有冻结试验维持原状。

完成标准是形成可运行的候选和对其目标有实际证据的结论。没有收益、仍有集成缺口或缺少某个目标环境时直接记录对应状态；不以“计划写完”“PR 已开”或“测试总数增加”代替本地执行结果。

