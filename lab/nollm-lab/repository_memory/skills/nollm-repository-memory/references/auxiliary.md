# 辅助工具与对照模式

## 目录

- [命令范围与迁移](#命令范围与迁移)
- [Git 清单和来源辅助](#git-清单和来源辅助)
- [机器事实与图导航](#机器事实与图导航)
- [明确的检索基线](#明确的检索基线)
- [显式 Coverage 实验](#显式-coverage-实验)
- [AOCI 编解码与物理表示](#aoci-编解码与物理表示)

## 命令范围与迁移

这些工具用于源文件导航、数据准备、结构检查与对照实验。普通原生记忆使用
`project --field FIELD encounter` 或 `em encounter`。旧的未限定命令返回新调用提示。

| 旧命令 | 显式调用 | 机制 |
| --- | --- | --- |
| `brief/source/inventory/capture/review/status/view` | `aux` 加原命令 | Git 证据清单 |
| `facts/records/route/check-marks` | `aux` 加原命令 | 静态源码、符号及声明关系 |
| `coverage` | `aux coverage` | 明确给定位置的几何实验 |
| `geometry` | `aux aoci` | AOCI 标签及槽位的可逆编解码 |
| `geometry-native` | `aux aoci-field` | 将 AOCI 槽位和显式 R 引用表示为原生 atom/bridge |
| `recall` | `baseline recall` | 词项评分入口、共享来源启发式布局 |
| `field` | `baseline field` | 来源/图路由选对象、启发式布局、几何邻域读取 |

把 `cli` 设为本 skill 的 `scripts/memory.py`，`repo` 设为源码 Git 仓库，
`rev` 设为实际要核查的提交。以下输出使用独立目录，原生工作场继续沿用其既有路径。

## Git 清单和来源辅助

```sh
manifest="$repo/.nollm/repository-notes.json"
python3 "$cli" aux brief --repo "$repo" --rev "$rev" --manifest "$manifest" --scope src
python3 "$cli" aux inventory --repo "$repo" --rev "$rev" --manifest "$manifest" --scope src
python3 "$cli" aux view --repo "$repo" --rev "$rev" --manifest "$manifest"
python3 "$cli" aux source --repo "$repo" --rev "$rev" --manifest "$manifest" --key "$key"
```

`brief/inventory` 在尚无清单时也能列跟踪路径。清单只说明已记录哪些来源；
阅读判断之前检查其来源版本。`source` 返回主证据的 Git blob 字节，
`--evidence-index 1` 返回第一份辅助证据。`view` 显示声明证据仍匹配的判断。

若维护已有清单，草案格式如下。所有正文由 Host 根据实际源码编写。

```json
{
  "reviewed_commit": "<已读取的完整提交 ID>",
  "notes": [{
    "key": "<稳定判断键>",
    "text": "<完整判断和条件>",
    "source": "<主证据路径>",
    "also": ["<辅助证据路径>"]
  }]
}
```

```sh
python3 "$cli" aux capture --repo "$repo" --rev "$rev" --manifest "$manifest" --draft draft.json
python3 "$cli" aux review --repo "$repo" --rev "$rev" --manifest "$manifest"
python3 "$cli" aux status --repo "$repo" --rev "$rev" --manifest "$manifest"
```

`capture` 按键更新，保留其余条目的核阅版本；`review` 给出来源改变、移动或缺失的线索。
将清单中的理解迁入原生项目场时，先核实来源，再由 Host 选择位置并保存固定来源窗口。
清单没有保存 Host 接受的原生布局，不能据它自动重建项目场。

## 机器事实与图导航

```sh
python3 "$cli" aux facts --repo "$repo" --rev "$rev" --out "$out/facts"
python3 "$cli" aux route --repo "$repo" --rev "$rev" --facts "$out/facts" \
  --mode graph --query "$question" --out "$out/seeds.json"
python3 "$cli" aux check-marks --repo "$repo" --rev "$rev" --marks marks.jsonl
```

`facts` 提取跟踪路径、符号、可解析导入及部分 C/C++/CMake 关系。
查看 `confidence` 与 `diagnostics.jsonl`；规则可解析范围见安装运行时的
`language_profiles.json`。`route` 的 `lexical` 模式按路径和标识符检索，
`graph` 增加源码图传播，`semantic` 加入已编写三元组，三者都是工程候选检索。
按候选的路径和行号回到原文，另行形成语义判断。

```sh
python3 "$cli" aux records --repo "$repo" --rev "$rev" --manifest "$manifest" \
  --claim-template --out "$out/claims.json"
# Host 按读过的证据填写 claims.json 的 atoms，例如 ["Reader", "imports", "Decoder"]。
python3 "$cli" aux records --repo "$repo" --rev "$rev" --manifest "$manifest" \
  --claims "$out/claims.json" --out "$out/records.jsonl"
python3 "$cli" aux route --repo "$repo" --rev "$rev" --facts "$out/facts" \
  --mode semantic --records "$out/records.jsonl" --query "$question" --out "$out/seeds.json"
```

这些显式关系和检索分数用于源码导航或比较，不充当原生项目记忆的入口选择器。

## 明确的检索基线

```sh
python3 "$cli" baseline recall --repo "$repo" --rev "$rev" --manifest "$manifest" \
  --query "$question" --limit 3 --format json
```

该基线按键、路径和正文的固定词项权重选一条说明，以共享来源规则布置场，
再经一次侧向几何传播返回邻域。JSON 的 `mode` 为 `lexical_source_layout_baseline`。
没有词项命中时直接返回 `no_match`。这不是 Host 观察 Surface 后的原生发现。
它复用 Git 目录的 `nollm-repository-memory/fields-v1/` 派生场；
`--no-cache` 使用临时场。旧缓存可用于原机制复现，不作为项目原生场迁移来源。

```sh
python3 "$cli" baseline field build --repo "$repo" --rev "$rev" --facts "$out/facts" \
  --records "$out/records.jsonl" --layout architecture --field "$out/baseline-field"
python3 "$cli" baseline field query --repo "$repo" --rev "$rev" --field "$out/baseline-field" \
  --seeds "$out/seeds.json" --include-records
```

该基线用 `route.json` 将来源候选映射为入口，`architecture` 按共享来源和依赖图
布置坐标，`shared` 只用共享来源。返回模式为 `source_routed_<layout>_baseline`。
它执行真实 Core 邻域读取，但入口和邻接已经由外部规则确定。历史实验保留原数据；
新的比较按完整机制报告，不用“native”概括整个检索链。

## 显式 Coverage 实验

```sh
python3 "$cli" aux coverage footprint --entry -1 -7 5 --direction down
python3 "$cli" aux coverage build --repo "$repo" --rev "$rev" --manifest "$manifest" \
  --field "$out/coverage-field" --place "$key" -7 8
python3 "$cli" aux coverage recall --repo "$repo" --rev "$rev" --field "$out/coverage-field" \
  --entry -1 -7 5 --direction down --steps 1 --beam 8 --limit 8
```

这里的坐标只是展示调用语法；实际实验由 Host 根据含义和几何足迹选择。
`build` 使用明确提供的 `--place KEY Q R`，不应用词项或来源布局规则。
`surface` 可逐页观察该场，`recall` 只接受一个物理入口。观察阶与物理层分别解释。
日常持久记忆使用 `project/em encounter`。

## AOCI 编解码与物理表示

```sh
python3 "$cli" aux aoci encode --volume aoci.code.txt --meta aoci.meta.txt --out code.nlg
python3 "$cli" aux aoci check --geometry code.nlg --meta aoci.meta.txt
python3 "$cli" aux aoci query --geometry code.nlg --meta aoci.meta.txt --axis C=7 --field F
python3 "$cli" aux aoci decode --geometry code.nlg --meta aoci.meta.txt --out restored.txt
python3 "$cli" aux aoci-field write --geometry code.nlg --meta aoci.meta.txt --field "$out/aoci-field"
python3 "$cli" aux aoci-field probe --meta aoci.meta.txt --field "$out/aoci-field"
python3 "$cli" aux aoci-field read --meta aoci.meta.txt --field "$out/aoci-field" --out physical-rows.json
```

`aoci` 用编码时的公共字典解释标签轴及 F/R/A/S 槽位；规范化回读保留对象身份、
列值和关系正文。`aoci-field` 将这些槽位写为原生 atom，对卷内已给出的 R 引用建立桥。
这是编码与显式引用的物理表示，适用于工程理解、回源和结构对照；
它不代表 Host 已从证据形成语义布局，也不证明旋转 Coverage 带来的发现收益。
