# Nollm CSTALD 活动基线真实性与公共合同修正任务书

**模块缩写**：`C=Core | S=Snapshot | T=Trace | A=Access | L=Lab | D=Distributions`

**日期**：2026-07-11
**任务文件名**：`NOLLM_CSTALD_BASELINE_CORRECTION_TASK_20260711.md`
**性质**：跨模块基线真实性修正、公共合同补正与进度账回填
**输入 Bundle**：`nollm_core_snapshot_trace_access_lab_distributions_boundary_reallocation_20260711_4f28f1d.bundle`
**输入 Bundle SHA-256**：`9137b6263233795482b5e95a0c9378c4f50c122c99a8ceac327385c764a3c45e`
**输入分支**：`codex/core-snapshot-trace-access-lab-distributions-boundary-reallocation`
**输入 HEAD**：`4f28f1db5d5998d0c052ac969bd3263496150626`
**已验证实现提交**：`3375f156c0a9ba3445b5d6fdf0c3101b22dde28b`
**建议分支**：`codex/cstald-baseline-correction`
**主环境**：Windows 10/11 + PowerShell
**交付形式**：全部修改提交、工作树干净、仓库外单一完整历史 Git bundle
**结论边界**：只形成绑定具体代码树和 HEAD 的能力记录或活动基线，不宣称封版、最终闭合或自动进入后续阶段。

---

## 0. 本次任务推进向量

```text
任务推进向量：
CORE +3% | SNAPSHOT +2% | TRACE 0% | ACCESS +2% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +2% | DISTRIBUTIONS +2%

主方向：
纠正活动项目依据、AGENTS 与能力记录的真实性；完成 Core 运行时 Profile 边界、
Access 持久绑定合同、Snapshot 结构差异和发行组合的剩余缺口，使前一任务的
正确重构能够成为可复现的活动基线。

范围变化：
无。模块章程和长期能力范围不扩大；不恢复 capability/security 路线，
不启动新的产品、模型、Host 或规模能力。
```

### 0.1 向量解释

- `CORE +3%`：移出仍残留的研究型 Profile 元数据，校验编译产物身份，并使能力验证可在交付 HEAD 复现。
- `SNAPSHOT +2%`：把 `structural_diff` 从布尔不等判断补成真实、稳定、有限的结构差异合同。
- `TRACE 0%`：不计划改变能力，仅做组合与回归确认。
- `ACCESS +2%`：补正 `HandleBinding` 严格类型合同，恢复普通失败回滚矩阵证据。
- `LAB +2%`：承接 Profile 研究元数据，完善生成链和代码源摘要验证。
- `DISTRIBUTIONS +2%`：补齐 Minimal/Debug 组合元数据，并确保活动项目依据与发行组合一致。
- 其余模块 `0%`：只确认没有意外依赖或范围变化。

### 0.2 执行纪律

1. 每个结果闸门开始和结束时在任务报告中复述推进向量。
2. 若新增受影响模块，或任何模块实际偏差超过 `5%`，立即更新范围、向量和状态记录。
3. Bundle 审核时必须计算实际推进向量并解释偏差。
4. 不得以测试数量增加替代能力推进说明。

---

## 1. 上一任务审核结论与保留成果

### 1.1 Bundle / Git 事实

```text
Bundle verify：通过
完整历史：通过
输入 HEAD：4f28f1db5d5998d0c052ac969bd3263496150626
实现提交：3375f156c0a9ba3445b5d6fdf0c3101b22dde28b
文档提交：4f28f1db5d5998d0c052ac969bd3263496150626
初始工作树：clean
```

### 1.2 已复现 Gate

```text
Manifest = 1457 / 1457
unclassified = 0
production violations = 0
production cycles = []
migration findings = 7

Core = 38 passed
Snapshot = 5 passed
Trace = 3 passed
Access = 25 passed
M0 = 18 passed
architecture / forbidden / hygiene = 8 passed
geometry parity = 9 / 9
Core capability validator = 25 dimensions passed
Minimal E2E = passed

GRF external audit:
109 passed
1 skipped
2 failed only because zstandard unavailable in the audit environment
```

