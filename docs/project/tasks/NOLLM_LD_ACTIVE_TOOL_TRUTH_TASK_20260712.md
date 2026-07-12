# Nollm LD 活动工具与机器清单真实性任务书

**模块缩写**：`L=Lab | D=Distributions`
**日期**：2026-07-12
**任务文件名**：`NOLLM_LD_ACTIVE_TOOL_TRUTH_TASK_20260712.md`
**性质**：Lab 活动资产清理、机器所有权真值修正、活动基线证据回填
**输入 Bundle**：`nollm_cstald_basis_dependency_truth_20260712_0735806.bundle`
**输入 Bundle SHA-256**：`9e26e7fab747cdba8aa44345f0be53dcedbad2e7c5bc2183abec51c8d97a5cb4`
**输入分支**：`codex/cstald-basis-dependency-truth`
**输入 HEAD**：`0735806c303ce7d1f61e0c38412b3784a31f16b9`
**已验证代码提交**：`7ff9690edeca71806bf5783787ef81367b9eb167`
**已验证代码树摘要**：`b8a17134c494d3610c306723281bcdede7c130de41ec010d290a02e093ecbd27`
**建议分支**：`codex/ld-active-tool-truth`
**主环境**：Windows 10/11 + PowerShell
**交付**：全部修改提交、工作树干净、仓库外一个完整历史 Git bundle
**结论边界**：只形成绑定具体代码树与最终 HEAD 的能力记录或活动基线，不宣称封版、最终闭合或自动进入后续阶段。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +5% | DISTRIBUTIONS +5%

主方向：
把已失效的历史 M1 对抗/复现脚本从活动 Lab 资产中准确降级，
建立“活动 Lab 文件必须能通过当前公共合同导入”的机器 Gate，
并使 Manifest、当前状态、进度账和活动基线报告保持一致。

范围变化：
无。模块章程和长期目标不扩大；不修改 Core 公共 API，
不恢复 capability/security 路线，不新增产品、模型、Host 或规模能力。
```

### 向量说明

- `LAB +5%`：活动 Lab 工具目录真实、可导入、可执行；历史对抗脚本保留但不再伪装为活动能力。
- `DISTRIBUTIONS +5%`：机器 Manifest、活动报告和进度账准确反映 Lab 生命周期及活动资产。
- `CORE / SNAPSHOT / TRACE / ACCESS 0%`：不改变能力，只做高风险回归。
- `HISTORY / AUDIT / OPENCLAW 0%`：确认无意外依赖或范围变化。

每个结果闸门开始、结束时复述当前向量。若新增受影响模块，或任一模块实际偏差超过 `5%`，必须更新任务范围、向量和状态记录。

---

## 1. 输入 Bundle 审核基线

### 1.1 Git 与 Bundle

```text
Bundle verify：通过
完整历史：通过
分支：codex/cstald-basis-dependency-truth
HEAD：0735806c303ce7d1f61e0c38412b3784a31f16b9
输入工作树：clean
输入提交：
  7ff9690 Correct CSTALD basis and dependency truth
  9bb3135 Record CSTALD dependency truth baseline
  0735806 Correct CSTALD boundary evidence inventory
```

### 1.2 已复现工程能力

```text
Manifest = 1479 / 1479
unclassified = 0
production violations = 0
production cycles = []
migration findings = 7

Core = 39 passed
Snapshot = 7 passed
Trace = 3 passed
Access = 32 passed
M0 = 32 passed
architecture / forbidden / hygiene = 8 passed
geometry parity = 9 / 9
Core capability validation = 25 / 25
Minimal E2E = passed

GRF external audit:
109 passed
1 skipped
2 failed only because zstandard was unavailable
```

独立包 Gate 均通过，最终 HEAD 上 generator、Manifest 和 capability validator 的 `--check` 均保持工作树干净。

### 1.3 必须保留的成果

```text
V3.1 是唯一活动项目书；
V3.0 / V2.2 已降级为 LEGACY_REFERENCE / SUPERSEDED；
AGENTS.md 已精简为泛用执行策略；
活动治理文件已由 Manifest 标记为 ACTIVE governance；
Lab 对 nollm_core.<private_submodule> 的直接导入数为 0；
Core 公共 API 未因 Lab 扩张；
9/9 Geometry parity 保持；
25/25 Core capability validator 保持；
Snapshot / Trace / Access 合同未回退；
production violations = 0；
production cycles = []。
```

不得回退上述成果。

---

## 2. 本轮发现的真实性阻断

Manifest 当前将以下文件标记为：

```text
owner = LAB
lifecycle_status = ACTIVE
migration_action = KEEP
review_status = DEPENDENCY_REVIEWED
```

但它们无法从当前 Core 公共 API 导入：

```text
lab/nollm-lab/m1/reproduce_m1c8_input_blockers.py
  缺失：FileCoreStateStore

