# Nollm M0-C1：所有权清单真实性、真实 Port 绑定与回归闭合任务书

**日期**：2026-07-11
**阶段编号**：M0-C1 — Ownership Truthfulness / Real Port Binding / Regression Closure
**状态**：M0 Bundle 审核未通过后的唯一下一任务
**基线 Bundle**：`nollm_m0_module_ownership_monorepo_separation_20260711_76eb10dc.bundle`
**基线 HEAD**：`76eb10dc37260f5c623398baceeea5b846813592`
**建议分支**：`codex/m0c1-ownership-port-regression-closure`
**主环境**：Windows 10/11 + PowerShell
**执行方式**：大跨度任务 + 内部 Gate + 最终单一 Git bundle
**交付目标**：闭合 M0，不进入 M1，不恢复 OpenClaw Live，不运行长 Corpus

---

# 0. 审核结论与本任务定位

M0 Bundle 的 Git 完整性、暂停现场保全、模块章程、目录骨架、发行组合、拆仓计划和基础防火墙均具有保留价值。

但当前不能输出：

```text
NOLLM_M0_MODULE_SEPARATION_ACCEPTED_CANDIDATE
```

原因不是文档小偏差，而是 M0 的三项基础事实尚未成立：

```text
1. MODULE_OWNERSHIP_MANIFEST 不能可靠代表真实所有权；
2. Snapshot / Trace Port 尚未绑定实际 GRF 行为；
3. 根架构已经切换，但现有架构回归测试仍断言旧 V2 是唯一活动架构。
```

M0-C1 只修复这些闭合问题。

M0-C1 不得扩展为：

```text
M1 Core/Access 语义重构；
OpenClaw Live Integration；
真实 LLM Placement 运行；
新的 Placement Corpus；
大规模删除 relation/index/source/history 代码；
远端 GitHub 拆仓；
新的产品功能；
PB/1M 长压测；
安全供应链、Evidence Capsule 或多层审计建设。
```

---

# 1. 开工前最高约束

## 1.1 必须把第一性原理放入仓库

当前仓库中没有：

```text
NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
```

先将该文件的已确认版本加入：

```text
docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
```

不得从旧任务书反推或自行重写其内容。

## 1.2 更新并遵守根目录 `AGENTS.md`

在现有规则基础上增加：

```text
- Before any Nollm task, read:
  docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
  and the current taskbook.
- First-principles invariants govern architecture direction.
- Current modular charters govern component ownership.
- If a filename-based classification conflicts with current code behavior,
  inspect the code and classify from behavior, dependencies, and state ownership.
- Never mark a component DELETE_LATER merely because an older version of a
  same-named file contained a forbidden path.
```

冲突解释规则：

第一性原理文件中的架构不变量保持最高优先级；其中带日期的“当前执行顺序”属于当时阶段记录。用户随后已明确将当前执行阶段调整为模块化 M0/M0-C1，因此阶段调度以本任务书和模块化修正书为准，但不得违反第一性原理的架构方向。不得据附录第 6 节在 M0-C1 中提前恢复 OpenClaw Live 或 Core 大规模删除。

```text
第一性原理继续约束：
  Architecture is the Index；
  不走 graph/vector/embedding 主路径；
  不用 Python 模拟语义 Placement；
  原始 Evidence 必须由 Nollm 系统保全；
  Windows-first；
  大跨度内部 Gate；
  单一 Git bundle。

最新模块化架构继续约束：
  Core 只拥有几何当前状态与确定性操作；
  Evidence/Source/History/Audit/Product policy 的具体持久所有权可在 Access、
  History、Audit 或外部 Source Store；
  但不得因此丢失原始 Evidence 或让 Geometry 替代 Evidence。
```

## Gate 1 PASS

```text
第一性原理已进入仓库；
AGENTS 明确要求先读；
AGENTS 不依赖 ChatGPT Source；
第一性原理和模块所有权的适用层级已写清。
```

---

# 2. Gate 0：保全 M0 当前状态

