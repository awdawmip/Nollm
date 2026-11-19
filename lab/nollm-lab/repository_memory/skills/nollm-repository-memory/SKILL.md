---
name: nollm-repository-memory
description: "在本地 Git 仓库中梳理模块职责、提取和核验机器标记、追踪跨文件影响、复核过期判断或为下个会话留下源码证据。Use for repository onboarding, machine-readable architecture facts, change-impact analysis, and engineering handoffs grounded in Git."
---

# Nollm 仓库记忆

根据用户的任务选择阅读范围。接手一个系统时先看全景；修改一个具体行为时先取相关判断；已知符号时直接查源码。每条记忆记录一个经过核对的工程判断，并绑定支持它的 Git 文件。作者可以是正在使用本 skill 的编码助手。

下列请求都可以直接用自然语言提出。

- “我第一次接手这个仓库。梳理主要入口和模块职责，标出还没读的部分。”
- “准备修改这个公共接口。找出受影响的调用方、契约和回归测试。”
- “合并后复核上次的结论，把仍然成立的判断交给下一个会话。”

## 从目标仓库启动

需要 Git 和 Python 3.11+。从宿主加载的**本文件的位置**找到同目录下的 `scripts/memory.py`。在目标工作树内运行它；脚本和要分析的仓库可以在不同位置。以下为 POSIX shell 示例，请用实际目录替换第一行。独立 shell 调用需重新设置变量，或使用解析后的绝对路径直接执行同一命令。

```sh
skill='/absolute/path/to/the/loaded/nollm-repository-memory'
repo=$(git rev-parse --show-toplevel)
rev=$(git -C "$repo" rev-parse --verify HEAD)
manifest="$repo/.nollm/repository-notes.json"
mem() {
  command_name=$1
  shift
  python3 "$skill/scripts/memory.py" "$command_name" --repo "$repo" --rev "$rev" "$@"
}
```

优先沿用项目已有的清单路径。默认使用上面的 `manifest`。在尚无提交的新项目，先按任务实现或阅读工作树；等项目有了可核对的提交，再建立首批记忆。切换分支或提交后重新解析 `rev`。

## 第一次接手或需要全景

1. 从 `mem brief` 开始。它列出目标提交、所选范围的文件覆盖数、当前判断、待复核项和未记录路径样本。还没有清单时也可运行。若项目另有清单，传入 `--manifest "$manifest"`。用户只关心一个目录时，用 `--scope` 指定该目录的仓库相对路径。多个目录可重复传入 `--scope`。`--limit` 默认每类展示 5 项，查看省略数后再决定是否展开。
2. 用引用路径去读模块说明、公开入口、实际实现和关键测试。可以用 `git -C "$repo" show "$rev:$path"` 读取选定文件。沿一次真实调用核对职责、数据流和约束。先写出能回答本次任务的结论。
3. 要确认某一范围的文件覆盖情况，使用 `mem inventory --scope "$scope"`；已有清单时加 `--manifest "$manifest"`。范围用仓库相对的文件或目录，整库用 `.`。`primary`、`support`、`unrecorded` 表示文件在记忆中充当的角色。回答里说明已核对的范围，以及仍需打开的路径。
4. 用户要求已有判断的完整正文时，用 `mem view --manifest "$manifest"`。用户要建立仓库记忆时，按模块分批核阅并执行下方的 `capture`。目录盘点得到的文件名只够确定阅读顺序，保存判断之前要读证据。

## 回答局部问题或评估改动影响

把任务中的领域词、项目原有标识符交给 `recall`。以下 `question`、`key`、`scope` 均取自实际任务或前一步输出。

```sh
mem recall --manifest "$manifest" --query "$question" --limit 3 --format view
mem source --manifest "$manifest" --key "$key"
```

从短视图选出相关的键，再用 `source` 打开对应的 Git blob。默认读取主证据；需要辅助证据时加 `--evidence-index 1`，其他索引按显示顺序递增。需要核阅提交、完整对象 ID 或遍历路径时使用 `--format json`。没有清单、出现 `no_match` 或命中还不足以回答时，继续用源码搜索。

已知符号时可以从 `git -C "$repo" grep -n -F -e "$symbol" "$rev" --` 直接开始。修改公开接口时，沿公开声明找到实现、跨模块调用方、约束接口的清单和相应测试。对 SQL 迁移、配置或协议也可以引用 Git 中的定义；实际运行中的数据库或部署状态需要单独的运行证据。

动手修改前，用 `git -C "$repo" status --short` 和 `git -C "$repo" diff "$rev" -- "$scope"` 检查现场。Git 记忆的核验范围是所选提交中的已声明证据；尚未提交的编辑、未引用的调用方和新增需求都需要本次核查。

## 保存本次核过的判断

用户需要记录、维护或交接时，把本次实际读过的实现和佐证写成一个小批次。每条选一个可重复使用的稳定键，用一句或几句写清触发条件、行为和影响。将实际读过的提交完整 ID、仓库相对路径和正文写入临时 JSON 草案。下面是字段模板。

```json
{
  "reviewed_commit": "<rev 的完整 Git 提交 ID>",
  "notes": [{
    "key": "<稳定的行为键>",
    "text": "<经源码核实的工程判断>",
    "source": "<主证据路径>",
    "also": ["<支持此结论的调用方、测试或契约路径>"]
  }]
}
```

没有辅助证据时用空数组。将 `draft` 设为实际草案路径。一次写入可以含多条已核过的判断。

```sh
mem capture --manifest "$manifest" --draft "$draft"
mem status --manifest "$manifest"
```

