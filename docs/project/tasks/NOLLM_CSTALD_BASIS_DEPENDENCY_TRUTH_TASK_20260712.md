# Nollm CSTALD 活动依据与公共依赖真值任务书

**模块缩写**：`C=Core | S=Snapshot | T=Trace | A=Access | L=Lab | D=Distributions`
**日期**：2026-07-12
**任务文件名**：`NOLLM_CSTALD_BASIS_DEPENDENCY_TRUTH_TASK_20260712.md`
**性质**：活动项目依据纠正、所有权清单真实性修正、公共依赖边界纯化和基线重新验证
**输入 Bundle**：`nollm_cstald_baseline_correction_20260711_3efae51.bundle`
**输入 Bundle SHA-256**：`b21018150723f4bbd6a17eaf7909f003275682349ccd78b80b41c83aa52e012f`
**输入分支**：`codex/cstald-baseline-correction`
**输入 HEAD**：`3efae5110ee283d29fd7fe03422240794eb1e467`
**已验证代码提交**：`a1c0b676c794ec7ca2bf20408cdf897bf2793c09`
**建议分支**：`codex/cstald-basis-dependency-truth`
**主环境**：Windows 10/11 + PowerShell
**交付**：全部修改提交、工作树干净、仓库外一个完整历史 Git bundle
**结论边界**：本任务只形成绑定具体代码树与最终 HEAD 的能力记录或活动基线，不宣称封版、最终闭合或自动进入后续阶段。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +5% | DISTRIBUTIONS +5%

主方向：
纠正仓库中的活动项目依据和机器所有权真值；使 Lab 只依赖 Core 公共合同，
不再绑定 Core 私有实现；重新验证前一任务已获得的 Core、Snapshot、Trace、
Access 和发行组合能力。

范围变化：
无。模块章程和长期能力目标不扩大；不新增产品能力，不重开安全化 capability 路线。
```

### 向量说明

- `CORE +5%`：消除 Lab 对 Core 私有子模块的依赖，使 Core 内部实现真正可演进；保持公共 API 不扩张。
- `LAB +5%`：Build/Compiler/Parity/E2E 工具拥有自己的编译期辅助实现，或仅使用 Core 根公共 API。
- `DISTRIBUTIONS +5%`：当前项目书、当前状态、进度账、当前任务和机器所有权清单形成一致的活动依据。
- `SNAPSHOT / TRACE / ACCESS 0%`：不改变能力，只做高风险回归。
- `HISTORY / AUDIT / OPENCLAW 0%`：确认无意外依赖或范围变化。

每个结果闸门开始、结束时复述当前向量。若新增模块或任一模块实际偏差超过 `5%`，必须更新范围、向量和状态记录。

---

## 1. 上一 Bundle 审核基线

### 1.1 Git 与 Bundle

```text
Bundle verify：通过
完整历史：通过
分支：codex/cstald-baseline-correction
HEAD：3efae5110ee283d29fd7fe03422240794eb1e467
已验证代码提交：a1c0b676c794ec7ca2bf20408cdf897bf2793c09
初始工作树：clean
```

### 1.2 已复现工程能力

```text
Manifest = 1470 / 1470
unclassified = 0
production violations = 0
production cycles = []
migration findings = 7