在基线 Bundle 的完整克隆中执行：

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git log -12 --oneline --decorate
```

保存到：

```text
docs/project/M0C1_STARTING_STATE.md
```

必须确认：

```text
HEAD = 76eb10dc37260f5c623398baceeea5b846813592
或明确记录其后仅属于 M0-C1 的本地提交。
```

禁止：

```text
git reset --hard
git clean -fd
回退暂停前的 Core Realignment checkpoint
覆盖 batch 7 已保全结果
重新启动 Corpus
```

## Gate 0 PASS

```text
M0 HEAD、branch、status 已记录；
工作树干净或修改已保全；
没有丢失 M0 四个提交及暂停 checkpoint。
```

---

# 3. 当前审核发现的硬事实

Codex 不得把以下内容解释为“审核者偏好”，它们是必须闭合的代码事实。

## 3.1 `relation_field.py` 被错误标记为应删除

当前文件：

```text
reference/python/nollm/grf/relation_field.py
```

当前实现特征：

```text
- 文件声明：without routes；
- 没有 _entry_lookup_cache；
- 没有 _patch_lookup_cache；
- 没有 _unique_routes / _shared_routes；
- 没有 identity → partition route table；
- 通过显式 Cell、Coverage、Lateral、Bridge 做稀疏传播；
- 某些查找仍是线性扫描，但不是外置关系索引。
```

当前 Manifest 却标记为：

```text
owner=LEGACY
lifecycle_status=BLOCKED
migration_action=DELETE_LATER
confidence=HIGH
reason=external relation index ...
```

这是错误分类。

除非 M0-C1 在当前代码中找到新的、可定位的禁用结构，否则不得继续把该文件标记为 `DELETE_LATER`。

## 3.2 `field_engine.py` 被错误标记为纯 Core HIGH

当前文件：

```text
reference/python/nollm/grf/field_engine.py
```

Manifest 标记：

```text
owner=CORE
migration_action=MOVE
confidence=HIGH
reason=pure geometry/current-state implementation
```

但它当前 import：

```text
.placement
.relation_field
```

现有防火墙自身已经报告：

```text
CORE → ACCESS
CORE → LEGACY
```

因此它不能同时被认定为“纯 Core HIGH”。

处理方式只能是：

```text
A. 安全抽取真正纯 Core 部分并完成移动；
或
B. 降为 MEDIUM + SPLIT，写明混合依赖和 M1 抽取边界。
```

不得保留矛盾状态。

## 3.3 72 个 `HIGH + MOVE` 条目并未全部移动

当前 Manifest 中约有：

```text
72 个 confidence=HIGH 且 migration_action=MOVE 的条目
```

其中包括：

```text
大量 experiments/grf/**；
12 个 reference/python/nollm/grf/** Core 候选。
```

但 M0 实际 R100 移动的主要是：

```text
experiments/openclaw/datasets/**
experiments/openclaw/results/**
→ lab/nollm-lab/openclaw/**
```

因此当前 `MOVE` 同时混用了：

```text
未来建议移动；
已完成移动；
应该移动但本阶段未动。
```

该字段不能支持 Final Gate。

## 3.4 Snapshot/Trace 只在 Fake 对象上通过

当前新增：

```text
ConsistentStatePort
SnapshotService
TraceSink
NullTraceSink
Jsonl/Console/Memory/Metrics/CompositeTraceSink
```

这些合同和实现可以保留。

但当前测试只使用：

```text
FakeStatePort
人工 operation(sink)
```

没有证明：

```text
真实 GRF workspace 可以通过 Snapshot Port create/restore/verify；
现有 GRFFacade.snapshot/restore 与新 Port 等价；
真实 CellStore/FieldEngine mutation 会发出可选 Trace；
NullTrace、MemoryTrace 和抛错 Sink 下真实 Core 结果相同。
```

因此 Gate 6 未实质闭合。

## 3.5 现有架构回归测试失败

当前命令：

```powershell
python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py
```

当前至少存在：

```text
reference/python/tests/test_architecture_language.py
```

仍要求：

```text
V2 is the only active architecture
Core does not import adapters or terminals
Adapters translate
Terminals present
...
```

而根文档已改为 M0 模块化架构。

测试不能删除或跳过；必须更新为当前架构合同，并保留对历史 V2 文档“已 superseded”的验证。

## 3.6 642 条防火墙 Baseline 大量是分类噪声

当前 642 条中，主要来源包括：

```text
LAB → LEGACY：约 574 条；
DISTRIBUTION → LEGACY：约 40 条。
```

但模块章程明确：

```text
Lab 可以依赖全部模块和迁移资产；
生产模块不得反向依赖 Lab。
```

因此 Lab 为测试历史实现而 import Legacy，不应全部被记为生产架构违规。

同时，很多 root/tool/test 文件被默认分配为 DISTRIBUTION，导致虚假违规。

M0-C1 必须让 baseline 代表真实债务，而不是把分类器噪声永久冻结。

## 3.7 Manifest generator 的 `--check` 当前并不存在

外部复核执行：

```text
python tools/generate_module_ownership_manifest.py --check
```

脚本没有参数解析，仍直接重写 CSV/JSON/UNCLASSIFIED 文件，并使干净审计工作树出现修改。

因此当前所谓 `--check` 不是只读检查。M0-C1 必须实现真正的：

```text
--write
--check
```

其中 `--check`：

```text
在内存生成期望结果；
与 tracked 文件比较；
不写磁盘；
不改变换行；
不改变工作树；
不一致时返回非零。
```

---

# 4. Gate 2：将 Manifest 升级为可审计事实清单

## 4.1 禁止继续仅按文件名分类

当前：

```text
CORE_NAMES
ACCESS_NAMES
SNAPSHOT_NAMES
TRACE_NAMES
```

只能作为初始候选，不得直接决定 `HIGH`、`BLOCKED` 或 `DELETE_LATER`。

最终分类必须至少综合：

```text
路径；
当前代码职责；
持久状态；
公开 API；
直接 imports；
反向 imported_by；
是否参与实际生产路径；
是否含禁用结构；
是否已存在目标替代实现。
```

## 4.2 Manifest Schema V2

在原字段基础上新增：

```text
target_path
migration_status
classification_evidence
forbidden_feature_evidence
review_status
reviewed_at
```

合法 `migration_status`：

```text
NOT_APPLICABLE
PENDING
COMPLETED
BLOCKED_BY_SPLIT
QUARANTINED
```

合法 `review_status`：

```text
AUTO_CANDIDATE
CODE_REVIEWED
DEPENDENCY_REVIEWED
MOVE_VERIFIED
```

## 4.3 `MOVE` 的严格语义

凡：

```text
migration_action=MOVE
```

必须同时满足：

```text
target_path 非空；
migration_status 明确；
若 migration_status=COMPLETED：目标文件存在，源文件已移除或仅保留登记的薄 re-export；
若未完成：不得计入 M0 Final Gate 的“已移动资产”。
```

M0-C1 最终不得存在：

```text
confidence=HIGH
migration_action=MOVE
migration_status=PENDING
```

处理方式：

```text
安全移动；
或把 action 改为 KEEP/SPLIT；
或把 confidence 降为 MEDIUM/LOW。
```

## 4.4 `HIGH` 的严格语义

`HIGH` 必须满足：

```text
职责单一；
状态所有权清楚；
依赖方向符合目标；
没有未解释的跨 owner import；
分类证据不是仅来自文件名。
```

机器规则：

```text
HIGH 文件若触发 forbidden_module_import，默认失败。
```

唯一例外：

```text
已登记、只做 import/re-export 的兼容入口。
```

例外必须出现在：

```text
packages/COMPATIBILITY_REEXPORTS.md
```

并由检查器验证没有业务逻辑。

## 4.5 `BLOCKED / DELETE_LATER` 的严格语义

必须包含：

```text
forbidden_feature_evidence:
  - symbol
  - file
  - line/range or AST identity
  - why correctness depends on it
  - replacement or extraction target
```

禁止：

```text
按历史印象；
按同名旧文件；
按任务书旧结论；
按文件名包含 relation/index/cache；
直接标记 DELETE_LATER。
```

## 4.6 修正关键文件

至少逐项人工代码审查：

```text
reference/python/nollm/grf/relation_field.py
reference/python/nollm/grf/field_engine.py
reference/python/nollm/grf/placement.py
reference/python/nollm/grf/placement_protocol.py
reference/python/nollm/grf/recall.py
reference/python/nollm/grf/storage.py
reference/python/nollm/grf/facade.py
reference/python/nollm/grf/openclaw_bridge.py
reference/python/nollm/grf/geometry_storage.py
reference/python/nollm/grf/kernel_registry.py
reference/python/nollm/grf/replay.py
reference/python/nollm/grf/ledger.py
reference/python/nollm/grf/evidence.py
reference/python/nollm/grf/source_window.py
reference/python/nollm/grf/capture.py
reference/python/nollm/grf/admission.py
reference/python/nollm/grf/admission_bridge.py
reference/python/nollm/grf/bridge_kernel.py
reference/python/nollm/grf/stitching.py
```

必须特别确认：

```text
relation_field.py 当前不是外置关系索引；
旧 deterministic/hash placement 是否已经退出当前主路径；
哪些文件只是对象合同；
哪些文件混合 Core state 和 Access policy；
哪些 Snapshot/Trace 结论是未来拆分，而不是当前事实。
```

## Gate 2 PASS

```text
Manifest V2 覆盖全部 tracked 文件；
默认 catch-all 不会把未知代码标为 ACTIVE/HIGH；
relation_field 不再被无证据 DELETE_LATER；
不存在 HIGH+MOVE+PENDING；
HIGH 文件无未解释跨 owner 依赖；
每个 BLOCKED/DELETE 条目有代码证据。
```

---

# 5. Gate 3：新增 Manifest 真值验证器

新增：

```text
tools/validate_module_ownership_manifest.py
```

必须检查：

```text
1. tracked 文件 100% 覆盖；
2. 无 stale manifest path；
3. owner/lifecycle/action/confidence/status 枚举合法；
4. HIGH 不得依赖禁止 owner；
5. MOVE 必须有 target_path 和 migration_status；
6. COMPLETED move 必须验证目标和兼容入口；
7. BLOCKED/DELETE 必须有 forbidden_feature_evidence；
8. LOW 不得 DELETE；
9. 默认/无法解释项必须 LEGACY + LOW + QUARANTINE；
10. relation/index/cache 名称本身不能作为删除证据；
11. `UNCLASSIFIED_TRACKED_FILES.txt` 必须由实际差集生成，不能无条件写空；
12. generator `--check` 不得改写工作树。
```

为验证器新增独立测试：

```text
reference/python/tests/m0/test_manifest_validation.py
```

测试必须构造负例：

```text
HIGH + forbidden import；
MOVE 无 target_path；
COMPLETED 但目标不存在；
BLOCKED 无证据；
LOW + DELETE；
tracked 文件遗漏；
默认分类错误地成为 ACTIVE/HIGH。
```

## Gate 3 PASS

```text
Manifest 不再只是“每个文件都有一行”；
错误归属可以被机器拒绝；
UNCLASSIFIED 是真实计算结果；
generator 与 validator 均可重复运行且工作树不变。
```

---

# 6. Gate 4：重建真实依赖 Baseline

## 6.1 修正规则图

目标规则：

```text
CORE -> none
SNAPSHOT -> CORE public
TRACE -> CORE trace contracts
ACCESS -> CORE public, optional SNAPSHOT public
HISTORY -> ACCESS contracts, optional SNAPSHOT
AUDIT -> ACCESS contracts, optional TRACE contracts
OPENCLAW -> ACCESS
LAB -> all public modules + LEGACY migration assets + distribution metadata
DISTRIBUTION -> composition metadata only
LEGACY -> no target architecture guarantee
```

注意：

```text
LAB import LEGACY 是允许的开发/迁移测试关系；
生产模块 import LAB 仍是硬错误；
LAB 不应被纳入生产模块循环依赖判定；
DISTRIBUTION 的文档和 JSON manifest 不应被当作 Python 业务模块；
root run_tests.py、验证脚本、repo tooling 应按 LAB/TOOL 分类，不应默认 DISTRIBUTION。
```

## 6.2 防火墙输出分层

`tools/check_module_boundaries.py` 输出至少区分：

```text
production_violations
migration_violations
compatibility_reexports
cycles_production
cycles_all
```

Final Gate 关注：

```text
new production violations = 0
new production cycles = 0
```

历史 Legacy 测试依赖不得淹没真实结果。

## 6.3 Baseline 重建纪律

不得直接执行：

```text
--write-baseline
```

先输出临时报告并人工核对：

```text
docs/architecture/module-ownership/M0C1_BOUNDARY_REVIEW.md
```

报告必须说明：

```text
旧 642 条如何减少；
哪些是 LAB→LEGACY 噪声；
哪些是真实 Core/Access/Snapshot/Trace 债务；
生产循环依赖的具体文件边；
每条真实债务的 M1 动作。
```

核对后再更新：

```text
M0_BOUNDARY_BASELINE.json
```

## Gate 4 PASS

```text
Baseline 只冻结真实债务；
LAB/Legacy 测试关系不再被误称生产违规；
生产 cycle 清晰、可定位；
新 package 无新增生产违规。
```

---

# 7. Gate 5：实际 Package 移动与迁移状态闭合

本 Gate 不要求为了“目录整齐”移动全部旧代码。

正确原则：

```text
明确纯净、依赖闭合、不会改变行为的叶子资产可以移动；
混合职责文件必须 SPLIT；
已有合法 Lab root 的实验文件可以 KEEP，不得虚报 MOVE；
不确定文件进入 LEGACY/QUARANTINE；
不因旧文件名删除当前正确实现。
```

## 7.1 Lab 资产

允许两种合法方案：

### 方案 A：保留多个 Lab root

```text
lab/nollm-lab/**
experiments/**
validation/**
reference/python/tests/**
```

全部在 config 中明确为 LAB，Manifest 标记 `KEEP`。

### 方案 B：实际迁移

真正 `git mv` 至 `lab/nollm-lab/**`，更新 imports、scripts、docs、fixtures 和测试。

不得：

```text
文件仍在 experiments/**，Manifest 却写 HIGH + MOVE + COMPLETED。
```

## 7.2 Core 候选

对下列类型优先做 leaf purity 审查：

```text
整数坐标；
Eisenstein；
fixed-point；
CellAddress；
CoverageTemplate；
纯 BridgeKernel 数据/验证；
无产品策略的几何函数。
```

若移动：

```text
进入 packages/nollm-core/src/nollm_core/**；
旧 path 只保留薄 re-export；
登记 COMPATIBILITY_REEXPORTS；
新旧 import 行为一致；
无 Access/Source/History/Audit import。
```

下列混合文件不得仅因名称直接移动：

```text
field_engine.py
relation_field.py
storage.py
facade.py
replay.py
ledger.py
placement.py
recall.py
```

它们应先明确 `SPLIT` 边界，除非本任务内能完成小而确定的纯合同抽取。

## Gate 5 PASS

```text
所有 HIGH MOVE 均真实完成；
其余改为 KEEP/SPLIT/QUARANTINE；
兼容入口无业务逻辑；
没有为过 Final Gate 进行大规模语义搬迁。
```

---

# 8. Gate 6：Snapshot Port 绑定真实 GRF Workspace

## 8.1 保留当前合同，但允许最小修正

现有：

```text
ConsistentStatePort.begin_consistent_read
ConsistentStatePort.export_state
ConsistentStatePort.import_state
ConsistentStatePort.end_consistent_read
SnapshotService
```

可以保留。

若 `bytes` 无法诚实表达现有 workspace snapshot，可做最小合同修正，但必须：

```text
保持 policy-free；
不引入 History 语义；
不把 Source/Audit 放入 Core；
Snapshot implementation 依赖 Core public port；
Core 不 import Snapshot implementation。
```

## 8.2 建立真实兼容 Adapter

建议新增：

```text
reference/python/nollm/grf/m0_ports.py
```

或职责等价路径，提供：

```text
GRFWorkspaceConsistentStateAdapter
```

该 Adapter 可以位于当前混合实现侧，依赖 `nollm_core` public contract。

不得让 `nollm_snapshot` import `reference/python/nollm/grf` private implementation。

## 8.3 真实行为测试

新增测试必须使用真实：

```text
GRFFacade
GRFFileStore
真实 workspace 文件
至少一个 capture + explicit placement/admission 或最小可重放状态
```

证明：

```text
1. SnapshotService.create 能导出真实 workspace current state；
2. restore 到新 workspace 后 validate_workspace 等结构事实一致；
3. clone 一致；
4. verify 一致；
5. structural_diff 只比较结构，不判断事实/历史；
6. export 失败时 consistent-read 正确结束；
7. 现有 GRFFacade.snapshot/restore 与 Port 路径等价，或改为兼容 wrapper；
8. Windows 路径、负坐标文件、UTF-8 payload 可恢复。
```

## 8.4 原子性与安全边界

只需功能正确性：

```text
临时目录；
同卷原子替换或明确的 staging；
失败不破坏原 workspace；
无 Merkle、Evidence Capsule、供应链框架。
```

## Gate 6 PASS

```text
Snapshot Port 不再只是 Fake 测试；
真实 GRF snapshot/restore 通过 public port；
Snapshot 不承担 History/Audit 语义；
Core 不依赖 Snapshot implementation。
```

---

# 9. Gate 7：Trace Port 绑定真实 Core 当前状态操作

## 9.1 实际注入点

在不改变几何结果的前提下，至少选择真实：

```text
CellStore.insert
CellStore.remove
CellStore.move
FieldEngine.add_bridge/remove_bridge
RelationField bounded propagation 的一个稳定入口
```

注入可选：

```text
TraceSink
```

默认：

```text
NullTraceSink
```

## 9.2 Core 侧失败隔离

任意 Sink 抛错不得：

```text
阻止 mutation；
留下半写状态；
改变返回值；
改变 Recall 结果。
```

不得只依赖 `CompositeTraceSink` 捕获异常，因为调用者可能传入普通失败 Sink。

Core public contract 应提供等价的安全发射方式，例如：

```text
safe_emit(trace_sink, event)
```

具体命名可调整。

## 9.3 真实等价测试

对同一实际操作序列运行：

```text
NullTraceSink
MemoryTraceSink
FailingTraceSink
CompositeTraceSink
```

比较：

```text
Cell occupancy
placement_count
bridge set
RelationField output
bounded Recall output
异常后的状态一致性
```

必须相同。

Trace 只允许额外产生：

```text
事件流；
计数；
耗时/预算等观测。
```

不得写入 Core 持久状态。

## Gate 7 PASS

```text
真实 Core 操作会发出 Trace；
Null/Memory/Failing Sink 下结果相同；
Trace failure 不影响 correctness；
Core 未持久化 Trace。
```

---

# 10. Gate 8：修复现行架构回归测试

不得删除：

```text
reference/python/tests/test_architecture_language.py
```

将其更新为当前 M0 架构断言，至少包括：

```text
Nollm is in the M0 modular-monorepo stage
Architecture is the Index
Core owns geometry current state
Snapshot, Trace, Access, History, Audit, OpenClaw, Lab, Distributions
OpenClaw Live Integration is paused
GRF8 is an engineering checkpoint, not accepted architecture
Evidence-first V2/V2.1/V2.2 are historical or superseded
M1 is not started
GitHub repositories are not physically split
```

同时验证：

```text
旧 V2 Layer Constitution 仍存在于历史路径；
但根导航不会把它标为唯一活动架构。
```

若旧测试还承担历史文档一致性，可拆成：

```text
test_current_architecture_language.py
test_historical_v2_language.py
```

但不得通过 skip、删除或缩小收集绕过。

## Gate 8 PASS

```text
当前架构测试与根文档一致；
历史文档仍可验证；
不再同时声称 V2 和 M0 都是唯一活动架构。
```

---

# 11. Gate 9：修正行为保持报告

更新：

```text
docs/validation/M0_BEHAVIOR_PRESERVATION_REPORT.md
```

必须区分：

```text
已验证事实；
环境依赖失败；
历史测试已修复；
真实 Port 绑定结果；
剩余 M1 债务。
```

当前外部复核事实应纳入：

```text
M0 tests: 7 passed（基线复核时）；
GRF core tests: 109 passed, 1 skipped；
2 个 zstandard 相关测试在缺少依赖环境中失败；
旧 architecture language test 曾失败，M0-C1 必须修复；
Boundary checker 曾为 642 baseline / 1 cycle，其中大量为分类噪声。
```

Windows 最终环境若有 `zstandard`，应运行完整 GRF suite。

若 Windows 环境仍没有该依赖：

```text
记录完整命令和 ModuleNotFoundError；
另运行排除精确两个可选压缩测试的 GRF suite；
不得把环境失败写成代码通过；
不得为 M0-C1 新增复杂依赖管理。
```

## Gate 9 PASS

```text
报告不再夸大；
命令、通过数、失败数可复核；
环境失败与代码失败分开；
真实 Snapshot/Trace 测试结果已记录。
```

---

# 12. Final Gate 命令

PowerShell：

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = @(
  "$PWD/reference/python",
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-trace/src",
  "$PWD/packages/nollm-access/src",
  "$PWD/packages/nollm-history/src",
  "$PWD/packages/nollm-audit/src"
) -join ";"

python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py

python -m pytest -q reference/python/tests/m0

python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py

python -m pytest -q reference/python/tests/grf

git diff --check
git status --short
```

若仅缺少 `zstandard`：

```powershell
python -m pytest -q reference/python/tests/grf `
  --ignore=reference/python/tests/grf/test_grf7r2_evidence_pack.py `
  --ignore=reference/python/tests/grf/test_grf7r3_compact_evidence.py
```

同时必须运行新真实 Port 测试的明确路径；即使其已经被 `tests/m0` 收集，也在报告中单独列命令。

---

# 13. Final Gate 必须满足的事实

只有全部满足，才能输出：

```text
NOLLM_M0_MODULE_SEPARATION_ACCEPTED_CANDIDATE
```

条件：

```text
1. 第一性原理已进入仓库，AGENTS 要求先读；

2. Manifest V2 覆盖全部 tracked 文件；

3. relation_field.py 不再被无代码证据标记 DELETE_LATER；

4. HIGH 分类与依赖一致；

5. 不存在 HIGH + MOVE + PENDING；

6. BLOCKED/DELETE 条目均有具体代码证据；

7. UNCLASSIFIED 文件由真实差集生成并为空；

8. Boundary baseline 已去除 LAB→LEGACY 等分类噪声；

9. 生产模块无新增违规和新增循环；

10. Snapshot Port 已绑定真实 GRF workspace；

11. Trace Port 已绑定真实 CellStore/FieldEngine 操作；

12. Trace failure 不影响真实 Core 结果；

13. 当前架构语言测试通过；

14. 旧 V2 文档仍保留但明确 superseded；

15. OpenClaw Live、LLM Corpus、远端拆仓未启动；

16. 主要 GRF 行为保持；

17. 工作树干净；

18. 最终只交单一 Git bundle。
```

---

# 14. M1 明确不得提前执行

M0-C1 不得借“修清单”实施：

```text
删除 RelationField；
重写整个 FieldEngine；
删除所有 Evidence/Source 对象；
完成 Core/Access 全量拆分；
实现 MemoryAtom 最终合同；
实现真实 LLM Statement Formation；
实现 OpenClaw Placement；
重写 History policy；
拆分 GitHub 仓库。
```

允许的实际代码变化仅限：

```text
清单生成与验证；
依赖防火墙准确化；
明确叶子资产安全移动；
兼容 re-export；
真实 Snapshot Port adapter；
真实 Trace Port injection；
测试和当前文档修正。
```

---

# 15. 建议 Checkpoint Commits

```text
docs(m0c1): bind first principles and correction scope

fix(m0c1): make ownership manifest evidence-based

test(m0c1): validate ownership truthfulness

fix(m0c1): rebuild production boundary baseline

refactor(m0c1): close verified high-confidence moves

refactor(snapshot): bind public port to real GRF workspace

refactor(trace): bind optional sink to real geometry operations

test(m0c1): align current architecture and behavior gates
```

可根据实际合并，但最终 Git 图必须可审查。

---

# 16. 最终交付

只交付：

```text
nollm_m0c1_ownership_port_regression_closure_20260711_<shorthead>.bundle
```

要求：

```text
完整 Git 历史；
包含 M0 基线和 M0-C1 全部提交；
工作树干净；
Bundle verify 通过；
不附加 receipt；
不附加 evidence capsule；
不附加 SHA 文档；
不 push 远端；
不创建 GitHub 仓库。
```

---

# 17. 一句话执行目标

> **把 M0 从“有目录、有表格、有假 Port 测试”闭合为“归属结论与当前代码一致、机器能拒绝错误分类、Snapshot/Trace 真正接入现有 GRF、当前架构回归全部通过”的可信模块化基线。**

---

# 附录 A：应写入仓库的第一性原理文件原文

Codex 必须将下列标记之间的内容原样写入：

```text
docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
```

不得改变标题、原则、禁止路线或最终一句话；仅允许把文件自身日期保持为原日期。

<!-- BEGIN CANONICAL FIRST PRINCIPLES -->
# Nollm 第一性原理与防漂移约束

**日期**：2026-07-11
**状态**：项目最高层目标约束
**用途**：供 ChatGPT、Codex 和后续交接在开始任务前读取，防止因历史任务书、局部性能目标或对话截断而偏离项目初衷。

> 当本文件与旧任务书、旧交接文件、旧阶段实现发生冲突时，以本文件为准。旧实现可以删除，不因“已经完成”而保留错误方向。

---

## 1. Nollm 的第一性原理目标

Nollm 不是传统数据库、向量数据库、知识图谱或检索框架。

Nollm 的目标是：

> **为 LLM 提供一个证据优先、文件优先、由几何结构直接承载关系的长期记忆场；LLM 负责语义理解和放置判断，Core 负责确定性验证、几何执行、持久化与回放。**

最小记忆单位是：

```text
一段独立、有意义、可回到原文的表达
```

不是：

```text
token
固定长度 chunk
摘要
embedding
实体节点
```

---

## 2. 不可动摇的原则

### 2.1 Evidence first

```text
原始 Evidence 是事实源。
解释、位置、覆盖、路径和召回结果都不能替代原文。
```

必须始终成立：

```text
Evidence ≠ Interpretation
Interpretation ≠ Placement
Placement ≠ Fact confirmation
Recall path ≠ Proof
```

### 2.2 File first

```text
文件是持久事实源。
缓存、快照、索引和运行时对象都只能是可重建派生物。
```

### 2.3 Architecture is the Index

Nollm 的关系必须主要来自：

```text
几何地址
Cell occupancy
Coverage kernel
层间覆盖
局部邻接
可逆 Stitch
有界传播
```

不得再建立一套外部关系索引，先找对象，再让几何做装饰。

正确方向：

```text
Geometry address
→ Cell / Partition
→ Local relation field
→ Sparse propagation
→ Evidence fallback
```

错误方向：

```text
Object ID / source / entity
→ 倒排索引 / route table / graph
→ 找到对象
→ 再进入 Geometry
```

### 2.4 LLM 决定语义放置

以下判断必须由真实 LLM 完成：

```text
这是新内容还是重复内容；
是相似但不同，还是同一事实；
是否是旧内容的 revision；
是否复用原 placement；
是否创建新 placement；
是否形成新簇；
是否提出 stitch；
是否暂缓准入。
```

Python/Core 不得用以下方式模拟语义：

```text
hash placement
固定权重打分
关键词规则
伪向量相似度
人工硬编码答案
```

Core 只负责：

```text
验证对象存在；
验证几何地址合法；
验证密度、边界和预算；
执行放置；
保存 Evidence；
回放；
拒绝非法输入。
```

### 2.5 OpenClaw 是语义 Host

应尽快让 OpenClaw 中的真实 LLM 进入 Placement 流程。

正确关系：

```text
OpenClaw / LLM
  负责理解、比较、选择和提出 PlacementDecision

Nollm Core
  负责验证、执行、存储和几何传播
```

OpenClaw 不是事实源，LLM 判断也不是事实本身；原始 Evidence 始终保留。

### 2.6 Capture、Placement、Admission、Recall 分离

```text
Capture 是记住原文；
Placement 是选择几何位置；
Admission 是正式进入可回放结构；
Recall 是从有限入口重建相关现场。
```

不得因为 Capture 成功就强制完成全部几何工作。

### 2.7 Geometry 不是语义真相

```text
Coverage 不是 parent；
Cell 不是文件夹；
Stitch 不是事实合并；
Gravity 不是重要性；
位置不是可信度；
距离不是事实关系证明。
```

---

## 3. 必须删除的错误方向

当发现以下结构成为正确性主路径时，原则上删除，不做兼容性保留。

### 3.1 外置关系索引

包括但不限于：

```text
PlacementIndex._by_shard

RelationField._entry_lookup_cache

RelationField._patch_lookup_cache

GlobalShardedField._unique_routes

GlobalShardedField._shared_routes

GlobalFieldDirectory._source_intervals

source_window → placements 倒排表

island / patch → placements 倒排表

object → related objects

identity → partition 全局关系路由
```

允许保留的仅是：

```text
对象文件的最小物理定位；
由几何坐标直接计算的 partition；
Cell 自身的局部 occupancy；
删除后不影响正确性的临时缓存。
```

判断标准：

```text
删除后结果不变，只是变慢：
  可丢弃缓存

删除后仍能从文件直接找到对象：
  最小物理定位器

删除后无法进入正确关系路径：
  错误的关系索引，必须重构
```

### 3.2 Python 模拟语义 Placement

以下路径必须退出主流程：

```text
source hash → cell

shard_id hash → cell

固定评分公式决定 placement

伪向量相似度决定复用或新建

纯 Python 决定 duplicate / revision / stitch
```

它们最多可作为测试对照，不得作为产品 Placement。

### 3.3 Graph / Vector / Embedding 主路径

不得把 Nollm 变成：

```text
弱版知识图谱
弱版向量数据库
GraphRAG 包装层
embedding + geometry 可视化
```

可以保留基线实验，但不能进入 Core 主路径。

### 3.4 为错误架构做性能优化

不得因为某个索引已经很快，就继续固化它。

禁止以以下指标证明 Nollm 成功：

```text
indexed lookup 比 linear scan 快

route table 命中率高

倒排表查询达到微秒级
```

必须测量：

```text
无外置关系索引时，
由 LLM 选择的几何入口能否正确放置与召回。
```

### 3.5 重复安全与审计基础设施

当前开发环境默认：

```text
用户、ChatGPT、Codex 均为善意主体；
Windows-first；
安全由外部系统负责。
```

Nollm Core 不再建设：

```text
多层 SHA 链
Merkle root
evidence capsule
delivery receipt
供应链安全框架
攻击矩阵
重复权限系统
```

只保留：

```text
功能测试
数学验证
回放一致性
性能验证
Git 历史
单一 Git bundle
```

### 3.6 小任务和重复外审

默认采用：

```text
大跨度任务
+
内部 Gate
+
失败直接修复
+
最终单一 bundle
```

不要为文档格式、小型日志、非架构问题反复拆任务。

---

## 4. 正确的目标架构

```text
Raw Evidence
    ↓
Capture
    ↓
LLM compares local context and existing nearby memory
    ↓
PlacementDecision:
  reuse / new / revision / stitch / defer
    ↓
Core validates deterministic constraints
    ↓
Geometry address
    ↓
Cell occupancy + Coverage / Bridge kernels
    ↓
Sparse bounded propagation
    ↓
Original Evidence fallback
```

### 数据的关系来源

```text
局部关系：
由同一 Cell、相邻 Cell 和 Coverage kernel 直接产生

跨层关系：
由预计算 Coverage template 产生

跨簇关系：
由 LLM 提出的、Core 验证的可逆 Stitch 产生

修订关系：
由 LLM 判断，Evidence revision 记录明确保存
```

不得由全局 object-to-object 索引预先维护。

---

## 5. 每次设计前必须回答的问题

开始任何新任务前，逐项检查：

```text
1. 它是否保留原始 Evidence？

2. 关系来自几何结构，还是另建索引？

3. 删除缓存后，正确性是否保持？

4. 语义判断是否交给真实 LLM？

5. Python/Core 是否只做确定性验证和执行？

6. 是否正在为错误架构做性能优化？

7. 是否重新引入 graph/vector/embedding 主路径？

8. 是否把 Host 或 Terminal 变成事实源？

9. 是否增加与核心记忆无关的安全、审计或交付复杂度？

10. 是否可以用更少的组件完成同一核心目标？
```

若任一答案与本文件冲突：

```text
停止扩展；
删除错误结构；
回到第一性原理重新设计。
```

---

## 6. 当前执行顺序

GRF8 已在执行，不中途打断。

GRF8 完成后，下一阶段必须优先：

```text
1. 审计 GRF8 中所有 Index / Route / Lookup / Cache；

2. 删除所有承担关系和召回正确性的外置索引；

3. 将 partition routing 改为几何坐标函数；

4. 将 Cell occupancy 还原为几何结构本身；

5. 删除 Python hash / 固定评分 Placement 主路径；

6. 接入 OpenClaw 真实 LLM Placement；

7. 让 LLM 判断 duplicate / similar / revision / reuse / new / stitch / defer；

8. 重新测试无关系索引条件下的效率和召回质量。
```

---

## 7. 项目协作与交付规则

```text
主环境：
Windows 10/11 + PowerShell

任务：
大跨度 + 内部 Gate

交付：
单一 Git bundle

版本识别：
文件名 + Git HEAD

安全：
外部负责

外审重点：
架构方向、功能正确性、数学、性能、真实 LLM 工作流
```

---

## 8. 最终一句话

> **Nollm 不是用索引找到记忆后再展示几何，而是让 LLM 把证据放入几何关系场，使几何结构本身成为记忆关系和召回路径。**
<!-- END CANONICAL FIRST PRINCIPLES -->