### 1.3 必须保留的成果

```text
Core 公共 Store / client lease / transaction capability 已退出公共面；
Core 使用私有 Store、简单 RLock 和 process-local single writer；
动态 Coverage 编译已迁入 Lab；
Core 运行时只加载生成模板；
Snapshot Protocol 已归 Snapshot；
Trace Sink/JSONL/Metrics/Inspector 已归 Trace；
Access 使用可信本地组合锁和普通失败回滚；
Bare / Minimal / Debug 不依赖旧混合 GRF；
production violations = 0；
production cycles = []；
9/9 Geometry parity 保持；
无 graph/vector/embedding、外置关系索引或 Python semantic Placement。
```

不得回退上述成果。

---

## 2. 上一任务预计向量与本次外部复算

上一任务预计：

```text
CORE +10% | SNAPSHOT +5% | TRACE +5% | ACCESS +5% |
LAB +10% | DISTRIBUTIONS +5% | HISTORY/AUDIT/OPENCLAW 0%
```

交付方自报：

```text
CORE +11% | SNAPSHOT +7% | TRACE +7% | ACCESS +5% |
LAB +10% | DISTRIBUTIONS +6% | HISTORY/AUDIT/OPENCLAW 0%
```

本次外部审核复算：

```text
CORE +7% | SNAPSHOT +3% | TRACE +5% | ACCESS +3% |
LAB +8% | DISTRIBUTIONS +3% | HISTORY/AUDIT/OPENCLAW 0%
```

### 2.1 复算依据

- Core 纯化、模板 lookup、独立验证有实质推进，但研究型 Profile 元数据仍留在 Core，且最终交付 HEAD 的验证记录不可只读复现。
- Snapshot 已获得 Protocol 所有权和原子 state bytes 组合，但 `structural_diff` 仍只是 `left != right`。
- Trace 已真实获得 Sink、JSONL、Metrics、Composite、Inspector，达到预计 `+5%`。
- Access 可信组合已简化并保持主要功能，但持久公共对象 `HandleBinding` 仍接受非 `AtomHandle`，且普通失败回滚矩阵被大幅删除。
- Lab 已获得编译器、生成器、parity 与 Core validator，但 Profile 的 role/description 等研究元数据仍留在 Core。
- Distribution manifests 已更新，但 Minimal 默认组合没有完整表达 `FileHandleStore`、`SnapshotService` 等必要组成。

本任务以外部复算值作为新的任务前基线，不复制上一任务自报值。

---

## 3. 任务开始前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务是否影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` 候选，尚非活动基线 | 72% | 中高 | 38项包测试；9/9 parity；25维能力验证；私有Store；显式入口Recall | Profile研究元数据仍在Core；生成产物摘要未在运行时核对；验证记录未对最终交付可复现 | 是，直接修改 |
| SNAPSHOT | `IMPLEMENTED` | 48% | 中 | 独立Protocol；5项测试；原子create/restore/clone/verify | `structural_diff`只是布尔不等；差异合同与报告不足 | 是，直接修改 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 3项包测试；Null/Memory/JSONL/Metrics/Composite/Inspector | 深度工具和性能可视化有限，但不属于本任务 | 是，仅高风险回归，预计0% |
| ACCESS | `ACTIVE_BASELINE` 候选 | 58% | 中高 | 25项包测试；动作映射、Evidence fallback、普通rollback存在 | HandleBinding直接构造类型不严；全动作普通失败回滚证据减少；组合文档仍需对齐 | 是，直接修改 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程存在；无活动实现 | 未实施 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程存在；无活动实现 | 未实施 | 否 |
| OPENCLAW | `LEGACY_REFERENCE` | 25% | 中低 | 迁移资产保留；Live暂停 | 未接当前Access；无真实模型E2E | 否 |
| LAB | `IMPLEMENTED` | 48% | 中高 | 编译器、生成器、9/9 parity、Core validator | Profile研究元数据未完全归Lab；验证记录缺少稳定代码源摘要 | 是，直接修改 |
| DISTRIBUTIONS | `IMPLEMENTED` | 38% | 中 | Bare/Minimal/Debug矩阵已更新；活动路径无Legacy GRF | Minimal/Debug组成元数据不够完整；活动项目依据与发行说明仍冲突 | 是，直接修改 |

