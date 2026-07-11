# Nollm M0：全仓模块归属审计与单仓 Package 分离任务书

**日期**：2026-07-11
**阶段编号**：M0 — Module Ownership and Monorepo Separation
**状态**：当前唯一允许执行的下一步任务
**上位架构**：`NOLLM_MULTI_PROJECT_MODULAR_ARCHITECTURE_CORRECTION_20260711.md`
**主环境**：Windows 10/11 + PowerShell
**执行方式**：大跨度任务 + 内部 Gate + 最终单一 Git bundle
**行为原则**：本阶段优先建立所有权和依赖边界，不继续产品功能扩张

---

# 0. 任务背景

当前 Nollm 仓库长期将以下不同职责混在同一运行路径中：

```text
几何 Core
Snapshot
Trace / Debug
Access policy
History
Audit
OpenClaw Adapter
实验与基准
发行与交付
Legacy / 迁移资产
```

由此产生：

```text
Core 被产品策略污染；
Trace 被当成事实状态；
Snapshot、History、Replay 混称；
Evidence、Admission、Audit 进入 Core；
实验对象升级为生产合同；
外置关系索引不断生长；
Python 固定规则模拟语义 Placement；
删除与迁移边界不清。
```

本任务只解决：

> **每个文件、对象、状态和 API 到底属于哪个模块，以及这些模块在单仓中怎样形成严格、可测试、可拆仓的边界。**

本阶段不是：

```text
OpenClaw Live Integration；
LLM Statement Formation；
新 Placement Corpus；
Geometry 行为重写；
历史策略实现；
审计产品实现；
立即拆分多个 GitHub 仓库。
```

---

# 1. 当前最高架构约束

## 1.1 多项目结构

Nollm 目标拆分为：

```text
nollm-core
nollm-snapshot
nollm-trace
nollm-access
nollm-history（可选）
nollm-audit（可选）
nollm-openclaw
nollm-lab
nollm-distributions
```

## 1.2 Core 边界

`nollm-core` 只负责：

```text
维护几何场当前状态；
执行确定性几何操作；
按几何入口进行有界 Recall；
提供 Snapshot Port；
提供 Observability Port；
保证当前状态写入原子性。
```

Core 不拥有：

```text
原文；
事实真实性；
当前事实；
历史版本；
用户；
会话；
权限；
Host；
LLM；
Prompt；
Placement 理由；
Trace 持久化；
Audit；
来源；
模型信息；
产品策略。
```

## 1.3 非 Core 不等于删除

所有现有文件必须先分类：

```text
CORE
SNAPSHOT
TRACE
ACCESS
HISTORY
AUDIT
OPENCLAW
LAB
DISTRIBUTION
LEGACY
DELETE
```

在完成归属审计前，不得把“不属于 Core”直接解释为“删除”。

## 1.4 当前明确错误方向

下列内容必须在归属清单中标为：

```text
BLOCKED / FUTURE REMOVAL
```

包括：

```text
承担主路径的外置关系索引；
Python hash / 固定评分语义 Placement；
Core 内 Host / Source / Session 策略；
Core 内 Trace/Audit 持久状态；
把 Snapshot 当语义历史；
把调试对象当生产事实。
```

本任务原则上不承担它们的完整功能删除，除非该代码可以在不改变运行行为、不丢失必要组件的情况下被安全隔离。

---

# 2. 基线处理

当前外部最后已知代码锚点：

```text
bundle:
nollm_grf8_real_data_productization_20260711_6c3a9230.bundle

HEAD:
6c3a923045a9a5c79bd2364c16ac792918497642
```

但用户已在其后暂停过一项长任务，实际开发机可能存在：

```text
新 commit；
未提交修改；
部分 OpenClaw 代码；
部分 Core Realignment 修改。
```

因此 Codex 不得强制回退到上述 HEAD。

---

# Gate 0：保全当前暂停状态

## 0.1 记录现场