Core = 39 passed
Snapshot = 7 passed
Trace = 3 passed
Access = 32 passed
M0 = 24 passed
architecture / forbidden / hygiene = 8 passed
geometry parity = 9 / 9
Core capability validation = 25 / 25
Minimal E2E = passed
```

GRF 外部审计：

```text
109 passed
1 skipped
2 failed only because zstandard was unavailable
```

### 1.3 必须保留的成果

```text
Core 公共面已移除 Store/client/capability/security 对象；
Core Profile 已缩为最小运行时视图；
模板 artifact SHA-256 在 Runtime 初始化时核对；
HandleBinding 严格类型化；
SnapshotDiff 已实现有限结构差异；
Trace 与 Access 包测试通过；
能力验证 --check 在最终 HEAD 上只读且工作树干净；
Bare / Minimal / Debug 组合元数据已补齐；
无外置关系索引、Python 语义 Placement 或 graph/vector/embedding 主路径。
```

---

## 2. 上一任务外部实际推进向量归一化

上一任务书使用了不符合现行规则的 `+3% / +2%` 粒度。历史任务报告保留原文，但当前进度账必须按5%粒度或区间归一化。

外部审核归一化实际向量：

```text
CORE +5% | SNAPSHOT +5% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +0~5% | DISTRIBUTIONS 0%
```

依据：

- Core Profile、artifact校验和能力记录真实推进。
- SnapshotDiff 和 Access 持久合同真实推进。
- Trace只做回归。
- Lab研究元数据已迁入，但仍直接导入6处Core私有子模块，故只计 `+0~5%`。
- 发行组合文件进步，但活动项目书、当前治理文件和Manifest分类不真实，故D净推进计 `0%`。

本任务不得直接复制上一任务“所有偏差为零”的自报结论。

---

## 3. 任务开始前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED`，尚非活动基线 | 75% | 高 | 39项包测试；9/9 parity；25维能力验证；私有Store；显式入口Recall | Lab仍依赖Core私有子模块，Core内部实现尚不能自由演进 | 是，公共依赖边界和高风险回归 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 7项包测试；SnapshotDiff；create/restore/clone/verify | 跨版本迁移和增量快照未验证 | 是，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 3项包测试；多Sink与Inspector；状态隔离 | 深度性能可视化有限 | 是，仅回归 |
| ACCESS | `ACTIVE_BASELINE`候选 | 60% | 中高 | 32项包测试；严格HandleBinding；普通失败矩阵 | 真实Host决策和多进程协调未验证 | 是，仅回归 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程与边界存在 | 未实现 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程与边界存在 | 未实现 | 否 |
| OPENCLAW | `LEGACY_REFERENCE` | 25% | 中低 | 迁移资产保留；Live暂停 | 无当前Access/LLM E2E | 否 |
| LAB | `IMPLEMENTED` | 50% | 中 | Research Profile、生成器、9/9 parity、validator | 6处Core私有子模块导入；Build工具绑定Core内部结构 | 是，直接修改 |
| DISTRIBUTIONS | `IMPLEMENTED`，活动依据不可信 | 40% | 中低 | Bare/Minimal/Debug导入通过；组合元数据完整 | 活动项目书错误；当前治理文件被Manifest标成Legacy；AGENTS仍含硬编码项目路径 | 是，直接修改 |

---

## 4. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 75% | 80% | +5% | 无Lab私有消费者；内部实现与公共API边界真实 | 私有导入扫描；Core独立测试；9/9 parity；25维validator | 跨进程、PB规模和真实LLM未验证 |
| SNAPSHOT | 50% | 50% | 0% | 无变化，确认SnapshotDiff与原子恢复不回退 | 7项包测试及组合回归 | 版本迁移、增量快照未验证 |
| TRACE | 40% | 40% | 0% | 无变化，确认Trace状态隔离不回退 | 3项包测试及Core parity | 深度可视化未完成 |
| ACCESS | 60% | 60% | 0% | 无变化，确认严格绑定和失败矩阵不回退 | 32项包测试及Minimal E2E | Host/LLM与多进程未验证 |
| HISTORY | 10% | 10% | 0% | 无变化 | 边界检查 | 未实现 |
| AUDIT | 10% | 10% | 0% | 无变化 | 边界检查 | 未实现 |
| OPENCLAW | 25% | 25% | 0% | 无变化 | 活动路径确认 | Live E2E未实现 |
| LAB | 50% | 55% | +5% | 编译、parity和E2E只使用公共Core合同或Lab自有辅助实现 | 私有导入扫描；生成器check；9/9 parity | Corpus与长压测未实施 |
| DISTRIBUTIONS | 40% | 45% | +5% | 活动项目依据唯一且正确；Manifest对治理文件分类真实；AGENTS泛用 | 活动Basis测试；Manifest truth测试；Docs一致性 | 安装器与版本协商未完成 |

---

## 5. 结果闸门：活动项目书与文档职责修正

### 必须完成

1. 仓库活动项目书必须采用当前V3.1 Core纯净性与可演进基线架构。
2. 不得继续把旧V3.0项目书提升为当前活动项目书。
3. V3.1项目书只定义：
   - 模块所有权；
   - 依赖方向；
   - 公共合同；
   - 可演进基线治理。
4. 从项目书移出：
   - 当前任务文件名；
   - 当前HEAD；
   - 当前执行阶段指针；
   - 临时禁止事项。
   这些只进入当前状态和当前任务书。
5. 旧V3.0与V2.2项目书标记为 `LEGACY_REFERENCE / SUPERSEDED`，并链接当前V3.1。
6. `ACTIVE_PROJECT.md` 只链接：
   - 当前V3.1项目书；
   - 当前状态；
   -持续模块进度账；
   - 当前授权任务；
   - 最近能力/基线报告。
7. 当前状态明确：
   - 输入HEAD；
   - 当前任务；
   - 审核中/已验证状态；
   - 不自动进入下一阶段。
