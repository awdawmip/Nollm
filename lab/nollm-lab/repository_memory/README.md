# Nollm 仓库与项目记忆 / Repository Memory

普通项目记忆从 **Surface → Host 选择 → 一个物理入口 → 局部事实或可写位置** 开始。
同一个 `encounter` 支持查询、补充表达、原位修订和新判断。真实 LLM 阅读语义、选择入口
和位置；Core 执行占用、Coverage、邻接和桥，Access 返回对应表达与固定来源。

Nollm 自身的持续开发工作场名为[速记本](../../../sujiben/README.md)，位于
`sujiben/field`，与当前代码一起保留在开发分支。概念、实现行为与成立条件由 LLM
沿原生场持续组织；先前 C1–C3 的开发和维护记录见[自举入口](self_bootstrap/README.md)。
进取数论已有研究场见 [EM 入口](enterprise_math/README.md) 与
[冷会话使用记录](enterprise_math/TRIAL.md)。AOCI 的[工程理解和回源分工](AOCI_COMPARISON.md)、
编码与显式引用另见下文。

## 安装和开始

需要 Python 3.11+ 和 Git。在 Nollm 仓库根目录执行：

```sh
python3 lab/nollm-lab/repository_memory/install_skill.py --host codex
```

安装器将运行时代码、使用说明和辅助参考放入新目录，工作场由调用方显式选择。
速记本和 EM 研究场均独立于安装目录。也可用
`--host claude|copilot|opencode`，或 `--dest /path/to/new/nollm-repository-memory`
指定新目录；安装品可独立移动。更多宿主位置见 [HOSTS.md](HOSTS.md)。

从实际安装位置运行，明确选择持续使用的项目场和源码仓库：

```sh
cli='/path/to/nollm-repository-memory/scripts/memory.py'
field='/path/to/project-field'
repo='/path/to/source-repository'
session='/tmp/nollm-encounter.json'
python3 "$cli" project --field "$field" encounter --cursor-file "$session"
```

阅读本页预览，以当前任务为依据选择本页候选，再继续观察：

```sh
python3 "$cli" project --field "$field" encounter "$candidate_id" --cursor-file "$session"
```

`surface` 页面展示聚合观察，`physical` 页面展示最终物理候选。选择一个物理入口后，
`locality` 页面返回 `entry`、当前事实 `items`、可写位置 `cells` 与实际预算。
`text_truncated` 表示展示的正文被裁剪，`truncated` 表示还有表达未展示；
局部页面返回完整判断与条件。`walk` 进一步只显示标题时也会标记正文裁剪。
新场先提供原点种子；Host 选择该物理候选后才能在本次局部中形成第一条记忆。
重复执行而不传新选择可重开当前页；`--restart` 开始新的观察。

在 Nollm 源码检出中，也可直接运行同一个 CLI：

```sh
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field sujiben/field \
  encounter --cursor-file /tmp/nollm-sujiben.json
```

场保留已有语义布局和来源；会话文件只保存可丢弃的导航状态。
运行时代码升级后继续用 `--field` 打开原场，不从来源清单自动重建坐标。

## 同一次相遇的读取与写入

在 `locality` 页面选择当前事实 ID 或可用位置 ID：

| Host 的语义决定 | 终结选项 | 持久结果 |
| --- | --- | --- |
| 查询得到所需事实 | `--recall FACT_ID` | 返回该事实与来源 |
| 新表达支持同一当前判断 | `--reuse FACT_ID --id NEW_ID` | 保存独立补充表达，复用原占用 |
| 同一事实需要更正 | `--revise FACT_ID --id NEW_ID` | 原位更新当前版本，保留旧正文和来源 |
| 新内容是独立判断 | `--new CELL_ID --id NEW_ID` | 在 Host 选定的局部位置放置 |
| 本次查询没有相关事实 | `--none` | 返回明确空结果 |
| 尚不确定 | `--defer` | 结束本次相遇，暂缓决定 |

查询示例：

```sh
python3 "$cli" project --field "$field" encounter --cursor-file "$session" --recall "$fact_id"
```

写入示例；将位置、版本 ID、路径和行号换成实际读过的内容，正文从 stdin 传入：

```sh
python3 "$cli" project --field "$field" encounter --cursor-file "$session" \
  --new "$cell_id" --id reading.v1 --repo "$repo" --rev HEAD \
  --cite 'src/reader.py#L10-L20' --cite 'tests/test_reader.py#L25-L40' < judgment.txt
```

将 `--new "$cell_id"` 换成 `--reuse "$fact_id"` 或 `--revise "$fact_id"` 保存补充或修订。
每条表达写清可独立理解的判断、条件和影响，关系表达引用双方证据。终结后会话文件删除。

