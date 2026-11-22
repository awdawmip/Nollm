# 从 AOCI-CODE 的用法到 Nollm 仓库记忆

当前 Nollm 开发使用[速记本](../../../sujiben/README.md)，通过 Surface、Host 选择、单一物理入口和局部事实继续形成理解。AOCI 用于工程观察与回源；它的对象目录、标签和引用不替代原生几何关系。现行命令入口见 [Repository Memory](README.md)。

对照版本为 AOCI-CODE 提交 `5be709e`。它面向需要长期理解和维护的代码库。已有项目可以从接手一个模块开始；新项目可以先写出可运行的原型，等到出现需要跨会话保留的决定再记录。写说明时可以问四个实际问题：这个模块负责什么，改它会影响谁，对外承诺了什么，哪条约束容易被漏掉？[上游开发流程与条目说明](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/README.md#how-a-development-task-runs)

| 当前要做的事 | AOCI-CODE 的做法 | Nollm skill 中的操作 |
| --- | --- | --- |
| 首次接手已有仓库 | 划定管理范围、扫描基线，由宿主读源码并撰写条目 | 用 `project --field FIELD encounter` 观察已有理解；需要源码盘点时显式使用 `aux brief --scope DIR`、`aux inventory`，核实后回到局部形成判断。`aux capture` 仍可维护辅助清单 |
| 理解总体设计或评估跨模块改动 | 在已对齐的索引上读取完整全景，并按任务查看实现 | 从原生场观察跨文件判断并回到契约、调用方和测试；`aux view` 仅用于显式阅读辅助清单 |
| 接手局部故障或小改动 | 结合全景中的工程理解与当前证据工作 | 用 `project --field FIELD encounter` 选择一个物理入口，阅读局部判断后以 `project source` 回到固定版本；已知符号也可直接搜索源码并记录辅助使用 |
| 改动结束，准备交给下一会话 | 按变更增量维护索引，用 `verify` 和 `check` 检查对齐 | 确定代码提交，核查受影响的原生判断并决定支持、修订或新增；维护辅助清单时显式用 `aux review` 和 `aux capture`。交接时说明实际版本和待复核项 |

AOCI-CODE 对管理范围内的对象区分建条目、观察或排除；其中普通全景读取可分块，但目标仍是送达完整的正式索引。Nollm 的 `aux inventory` 显示已有主证据、辅助证据和未记录文件。Nollm 的 `aux view` 覆盖当前清单中有效的条目，一份局部清单能说明的范围取决于已经读过并记录的证据。[上游范围与预算](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/docs/managed-scope-and-budget.md) · [全景交付](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/docs/overview-delivery.md) · [首次构建和日常维护](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/docs/getting-started.md)

**宿主接入。** AOCI-CODE 通过 CLI、项目说明和 MCP 工具接入。安装器为 Codex、Claude Code 和 OpenCode 写入各自的 MCP 配置，给 Cursor 输出手动配置片段。Nollm 把说明和 Python 命令打包成 Agent Skill，宿主用本机的 Git 与 Python 对目标仓库工作。两类安装步骤各自对应自己的工具。[上游宿主接入文档](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/docs/agent-integrations.md) · [上游安装器实现](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/internal/hooks/installer.go#L268-L339) · [Nollm 安装与使用](README.md)

**证据范围。** AOCI-CODE 另有可选的数据库目录元数据采集。Nollm 此 skill 核对本地 Git 中的普通文件，例如项目提交的迁移脚本、schema 定义和契约测试。关于已部署数据库或运行中服务的结论需要相应的运行时证据。早期三种阅读方式已有 Nollm 内部试改记录，AOCI-CODE 仅作为工作方法参考，未参加这组计时和评分。[上游数据库证据说明](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/docs/database-evidence.md) · [Nollm 历史试改记录](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/comparison/README.md)

## 历史记录：在 AOCI-CODE 仓库实跑一次交接

以下保留原清单流程的实测观察。完整旧报告和配套材料由 `archive/legacy-code-20261122` 的固定 [beaafab 快照](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/AOCI_COMPARISON.md)保留；当时的清单命令现在属于显式 `aux` 路径。

在上述固定提交的临时副本里，从一个项目级安装启动 Nollm skill。没有初始清单，`brief` 盘点出 1,722 个跟踪文件；限定 `internal/cli` 后是 154 个。`internal/hooks` 中另有 19 个文件。接手者实际读取 CLI 初始化、宿主安装分派和三个测试文件，写入键 `init-cursor-in-installed-agents`。判断指出，`init --agent all` 会将 Cursor 列入已处理宿主，Cursor 分支给出手工配置片段，因此这张名单不足以证明 MCP 已连接。[初始化入口](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/internal/cli/init.go) · [宿主分派](https://github.com/aoci-spec/aoci-code/blob/5be709e62d93861f56257e7ee7066f5d64d576c3/internal/hooks/installer.go#L268-L339)

随后从子目录发起局部召回，工具自动找到根清单，五份证据逐字节匹配原始 Git blob。在临时副本只给辅助文件加一行注释并提交后，`review` 指向该文件，当前召回返回 `no_match`，指定原核阅提交仍能读回五份相同证据。这个试验运行的是 Nollm 安装、记录、召回和失效流程；AOCI 的 Go 测试在此处作为阅读材料。