在仓库根目录执行：

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git log -10 --oneline --decorate
```

保存到：

```text
docs/project/M0_STARTING_STATE.md
```

## 0.2 保护未提交修改

如果工作树不干净：

```text
1. 不丢弃；
2. 不 reset；
3. 不 checkout 覆盖；
4. 先检查是否包含密钥或机器生成缓存；
5. 对应保留内容做 checkpoint commit。
```

建议 commit：

```text
checkpoint(paused): preserve pre-modularization work
```

纯缓存、构建产物和临时日志不提交，应先加入正确 ignore 或移出工作树。

## 0.3 创建工作分支

```text
codex/m0-module-ownership-separation
```

若已经位于同名或等价分支，继续使用，不重复创建。

## Gate 0 PASS

```text
当前 HEAD 已记录；
暂停修改未丢失；
工作分支明确；
无 reset / clean -fd / 强制 checkout。
```

---

# Gate 1：更新 Codex 执行约束

替换仓库根目录 `AGENTS.md`：

```markdown
# Nollm Codex Rules

Execute the current taskbook exactly. Do not redesign or broaden scope.

- This stage is module ownership and monorepo separation only.
- Preserve all potentially useful components until ownership is proven.
- Classify before moving; move before deleting.
- Core owns geometry current-state operations only.
- Snapshot, Trace, Access, History, Audit, OpenClaw, Lab, and Distributions are separate modules.
- Do not add relation indexes, embeddings, semantic graphs, or Python semantic-placement logic.
- Do not run live OpenClaw, long LLM corpus jobs, or remote GitHub changes in this stage.
- Windows-first; fix ordinary failures inside the task.
- Deliver one clean Git bundle and a clean working tree.
```

## Gate 1 PASS

```text
AGENTS 简短；
不要求 Codex 读取 ChatGPT Source；
不允许扩展到 OpenClaw 或 LLM 长任务；
明确 classify-before-delete。
```

---

# Gate 2：全仓资产清单

## 2.1 扫描范围

至少扫描全部 Git tracked：

```text
Python source
TypeScript / JavaScript source
tests
scripts
protocol
docs
examples
experiments
fixtures
OpenClaw integrations
package metadata
root navigation
release / delivery artifacts
```

排除：

```text
.git
virtualenv
node_modules
__pycache__
build output
临时模型运行结果
未跟踪本机缓存
```

## 2.2 所有权清单

生成：

```text
docs/architecture/module-ownership/MODULE_OWNERSHIP_MANIFEST.csv
docs/architecture/module-ownership/MODULE_OWNERSHIP_MANIFEST.json
```

每一行至少包含：

```text
path
file_type
current_namespace
owner
secondary_owner
lifecycle_status
runtime_role
owned_state
public_api
imports
imported_by
migration_action
confidence
reason
```

合法 `owner`：

```text
CORE
SNAPSHOT
TRACE
ACCESS
HISTORY
AUDIT
OPENCLAW
LAB
DISTRIBUTION
LEGACY
DELETE
```

合法 `lifecycle_status`：

```text
ACTIVE
CANDIDATE
MIGRATION_ASSET
BLOCKED
HISTORICAL
GENERATED
```

合法 `migration_action`：

```text
KEEP
MOVE
SPLIT
WRAP_TEMPORARILY
QUARANTINE
DELETE_LATER
DELETE_NOW
```

## 2.3 归属置信度

```text
HIGH：
职责单一、依赖清楚，可以移动。

MEDIUM：
主要职责清楚，但与其他模块耦合。