---

## 4. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 72% | 75% | +3% | 运行时Profile只保留必要约束；研究元数据退出；编译产物摘要核对；能力记录可复现 | Core独立测试；9/9 parity；artifact digest；代码源摘要；只读验证 | 跨进程恢复、PB规模、真实LLM未验证 |
| SNAPSHOT | 48% | 50% | +2% | 有限、稳定、结构化Snapshot diff | SnapshotDiff合同；确定性diff测试；失败恢复 | 跨版本迁移和增量快照未验证 |
| TRACE | 40% | 40% | 0% | 无能力变化，仅确认组合不回退 | 独立Trace测试；Core/Snapshot parity | 深度可视化仍待后续 |
| ACCESS | 58% | 60% | +2% | HandleBinding严格持久合同；普通全动作失败回滚证据恢复 | 直接构造负例；new/revision/forget/reuse普通故障矩阵 | 真实Host/LLM和多进程协调未验证 |
| HISTORY | 10% | 10% | 0% | 无变化 | 边界检查 | 未实施 |
| AUDIT | 10% | 10% | 0% | 无变化 | 边界检查 | 未实施 |
| OPENCLAW | 25% | 25% | 0% | 无变化 | 活动路径确认 | Live E2E未实施 |
| LAB | 48% | 50% | +2% | Profile研究定义归Lab；生成链和代码源摘要可复现 | 生成器check；metadata ownership test；validator check | Corpus、长压测未实施 |
| DISTRIBUTIONS | 38% | 40% | +2% | Minimal/Debug组成声明完整；活动项目依据唯一 | manifest schema/tests；README/Architecture/Project Book一致性 | 安装器、版本协商未完成 |

---

## 5. 结果闸门：活动项目依据与 AGENTS 去漂移

### 开始向量

```text
CORE +3% | SNAPSHOT +2% | TRACE 0% | ACCESS +2% |
LAB +2% | DISTRIBUTIONS +2% | 其余 0%
```

### 必须完成

1. 将当前活动项目书、Core纯净性重新归属决定、本任务书和持续进度账纳入仓库的明确活动文档路径。
2. 仓库中不得只剩旧 V2.2 项目书作为唯一 `PROJECT_BOOK`。
3. 旧 V2.2 项目书：
   - 移入历史目录；或
   - 在文件顶部明确标记 `LEGACY_REFERENCE / SUPERSEDED`，并链接当前活动项目书。
4. 将根目录 `AGENTS.md` 收缩为泛用、精简的执行策略：
   - 只写仓库操作、测试、提交、工作树和 Bundle 交付规则；
   - 不写当前路线、阶段、HEAD、推进向量、具体模块职责或本任务要求；
   - 删除历次任务累积的 capability、callback fence、client lease 等具体项目规则；
   - 不复制项目书、模块章程、当前状态或任务书。
5. 根 README、ARCHITECTURE、ROADMAP、CURRENT_STATUS 与当前项目书一致。

### 必须新增测试

```text
test_active_project_book_is_unique.py
test_agents_is_generic_and_concise.py
test_current_task_and_progress_ledger_are_reachable.py
```

### 通过条件

```text
活动项目依据唯一；
AGENTS 仅包含泛用执行策略，不再形成长上下文漂移源；
历史项目书不会覆盖当前模块化架构；
任务推进向量不变。
```

---

## 6. 结果闸门：Core Runtime Profile 边界纯化

### 当前问题

Core 当前公开的 `Profile` 仍包含：