lab/nollm-lab/m1/run_m1_public_api_adversarial_matrix.py
  缺失：CompilerMetadata
  缺失：CoverageTemplateCompiler
  缺失：FileCoreStateStore
```

确定性复现：

```text
python lab/nollm-lab/m1/reproduce_m1c8_input_blockers.py --help
→ ImportError

python lab/nollm-lab/m1/run_m1_public_api_adversarial_matrix.py --help
→ ImportError
```

这两份文件记录的是已经撤回的 M1-C7/M1-C8 capability、callback fence、影子 Store 和恶意调用路线。它们具有历史追溯价值，但不属于当前活动 Lab 能力。

当前测试只证明：

```text
Lab 不导入 nollm_core.<private_submodule>
```

尚未证明：

```text
Manifest 标记为 ACTIVE 的 Lab Python 文件可以通过当前公共 API 导入。
```

因此，当前报告中的“Lab 公共依赖真值”和“所有活动 Lab 资产有效”尚未成立。

---

## 3. 上一任务推进向量外部复算

上一任务预计及交付方自报：

```text
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +5% | DISTRIBUTIONS +5%
```

本次外部审核复算：

```text
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% |
LAB +0~5% | DISTRIBUTIONS +0~5%
```

偏差原因：

- Core 已无 Lab 私有子模块消费者，`CORE +5%` 成立。
- Lab 编译器、Parity 与 Minimal E2E 已使用公共合同，但两份 Manifest 标记为 ACTIVE 的历史脚本已失效，因此 `LAB +5%` 不能无条件确认。
- 活动 Basis 和治理文件分类已修正，但机器清单仍把失效历史脚本标成 ACTIVE，因此 `DISTRIBUTIONS +5%` 不能无条件确认。

本任务不得直接复制上一报告“全部偏差为零”的结论。

---

## 4. 任务开始前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 80% | 高 | 39项测试；9/9 parity；25维能力验证；无Lab私有子模块消费者 | 跨进程恢复、规模和真实LLM未验证 | 是，仅高风险回归，预计0% |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 7项测试；SnapshotDiff；原子create/restore/clone/verify | 跨版本迁移、增量快照未验证 | 是，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 3项测试；多Sink、Inspector与状态隔离 | 深度性能可视化有限 | 是，仅回归 |
| ACCESS | `ACTIVE_BASELINE`候选 | 60% | 中高 | 32项测试；严格HandleBinding；普通失败矩阵 | 真实Host决策、多进程协调未验证 | 是，仅回归 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程与边界存在 | 未实现 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程与边界存在 | 未实现 | 否 |
| OPENCLAW | `LEGACY_REFERENCE` | 25% | 中低 | 迁移资产保留；Live暂停 | 无当前Access/LLM E2E | 否 |
| LAB | `IMPLEMENTED`，活动资产真值不足 | 50% | 中 | 编译器、生成器、9/9 parity、validator可运行 | 两份历史对抗脚本被误标ACTIVE且无法导入；无活动工具导入Gate | 是，直接修改 |
| DISTRIBUTIONS | `IMPLEMENTED`，活动清单真值不足 | 40% | 中 | V3.1 Basis、治理分类、Bare/Minimal/Debug已建立 | Manifest将失效历史Lab脚本标为ACTIVE；报告/进度账夸大 | 是，直接修改 |

---

## 5. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 80% | 80% | 0% | 无能力变化；确认公共 API 不为历史 Lab 扩张 | Core独立测试；allowlist；9/9 parity；25维validator | 跨进程、PB规模、真实LLM未验证 |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | 7项测试及组合回归 | 版本迁移、增量快照未验证 |
| TRACE | 40% | 40% | 0% | 无变化 | 3项测试及组合回归 | 深度可视化未完成 |
| ACCESS | 60% | 60% | 0% | 无变化 | 32项测试及Minimal E2E | Host/LLM、多进程未验证 |
| HISTORY | 10% | 10% | 0% | 无变化 | 边界检查 | 未实现 |
| AUDIT | 10% | 10% | 0% | 无变化 | 边界检查 | 未实现 |
| OPENCLAW | 25% | 25% | 0% | 无变化 | 活动路径确认 | Live E2E未实现 |
| LAB | 50% | 55% | +5% | 活动工具清单真实；所有ACTIVE Python资产可通过当前公共合同导入；历史脚本保留为Legacy | Manifest生命周期；活动工具import smoke；生成器/parity/E2E | Corpus、长压测未实施 |
| DISTRIBUTIONS | 40% | 45% | +5% | Manifest与活动Lab资产一致；报告和进度账不夸大 | Manifest truth test；活动工具清单测试；Basis/ledger一致性 | 安装器、版本协商未完成 |

---

## 6. 结果闸门：Lab 活动资产逐项分类

### 必须完成

对 `lab/nollm-lab/**` 全部文件逐项确认：

```text
ACTIVE_LIBRARY
ACTIVE_TOOL
ACTIVE_FIXTURE
LEGACY_REFERENCE
HISTORICAL_RESULT
```

分类必须以当前用途和可执行性为依据，不得仅因文件位于 `lab/` 就默认 ACTIVE。

至少处理：

```text
lab/nollm-lab/m1/reproduce_m1c8_input_blockers.py
lab/nollm-lab/m1/run_m1_public_api_adversarial_matrix.py
```

默认处理方向：

1. 移入：
   ```text
   lab/nollm-lab/history/m1/
   ```
   或等价明确历史目录；
2. 生命周期改为：
   ```text
   LEGACY_REFERENCE / HISTORICAL
   ```
3. 保留原始内容和 Git 历史；
4. 增加简短 README，说明：
   - 它们复现已撤回的 capability/security 路线；
   - 依赖当时公共 API；
   - 不属于当前活动验证；
   - 不要求当前 Core 为其恢复旧公共符号。
5. 不得通过重新导出以下对象使旧脚本恢复：
   ```text
   FileCoreStateStore
   CompilerMetadata
   CoverageTemplateCompiler
   CoreClientLease
   CoreTransaction
   capability / binder / writer authority
   ```

若选择保留任何脚本为 ACTIVE，必须改写为当前公共合同且通过本任务新增的 import/entrypoint Gate。

### 通过条件

```text
活动与历史Lab资产边界真实；
历史脚本得到保留而非删除；
Core公共API不扩张；
LAB +5%方向成立。
```

---

## 7. 结果闸门：Manifest 的 Lab 生命周期真值

### 必须完成

更新 Manifest 生成器和模块章程，使：

```text
lab/nollm-lab/history/** -> LAB + LEGACY_REFERENCE/HISTORICAL
当前编译器、生成器、parity、validator、Minimal E2E -> LAB + ACTIVE
历史对抗/复现脚本 -> 非ACTIVE
```

不得继续使用：

```text
任何 lab/nollm-lab/** 文件默认 ACTIVE
```

分类权威来源应保持单一。优先使用稳定目录约定与 Lab Charter，不新增重复的临时任务清单。

更新：

```text
docs/architecture/modules/NOLLM_LAB_CHARTER.md
tools/generate_module_ownership_manifest.py
tools/validate_module_ownership_manifest.py
MODULE_OWNERSHIP_MANIFEST.json/.csv
```

新增负例：

```text
历史目录脚本不得分类为 ACTIVE；
ACTIVE Lab 文件引用缺失公共符号时 Manifest 验证失败；
任务文件名或历史阶段号不得自动决定 ACTIVE。
```

### 通过条件

```text
Manifest中不存在失效ACTIVE Lab工具；
Lab历史资产保留且分类明确；
机器清单与实际可用性一致；
DISTRIBUTIONS +5%方向成立。
```

---

## 8. 结果闸门：活动 Lab 公共合同导入 Gate

新增：

```text
reference/python/tests/m0/test_active_lab_public_imports_resolve.py
reference/python/tests/m0/test_active_lab_entrypoints_import_cleanly.py
```

### 8.1 公共符号解析

对 Manifest 中：

```text
owner = LAB
lifecycle_status = ACTIVE
file_type = py
```

的文件执行 AST 检查：

1. 禁止：
   ```text
   import nollm_core.<submodule>
   from nollm_core.<submodule> import ...
   ```
2. 对：
   ```text
   from nollm_core import Symbol
   ```
   每个 `Symbol` 必须真实存在于 `nollm_core.__all__`。
3. 同样检查 `nollm_access`、`nollm_snapshot`、`nollm_trace` 的根公共导出。
4. 不得以动态 `getattr`、`__import__` 或字符串导入绕过测试。

### 8.2 活动文件导入 Smoke

在隔离 `PYTHONPATH` 下导入所有 ACTIVE Lab Python 文件：

```text
packages/nollm-core/src
packages/nollm-snapshot/src
packages/nollm-trace/src
packages/nollm-access/src
reference/python（仅经章程允许的Legacy validation）
```

要求：

```text
模块导入无 ImportError；
导入不得修改工作树；
导入不得执行长任务；
导入不得启动OpenClaw、模型、Corpus或网络。
```

对明确 CLI 工具，可增加 `--help` Smoke；但不得用 `--help` 代替模块导入真值。

### 通过条件

```text
ACTIVE Lab Python import failures = 0；
missing public root symbols = 0；
private submodule imports = 0；
导入后工作树干净。
```

---

## 9. 结果闸门：活动 Basis、报告与进度账回填

更新：

```text
docs/project/ACTIVE_PROJECT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
docs/project/LD_ACTIVE_TOOL_TRUTH_REPORT.md
docs/project/tasks/NOLLM_LD_ACTIVE_TOOL_TRUTH_TASK_20260712.md
```

### 必须记录

上一任务实际向量：

```text
CORE +5%
SNAPSHOT 0%
TRACE 0%
ACCESS 0%
HISTORY 0%
AUDIT 0%
OPENCLAW 0%
LAB +0~5%
DISTRIBUTIONS +0~5%
```

不得继续记录“上一任务全部偏差为零”。

本任务完成后重新计算：

```text
预计推进向量
实际推进向量
各模块偏差
实际完成度
置信度
最近验证代码提交/代码树摘要
已验证能力
主要缺口
下一候选动作
```

允许结论：

```text
CAPABILITY_VALIDATED_AT_7ff9690...
ACTIVE_BASELINE_AT_<final_head>
```

前提：

```text
所有ACTIVE Lab工具可导入；
Manifest生命周期真值通过；
所有只读check保持工作树干净；
最终HEAD之后无未验证代码改动。
```

禁止：

```text
sealed
final closure
永不修改
自动进入下一阶段
```

---

## 10. 模块独立与跨模块回归

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
```

### 独立包

```powershell
$env:PYTHONPATH = "$PWD/packages/nollm-core/src"
python -m pytest -q packages/nollm-core/tests

$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src"
) -join ";"
python -m pytest -q packages/nollm-snapshot/tests

$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-trace/src"
) -join ";"
python -m pytest -q packages/nollm-trace/tests

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
  docs/architecture/module-ownership/LD_ACTIVE_TOOL_TRUTH_BOUNDARY_REPORT.json

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
  packages/nollm-access/src `
  lab/nollm-lab

git diff --check
git status --short
```

若仅缺 `zstandard`，只允许精确排除既有两项历史压缩测试并明确记录。

---

## 11. Final Gate 必须满足

```text
Manifest tracked = git ls-files；
unclassified = 0；
production violations = 0；
production cycles = []；

ACTIVE Lab private submodule imports = 0；
ACTIVE Lab missing public root symbols = 0；
ACTIVE Lab import failures = 0；

历史M1对抗脚本保留但不再ACTIVE；
Core公共API未为历史脚本扩张；
9/9 Geometry parity；
25/25 Core capability；
Snapshot / Trace / Access包测试不回退；
Minimal E2E通过；
所有--check只读；
Final Gate后工作树干净；
完整历史Bundle验证通过。
```

---

## 12. 真实停止条件

只在以下情况停止：

```text
1. 失效历史脚本仍是当前验证不可替代输入；
2. 将历史脚本降级会导致9/9 parity或25维Core能力验证丢失；
3. 活动Lab文件无法通过公共API且只能扩大Core公共面解决；
4. Manifest无法表达Lab ACTIVE与LEGACY_REFERENCE的真实区别；
5. production cycle或边界违规无法清零；
6. 大规模环境失败无法定位。
```

不要因以下问题停止：

```text
历史脚本文件移动；
旧文档链接更新；
测试数量变化；
Manifest行数变化；
历史阶段编号保留在history目录；
既有两项zstandard环境依赖。
```

---

## 13. 交付要求

必须：

```text
全部修改commit；
工作树干净；
仓库外生成一个完整历史Git bundle；
验证Bundle；
只交一个Bundle。
```

建议 Bundle 名称：

```text
nollm_ld_active_tool_truth_20260712_<shorthead>.bundle
```

Codex 最终回复只报告：

```text
branch / final HEAD / validated code commit / code tree digest
预计推进向量 / 实际推进向量 / 偏差
全部模块任务前后实际完成度
Lab活动/历史资产迁移摘要
ACTIVE Lab import Gate
Manifest / boundary / cycles
package tests / M0 / architecture / GRF
9/9 parity / 25维能力 / Minimal E2E
known limitations
Bundle filename / SHA-256
```

不得声称：

```text
Core已封版
项目最终闭合
自动进入下一阶段
恶意Python调用已被隔离
OpenClaw / LLM / Memory Quality / PB scale已验证
```