LOW：
职责混合、用途不明或可能仍含迁移价值。
```

规则：

```text
LOW 不能 DELETE；
LOW 默认进入 LEGACY / QUARANTINE；
MEDIUM 必须形成拆分建议；
HIGH 才可在本任务内实际移动。
```

## 2.4 100% 覆盖

生成：

```text
UNCLASSIFIED_TRACKED_FILES.txt
```

Final Gate 时必须为空。

## Gate 2 PASS

```text
Tracked 活动资产 100% 分类；
LOW 文件未删除；
每个文件都有理由；
relation index / Python semantic placement 已标记 BLOCKED。
```

---

# Gate 3：模块章程和状态所有权

为每个模块生成：

```text
docs/architecture/modules/NOLLM_CORE_CHARTER.md
docs/architecture/modules/NOLLM_SNAPSHOT_CHARTER.md
docs/architecture/modules/NOLLM_TRACE_CHARTER.md
docs/architecture/modules/NOLLM_ACCESS_CHARTER.md
docs/architecture/modules/NOLLM_HISTORY_CHARTER.md
docs/architecture/modules/NOLLM_AUDIT_CHARTER.md
docs/architecture/modules/NOLLM_OPENCLAW_CHARTER.md
docs/architecture/modules/NOLLM_LAB_CHARTER.md
docs/architecture/modules/NOLLM_DISTRIBUTIONS_CHARTER.md
```

每份章程必须回答：

```text
模块目的；
拥有的持久状态；
允许的运行时临时状态；
公共 API；
禁止 API；
允许依赖；
禁止依赖；
失败是否影响 Core correctness；
进入哪些发行版；
未来独立 Git 仓库名称；
当前代码迁移来源。
```

---

## 3.1 nollm-core

拥有：

```text
GeometryKernel
CoverageTemplate
整数坐标和分区函数
CellStore
局部 occupancy
Bridge/Stitch runtime
Bounded Recall
Atomic batch
Crash-safe current state
Snapshot Port
Observability Port
```

不拥有：

```text
LLM
Host
Session
User
Source
History semantics
Audit
Trace store
Product policy
```

建议最小对象：

```text
MemoryAtom:
  atom_id
  payload_utf8

AtomHandle:
  geometry_address
  local_atom_id