```text
role
scale_model
rotation_model
description
production_candidate / baseline / research 分类
```

这些属于 Lab 研究与生成元数据，不是 Core 运行时必要状态。

### 必须完成

1. 将完整 Profile 定义、角色、描述、生成模型和研究说明迁入 Lab。
2. Core 仅保留运行时必要、稳定、最小的 Profile 合同，例如：
   - `profile_id`
   - coordinate/runtime format
   - weight format
   - runtime float/polygon flags
   - 与编译产物身份核对所需字段。
3. 默认不再从 `nollm_core.__all__` 公开研究型 `Profile` 构造器。
4. 若外部需要读取 Profile，只提供：
   - `available_profile_ids()`
   - `runtime_profile(profile_id)` 的只读最小视图；
   - 不暴露 role/description 等研究信息。
5. Lab generator 从 Lab 自己的 Profile definitions 生成模板，不再依赖 Core 研究元数据。
6. `KernelRegistry` 初始化时必须验证：

```text
sha256(COMPILED_TEMPLATES_JSON) == COMPILED_TEMPLATES_SHA256
```

7. 保持：
   - 3 profile × 3 direction = 9模板；
   - 9/9 Legacy parity；
   - registry identity与现有Core状态兼容，或提供明确迁移说明与测试。

### 通过条件

```text
Core 运行时无研究型 Profile 元数据；
Lab 成为研究定义的唯一 owner；
编译产物摘要真实校验；
现有 Core state 可重开或有明确、测试通过的迁移；
CORE +3%、LAB +2%方向未偏移。
```

---

## 7. 结果闸门：Access 持久绑定合同修正

### 当前问题

以下直接构造当前会被接受：

```python
HandleBinding(handle="not-an-AtomHandle", current_statement_id="s")
```

随后只会在序列化或使用阶段失败。

### 必须完成

1. `HandleBinding.__post_init__` 必须要求：
   - `handle` 为 exact `AtomHandle`；
   - `current_statement_id` 为非空 exact `str`；
   - `supporting_statement_ids` 为排序、唯一、非空字符串 tuple；
   - current 不得同时 supporting。
2. `FileHandleStore` decode/encode 保持 strict canonical bytes。
3. 恢复普通、受支持失败模型下的全动作回滚测试：
   - `new`
   - `revision_current`
   - `revision_keep_history`
   - `forget`
   - `reuse` 的 Store 失败不产生绑定
4. 故障注入只使用 Lab/test monkeypatch 私有写函数，不恢复公共 fault hook 或 capability/security 体系。
5. 保持两个 AccessRuntime 共享同一可信 composition lock 时：
   - 失败操作不会擦除随后成功操作；
   - 不测试恶意回调、影子Store或私有API攻击。
6. `AccessRuntime` 与 `FileHandleStore` 的支持合同写入 Access Charter。

### 通过条件

```text
公共持久对象直接构造严格；
普通失败回滚矩阵完整；
没有恢复 Core client lease、writer capability或callback sandbox；
ACCESS +2%成立。
```

---

## 8. 结果闸门：Snapshot 结构差异合同落实

### 当前问题

当前：

```python
SnapshotService.structural_diff(left, right) -> bool
```

仅返回 `left != right`，不能称为结构差异。

### 必须完成

二选一，优先方案A：

#### 方案A：实现有限结构化差异

新增不可变 `SnapshotDiff`，至少包括：

```text
equal
left_sha256
right_sha256
changed_top_level_sections
left_size_bytes
right_size_bytes
```

若输入是 Core canonical JSON，可稳定比较顶层：

```text
schema_version
geometry_registry
cells
bridges
```

不得把 Snapshot 模块变成 History 或语义 diff。

#### 方案B：收缩合同

若当前阶段不实施结构化差异：

```text
structural_diff
```

必须改名为：

```text
differs
```

并同步降低 Snapshot 完成度目标、章程和报告；不得继续宣称已实现 structural diff。

