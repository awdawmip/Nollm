# 用外部记忆继续进取数论研究

这是给真实模型使用的 TASK／知情综合研究入口。当前记忆涉及六格 CRT 前缀、X6 二次探测、有限生成模的枚举条件和素操作未来树。可以直接问「给定读头需要保留哪些联合信息？」「什么条件下能借用另一条线的编码或枚举证明？」。由拿到任务的模型操作下面的 CLI、选择证据和作答。[已保存的原生场](field/) · [实际使用与成本](TRIAL.md)

## 在一个新会话打开

在这个 PR 的 Nollm 工作树根目录运行。Python 3.11+ 可直接加载仓库内的 Core 和 Access。查看记忆无需 EM 全库或重建场。回源需要 Git 能读取 EM 的固定提交，本次是 `f16294a5a7ffa435a32b70214d881fd4450eb494`。

```sh
D=lab/nollm-lab/repository_memory
cli="$D/skills/nollm-repository-memory/scripts/memory.py"
em() { python3 "$cli" em "$@"; }
EM=../enterprise-math
em walk
```

如果本机还没有 EM 工作副本，可执行以下两行。已有副本只需让 `EM` 指向它。部分克隆会在首次需要时获取相应的 Git 对象。

```sh
git clone --filter=blob:none --no-checkout https://github.com/awdawmip/enterprise-math.git "$EM"
git -C "$EM" fetch origin f16294a5a7ffa435a32b70214d881fd4450eb494
```

**开放问题。** 阅读 `walk` 返回的本页语句首行，根据问题选择窗口。把显示的候选 ID 依次追加到同一命令。需要翻页时追加 `next`。下例中的变量取自实际页；回退时去掉最后一个选择。

```sh
em walk "$window"
em walk "$window" "$physical"
```

上例从零阶窗口出发。若选择 `--order 1`，先选一阶窗口，再选零阶窗口，最后选其物理候选。每次保持同一 `--order`、`--page-size`。菜单中的 `surface:…` 和 `physical-entry:…` 供 `walk` 选择；`show` 和 `source --id` 接受召回条目的语句版本 ID。最终结果有一个 `entry=[layer,q,r]`，以及各命中的版本 ID、完整判断、坐标、实际核路径 `via`。空路径表示入口自身。默认一步、最多五条；可调 `--steps`、`--limit`。默认允许同层邻接及上下层 Coverage；`--via vertical --steps 2` 单独观察跨层往返。加深后仍遗漏所需材料时，按来源引用展开或返回 Surface 另选入口。解释数学联系时应核对两端对象、前提与证据。

长路径可把当页保存在 Host 的临时文件里。无选择的调用开始新走读，以后只传本页的一个选择。文件包含可重开的 Access 状态，选择最终物理入口后清除。同一组显式参数和选择在历史重放与续页下得到相同候选和召回。需要分叉时可在选择前复制当页文件。

```sh
page=$(mktemp)
em walk --cursor-file "$page"
em walk --cursor-file "$page" next       # 当前页有 has_more 时
em walk --cursor-file "$page" "$window"
em walk --cursor-file "$page" "$physical"
```

首屏的 `start` 给出实际起始阶、根格数、预计根页数、软目标和 Access 活动面是否溢出；`pages_left` 是 24 页硬预算的余量。零余量时仍可选择已经展示的物理候选。默认先试页宽 3。全阶都超出窄菜单软目标时，在 3 至 8 中取首个预计可容纳「扫完根菜单 + 每次下钻一页 + 物理菜单」的宽度，选该宽度估计页数最少的阶，同值取浅阶。如果各宽度都不够则使用宽 8 下的最低估计。子菜单也可能翻页，预算不能保证覆盖所有目标。`--order` 固定起始阶，`--page-size 3` 复现过去的显式窄页策略；选择 ID 与生成它的页关联。

在独立可写场，Host 可以把两条当前理解所在的格子单向连接，再按实际证据撤销。在既有场的副本中可以这样试用：

```sh
em --field "$field" stitch crt-probe-lead CRT.repair X6-QUADRATIC-MODULAR.v2
em --field "$field" walk --cursor-file "$page" --via connected
# 从菜单选择入口；在最后物理选择时也传 --via connected
em --field "$field" walk --cursor-file "$page" --via connected "$physical"
em --field "$field" unstitch crt-probe-lead
```

`connected` 在通常的局部核之外允许一次定向 bridge 跳转。连接附着于物理格，命中可能包含该格的其他理解。普通 `local` 只考虑原有邻域。研究者需在两端原文上检验可迁移的操作与前提。

**已知标识、式子或出处。** `find` 是对当前判断的 ID 和正文做不分大小写的连续字面匹配。它独立于原生导航。引用按 `show` 返回的顺序从 1 编号。

```sh
em find 'K(m)'
em show X6-QUADRATIC-MODULAR.v2
em source --id X6-QUADRATIC-MODULAR.v2 --number 1 --repo "$EM"
em show X6-QUADRATIC-MODULAR.oct
```