```

注意：

```text
该对象只是合同候选；
本任务不强制重写全部运行代码；
必须先记录现有对象到该候选合同的迁移差异。
```

---

## 3.2 nollm-snapshot

拥有：

```text
create
restore
clone
verify
structural diff
optional incremental snapshot
```

Snapshot 不判断：

```text
当前事实；
历史事实；
正式版本；
审计效力；
保留期限。
```

---

## 3.3 nollm-trace

拥有：

```text
TraceSink implementations
operation events
Cell mutation trace
Coverage/frontier trace
Bridge traversal trace
budget/cache/partition events
performance metrics
inspectors
debug replay inputs
```

Core 只暴露：

```text
TraceSink.emit(event)
```

默认：

```text
NullTraceSink
```

Trace 失败不得改变 Core 结果。

---

## 3.4 nollm-access

拥有：

```text
怎样形成 MemoryStatement；
怎样做 Placement；
怎样选择 Recall 入口；
怎样格式化 Recall；
当前/历史策略；
Source policy；
用户、会话和产品策略；
Core Handle 保存。
```

Access 决策映射：

```text
reuse → no write
new → put
revision-current → replace / remove + put
revision-keep-history → keep old + put new
stitch → bridge_add
defer → no write
forget → remove
```

Core 不知道这些动作的业务意义。

---

## 3.5 nollm-history

可选，拥有：

```text
语义版本链
时间线
历史检索
与 Snapshot 的产品级关联
```

History 不等于 Trace。

---

## 3.6 nollm-audit

可选，拥有：

```text
Host/User/Session 操作记录
外部 Source handle
模型/Prompt
Access 决策
Core command result
审计报告
```

Core 不依赖 Audit。

---

## 3.7 nollm-openclaw

拥有：

```text
typed hooks
Plugin manifest
Tools
Skills
llm-task
Session mapping
queues
statement formation
placement
Recall injection
install/update/logging/diagnose
```

---

## 3.8 nollm-lab

拥有：

```text
corpora
gold labels
math validation
benchmarks
stress tests
migration tools
compatibility tests
visualization
failure injection
baselines
```

Lab 可以依赖全部模块，反向依赖禁止。

---

## 3.9 nollm-distributions

只组装：

```text
nollm-bare
nollm-minimal
nollm-openclaw
nollm-debug
nollm-audited
```

不得实现业务逻辑。

## Gate 3 PASS

```text
九个模块章程完成；
状态所有权无冲突；
Snapshot/Trace/History/Audit 定义互不混淆；
依赖方向明确。
```

---

# Gate 4：依赖图与防火墙

## 4.1 目标依赖方向

```text
core ← snapshot
core ← trace contracts/ports
core ← access
access ← history
access ← audit（通过公共合同）
access ← openclaw
all modules ← lab
modules ← distributions（仅组装）
```

更严格规则：

```text
Core 不依赖任何其他 Nollm 产品模块；
Snapshot 只依赖 Core public ports；
Trace implementation 只依赖 Core trace contracts；
Access 只依赖 Core public API，可选使用 Snapshot public API；
History 依赖 Access contracts，可选依赖 Snapshot；
Audit 依赖 Access contracts，可选依赖 Trace contracts；
OpenClaw 依赖 Access，不访问 Core private；
Lab 可依赖全部；
Distributions 只声明组合。
```

## 4.2 自动检查工具

新增：

```text
tools/check_module_boundaries.py
```

或适合当前仓库语言的等价工具。

必须检查：

```text
Python import
TypeScript package import
循环依赖
Core private import
OpenClaw → Core private
Lab 被生产模块 import
Distribution 含业务逻辑
```

## 4.3 规则文件

生成：

```text
config/module-boundaries.json
```

不得把规则只写在文档中。

## 4.4 基线报告

首次运行可存在违规，但必须：

```text
完整列出；
逐项映射到迁移动作；
不以删除测试隐藏违规。
```

高置信度、低风险的边界违规在本任务内修复。

会改变业务语义的违规：

```text
记录为 M1 follow-up；
不得在 M0 偷偷重写。
```

## Gate 4 PASS

```text
自动防火墙可运行；
循环依赖清单生成；
Core 禁止依赖得到机器检查；
剩余违规有明确 owner 和下一阶段。
```

---

# Gate 5：建立单仓 Package 骨架

建立目标目录。根据当前仓库语言和构建系统可做等价调整，但职责不能变化：

```text
packages/
  nollm-core/
  nollm-snapshot/
  nollm-trace/
  nollm-access/
  nollm-history/
  nollm-audit/

integrations/
  openclaw/

lab/
  nollm-lab/

distributions/
  nollm-bare/
  nollm-minimal/
  nollm-openclaw/
  nollm-debug/
  nollm-audited/

legacy/
  quarantine/
