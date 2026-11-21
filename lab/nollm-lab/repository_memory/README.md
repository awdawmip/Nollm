# Nollm 仓库与项目记忆 / Repository Memory

普通项目记忆从 **Surface → Host 选择 → 一个物理入口 → 局部事实或可写位置** 开始。
同一个 `encounter` 支持查询、补充表达、原位修订和新判断。真实 LLM 阅读语义、选择入口
和位置；Core 执行占用、Coverage、邻接和桥，Access 返回对应表达与固定来源。

Nollm 自身的持续工作场和开发记录见 [自举入口](self_bootstrap/README.md)。
进取数论已有研究场见 [EM 入口](enterprise_math/README.md) 与
[冷会话使用记录](enterprise_math/TRIAL.md)。AOCI 是
[工程理解和回源辅助](self_study/aoci/README.md)，其编码与显式引用另见下文。

## 安装和开始

需要 Python 3.11+ 和 Git。在 Nollm 仓库根目录执行：

```sh
python3 lab/nollm-lab/repository_memory/install_skill.py --host codex
```

安装器将运行时代码、使用说明和辅助参考放入新目录。也可用
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
页面预览可能截短正文；局部页面返回完整判断与条件。
新场先提供原点种子；Host 选择该物理候选后才能在本次局部中形成第一条记忆。
重复执行而不传新选择可重开当前页；`--restart` 开始新的观察。

在 Nollm 源码检出中，也可直接运行同一个 CLI：

```sh
python3 lab/nollm-lab/repository_memory/skills/nollm-repository-memory/scripts/memory.py \
  project --field lab/nollm-lab/repository_memory/self_bootstrap/field \
  encounter --cursor-file /tmp/nollm-self-encounter.json
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
历史清单及实验数据继续保留；迁入项目场时由 Host 阅读判断和原文后选择位置。
AOCI 的对象、字典和 R 引用来自输入代码卷，其往返成功验证的是表示保真。

## 历史量化结果与复现

以下保留早期清单/来源读取实验的原范围和计量。它们用于比较已编写理解与来源材料，
不会作为当前原生发现路径的质量结论。


```sh
python3 "$D/evaluate_reads.py" --repo .
PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src \
  python3 -m unittest discover -v -s "$D"
```

早期字节实验固定使用 `examples/nollm-notes.json` 和 Nollm 提交 `314eb47490adcad22e37d6e05d2da3983e78956d` 的 5 个真实文件。这 5 个 Git blob 共 **31,271 B**；默认阅读视图 **1,866 B**；含完整证据的 JSON **3,511 B**。`evaluate_reads.py` 用六个工程问题比较整文件读取量。每题重新读取全部源码共 187,626 B；预先给出每题的正确证据文件时，六题回源共 65,702 B。若同一会话完整保留前文，六题的来源并集覆盖全部五个文件，此时先读视图再读完整证据共 33,137 B。这是输入字节计算，不包含模型 token、工具负担、时延或语义准确率。

另一次独立试读中，答题者先根据五条说明的简写选定要读的文件，之后才开放所选源码；六题的答复与事先写好的判分要点相符。它只凭说明答了一道题，其余五道回源。这个小样本用于检查说明是否能引导核查；它没有比较模型优劣或自动选择几何入口的表现。`evaluate_reads.py --questions-only` 可导出不含答案的题目供新实验使用。

## 设计与后续比较

[AOCI-CODE](https://github.com/aoci-spec/aoci-code) 将模型编写的源码说明保存在 Git 中，
用版本变化驱动维护；[作者论文](https://arxiv.org/abs/2605.02421)提供研究背景。
本分支使用 Nollm 的证据、语句、绑定和原生几何接口。旧路线的说明与报告按形成时的
实现保存，新工作从上面的原生入口继续。

- [项目缩影与原生几何架构研究](PROJECT_MINIATURE_DESIGN.md)
- [自身开发、理解维护与已观察失败](self_bootstrap/README.md)
- [历史清单/词项路线的架构与实施记录](ARCHITECTURE_AND_PLAN.md)
- [三种阅读方式的改动对照与复现](comparison/README.md)
- [机器事实的字段和解析范围](FACTS.md)
- [AOCI-CODE 的工程工作流对照](AOCI_COMPARISON.md)