`--steps`、`--beam`、`--limit` 分别控制传播步数、每步候选数和结果数；
`--via local|connected|vertical|lateral` 控制本次可用的几何核。
需要改变预算时，先重开同一个局部并观察结果，再选择终结动作。
预算耗尽或空结果不会隐式改走词项搜索。需要源码辅助时可以直接使用，并按实际机制
记录取得的证据与仍然存在的原生发现缺口。

## 回源、版本和持续维护

```sh
python3 "$cli" project --field "$field" show "$statement_id"
python3 "$cli" project --field "$field" source --id "$statement_id" --number 1 --repo "$repo"
python3 "$cli" project --field "$field" links
```

`show` 展开准确的表达版本和引用；`source` 返回固定 Git 提交的原文行。
`current` 表示场内当前绑定，引用中的提交说明理解基于哪个源码版本。
支持表达有自己的 ID、正文和固定来源，显示 `current: false`；
修订后前一版本与支持表达仍可精确读取。

按代码差分与场内引用核查受影响的理解，Host 决定保留、补充或修订。
`stitch LINK_ID FROM_ID TO_ID`、`unstitch LINK_ID` 维护有依据的定向格级连接。
同格其他表达也可能被桥召回，因此正文修订后按实际含义判断连接是否继续有用。

`walk` 保留为只读 Surface 导航与单入口展开；
`save --at Q R|--reuse ID|--revise ID` 保留为 Host 已明确选择时的直接写入接口。
普通形成和召回优先使用共同的 `encounter`。完整用法见
[仓库记忆 skill](skills/nollm-repository-memory/SKILL.md)。

## 源码辅助、对照基线与 AOCI

源码盘点、符号与图检索、旧清单、明确给定坐标的 Coverage 实验、AOCI 编解码仍然可用，
使用显式命名空间：

| 调用 | 实际机制 |
| --- | --- |
| `aux brief/inventory/capture/review/source/view/status` | Git 证据清单与源码核查 |
| `aux facts/records/route/check-marks` | 机器事实、声明关系与源码候选导航 |
| `aux coverage` | Host 明确给定位置的几何实验 |
| `aux aoci`、`aux aoci-field` | AOCI 槽位编码和显式引用的物理表示 |
| `baseline recall` | 固定词项评分入口与共享来源启发式布局 |
| `baseline field` | 来源/图路由入口与启发式布局，再执行 Core 邻域读取 |

旧的未限定命令会明确提示对应的新调用，不再充当普通记忆入口。
`project/em find TERM` 是另一个显式字面工具。工程搜索、字面扫描、对照基线与
原生 Surface 发现按完整路径分别评价。

[辅助命令与迁移示例](skills/nollm-repository-memory/references/auxiliary.md)
保留原清单格式、机器语料、Coverage 和 AOCI 的操作说明。
已停用的历史清单及配套实验在下述归档中保留；迁入项目场时由 Host 阅读判断和原文后选择位置。
AOCI 的对象、字典和 R 引用来自输入代码卷，其往返成功验证的是表示保真。

## 当前开发与旧实验归档

速记本、当前 EM 场、原生运行时、skill、现行测试与 `baseline`/`aux` 工具继续在开发分支维护。
归档范围只包括已经停用的固定源码清单、三组改动实验、旧 AOCI 卷及对应建场/六题评估。
`self_study` 中独立的[几何探针](self_study/README.md)和
`comparison` 中仍在用的[宿主发现与 Access 计时工具](comparison/README.md)保留。

旧资产由 `archive/legacy-code-20261122` 保存，锚点为
`beaafabfe8dec4ba1c154ecd324954fa81417489`。复现历史实验时使用该固定版本的
[旧说明与评估器](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/README.md#历史量化结果与复现)，
其中的源码版本、题目、命令和计量仍按当时范围解释。

这些结果比较的是固定材料与任务，仍包含原始失败和限制；它们不构成当前原生发现质量的结论。
当前回归可从仓库根执行：

```sh
PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src \
  python3 -m unittest discover -v -s lab/nollm-lab/repository_memory
```

## 设计与后续比较

[AOCI-CODE](https://github.com/aoci-spec/aoci-code) 将模型编写的源码说明保存在 Git 中，
用版本变化驱动维护；[作者论文](https://arxiv.org/abs/2605.02421)提供研究背景。
本分支使用 Nollm 的证据、语句、绑定和原生几何接口。旧路线的说明与报告按形成时的
实现保存，新工作从上面的原生入口继续。

- [项目缩影与原生几何架构研究](PROJECT_MINIATURE_DESIGN.md)
- [速记本：当前概念与代码理解](../../../sujiben/README.md)
- [自身开发、理解维护与已观察失败](self_bootstrap/README.md)
- [历史清单/词项路线的架构与实施记录](ARCHITECTURE_AND_PLAN.md)
- [三种阅读方式的历史改动对照与复现](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/comparison/README.md)
- [机器事实的字段和解析范围](FACTS.md)
- [AOCI-CODE 的工程工作流对照](AOCI_COMPARISON.md)