```

## 5.1 只移动 HIGH 置信度文件

本阶段实际移动：

```text
职责明确且不改变语义的 Snapshot 文件；
职责明确的 Trace/metrics/inspector 文件；
明确的 OpenClaw Adapter 文件；
明确的实验、数据集、benchmark、迁移脚本；
明确的 distribution/package 文件。
```

## 5.2 Core 大规模移动纪律

若当前 Core 文件职责混杂：

```text
不得整文件盲目移动；
先标记 SPLIT；
只抽取纯合同或纯工具部分；
业务重写留给 M1。
```

## 5.3 临时兼容入口

为了保持当前测试和导入可用，允许：

```text
旧公共 import path → 新 package public API 的薄 re-export
```

限制：

```text
只能 import/re-export；
不得包含业务逻辑；
必须集中在 compat 目录；
必须列入 COMPATIBILITY_REEXPORTS.md；
必须注明后续删除阶段。
```

不允许用兼容层保留错误关系索引或 Python 语义 Placement。

## 5.4 LEGACY Quarantine

LOW 置信度和混合职责代码移动到：

```text
legacy/quarantine/
```

仅当：

```text
当前生产路径已经不依赖；
对应测试/研究价值仍可能存在；
Manifest 记录恢复方式。
```

若当前生产路径仍依赖，则保持原位并标记：

```text
LEGACY_PENDING_EXTRACTION
```

## Gate 5 PASS

```text
Package 骨架存在；
HIGH 置信度资产完成移动；
LOW 资产未丢失；
兼容入口无业务逻辑；
当前导入路径可运行。
```

---

# Gate 6：Snapshot 和 Trace 的最小公共 Port

本阶段不重写全部实现，只建立最小、稳定、无业务策略的 Port。

## 6.1 Snapshot Port

Core 暴露候选合同：

```text
begin_consistent_read()
export_state()
import_state()
end_consistent_read()
```

具体命名可根据现有代码调整。

要求：

```text
Core 不 import snapshot implementation；
Snapshot module 使用 public port；
现有 snapshot 行为保持；
结构 diff 不做语义判断。
```

## 6.2 Trace Port

Core 暴露：

```text
TraceSink.emit(event)
```

提供：

```text
NullTraceSink
```

`nollm-trace` 提供：

```text
JsonlTraceSink
ConsoleTraceSink
MemoryTraceSink
MetricsTraceSink
CompositeTraceSink
```

要求：

```text
关闭 Trace 后结果相同；
TraceSink 抛错不得损坏 Core；
事件合同区分 stable/internal/experimental。
```

## Gate 6 PASS

```text
Snapshot 和 Trace 不再与 Core 状态混为一体；
现有 Snapshot 测试保持；
NullTrace 与有 Trace 结果一致。
```

---

# Gate 7：发行组合清单

生成：

```text
distributions/DISTRIBUTION_MATRIX.md
distributions/distribution-matrix.json
```

组合：

## nollm-bare

```text
core
```

## nollm-minimal

```text
core
snapshot
minimal access API
```

## nollm-openclaw

```text
core
snapshot
access
openclaw
```

## nollm-debug

```text
nollm-openclaw
trace
inspector
selected lab tools
```

## nollm-audited

```text
nollm-openclaw
trace
audit
optional external source-store connector
```

必须明确：

```text
哪些是正式运行依赖；
哪些是可选；
哪些只在开发环境；
Trace/Audit 关闭后 Core correctness 不变。
```

## Gate 7 PASS

```text
五种发行组合定义清楚；
无业务逻辑写入 distributions；
最小版和调试版边界可验证。
```

---

# Gate 8：未来 Git/GitHub 拆仓计划

本阶段不创建远端仓库、不 push、不拆当前 Git 历史。

生成：

```text
docs/project/NOLLM_FUTURE_REPOSITORY_SPLIT_PLAN.md
docs/project/NOLLM_REPOSITORY_COMPATIBILITY_MATRIX.md
```

## 8.1 未来仓库

建议：

```text
nollm-core
nollm-snapshot
nollm-trace
nollm-access
nollm-openclaw
nollm-lab
nollm-distributions
```

可选：

```text
nollm-history
nollm-audit
```

## 8.2 拆仓前置条件

```text
Core Handle API 稳定；
Snapshot Port 稳定；
TraceSink API 稳定；
Access/Core command mapping 稳定；
无循环依赖；
每个 package 独立测试可运行；
至少一次完整 OpenClaw E2E 通过。
```

## 8.3 历史保留方案

提供 Windows 可执行方案，例如：

```text
git filter-repo
或
git subtree split
```

只写计划和验证命令，不实际操作远端。

## 8.4 版本策略

定义：

```text
独立 SemVer；
兼容矩阵；
Distribution 锁定组合；
breaking Core API 的迁移规则；
Snapshot 格式版本；
Trace event 非稳定部分的兼容原则。
```

## Gate 8 PASS

```text
拆仓计划完整；
没有远端副作用；
接口稳定条件明确；
Git 历史保留方法可执行。
```

---

# Gate 9：根文档和当前状态

更新：

```text
README.md
ARCHITECTURE.md
ROADMAP.md
docs/project/NOLLM_CURRENT_STATUS.md
```

必须明确：

```text
当前是模块化单仓阶段；
未物理拆 GitHub；
OpenClaw Live Integration 暂停；
旧 Evidence-first V2 文件为历史参考；
GRF8 是工程 checkpoint，不是 accepted architecture；
M1 才处理 Core 语义重构和错误路径删除。
```

旧文件不得物理删除，但应标记：

```text
HISTORICAL / SUPERSEDED
```

尤其：

```text
V2.1 Evidence/Capture/Admission Core；
V2.2 Evidence-first Core；
旧 GRF handoff；
旧 OpenClaw Live Integration tasks；
旧 raw-slice / source-fallback tasks。
```

## Gate 9 PASS

```text
根导航只指向当前模块化架构；
旧路线不会被误读为活动约束；
当前下一步明确。
```

---

# Gate 10：行为保持与回归

## 10.1 本阶段不运行

```text
OpenClaw live update
真实模型长运行
旧 348 corpus
新 Statement corpus
远端 GitHub 操作
PB/1M 长压测
```

## 10.2 必须运行

根据实际仓库执行：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
```