旧版会显示 `current: false`，仍可展开当时的来源。新版的 `revises` 指回旧版。每个引用指向核阅时的 EM 提交、真实路径及闭区间行号。`source` 读取该 Git blob，只把引用的原文行送给模型；改变工作树 HEAD 不会改变旧引用。

## 形成与局部更正

模型先读问题所需的成果卡、原稿或复核，在第一行写可导航的提要，随后用自然语言和公式写下判断、作用域及未满足的前提。直接处理一段新材料可用 `em source --repo "$EM" --at '路径#L起行-L末行' --rev 提交`。判断适用性、选择物理位置与判断是否需要更正由 Host 完成。相同内容可继续使用原判断。有限计算、模型推论和未决路线均可按各自证据写入。

下面用一个**新的工作场**重放从历史成果卡到后续论文的局部更正。研究者只需提供正常研究材料，调用方模型负责写语句和引用。

```sh
field=../em-research-notes/x6-field
rev=f16294a5a7ffa435a32b70214d881fd4450eb494
em --field "$field" save x6.opt.oct --at 0 0 --repo "$EM" --rev "$rev" \
  --cite 'docs/research_library/202610_month/native_brc.md#L65-L80' <<'NOTE'
X6 平移未来等价类的固定探测次数
十月卡给出七次上界和奇模 m>1 的最优性；偶模最少次数在此卡中待解。
NOTE
em --field "$field" walk
em --field "$field" save x6.opt.updated --revise x6.opt.oct --repo "$EM" --rev "$rev" \
  --cite 'research_notes/balanced_resume_20261028/native/QUADRATIC_EVEN_PROBES.md#L7-L35' \
  --cite 'research_notes/balanced_resume_20261028/review/NATIVE_REVIEW.md#L5-L14' <<'NOTE'
X6 增补给出全部模数的最优探测次数
同一有符号整数六维状态、固定非自适应精确二次读数、全部单位平移未来下，
K(1)=0，K(2)=1，K(4)=6，其余 m≥1 皆为 7。非作者复核范围限于这个探测模型。
NOTE
em --field "$field" show x6.opt.updated
```

**实际持久位置。** 默认场在本目录的 `field/`。`core/current_state.json` 保存物理占用，`access/bindings.json` 记录当前绑定，`access/statements/` 保存语句版本与来源。复制整个目录并传 `em --field /path/to/copy ...` 就能续写本次已有理解；要在团队中交接，把修改后的同一场提交到工作分支。skill 安装器也把这份记忆带到 `scripts/runtime/enterprise_math/field/`。安装副本与工作树各自持久。实验按单写者使用。

Core 的活动写入层为 0；不同语义粒度的判断可以同处这一层。聚合阶数控制 Surface 的观察尺度。覆盖、邻接和预览帮助模型找到判断；定理证明和接纳状态沿 EM 原文。这个适配器只保存 Host 理解与 Git 窗口，不定期抓取或重排全库。FREE A 接入时需沿 EM 当时的来源规则选择可用视图。

## 供已有服务调用

已安装 skill 的 `scripts/runtime/` 可以作为 Python 模块路径，一次加载 `enterprise_math.research` 后直接调用。场目录由宿主显式传入，放在独立持久目录；更新运行时代码时继续使用原工作场。

- `save_statement(field, note_id, body, sources, at, revise)` 接收 Host 已经选定的固定来源引用，例如 `提交:路径#L起行-L末行`。`sources` 的顺序就是后续回源顺序；新增使用 `at=(q,r)`，原位更正使用 `revise=当前版本ID`。返回版本 ID、物理坐标和修订目标。
- `describe(field, note_id)` 返回正文、来源、`current` 和适用的 `revises`。`current` 指该工作场的当前绑定，不判断来源库是否有更新。
- `walk` 与 `literal_matches` 复用同一场；词法查询单列辅助路径，Surface 导航仍由 Host 逐页选择一个最终物理入口。
- `excerpt(repo, reference)` 保留本地 Git 回源；已有服务也可用自己的精确来源读取接口展开同样的引用。原 CLI 的 `save --repo --rev --cite` 继续把 Git 引用解析后调用 `save_statement`。

服务无需为了保存理解另建一份 Git 工作树；出处由现有来源读取链提供。所有访问同一场的操作由同一个实际访问点串行处理，沿本实验单写者方式使用。新建空场可显式打开并关闭一次 `CoreRuntime(field)`；也可在初次部署时复制已有场，后续启动直接打开原目录。`walk`、`show` 和 `find` 对已经存在的场不改写持久状态。

## 针对性回归

从 Nollm 根目录执行。科研回归通过已安装的 CLI 对比更正前后的证据窗口、当前绑定、相邻召回与远格排除。安装回归覆盖既有 skill 入口。新增直接 API 回归覆盖无需 Git 工作树的保存、固定来源顺序、原位修订与独立进程读取；既有安装回归继续按实际受影响范围使用。

```sh
D=lab/nollm-lab/repository_memory
python3 -m unittest discover -s "$D" -p 'test_enterprise_math*.py'
python3 -m unittest discover -s "$D" -p test_skill_install.py
```