本任务目标默认采用方案A。

### 通过条件

```text
Snapshot diff 名称与真实能力一致；
结果确定性、可序列化、无语义历史；
create/restore/clone/verify不回退；
SNAPSHOT +2%成立。
```

---

## 9. 结果闸门：Trace 组合回归确认

本任务不计划提升 Trace 完成度。

必须确认：

```text
Null/Memory/Failing/Jsonl/Metrics/Composite/Inspector tests通过；
Trace event只含不可变标量；
Trace不进入Core state bytes；
删除Trace文件不影响Core；
Core不import nollm_trace；
本任务未恢复恶意插件沙箱或callback fence。
```

实际向量应保持 `TRACE 0%`，除非执行中新增真实能力并更新范围。

---

## 10. 结果闸门：Lab 生成链与能力记录可复现

### 10.1 模板生成链

新增只读检查方式：

```powershell
python lab/nollm-lab/geometry/generate_compiled_templates.py --check
```

要求：

```text
--check 不修改工作树；
生成产物与仓库文件不一致时失败；
输出artifact SHA-256；
9/9 parity使用同一生成源。
```

### 10.2 能力验证记录

不能要求一个被提交文件包含其所在提交自身的 Git hash；避免自引用循环。

采用：

```text
validated_code_commit
validated_code_tree_digest
validation_schema
validation_command
verified_capabilities
```

规则：

1. `validated_code_commit` 指向最后一个影响受验证代码的提交。
2. 后续纯文档提交可以位于其后，但不得修改受验证代码路径。
3. `validated_code_tree_digest` 对以下受验证路径计算稳定摘要：

```text
packages/nollm-core/src
packages/nollm-core/tests
packages/nollm-snapshot/src
packages/nollm-trace/src
必要的Lab生成产物与验证脚本
```

4. 新增：

```powershell
python lab/nollm-lab/m1/run_core_capability_validation.py --check
```

其在最终 Bundle HEAD 上：
- 不改工作树；
- 重新计算代码树摘要；
- 确认记录仍绑定相同代码；
- 若最终文档提交未改受验证代码，则通过。

5. 若最终 HEAD 修改任何受验证代码，必须重新生成记录并建立新的验证提交。

### 通过条件

```text
最终Bundle HEAD运行所有check后工作树干净；
能力记录不会因纯文档提交产生伪差异；
记录真实绑定受验证代码；
LAB +2%成立。
```

---

## 11. 结果闸门：发行组合完整性修正

### 必须完成

1. `nollm-bare`：
   - Core only；
   - entrypoint与公开API一致。
2. `nollm-minimal`：
   - runtime明确包括 Core、Snapshot、Access；
   - defaults或composition明确包括：
     - `FileEvidenceStore`
     - `FileHandleStore`
     - `SnapshotService`
     - `trace=None`
3. `nollm-debug`：
   - extends Minimal；
   - 增加Trace；
   - Lab工具只在development，不作为runtime。
4. 增加manifest schema验证和组合导入测试。
5. README/ARCHITECTURE/ROADMAP不得把旧V2.2称为当前活动项目书。
6. History/Audit/OpenClaw保持 `0%`，不借此任务启动其能力。

### 通过条件

```text
发行组合元数据足以描述真实构造所需组件；
Distribution不实现业务逻辑；
DISTRIBUTIONS +2%成立；
未受影响模块无变化。
```

---

## 12. 结果闸门：最终能力、向量与进度账回填

生成或更新：

```text
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
docs/project/CORE_SNAPSHOT_TRACE_ACCESS_LAB_DISTRIBUTIONS_BASELINE_TRUTH_REPORT.md
docs/validation/CORE_CAPABILITY_VALIDATION.json
docs/validation/CORE_CAPABILITY_VALIDATION_REPORT.md
```

必须记录：

### 实际推进向量

```text
预计向量
实际向量
各模块偏差
偏差原因
代价
下一承接模块或恢复条件
```

### 实际完成度