8. README、ARCHITECTURE、ROADMAP不得复制当前任务和HEAD，只链接活动Basis并描述稳定架构。

### 必须新增或修正测试

```text
test_active_project_book_is_v31_and_role_correct.py
test_project_book_has_no_current_task_or_head.py
test_active_basis_links_exist_and_are_unique.py
test_legacy_project_books_are_not_active.py
```

### 通过条件

```text
活动项目书与Project Source一致；
项目书、状态、任务书职责单一；
未来更换任务不需要改项目书；
没有旧V3.0/V2.2反向覆盖。
```

---

## 6. 结果闸门：AGENTS 泛用化

将根目录 `AGENTS.md` 收缩为泛用、精简的仓库执行策略。

允许内容：

```text
开工前核对任务输入、branch、HEAD、status和最近提交；
不擅自reset/clean/改写历史/扩大范围；
Windows-first；
大跨度任务使用内部检查点；
代码、测试和必要文档同步；
所有修改提交并保持clean tree；
仓库外生成并验证完整历史Bundle；
报告区分事实、假设、环境依赖、限制和未验证事项。
```

禁止内容：

```text
任何NOLLM_文件名或日期；
当前项目路线、阶段、HEAD或推进向量；
具体模块名称、职责或架构；
当前任务入口或撤回任务；
具体capability、callback、OpenClaw或临时禁令。
```

新增测试：

```text
test_agents_is_generic_concise_and_path_free.py
```

建议约束：

```text
不超过15行；
不含"NOLLM_"；
不含8位日期；
不含Core/Access/OpenClaw等项目模块名；
不含current task/current stage等当前指针。
```

---

## 7. 结果闸门：机器所有权清单的活动治理真值

### 当前错误

以下当前活动文件被Manifest标成：

```text
owner = LEGACY
lifecycle_status = HISTORICAL
review_status = AUTO_CANDIDATE
```