至少：

```text
现有 GRF 单元测试；
Snapshot 测试；
Trace Port 测试；
Import boundary 测试；
Package import smoke；
Repository hygiene；
git diff --check。
```

若现有完整测试因环境依赖失败：

```text
记录执行命令；
记录失败数量；
区分代码失败与环境失败；
不得通过删除测试缩小范围。
```

## 10.3 行为对比

生成：

```text
docs/validation/M0_BEHAVIOR_PRESERVATION_REPORT.md
```

比较：

```text
迁移前测试；
迁移后测试；
公共 import；
Snapshot；
Recall；
当前 Host fixture。
```

## Gate 10 PASS

```text
主要行为未被 M0 改写；
模块移动没有丢失组件；
现有失败有明确分类；
无测试被偷偷删除。
```

---

# Final Gate

必须满足：

```text
1. M0_STARTING_STATE 已提交；

2. 所有 tracked 活动文件完成归属分类；

3. UNCLASSIFIED_TRACKED_FILES.txt 为空；

4. 九个模块章程完成；

5. 自动依赖防火墙可运行；

6. Package 骨架建立；

7. HIGH 置信度资产已移动；

8. LOW 资产未删除；

9. Snapshot Port 与 Trace Port 建立；

10. 五种发行组合定义完成；

11. 未来 GitHub 拆仓计划完成；

12. OpenClaw Live、LLM corpus、远端拆仓均未误启动；

13. 主要行为保持；

14. 工作树干净。
```

仅全部满足时输出：

```text
NOLLM_M0_MODULE_SEPARATION_ACCEPTED_CANDIDATE
```

---

# 真实停止条件

仅以下情况停止并回报：

```text
当前暂停工作树无法安全保全；
Git 仓库存在损坏；
必要源文件缺失，无法完成归属审计；
构建系统无法表达任何模块边界；
现有代码存在无法隔离的循环依赖且必须重新设计公共 API；
高置信度移动必然改变核心行为。
```

以下不是停止条件：

```text
某些文件难以判断归属；
现有测试有环境失败；
文档过时；
目录命名不统一；
兼容 import 需要薄 re-export；
旧组件数量多。
```

这些应分别进入：

```text
LEGACY
MEDIUM/LOW confidence
follow-up issue
```

---

# 建议 Checkpoint Commits

```text
checkpoint(paused): preserve pre-modularization work

docs(m0): establish module ownership model

chore(m0): inventory repository assets

arch(m0): define module charters and dependency rules

refactor(m0): create monorepo package boundaries

refactor(snapshot): expose snapshot port

refactor(trace): expose optional observability port

build(distributions): define composable runtime variants

docs(project): plan future repository split

test(m0): verify boundaries and behavior preservation
```

---

# 最终交付

只交付：

```text
nollm_m0_module_ownership_monorepo_separation_20260711_<shorthead>.bundle
```

要求：

```text
完整 Git 历史；
工作树干净；
任务书、Manifest、章程、报告已提交；
不附加 receipt、capsule、SHA 文档或外部 evidence pack。
```
