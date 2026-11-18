---
name: nollm-repository-memory
description: 用带 Git 证据的工程判断接手仓库任务。Use when a user wants to recall, verify, update or hand off previously reviewed code behavior, identify which notes need rereading after a change, or find sources for a local modification.
---

# Nollm 仓库记忆

用仓库作者或模型已核过的短说明定位证据。交付代码改动时，仍需检查当前实现、工作树改动及测试。一个键对应一个可单独复核的判断。

## 运行入口

需要 Python 3.11+、Git 和目标仓库的本地 Git 对象。把 `SKILL` 设为本文件所在目录的绝对路径。从 Nollm 实验分支可以原地使用，也可以装成能独立移动的 skill。在 Nollm 根目录运行以下安装命令，目标目录须为新目录。

```sh
SKILL="$HOME/.agents/skills/nollm-repository-memory"
python3 lab/nollm-lab/repository_memory/install_skill.py --dest "$SKILL"
python3 "$SKILL/scripts/memory.py" --help
```

从目标仓库开始，每个会话先解析一次提交。优先使用项目已约定的 manifest，新项目可采用下列位置。草案路径和 manifest 路径相对于调用者的工作目录解析。

```sh
repo=$(git rev-parse --show-toplevel)
rev=$(git -C "$repo" rev-parse HEAD)
manifest="$repo/.nollm/repository-notes.json"
mem() { python3 "$SKILL/scripts/memory.py" "$@"; }
```

## 接手一个局部任务

1. 任务给出文件或符号时，直接用 `git show` 或 `git grep -n -F` 在目标提交中定位。需要接手一个行为判断、且已有清单时，把问题交给 `recall`。尽量沿用项目的命名；英文说明可以用代码标识符或英文术语查询。
2. 读返回的说明键、正文和引用路径。用 `source` 核对选中的主文件和有关的辅助文件。证据索引从 0 开始，顺序与显示的引用路径一致。
3. 如果查询没有命中、命中与任务无关，或任务需要的细节超出了说明，搜索目标提交的实现、调用方及测试。首次接手还没有 manifest 时直接从源码开始。若需要全景，再显式调用 `view` 阅读全部新鲜说明。
4. 涉及公共接口时，从包的公开导出或端口声明追到实现和跨包调用方。检查归属清单所指的模块、当前契约和验证它的测试。只把能支持本条判断的文件填入 `source` 和 `also`。
5. 检查相关路径的工作树差异，再决定修改方案。实现、测试通过后，在回复中标明判断所依据的提交、文件及验证结果。超出证据的推断要标明。

下面的查询可在 Nollm 仓库用样本验证。示例命令单独指定样本清单。在其他仓库使用项目自己的 `$manifest`、查询、键和路径。

```sh
sample="$repo/lab/nollm-lab/repository_memory/examples/current-notes.json"
mem recall --repo "$repo" --rev "$rev" --manifest "$sample" \
  --query 'Which statement stays current when another is attached to an occupied handle?' --limit 3 --format view
mem source --repo "$repo" --rev "$rev" --manifest "$sample" --key binding.current
mem source --repo "$repo" --rev "$rev" --manifest "$sample" --key recall.evidence --evidence-index 1
git -C "$repo" grep -n 'current_statement' "$rev" -- packages/nollm-access
git -C "$repo" diff "$rev" -- packages/nollm-access
```

`--format view` 按原生召回顺序显示正文，每条说明下方是证据路径和 Git blob 短标识。检查结果是否切题；若输出 `no_match`，请直接搜源码。需要所选入口、遍历路径、核阅提交及完整 Git 对象标识时，用 `--format json`。新鲜度只覆盖声明过的证据在所选提交中的内容；未声明的调用方、未提交的改动和新增需求都可能改变判断的适用范围。

以 Nollm 的公共方法 `CoreRuntime.export_state_bytes` 为例，已知名字时可直接运行如下查询。

