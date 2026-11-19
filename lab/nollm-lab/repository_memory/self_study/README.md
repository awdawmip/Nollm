# 从 Nollm 源码理解旋转蜂巢的上下覆盖

这项 Lab 研究在 Nollm 提交 `691590dcc6009b59a9cf51dfe7a9e7a7516eca0b` 上用官方 AOCI-CODE 整理工程说明，再用原生 Core 写入、重开、遍历，用 Access 取回说明和 Git 证据。907 个跟踪文件有去向，903 个形成正式条目。两个空文件和两份超过工具大小上限的治理清单有跳过记录。Core、Access 共 44 个 Python 源文件逐份整理了职责，其余许多条目从声明、导入、测试名和文档标题提取。源码目录和包导入路径沿用固定提交的组织。[AOCI 卷与复开方法](aoci/README.md)

全仓场已将 903 个正式对象各写入一次，分布在 520 个第 0 层物理格。重开后从 125 个上层入口逐个进行单入口查询，959 条返回逐项核对正文、Git 引用、物理地址和方向权重，覆盖全部 903 个对象。44 个运行时代码文件保留职责重叠；其余 859 个按项目区域和既有路径分为 118 页，每页实际读回 1–8 个对象。页目录保存入口坐标；入口实际返回什么由物理核和占用决定。跨职责定位准确率的对照仅在前述 44 份源码上进行。[全仓场构建与回读](full_field.py)

## 两种上下关系分别用在哪里

