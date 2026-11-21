---
name: nollm-repository-memory
description: "用 Nollm 原生场理解和维护本地 Git 项目记忆。适用于仓库接手、跨文件影响分析、持续形成和修订有来源的判断，以及 Enterprise Math 研究记忆。默认从 Surface 观察，经 Host 选择一个物理入口，遇到已有事实或可写位置后完成召回、复用、修订或新放置。Use for native project memory, repository onboarding, evidence-backed change analysis and handoffs."
---

# Nollm 仓库记忆

使用正在加载的本 skill 的 `scripts/memory.py`。需要 Python 3.11+ 和 Git。
普通项目记忆统一走 `project --field FIELD encounter`；进取数论的已有研究场走
`em encounter`。Host 负责理解、选择入口和判断新内容的关系，Core 执行几何与持久化，
Access 返回正文及固定来源。

## 打开持续使用的场

沿用项目已有的场路径，并分别指定对应的源码仓库。场保留已接受的几何位置、占用、
当前绑定和连接；升级或重新安装 skill 后继续打开同一工作场。
以下为 POSIX 示例，使用实际路径。每次独立 shell 调用重新设置变量，或使用绝对路径。

```sh
cli='/absolute/path/to/nollm-repository-memory/scripts/memory.py'
repo='/absolute/path/to/source-repository'
field='/absolute/path/to/project-field'
session='/tmp/nollm-encounter.json'
python3 "$cli" project --field "$field" encounter --cursor-file "$session"
```

首次接手仓库和回答局部问题都从这个入口观察。读取页面预览，根据当前问题选择
**本页显示的**候选 ID，逐次传入同一会话文件。需要续页时选择 `next`。

```sh
python3 "$cli" project --field "$field" encounter "$candidate_id" --cursor-file "$session"
```

聚合页 `kind: surface` 用于观察；`kind: physical` 显示最终物理候选。
选择一个物理入口后得到 `kind: locality`、`entry`、完整 `items` 及可放置的 `cells`。
页面预览可能只是已保存正文的截段；在局部页面阅读完整判断与条件。
根据其中的正文、来源和可用位置作语义决定。运行脚本的助手就是 Host；程序不会
按任务词、文件名、来源重合或固定分数替你选择。

不传新选择会恢复当前页或同一个局部。`--restart` 重新开始一次观察。
会话文件只保留临时导航和入口参数，可丢弃；它不是长期的“问题→位置”路由。
新场从原点种子开始，先选择这个物理候选，再在局部页面选择新位置。

## 在同一次相遇中读取或写入

| 本次判断 | 命令选项 | 结果 |
| --- | --- | --- |
| 已遇到能回答问题的当前事实 | `--recall FACT_ID` | 返回该事实及来源 |
| 新表达支持同一当前判断 | `--reuse FACT_ID --id NEW_ID` | 保存补充表达，复用已有占用 |
| 新判断更正同一事实 | `--revise FACT_ID --id NEW_ID` | 原位设为当前版本，保留旧版本 |
| 新内容是独立判断 | `--new CELL_ID --id NEW_ID` | 在本页可写位置新增占用 |
| 本次查询没有找到事实 | `--none` | 明确结束为空结果 |
| 语义关系或位置尚不确定 | `--defer` | 暂缓写入 |

使用 `items` 的当前 ID 或 `cells` 的位置 ID；所有决定沿用同一个最终物理入口。
写入时正文经 stdin 传入，并提供实际读过的 Git 来源窗口：

```sh
python3 "$cli" project --field "$field" encounter --cursor-file "$session" \
  --new "$cell_id" --id binding.v1 --repo "$repo" --rev HEAD \
  --cite 'src/reader.py#L10-L20' --cite 'tests/test_reader.py#L25-L40' < judgment.txt
```

