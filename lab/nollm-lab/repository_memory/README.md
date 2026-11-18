# Nollm 仓库记忆实验 / Repository Memory

这条实验分支让下一个读代码的人或模型可以接着使用已经核过的工程判断。例如，在同一个记忆位置附加第二条说明后，正常召回仍读哪一条？示例用两条带源码证据的说明回答这个问题。仓库里保存的是说明和 Git 证据；原生几何记忆演示在临时工作区内运行。

## 先试读

在本分支的仓库根目录运行。源码盘点与阅读只依赖 Git 和 Python 标准库；原生记忆演示直接导入仓库自带的 Core 与 Access。

```sh
D=lab/nollm-lab/repository_memory
M="$D/examples/nollm-notes.json"
python3 "$D/repo_notes.py" view --repo . --manifest "$M"
python3 "$D/repo_notes.py" source --repo . --manifest "$M" --key binding.current
python3 "$D/repo_notes.py" inventory --repo . --scope packages/nollm-access --manifest "$M"
```

`view` 只显示全部已声明证据仍匹配的说明。`source` 取回所选说明的原始 Git blob 字节；`--evidence-index 1` 选第一份辅助证据。`inventory` 列出范围内 Git 跟踪的普通文件：哪些是主证据、哪些只用来佐证、哪些尚无人记录。`review` 列出需要重读的说明；其中一个外部依赖变化，也会影响这条说明。来源受版本控制，工作树里尚未提交的编辑不参与比较。

## 为自己的仓库写第一条记忆

1. 用 `inventory --repo /path/to/repo --scope src` 盘点指定范围。首次无需 manifest；`--scope .` 明确表示整库。
2. 作者或宿主模型读取固定提交中的源码及相关证据，写下完整判断。优先记录“修改这里时还要考虑什么”“为什么这个分支要保留”。路径和标签本身不能回答这些问题。
3. 将下面的 JSON 存成草案，将占位值替换为实际提交、路径与判断。`reviewed_commit` 使用 `git -C /path/to/repo rev-parse HEAD` 的完整输出；`also` 可省略。

```json
{
  "reviewed_commit": "<full commit the author actually read>",
  "notes": [{
    "key": "order.commit-visibility",
    "text": "<one independently understandable conclusion supported by these sources>",
    "source": "src/order.py",
    "also": ["tests/test_order.py"]
  }]
}
```

```sh
python3 "$D/repo_notes.py" capture --repo /path/to/repo --draft draft.json --manifest notes.json
python3 "$D/repo_notes.py" status  --repo /path/to/repo --manifest notes.json
```

一次 `capture` 只更新所给的键，其余说明保留各自核阅时的版本。草案与目标提交不符、或一个批次里有无效来源时，不改已有清单。证据字节改变、移除或换成其他类型后，先重读影响到的说明，再提交新版草案。`--rev <commit>` 可以重放历史视图。清单由一名写者维护，可以和所描述的项目一起提交；仓库规则的效力仍由原始规则文件决定。

## 原生 Nollm 实验

```sh
PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src \
  python3 "$D/field_demo.py" --repo . --manifest "$M" \
  --place binding.current 0 0 --place recall.evidence 1 0 \
  --place snapshot.scope 8 0 --entry 0 0
```

宿主把“当前绑定”和“召回时核对当前正文”放在相邻位置，把快照职责放得远一些。程序只把新鲜说明转换为原生 `MemoryStatement`，通过 Access 写入，释放运行时，再从磁盘重开。一个物理入口、一步侧向传播，能取回入口和邻格的正文与引用，远处的快照说明不在结果中。这里坐标由宿主显式给出，文件名、内容关键词和说明键均不决定位置。临时场在演示结束后销毁。

## 量化结果与复现

```sh
python3 "$D/evaluate_reads.py" --repo .
PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src \
  python3 -m unittest discover -v -s "$D"
```

示例基于 Nollm 提交 `314eb47490adcad22e37d6e05d2da3983e78956d` 的 5 个真实文件。这 5 个 Git blob 共 **31,271 B**；默认阅读视图 **1,866 B**；含完整证据的 JSON **3,511 B**。`evaluate_reads.py` 用六个工程问题比较整文件读取量。每题重新读取全部源码共 187,626 B；预先给出每题的正确证据文件时，六题回源共 65,702 B。若同一会话完整保留前文，六题的来源并集覆盖全部五个文件，此时先读视图再读完整证据共 33,137 B。这是输入字节计算，不包含模型 token、工具负担、时延或语义准确率。

另一次独立试读中，答题者先根据五条说明的简写选定要读的文件，之后才开放所选源码；六题的答复与事先写好的判分要点相符。它只凭说明答了一道题，其余五道回源。这个小样本用于检查说明是否能引导核查；它没有比较模型优劣或自动选择几何入口的表现。`evaluate_reads.py --questions-only` 可导出不含答案的题目供新实验使用。

## 设计对照及后续实验

[AOCI-CODE](https://github.com/aoci-spec/aoci-code) 将模型编写的源码说明保存在 Git 中，用版本变化驱动维护，主要入口会读取项目全景。[作者论文](https://arxiv.org/abs/2605.02421)提供了这种做法的研究背景。本分支采用 Nollm 自己的说明格式、证据处理和原生记忆接口，未复制 AOCI 的源码、资产或协议，也无需安装其服务。上游当前版本列明 [FSL-1.1-MIT](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/LICENSE)。

建议下一项实验：让不了解答案的宿主在真实改动任务中选择入口，对比直接搜索源码、先读全景再回源、Nollm 按需召回再回源，统一记录答案正确性、来源、实际模型输入和首次启动代价。这样才能决定哪些场景值得接入日常开发。