**从一个物理格发现相关证据。** 默认剖面中，层号增大时格子变细，相邻网格相对旋转 22.5°，粗细边长比为 2 的四次方根。生产核将出发格分成 96 个等面积微三角，采样并映射到相邻层，将命中数换算成总和 65,536 的 Q16 权重。粗格向下能到多个细格，一个细格也能被不同粗格触及。反向遍历会在新的出发格重新采样。Core 扩展有界前沿，按路径连乘权重，对同一格保留最佳路径，并按预算截取。Access 从唯一的物理入口接收命中的句柄，解析绑定并校验正文。[旋转剖面](../../../../packages/nollm-core/src/nollm_core/profiles.py#L61) · [定向核](../../../../packages/nollm-core/src/nollm_core/approximate_coverage.py#L65) · [前沿与排序](../../../../packages/nollm-core/src/nollm_core/recall.py#L74) · [单入口](../../../../packages/nollm-access/src/nollm_access/recall.py#L28) · [正文解析](../../../../packages/nollm-access/src/nollm_access/runtime.py#L224)

**从一个观察窗口枚举已有成员。** Surface 把范围内的物理占用投影到参考层，再逐阶按上投影建立观察窗口。窗口保存实际贡献的下一级成员、权重和来源。宿主可以分页打开这些成员，到零阶后选择一个展示过的物理入口；多个窗口可以通向同一份源码。物理层号描述记忆写在哪里，聚合阶数描述如何观察这些写入。现行语义写入策略在第 0 层放置记忆，高层入口可以是空物理格。窗口中的多份预览也不能算作一次多入口物理召回。[Surface 建立](../../../../packages/nollm-core/src/nollm_core/surface.py#L210) · [成员下钻](../../../../packages/nollm-core/src/nollm_core/surface.py#L322) · [Access 导航](../../../../packages/nollm-access/src/nollm_access/surface_navigation.py) · [写入策略](../../../../packages/nollm-access/src/nollm_access/write_policy.py#L28)

一个能区分两者的回归例子：在独立的 Core 测试场把一条带有 Git 来源的判断写在 `L3(2,2)`，重开后观察阶 1 的窗口 `(0,2)` 可以沿成员权重 683 找回它。从对应的物理格 `L2(0,2)` 向下采样却返回零条。独立 Lab 面积计算把这个方向的理想重叠约束在出发格的 0.6290% 到 0.6291% 之间。需要完整枚举该窗口已登记的成员时，应使用 Surface 的记录。两个方向各扫描 441 个出发格时，1,993 条下行边有 14 条在反向采样中缺失，1,407 条上行边有 6 条在反向采样中缺失。[方向探针](directional_probe.py) · [独立面积方法](../../../../docs/architecture/CERTIFIED_OVERLAP.md)

## 怎样用空间承载代码关系

宿主先根据源码指定每个文件的一项主要职责和可能共享的职责。几何实验固定七个第 −1 层入口，在它们的实际下行足迹中给每个文件挑一个第 0 层位置。AOCI 的 F/R/A/S 原文和 Git 引用绑定到一个 Statement。实验用 44 次放置，写入零条 Bridge。物理召回获得句柄之后才用 Git 引用回源。同一组作者判断也用于事后计分；改变某个格的坐标会改变返回结果，无须写一条入口到文件的有向边。[放置与原生回读](vertical_atlas.py)

例如，`physical_coverage.py` 放在 `L0(1,0)`。从几何入口和 Surface 入口向下各走一步，分别以 27,989 和 15,019 的权重取回同一个原生句柄。反过来从这个细格出发，两个上行权重是 38,229 和 19,797。状态入口也能以 2,730 的权重向下命中它。作者为这个文件指定了几何和 Surface 两项职责，因而第三个命中计为额外关系。

| 固定 44 份源码、86 项预期职责归属 | 正确命中 | 额外命中 | 漏掉 | 归属精确率 | 归属召回率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 一个文件只给一个主要入口 | 44 | 0 | 42 | 100% | 51.2% |
| 初始多覆盖布局 | 73 | 27 | 13 | 73.0% | 84.9% |
| 调整入口位置后的多覆盖布局 | 74 | 22 | 12 | 77.1% | 86.0% |

调整布局只用先前写下的职责意图。遍历相同七个坐标的 5,040 种职责排列，以漏项加额外项最少为目标，用主要入口的权重及固定顺序打破平局。精确率的分母为全部命中的“入口、文件”对，召回率的分母为 86 个宿主预期对。这是对放置意图的拟合；独立工程问题另行测量。[布局拟合](fit_layout.py)

在初始场的同一个已占用格 `L0(0,1)`，限定两步、beam 64、返回 10 条。两组首先都拿到本格的 `cartography.py`。允许上下遍历时，接下来是 `locality.py`、`surface_navigation.py`、`surface_selection.py`，三条胜出路径都是先上后下。只允许同层遍历时，接下来是 Access 的包入口、`field_encounter.py` 和 `memory_loop.py`。

同一场从观察阶 0 到 2 分别出现 12、18、19 个非空窗口，每阶总质量都是 2,883,584，恰为 44 × 65,536。12 个零阶位置中有 11 个可从多个一阶窗口打开。这个稀疏布局提高观察阶时，边界重叠让窗口数量上升。页大小限制对宿主展示的候选量，生成预览还涉及内部来源读取。[观察面实验](surface_walk.py)

## 工程问题和实际试改

八道工程题及 14 个必需源码证据在评估者见到 AOCI 条目、入口名称和布局前冻结。每题最多打开三个源码文件。源码搜索组按全文 BM25 排序；平面 AOCI 按同一批 44 条说明排序；空间组先由固定英文词法规则选一个入口，在实际向下命中的条目中用同一说明评分器排序。混合组取一个局部命中，然后用全局 AOCI 顺序补齐。这是宿主策略对照。[冻结题目](tasks.json) · [评估器](evaluate.py)

| 打开三份源码 | 找齐证据的题 | 命中 / 打开 | 命中 / 需要 | 八次独立源码包 token |
| --- | ---: | ---: | ---: | ---: |
| 直接搜索源码 | 5/8 | 10/24 | 10/14 | 133,400 |
| 平面 AOCI | 6/8 | 10/24 | 10/14 | 54,794 |
| 单归属，入口内重排 | 3/8 | 8/24 | 8/14 | 79,319 |
| 初始上下覆盖，入口内重排 | 3/8 | 8/24 | 8/14 | 68,821 |
| 调整后的上下覆盖，入口内重排 | 3/8 | 8/24 | 8/14 | 73,808 |
| 调整后的一个局部结果，AOCI 补齐 | 6/8 | 10/24 | 10/14 | 50,613 |

调整后的布局让 10 个必需来源能从选中入口触及，单归属只能触及 8 个。多出来的两份是 `kernel_registry.py` 和 Core 的 `recall.py`，分别排到第 10 和第 5；首三份仍未读到。混合方案相对平面少读的 4,181 个 token 全部来自一道仍未找齐证据的题，其中一份无关文件较短。这项差值不能证明有用信息的读取效率提高。源码包用 `o200k_base` 对完整返回文件计数，未包含模型推理或供应商用量。

另在三个独立 Codex 会话完成同一项跨模块修改：让 Core 和 Access 报告 `max_results` 截去了多少个已遇到的不同句柄。三组各自通过 8 项新验收和 244 项既有回归，均读到并引用了 3/3 个必需来源。直接源码搜索、先读 44 条 AOCI 全景、宿主自选单入口 `recall` 后回源，观察到的文本分别为 3,975、8,151、4,771 token。每次起始包、搜索、打开文件、物理召回输出均按原文分词；模型内部推理与计费未提供。这次任务点名了字段和接口，三份试验补丁保存在复算包中。

## 两道失分题的 Surface 定向复测

在看到上述失分后，另开两个互不共享答案的 Codex 会话，分别处理路由分派和单入口预算两题。每个会话只能看到安装版 skill 的 Surface 候选页，由宿主逐阶选到一个物理入口，随后只做一次上下覆盖召回，最多从返回结果选三份源码。路由题浏览了 6 次，选中 `L0(0,1)`，交回的两个文件是 Core 的 `kernel_registry.py`、`recall.py`。单入口题浏览了 8 次，选中 `L0(1,1)`，三个文件包括 Access 和 Core 各自的 `recall.py`，并多选了一份 `surface_navigation.py`。共选中 4/4 个指定证据，5 份返回选择中有一份额外文件。两次独立召回均有单个真实物理入口。这个复测针对已知失败，额外浏览、双向两步、模型读预览和选文件共同发生，不能将提升单独归给几何摆放。

## 复算

从 Nollm 仓库根运行。Python 脚本使用 checkout 中的 Core 和 Access。输出目录由调用方指定。加 `--tokens` 需要安装 `tiktoken` 并能读取 `o200k_base` 词表。

```sh
D=lab/nollm-lab/repository_memory/self_study
OUT=$(mktemp -d)
python "$D/full_field.py" build --repo . --field "$OUT/project"
python "$D/full_field.py" verify --repo . --field "$OUT/project"
python "$D/full_field.py" read --field "$OUT/project" --room openclaw-provider/01
python "$D/directional_probe.py" --certify
python "$D/vertical_atlas.py" build --repo . --field "$OUT/base"
python "$D/vertical_atlas.py" verify --field "$OUT/base"
python "$D/vertical_atlas.py" view --field "$OUT/base" --topic geometry --mode coverage
python "$D/surface_walk.py" --workspace "$OUT/base" --order 2 --page-size 2 --ranks 2 0 0 0 --audit
python "$D/fit_layout.py" --repo . --field "$OUT/fitted"
python "$D/evaluate.py" --repo . --field "$OUT/base" --out "$OUT/base.json"
python "$D/evaluate.py" --repo . --field "$OUT/fitted" --out "$OUT/fitted.json"
```

这组结果支持把上下覆盖用于共享上下文和单入口局部发现。需要完整列举某个窗口时走 Surface；要核实工程判断时回到对应 Git 版本。下一轮应固定布局，在未用于布置和诊断的新任务上，对齐宿主、步数、候选页数与可读 token 后，再比较 Surface 选入口与平面 AOCI。