`capture` 按键更新，保留其余条目的原核阅版本。核阅的行为如果只存在于未提交修改，先在交接里写明工作树差异，待相应代码有了提交，再核阅并保存。团队可把清单与项目一同纳入版本控制。

## 变更后的复核与交接

在新的 `rev` 执行 `mem review --manifest "$manifest"`，查看受影响的键和变更路径。辅助证据改变也会使该判断退出默认视图。逐条重读当前证据，文件移动时确认新路径；用新提交和同一键写回已确认的判断。证据暂缺的留在复核队列。追溯已被重写的判断时，从 Git 取出当时版本的清单，指定它记录的核阅提交运行 `source`。

交接时给出目标提交、所选范围、判断键、来源和实际运行的测试，再列出仍需核实的事项。重复查询默认复用仓库 Git 目录下的原生场。若只需临时场，可在 `recall` 上加 `--no-cache`。

## 提取机器标记并检验架构关系

用户需要机器可读语料、追踪显式依赖、或对照几何布置的效果时，用 `facts` 从提交直接生成 JSONL。每个跟踪路径均有 Git 对象信息；符号声明、可解析导入和部分 C/C++、CMake 关系还带行号。用 `confidence` 区分静态规则唯一解析的边和待核的候选，查看 `diagnostics.jsonl` 了解解析缺口。安装目录内的 `scripts/runtime/language_profiles.json` 说明 JavaScript、PowerShell、SQL、HTML 与 CSS 的提取规则和候选级别。

```sh
out=$(mktemp -d)
mem facts --out "$out/facts"
mem route --facts "$out/facts" --mode graph --query '你的实际工程问题' --out "$out/seeds.json"
```

`lexical` 只用路径及标识符，`graph` 还利用有证据的相邻文件。命中是候选；根据返回路径和行号读原始 Git 源码，再形成工程判断。提交变化时为新版本重建输出。批量比较可传 `--queries questions.json`，每题含 `id` 和 `query`。

待核验标记按行写入 JSONL。每条包括 `id`、`kind` 与该类所需的证据字段。例如，`symbol` 行含 `path`、`blob`、`line`、`qualname`、`symbol_kind`。用 `mem check-marks --marks marks.jsonl` 对当前提交重新取证，读取逐条状态与原因。设 `--require-verified` 可在任一条未验证时返回退出码 1。职责、约束等 `judgment` 标记保留人工复核状态。

维护能复用的行为判断时，先运行下面的模板命令，再按实际证据填写每条判断的 `atoms`。每个三元组使用符号，例如 `["Reader","imports","Decoder"]`。模板内的哈希绑定原判断和证据，正文或证据一旦变动，需要按新版重审。

```sh
mem records --claim-template --manifest "$manifest" --out "$out/claims.json"
# 填写 claims.json 中的 atoms 后执行
mem records --manifest "$manifest" --claims "$out/claims.json" --out "$out/records.jsonl"
mem route --facts "$out/facts" --mode semantic --records "$out/records.jsonl" \
  --query '你的实际工程问题' --out "$out/seeds.json"
```

要把这些判断放入持久化原生场，在临时目录中执行：

```sh
cli="$skill/scripts/memory.py"
python3 "$cli" field build --repo "$repo" --rev "$rev" --facts "$out/facts" \
  --records "$out/records.jsonl" --layout architecture --field "$out/field"
python3 "$cli" field query --repo "$repo" --rev "$rev" --field "$out/field" \
  --seeds "$out/seeds.json" --include-records
```

Host 以任务候选选一个物理入口；Core 在场中取邻近语句，Access 读回语句正文与引用。对照实验可用同一输入另建 `--layout shared` 的场。没有证据能够回答时，把源码搜索和回源结果一起交接。

## AOCI 代码卷的几何标记

当任务要求转换已有 AOCI 代码卷时，提供卷本身和项目的元数据字典。使用新输出路径。下例在 Codex 中调用已安装的 skill。

```sh
cli="$skill/scripts/memory.py"
python3 "$cli" geometry encode --volume aoci.code.txt --meta aoci.meta.txt --out code.nlg
python3 "$cli" geometry check --geometry code.nlg --meta aoci.meta.txt
python3 "$cli" geometry query --geometry code.nlg --meta aoci.meta.txt --axis C=7 --field F
python3 "$cli" geometry decode --geometry code.nlg --meta aoci.meta.txt --out restored.txt
```

`query` 按标签轴处理几何条件，`--field` 按相对位置读出 F、R、A 或 S 槽。多个 `--axis` 条件同时生效，`--min-importance` 按重要性过滤，`--feature-state present|missing` 区分可选 D 的有无。用 `--id` 指定对象。`decode --format json` 给出规范化对象；默认输出可重新导入的 AOCI 代码卷。列值、对象身份和关系正文保留，排版、注释与紧凑或点分标签的原始拼写按规范化格式输出。读取需使用编码时的标签字典。此命令验证几何编码的完整性；核实工程含义时回到对应源码与测试。

要从编译好的卷进入 Nollm 的物理场，指定一个新目录。写入后可在独立进程中从原点查看相邻字段，或从解析成功的 R 引用沿定向桥抵达目标对象。

```sh
python3 "$cli" geometry-native write --geometry code.nlg --meta aoci.meta.txt --field native-field
python3 "$cli" geometry-native probe --meta aoci.meta.txt --field native-field
python3 "$cli" geometry-native read --meta aoci.meta.txt --field native-field --out physical-rows.json
```

原生读回按对象身份排序。R 引用的目标出现在同一卷时可以建桥；卷外引用保留目标标识以便回源。
