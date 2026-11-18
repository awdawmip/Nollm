# 在编程助手中使用仓库记忆

从 Nollm 仓库根目录运行下面的命令。安装器会把 `SKILL.md`、命令入口、原生运行时和许可证复制到宿主能发现的目录，并打印安装位置。使用 skill 的机器需要 Python 3.11+、Git 和目标提交的本地 Git 对象。复制完成后，仓库记忆命令可离线工作。模型会话的联网、工具执行和目录访问由宿主控制。

## 选择宿主和范围

表中的目录是安装根目录，其中包含 `nollm-repository-memory/SKILL.md`。`user` 用于个人跨仓库使用；`repo` 用于单个 Git 工作树。表格列出默认配置。

| 宿主 / 安装参数 | 个人目录 | 仓库内目录 | 在助手中使用 |
| --- | --- | --- | --- |
| Codex / `codex` | `~/.agents/skills` | `.agents/skills` | 输入 `$nollm-repository-memory`，接上任务 |
| Claude Code / `claude` | `~/.claude/skills` | `.claude/skills` | 输入 `/nollm-repository-memory`，接上任务 |
| GitHub Copilot CLI / `copilot` | `~/.copilot/skills` | `.github/skills` | 用 `/skills info nollm-repository-memory` 查看位置，或用 `/nollm-repository-memory` 指定技能 |
| OpenCode / `opencode` | `~/.agents/skills` | `.agents/skills` | 提示“使用 nollm-repository-memory”，宿主通过 skill 工具加载；`opencode debug skill` 可检查发现结果 |

Codex、OpenCode 和 Copilot CLI 都支持表中的 `.agents/skills`。同一台机器或同一个仓库可以安装一次，三个宿主共享一份。Claude Code 可用其自身的目录。需要团队成员或云端仓库会话发现项目安装时，应按项目惯例把技能目录纳入版本控制，并确保会话能读取它。个人目录仅在相应宿主环境内生效。

以下两条是不同的安装示例。个人安装默认使用 `user`。项目安装可传工作树根或其子目录，省略 `--repo` 会使用当前工作树。

```sh
I=lab/nollm-lab/repository_memory/install_skill.py
python3 "$I" --host codex
python3 "$I" --host claude --scope repo --repo /path/to/project
```

其他宿主同样可使用标准技能包。可指定一个新的完整目录，例如 `python3 "$I" --dest /path/to/skills/nollm-repository-memory`。自定义宿主配置时，使用其实际的发现目录。目标目录已存在时安装器会退出，保留现有内容。使用打好的 ZIP 时，将其中的 `nollm-repository-memory` 文件夹直接放在表中一个根目录下。

## 从正常入口运行

在目标仓库启动助手。例如，在 Codex 中可以输入下面的请求。

```text
$nollm-repository-memory 接手这个仓库，概括各模块的职责，并核查与当前改动有关的证据。
```

也可描述具体行为问题，例如“给绑定附加第二条语句后，正常召回会返回哪一条？” 宿主可依据技能描述选择是否调用。请在技能指向的目录运行其 `scripts/memory.py`，将目标 Git 仓库作为 `--repo`。首次使用的仓库可以从盘点和采集开始。

若需单独检查安装，在一次新的安装中保存输出路径，然后从任意目录验证。

```sh
skill=$(python3 "$I" --host opencode --scope repo --repo /path/to/project)
python3 "$skill/scripts/memory.py" --help
python3 "$skill/scripts/memory.py" brief --repo /path/to/project --scope .
```

## 原生目录发现与交接实测

下列检查分别在隔离的用户目录和 Git 工作树运行。为每个范围比较安装前后的原生技能清单，并核对返回位置或范围。

| 实际 CLI 版本 | 发现入口 | 个人与项目范围的结果 |
| --- | --- | --- |
| Codex 0.167.0-alpha.4 | app-server 的 `skills/list` | 两个范围均启用，`user` 和 `repo` 返回对应的绝对路径 |
| Claude Code 2.1.327 | headless control `initialize` 的命令清单 | 安装后出现同名斜杠命令，来源分别为 `user`、`project` |
| GitHub Copilot CLI 1.0.114 | `copilot skill list --json` | 启用项的目录匹配，来源分别为 `personal-copilot`、`project` |
| OpenCode 1.19.6 | `opencode debug skill` | 两个范围的 `.agents/skills` 均返回对应的绝对路径 |

这些结果覆盖宿主的技能发现和注册。模型如何自动选择技能、云托管产品如何下发技能需要在相应会话中验证。本地交接回归使用两个独立安装：通过 Codex 目录中的 CLI 写入判断，再通过 Claude Code 目录中的 CLI 使用仓库默认清单召回；辅助证据改动提交后，Claude Code 目录的 CLI 会对这个键返回复核项。

已装对应 CLI 时，可从 Nollm 仓库根目录运行 `python3 lab/nollm-lab/repository_memory/comparison/check_skill_discovery.py codex`，将 `codex` 换为需要验证的宿主。安装和交接回归运行 `python3 -m unittest discover -s lab/nollm-lab/repository_memory -p test_skill_install.py`。

官方发现路径与调用方式可在下列文档核对。

- [Codex skills](https://developers.openai.com/codex/skills/) · [Codex 目录发现测试](https://github.com/openai/codex/blob/8e9746b19d20539ab3fbce5d69a4e0cd09b27305/codex-rs/ext/skills/src/host_roots_tests.rs)
- [Claude Code skills](https://code.claude.com/docs/en/skills) · [Claude Code 技能目录和加载记录](https://github.com/anthropics/claude-code/blob/154c06539c4309e172b8ce6f2b07388987617d68/CHANGELOG.md)
- [Copilot 支持的位置](https://github.com/github/docs/blob/1956c559c015c3871dfa60baecfe7637d894436f/content/copilot/concepts/customizations/agent-skills.md) · [Copilot CLI 调用和重载命令](https://github.com/github/docs/blob/1956c559c015c3871dfa60baecfe7637d894436f/content/copilot/how-tos/copilot-cli/customize-copilot/add-skills.md)
- [OpenCode 技能目录和发现规则](https://github.com/anomalyco/opencode/blob/f4e363c8295fa90a03dddc451882fffe8fbce357/packages/web/src/content/docs/skills.mdx)