用实际来源路径、行号和表达版本 ID 替换示例。将 `--new "$cell_id"` 换成
`--reuse "$fact_id"` 或 `--revise "$fact_id"` 即可保存支持表达或修订。
一条表达写清独立可理解的事实、成立条件和影响；关系的成立依据写入正文并引用双方来源。
终结结果为 `kind: result`，`effect` 说明实际动作，会话文件随之删除。

查询没有找到足够判断时，可继续观察、重开入口或显式转向源码核查。报告实际使用的
来源搜索或字面辅助；这些结果不会被当成原生场已经发现的关系。不要将缺失场、空结果
或预算耗尽隐式改走旧检索器。

## 控制本次几何展开

`--steps` 控制传播步数，`--beam` 控制每步保留的物理候选数，`--limit` 控制返回表达数。
`--via local` 使用上下 Coverage 和侧向邻接，`connected` 还使用已有定向桥，
`vertical` 只用上下 Coverage，`lateral` 只用侧向邻接。
按当前问题显式调整，并检查返回的预算状态；在同一局部修改参数会从原入口重新展开。
先观察调整后的局部，再在另一次调用中选择终结动作。
物理层与聚合观察阶是不同参数；跨层传播或距离本身不证明语义关系。

已有 `project/em walk` 保留为只读的逐页观察及单入口召回工具。
它不自动选择任务入口。`save --at Q R|--reuse ID|--revise ID` 保留为已完成
Host 决定时的显式直接写入接口；日常形成和查询优先共用上述 encounter。

## 回源、修订与交接

```sh
python3 "$cli" project --field "$field" show "$statement_id"
python3 "$cli" project --field "$field" source --id "$statement_id" --number 1 --repo "$repo"
```

`show` 展开准确的表达版本、来源和 `current`。`current` 只表示当前绑定，
源码引用中的提交说明形成依据。支持表达保留自己的 ID 与来源，`current: false`；
修订后旧版本仍可精确展开。`source` 返回固定提交的原文行。
形成首条理解时，可用 `source --at PATH#Lfirst-Llast --repo "$repo" --rev COMMIT`
打开指定源码窗口。

代码变化后按 `git diff` 与已保存来源核查受影响的判断，由 Host 决定保留、补充、修订
或调整连接。文件变化本身不触发全场重排。用 `links [ID]` 观察当前连接，
`stitch LINK_ID FROM_ID TO_ID` 建立有依据的定向格级连接，`unstitch LINK_ID` 撤销。
同格其他表达也可能经桥被取回；修订正文后按实际含义判断该连接是否仍有用。

交接提供场路径、源码仓库及引用版本、实际使用的入口和判断、代码变化与测试结果、
未处理的来源变化。保留失败和辅助回源情况，按实际路径归类效果。

## 进取数论已有研究场

```sh
python3 "$cli" em encounter --cursor-file "$session"
python3 "$cli" em show "$statement_id"
python3 "$cli" em source --id "$statement_id" --repo /path/to/enterprise-math
```

`em` 复用同一原生接口，默认场是安装目录的
`scripts/runtime/enterprise_math/field/`，仓库版位于 `enterprise_math/field/`。
用 `em --field PATH` 打开独立持续场。新的运行时代码不能覆盖既有工作场。
研究任务的身份与项目规则继续从其当前 Source 入口读取。

## 显式辅助与历史基线

已知符号可直接用 `git grep` 或 `rg` 阅读源码；`project/em find TERM` 是显式字面扫描。
需要旧 manifest 的盘点、证据导入材料、源码图导航、Coverage 实验或 AOCI 编解码时，
读取 [辅助工具与对照模式](references/auxiliary.md)，使用 `aux ...`。
需要复现旧词项评分、来源布局或图路由实验时，使用 `baseline ...`。

旧的未限定 `recall`、`field`、`brief`、`geometry` 等命令会提示新调用方法，
不再作为普通记忆入口。历史清单和实验场保留其原机制；迁入项目记忆时由 Host 阅读
判断和原文，再通过正常相遇选择几何位置，不按来源或词项自动重建语义布局。