```sh
git -C "$repo" grep -n -F 'export_state_bytes' "$rev" -- \
  packages/nollm-core/src packages/nollm-snapshot \
  docs/architecture/module-ownership/CORE_PUBLIC_API_ALLOWLIST.json
```

其中 Core 的 `state.py` 实现该方法，Snapshot 的 `ports.py` 声明调用方需要的接口，`service.py` 和 `tests/test_core_snapshot.py` 展示用法及字节相等断言。变更公开方法时，Core 的 `tests/test_core_public_api_allowlist.py` 检查操作名；签名和行为还需要调用方测试核实。需要确认文件归属时，按仓库相对路径到 `MODULE_OWNERSHIP_MANIFEST.csv` 查对应行。接手者可沿这些真实路径重新核查。

同一个仓库反复查询时，`recall` 默认复用已写入磁盘的原生场。每次先按目标提交核验证据；新鲜条目集合、正文及其证据一致时，就能从本次任务选定的入口读取已有场。若希望本次只使用临时场，在 `recall` 命令末尾加 `--no-cache`。已生成的场保存在仓库 Git 目录的 `nollm-repository-memory/fields-v1/` 下，其中包含说明正文。可以在查询都结束后清理这个派生目录。

## 写入或更新一个判断

先用 `inventory` 看任务范围。已有清单时加 `--manifest "$manifest"`。输出中的 `primary` 表示作为说明主来源，`support` 表示仅作辅助证据，`unrecorded` 表示尚未引用。

```sh
mem inventory --repo "$repo" --rev "$rev" --scope packages/nollm-access
```

在准备保存的提交上用 `git show "$rev:<仓库相对路径>"` 阅读源码，核对测试或跨模块依赖。选择描述行为的稳定键，写清触发条件、结果和对调用者的影响。用一个草案提交这一轮核过的键。以下是在 Nollm 样本上的格式示例，使用时将正文和来源换成自己实际核过的内容。

```sh
draft=$(mktemp)
cat >"$draft" <<EOF
{
  "reviewed_commit": "$rev",
  "notes": [{
    "key": "binding.current",
    "text": "Attaching another statement to an occupied handle preserves the current statement. The newly attached statement is supporting evidence.",
    "source": "packages/nollm-access/src/nollm_access/handle_store.py",
    "also": ["packages/nollm-access/tests/test_binding_store_invariants.py"]
  }]
}
EOF
mem capture --repo "$repo" --rev "$rev" --draft "$draft" --manifest "$manifest"
mem status --repo "$repo" --rev "$rev" --manifest "$manifest"
rm "$draft"
```

`source` 和 `also` 接受仓库相对的普通文件路径。每条引用都会参与新鲜度检查。相同键会更新，其他键保留各自的核阅提交。若发现新行为只存在于工作树，等相应改动有了 Git 提交，再核阅并写入。需要团队或另一台机器接手时，把清单和源码一同纳入项目约定的版本控制流程。

## 处理变更和历史追溯

新会话或切换分支后重新解析 `rev`，再运行以下命令。

```sh
rev=$(git -C "$repo" rev-parse HEAD)
mem review --repo "$repo" --rev "$rev" --manifest "$manifest"
```

逐一检查被标记的键和 `changes` 中的路径。若文件移动，在新提交里找到接替的文件。重读主来源和必要的辅助来源，重写仍然成立的判断，并用新的核阅提交执行 `capture`。证据不足的条目可留在复核队列，默认视图和任务召回会将其排除。

追溯还保存在清单中的旧判断时，使用它的 `reviewed_commit` 作为 `--rev` 调用 `source`。若同一键已经改写，从 Git 中取出历史版本的清单，再对历史源码提交执行 `view` 或 `source`。留意保存清单的提交可以晚于它引用的源码提交。把结论交给下一个会话时，一并给出清单位置、核阅提交、相关键以及需要重新核查的证据。