包括：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
docs/project/tasks/NOLLM_CSTALD_BASELINE_CORRECTION_TASK_20260711.md
docs/project/CORE_SNAPSHOT_TRACE_ACCESS_LAB_DISTRIBUTIONS_BASELINE_TRUTH_REPORT.md
```

同时旧M1任务仍被标为ACTIVE governance。

### 必须完成

1. Manifest生成器不得再依赖M0C1、旧任务文件名或历史固定路径识别治理文件。
2. 从 `ACTIVE_PROJECT.md` 的实际链接动态解析活动治理文件，或建立单一机器可读 `ACTIVE_GOVERNANCE.json`。
3. 当前项目书、状态、进度账、任务书和最近报告必须：
   - `lifecycle_status=ACTIVE`
   - `public_api=governance`
   - `review_status=CODE_REVIEWED`或等价人工确认状态。
4. 被替代项目书、任务书和报告必须是：
   - `LEGACY_REFERENCE`或`HISTORICAL`
   - 不得仍被分类为当前治理。
5. `ACTIVE_PROJECT.md` 自身必须是活动治理文件。
6. Manifest `--check` 必须只读。
7. 新增负例：改变ACTIVE_PROJECT链接但不更新Manifest时，校验必须失败。

### 必须新增测试

```text
test_manifest_classifies_linked_governance_as_active.py
test_manifest_classifies_unlinked_tasks_as_historical.py
test_manifest_has_no_m0c1_filename_heuristic.py
test_active_basis_change_requires_manifest_refresh.py
```

### 通过条件

```text
机器清单与实际活动Basis一致；
当前治理文件不再被归为Legacy；
旧任务不再被归为Active；
production violations=0；
production cycles=[]。
```

---

## 8. 结果闸门：Lab 只依赖Core公共合同

### 当前错误

Lab当前至少存在6处私有Core子模块导入：

```text
nollm_core.axial
nollm_core.coverage_template
nollm_core.fixed_point
nollm_core.compiled_templates
nollm_core.storage
```

### 必须完成

1. `lab/nollm-lab/**` 不得导入 `nollm_core.<submodule>`。
2. Lab可：
   - 从 `nollm_core` 根包导入明确公共符号；或
   - 在Lab内部拥有编译期Axial、Q16 normalization、canonical JSON等辅助实现。
3. 不得为了方便Lab而扩大Core公共API，除非该符号对真正Core调用方具有长期公共价值，并更新项目书/allowlist。
4. 建议实现：
   - Lab拥有自己的compile-only axial/ring helper；
   - Lab拥有自己的Q16 normalization；
   - Lab编译器生成canonical mapping/JSON，不依赖Core内部CompilerMetadata构造器；
   - parity通过公共`KernelRegistry`、`runtime_profile`、`expand_template`验证；
   - Minimal E2E使用本地canonical JSON helper，不导入`nollm_core.storage`。
5. 保持：
   - artifact SHA-256不变，或明确说明变化并证明9/9 parity与state identity兼容；
   - Core公共allowlist不扩张；
   - Core stdlib-only；
   - 生成器`--check`只读；
   - capability validator`--check`只读。

### 必须新增测试

```text
test_lab_imports_no_nollm_core_private_submodules.py
test_core_public_api_not_expanded_for_lab.py
```

### 通过条件

```text
Lab私有Core导入数=0；
Core内部实现可在不改Lab的情况下重构；
生成器、parity和E2E全部通过；
CORE +5%、LAB +5%成立。
```

---

## 9. 结果闸门：能力记录与进度账归一化

1. 保留 `validated_code_commit + validated_code_tree_digest` 模式。
2. 修改受验证代码后重新生成能力记录。
3. 最终纯文档提交不得修改受验证代码路径。
4. 最终HEAD运行：
   - generator `--check`
   - capability validator `--check`
   - Manifest `--check`
   后工作树必须干净。
5. 当前进度账所有百分比和推进向量使用5%粒度或区间。
6. 历史任务报告中的3%/2%原文可保留，但当前状态必须标明已归一化，不得继续作为活动向量。
7. 任务报告必须写：
   - 预计向量；
   - 实际向量；
   - 偏差；
   - 全部模块实际完成度；
   - 活动项目依据和Manifest真值验证结果。

允许结论：

```text
CAPABILITY_VALIDATED_AT_<code_commit>
ACTIVE_BASELINE_AT_<final_head>
```

前提是本任务全部通过。

---

## 10. 高风险回归：Snapshot、Trace、Access与发行组合

本任务不计划改变S/T/A能力，必须确认：

```text
Snapshot = 7项或更多测试通过；
SnapshotDiff行为不变；
Trace = 3项或更多测试通过；
Trace不进入Core state；
Access = 32项或更多测试通过；
HandleBinding和普通失败矩阵不回退；
Minimal E2E通过；
Bare/Minimal/Debug导入与组合元数据不回退；
History/Audit/OpenClaw保持0%。
```

若执行中必须修改S/T/A公共合同，立即更新任务范围、文件名建议和推进向量，不得静默修改。

---

## 11. 独立包与项目回归

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
  docs/architecture/module-ownership/CSTALD_BASIS_DEPENDENCY_TRUTH_BOUNDARY_REPORT.json

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

若仅缺 `zstandard`，只允许精确排除既有两项历史压缩测试并记录环境依赖。

---

## 12. 实际推进向量与状态回填

更新：

```text
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/CSTALD_BASIS_DEPENDENCY_TRUTH_REPORT.md
docs/validation/CORE_CAPABILITY_VALIDATION.json
docs/validation/CORE_CAPABILITY_VALIDATION_REPORT.md
```

必须记录：

```text
预计推进向量
实际推进向量
各模块偏差与原因
全部模块任务前/目标/实际完成度
validated_code_commit
validated_code_tree_digest
final bundle HEAD
活动项目书路径
当前任务路径
Manifest中活动治理文件的分类
Lab私有Core导入扫描结果
已知限制与未验证事项
```

不得直接复制目标值。

---

## 13. 真实停止条件

只在以下情况停止：

```text
1. V3.1项目书与最高原则存在无法解释的冲突；
2. 消除Lab私有Core导入必须扩大Core公共API或改变9/9几何语义；
3. 动态治理文件分类无法在不引入新模块体系的情况下实现；
4. production cycle或边界违规无法清零；
5. Snapshot/Trace/Access回归出现无法定位的真实功能丢失；
6. 大规模环境错误无法定位。
```

不要因以下问题停止：

```text
项目书改名或移动；
旧V3.0/V2.2归档；
Manifest行数变化；
测试数量变化；
历史报告保留旧向量；
既有两项zstandard环境依赖。
```

---

## 14. 交付要求

必须：

```text
所有修改commit；
工作树干净；
仓库外生成并验证一个完整历史Git bundle；
只交一个Bundle。
```

建议文件名：

```text
nollm_cstald_basis_dependency_truth_20260712_<shorthead>.bundle
```

最终回复只报告：

```text
branch / final HEAD / validated code commit / code tree digest
预计推进向量 / 实际推进向量 / 偏差
全部模块实际完成度
活动项目书、状态、任务与AGENTS修正
Manifest活动治理真值
Lab私有Core导入扫描
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