```text
模块 | 任务前 | 目标 | 实际 | 生命周期状态 | 置信度 |
最近验证代码提交/代码树摘要 | 已验证能力 | 主要缺口 | 下一候选动作
```

不得直接复制目标值。

允许结论：

```text
CAPABILITY_VALIDATED_AT_<validated_code_commit>
ACTIVE_BASELINE_AT_<bundle_head>
```

前提是明确区分：

- 能力绑定代码提交/代码树摘要；
- 活动基线绑定最终 Bundle HEAD；
- 最终 HEAD 与已验证代码之间只有经核验的非代码提交。

禁止：

```text
sealed
final closure
永不修改
自动进入M2
```

---

## 13. 独立包和项目回归

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
```

### Core

```powershell
$env:PYTHONPATH = "$PWD/packages/nollm-core/src"
python -m pytest -q packages/nollm-core/tests
```

### Snapshot

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src"
) -join ";"
python -m pytest -q packages/nollm-snapshot/tests
```

### Trace

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-trace/src"
) -join ";"
python -m pytest -q packages/nollm-trace/tests
```

### Access

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-access/src"
) -join ";"
python -m pytest -q packages/nollm-access/tests
```

### 统一回归

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-trace/src",
  "$PWD/packages/nollm-access/src",
  "$PWD/reference/python"
) -join ";"

python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py --report `
  docs/architecture/module-ownership/CORE_SNAPSHOT_TRACE_ACCESS_LAB_DISTRIBUTIONS_BASELINE_TRUTH_BOUNDARY_REPORT.json

python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests
python -m pytest -q packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests
python -m pytest -q reference/python/tests/m0
python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py
python -m pytest -q reference/python/tests/grf

python lab/nollm-lab/geometry/generate_compiled_templates.py --check
python lab/nollm-lab/m1/run_geometry_parity.py
python lab/nollm-lab/m1/run_core_capability_validation.py --check
python lab/nollm-lab/m1/run_m1_minimal_e2e.py

python -m compileall -q `
  packages/nollm-core/src `
  packages/nollm-snapshot/src `
  packages/nollm-trace/src `
  packages/nollm-access/src

git diff --check
git status --short
```

若仅缺 `zstandard`，只允许精确排除既有两项历史压缩测试并明确记录；不得扩大排除。

---

## 14. 真实停止条件

仅在以下情况停止：

```text
1. 移出Core研究型Profile元数据会改变9/9几何语义且无法兼容；
2. 能力验证无法在不自引用Git hash的情况下形成稳定代码源摘要；
3. Snapshot真实结构差异必须引入History语义；
4. Access普通失败回滚无法在可信组合合同下维持；
5. production cycle或边界违规无法清零；
6. 修正活动项目书会与最高原则产生无法解释的冲突；
7. 大规模环境失败无法定位。
```

不要因以下问题停止：

```text
历史测试名称；
文档移动；
旧V2.2项目书归档；
测试数量变化；
公共Profile API减少；
既有两项zstandard环境依赖；
进度百分比下调。
```

---

## 15. 交付要求

必须：

```text
所有修改commit；
工作树干净；
仓库外生成一个完整历史Git bundle；
验证Bundle；
只交一个Bundle。
```

建议 Bundle 名称：

```text
nollm_cstald_baseline_correction_20260711_<shorthead>.bundle
```

Codex 最终回复只报告：

```text
branch / final HEAD / validated code commit / code tree digest
预计推进向量 / 实际推进向量 / 偏差
全部模块任务前后实际完成度
活动项目依据与AGENTS修正
Core Profile边界与artifact digest
SnapshotDiff合同
Access持久合同与失败矩阵
Trace回归
Distribution组合
package tests / boundary / cycles / GRF
known limitations
Bundle filename / SHA-256
```

不得声称：

```text
Core已封版
项目最终闭合
M2自动启动
恶意Python调用已被隔离
OpenClaw / LLM / Memory Quality / PB scale已验证
```
