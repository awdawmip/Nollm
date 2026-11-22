# Nollm PR #7 独立实现复测

日期：2026-11-21。候选：`awdawmip/Nollm@34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766`。比较基线：研究试验 `f038edcae50594a705e0886c7818c27579d79154`，原运行库 `ddf7dc00b2cea43dccc5d783d20aa88e21de4e0b`。

## 结论

本地候选确实改善了导航，并实现了可撤销的有向物理格连接。独立复测重现：128 格中心在 14 个逻辑导航页内到达，512 格中心在 17 页内到达；同一 128 格场固定旧页宽 3 后仍于第 24 页耗尽。恢复游标删除了从根开始的整条路径重放，连续 `next` 只渲染新页；点选窗口仍会重建当前页并产生下页，故不能表述为完全没有重建。

现有三个受影响回归和四组新增行为断言均通过，没有在本轮有信息量的实测中发现需要修改候选产品代码的缺陷。本报告只确认本地候选能力，未部署线上、未写入线上工作场、未改变远端仓库，也不把该工程能力当成新定理接纳或研究质量优势。

## 依据与实际改动

从当前固定提交读取了 [AGENTS.md](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/AGENTS.md)、[README 的 Project understanding](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/README.md#project-understanding)、[ACTIVE_PROJECT.md](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/docs/project/ACTIVE_PROJECT.md) 和[第一性原则](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md)。沿用根代理已核阅的 GK 入口与代码规范，不重启科研领取或数学任务。

GitHub connector 比较确认：从旧运行库到此候选，运行逻辑只修改了以下两个文件；Core、Access 和其持久格式没有改动。

| 文件 | 实际新增能力 | 边界 |
|---|---|---|
| `lab/nollm-lab/repository_memory/coverage_cli.py` | 在旧窄页软目标溢出时评估起始阶与页宽；返回预算信息；序列化、恢复本页游标；连续翻页直接使用 continuation | 规划值是估计，子页可能额外翻页；无游标的完整 choices 仍按旧方式回放 |
| `lab/nollm-lab/repository_memory/enterprise_math/research.py` | `walk` 传递游标；CLI 保存临时游标；`stitch` / `unstitch`；`via=connected` 允许一次桥传播 | Stitch 是当前物理格间的有向关系；默认 `local` 不使用桥；不判断数学命题有效性 |

源代码：[coverage_cli.py](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/lab/nollm-lab/repository_memory/coverage_cli.py)、[research.py](https://github.com/awdawmip/Nollm/blob/34c16d166bf8e232fc8c1c35ff9c6d6ed1dbd766/lab/nollm-lab/repository_memory/enterprise_math/research.py)。其余变化是文档、研究试验材料和针对性回归。

## 实际执行结果

### 安装、CLI、直接 API 与既有 Coverage

独立 source 副本运行 `python -m unittest -v test_enterprise_math test_enterprise_math_api test_coverage_install`，3 项通过，64.308 秒。这些测试实际安装 portable skill，通过独立子进程读写临时场，并覆盖固定 Git 原文窗口、旧版/新版绑定、邻域排除、研究 CLI 游标恢复、桥撤销和原有跨层 Coverage。

原始观察摘录与命令保存在 `regression-results.txt`。未重复执行无关 Core 全套、全仓治理或旧研究矩阵。

### 独立游标、缓存与场变化探针

自编 `audit_native.py behavior` 使用显式合成语句与物理位置，未用作者报告充当预期结果。`behavior-results.json` 保存逐步输入效果和渲染计数。

| 动作 | 游标路径实际渲染 | 同一 choices 从根回放 | 结果 |
|---|---:|---:|---|
| 初始页 | 1 | 1 | 取得首屏 |
| 一次 `next` | 1 | 2 | 页、候选 ID 与回放一致 |
| 点选已显示的零阶窗口 | 2 | 3 | 重开本页，再产生物理菜单；结果与回放一致 |
| 点选物理入口 | 1 | 3 | 仅重开物理菜单；最终唯一入口与召回一致 |

四组行为断言全部通过：

1. 清空 Surface order cache 和 physical Coverage cache 后，旧物理游标重建出相同候选页；`core/current_state.json` 与 `access/bindings.json` 原始字节保持不变。这验证本次路径的正确性不依赖不可删除的缓存。
2. 将 `A.v1` 原位更正为 `A.v2` 后，同一个旧物理游标展示新版首行并实际召回新版；旧语句仍可读取且 `current=false`，没有把缓存中的旧文本当成当前结果。
3. 在原首屏之前加入新占用格后，旧游标重开当前场的新首屏；原先已移出本页的候选 ID 被普通 `ValueError` 拒绝，没有静默选成另一格。这是可恢复的场变化语义，不是快照游标。
4. 加入 `A→B` 后，从 A 的同一物理入口通过 `bridge` 召回 B；从 B 反向没有召回 A；默认 `local` 结果保持原样。B 所在格中的 `B.peer` 一起被召回；B.v1 更正为 B.v2 后桥自动通向当前版本，旧版仍保留。撤销桥后，A 的整个 connected 召回返回值与连接前完全相同。

### 独立导航规模探针

同一个明确规则生成 128 和 512 个合成独立语句，每格一条。目标由已知物理坐标及显示窗口的 source memberships 选择；这是一种公开声明的几何 oracle，用于区分菜单规划与语义判断，不能解释成 LLM 的研究正确率。

| 场规模与策略 | 实际起始阶 / 页宽 | 中心目标逻辑页 | 实际成功渲染次数 | 结果 |
|---|---:|---:|---:|---|
| 128，自适应默认 | 6 / 4 | 14 | 22 | 到达中心并取回目标语句 |
| 128，固定旧窄页 3（失败试验） | 8 / 3 | 24 | 32 | 仍停在一阶窗口，下一步重开本页后报调用预算耗尽 |
| 512，自适应默认 | 8 / 8 | 17 | 27 | 到达中心并取回目标语句 |

成功路径数据文件为 `scale-results-128.json` 和 `scale-results-512.json`。失败试验的总成本以 `scale-narrow-failure-renders.json` 为准：最初 instrumentation 在异常返回时漏计该次已完成的本页重建，原始文件中的 31 予以保留并在此更正；仅复跑这个窄页失败 case 后确认总数是 32，其中最后一次是在预算报错前重建一阶第 24 页。24 页是逻辑导航预算，并不等于所有底层重建工作总共只能渲染 24 次。若服务仍把历史 choices 全部传回而不保存 cursor，仍然会产生整条路径回放；仅升级候选库不会自动消除宿主调用方式的成本。

512 场首屏显示 `root_plus_descent=26`，超过 24，因所有估计都超限而回退到页宽 8；中心成功不能推出全场全部目标可达。代码注释和 README 已如实说明此估计不是预算保证。本次又在相同已建场上测试边缘物理格 `[0,12,0]`（fixture 468），以 10 页 / 20 次渲染到达。随后按明确规则选择“在全部八阶根窗口中，首次出现在最靠后位置的物理目标”：`[0,-13,2]`（fixture 471），最早出现于第 77 个根窗口，实际以 19 页 / 29 次渲染到达。两个边缘目标也通过，不应把保守估计 26 直接当成失败事实；它们仍不是全域预算证明。数据：`scale-results-512-target-468.json`、`scale-results-512-target-471.json`，选择规则为 `hard-target-selection.json`。至此停止扩测。

规模脚本第一次运行时，测试 harness 请求了超出现有 Core 上限的 10000 页宽，构造完场后报错。修正 harness 为原生 256 分页后，复用已构造的两个场继续完成实测；这不是候选产品缺陷，也没有隐去失败或为复测重新形成全部记忆。

## 对研究与中控台的实际含义

**已成立的工程收益**是省去历史路径反复计算、让原先失败的中心导航恢复、在不改证据文本和 Core 格式的情况下添加/撤销跨格联系，以及让原位修订立即影响读取。它们值得接入宿主，但服务端需要真实贯通 `cursor`、预算和 `connected` 行为；线上何时升级由部署证据另行判断。

**新发现进入记忆的能力**仍然是 Host 提供有意义的正文、固定来源窗口、物理放置或修订判断。写入后能被另一会话原生召回，不等于该发现自动成为研究成果库中的已接纳定理。`current` 是当前工作场的绑定状态，不是来源库最新状态，也不是数学审查结论。

**Stitch 的含义**是给后续询问一条有界物理到达路径。目标同格其他语句也会命中，修订后桥继续存在，这与第一性原则一致。需要迁移哪些操作、前提是否仍满足、修订是否要求撤销连接，都由 Host 根据两端证据判断。不要在 Core 上加一个与几何平行的语义图或自动证明关系系统。

**本轮没有证明的优势**包括：真实研究问答准确率优于相同内容的平面记忆、形成与维护成本之后的净 token 节省、未知任务下的全场预算保证。当前独立实测是具体功能验收，不扩展为这些更强结论。

## 可复现位置

根目录：`/workspace/scratch/4eeff3663e39/nollm_intake_audit_20261121/native/`。

- `source/`：独立候选源码；旧基线目录未修改。
- `runtime/scripts/runtime/`：独立安装形态的候选运行库，供其他代理复用验证。
- `audit_native.py`：独立行为与规模探针。
- `behavior-results.json`、`scale-results-*.json`：实际观察结果。
- `regression-results.txt`：三项回归和 harness 修正的执行记录。

复跑时可给 harness 传 `--work-dir /path/to/new-audit-dir`，在新目录生成 fixture 和结果而保留本轮证据；例如 `python audit_native.py behavior --work-dir /tmp/nollm-new-audit`，然后 `python audit_native.py scale --count 128 --work-dir /tmp/nollm-new-audit`。如复用同一已建 scale fixture，显式传 `--reuse`。无需改动候选运行库或清理已有结果。

候选产品源码没有加入本轮补丁。测试 fixture 仅在本地独立目录创建，未触及线上记忆。
