# Nollm 自身的 AOCI 工程索引

本卷以 Nollm 提交 `691590dcc6009b59a9cf51dfe7a9e7a7516eca0b` 为对象。打开 `aoci.code.txt` 可以按源码目录阅读。在新检出中使用官方 AOCI CLI 或 MCP，可以查询条目、检查版本和维护说明。索引放在 Lab，方便重复对照同一版源码。

## 打开

需要本地 Nollm Git 仓库、Python 3.11+ 和 AOCI-CODE CLI。研究使用官方 `0.2.0-rc2`。[下载该版 AOCI](https://github.com/aoci-spec/aoci-code/releases/tag/v0.2.0-rc2)

从 Nollm 仓库根运行，最后一个参数指定一个尚未存在的目录。

```sh
python3 lab/nollm-lab/repository_memory/self_study/aoci/open_study.py /tmp/Nollm-aoci-study
aoci --repo /tmp/Nollm-aoci-study check
aoci --repo /tmp/Nollm-aoci-study verify
aoci --repo /tmp/Nollm-aoci-study index agent guide --agent codex --json
```

使用主机的 MCP 客户端时，服务器命令为 `aoci --repo /tmp/Nollm-aoci-study mcp`。可执行文件不在 PATH 时，为 Python 命令指定 `--aoci /path/to/aoci`。打开工具先验证三份标准卷的 SHA-256，再检出固定 Git 树，建立本地指纹并核对 AOCI 的复合标识。安装产生的本地运行日志保存在新检出中。

## 工程说明怎么读

每个条目使用 AOCI 原生标签和 F/R/A/S。F 给出文件职责，R 列出有证据的相关文件，A 列出所选接口，S 记录修改时容易破坏的约束。Core 和 Access 的 44 个 Python 源文件均有按源码整理的职责。其中，`surface.py` 记录多父成员关系和下钻，`approximate_coverage.py` 记录生产采样和舍入，`surface_navigation.py` 记录何时能打开物理入口。21 份实现条目同时指向仓库内对应测试。其余大量条目依据模块文档、声明、导入、测试名称、配置键和文档标题生成，适合初步定位；具体行为仍可循路径核对。

官方全量 scope 盘点了 907 个跟踪文件，903 个进入正式 Code 卷，包括全部 593 个 Python 文件。两个空文件和两份超过 AOCI 大小阈值的治理清单列在 `study.json` 的 `source_skip`。该文件亦记录目录分布、各字段覆盖、官方批写闭环及校验结果。903 个 F、503 个含 R、440 个含 A、13 个含 S。缺少高价值约束的条目使用原生 `S:-`。

## 复核

首次构建经官方 `aoci_maintain` 和 `aoci_update_entry` 连续写入 23 批，最后一次 Apply 返回 aligned 与 check_passed。独立新检出从固定源码和正式卷重建后返回相同复合标识。仅编辑 `approximate_coverage.py` 后，原生 verify 标记该路径 stale 并退出 1；恢复文件字节后再次 aligned。这项检查针对源码与条目的同步状态。与空间检索的效果对照见上级研究报告。
