# Nollm LD 活动资产分类与机器清单真实性任务书

**模块缩写**：`L=Lab | D=Distributions`
**日期**：2026-07-12
**任务文件名**：`NOLLM_LD_ASSET_TAXONOMY_TRUTH_TASK_20260712.md`
**性质**：Lab资产生命周期分类、活动Gate归属、Manifest真值和进度账纠正
**输入Bundle**：`nollm_ld_active_tool_truth_20260712_bdd9049.bundle`
**输入Bundle SHA-256**：`9926397f7e0a2ed9194208912f55c06a1dd2a514a0c3f2853ae58be73fecb52b`
**输入分支**：`codex/ld-active-tool-truth`
**输入HEAD**：`bdd90499b240eb65ecc089059c249a8eb862d570`
**已验证代码提交**：`7ff9690edeca71806bf5783787ef81367b9eb167`
**已验证代码树摘要**：`b8a17134c494d3610c306723281bcdede7c130de41ec010d290a02e093ecbd27`
**建议分支**：`codex/ld-asset-taxonomy-truth`
**主环境**：Windows 10/11 + PowerShell
**交付形式**：所有修改提交、工作树干净、仓库外单一完整历史Git Bundle
**结论边界**：只形成绑定具体代码树和最终HEAD的能力记录或活动基线，不宣称封版、最终闭合或自动进入后续阶段。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +5% | DISTRIBUTIONS +5%

主方向：
建立覆盖全部Lab所有权资产的生命周期与用途分类，
使“ACTIVE”只表示当前真实使用并有明确Gate覆盖的资产；
纠正Manifest、任务报告和模块进度账中的范围与推进向量失真。

范围变化：
无。模块章程和长期目标不扩大；不修改Core、Snapshot、Trace、
Access公共合同，不恢复capability/security路线，不启动新的产品能力。
```

### 0.1 向量解释

- `LAB +5%`：活动库、工具、Fixture、测试、验证和Legacy回归具有真实、可机检的类别与Gate。
- `DISTRIBUTIONS +5%`：Manifest、边界报告、活动Basis、任务报告和进度账准确表达资产生命周期。
- 其余模块 `0%`：只做高风险回归，不改变能力或公共合同。

### 0.2 执行纪律

1. 每个结果闸门开始和结束时复述推进向量。
2. 若新增受影响模块，或任何模块实际偏差超过 `5%`，必须更新任务范围、向量和状态记录。
3. Bundle审核时必须计算实际推进向量并解释偏差。
4. 不以Manifest行数、测试数量或文件移动数量替代能力推进证据。

---

## 1. 输入Bundle审核基线

### 1.1 Git事实

```text
Bundle verify：通过
完整历史：通过
分支：codex/ld-active-tool-truth
HEAD：bdd90499b240eb65ecc089059c249a8eb862d570
输入工作树：clean

新增提交：
bdd9049 Establish active Lab tool truth gate
```

### 1.2 已复现能力

```text
Manifest = 1485 / 1485
unclassified = 0
production violations = 0
production cycles = []
migration findings = 7

Core = 39 passed
Snapshot = 7 passed
Trace = 3 passed
Access = 32 passed
M0 = 38 passed
architecture / forbidden / hygiene = 8 passed
geometry parity = 9 / 9
Core capability validation = 25 / 25
Minimal E2E = passed
```

外部GRF审核：

```text
109 passed
1 skipped
2 failed only because zstandard was unavailable
```

### 1.3 必须保留的成果

```text
V3.1是唯一活动项目书；
AGENTS.md为泛用精简执行策略；
活动治理文件分类为ACTIVE；
两份M1-C7/M1-C8历史对抗脚本已R100移动到Lab/history；
历史脚本未被删除；
Core公共API未为历史脚本扩张；
lab/nollm-lab当前活动库与工具导入Gate通过；
9/9 Geometry、25维Core能力和S/T/A合同未回退；
production violations=0；
production cycles=[]。
```

不得回退上述成果。

---

## 2. 本轮审核发现

### 2.1 新增Gate只覆盖局部目录

当前：

```python
active_lab_contract_errors(...)
```

只处理：

```text
path.startswith("lab/nollm-lab/")
```

活动导入Smoke同样只枚举：

```text
lab/nollm-lab/**
```

但Manifest当前标记：

```text
LAB + ACTIVE 资产：548项
其中Python文件：414项
lab/nollm-lab下活动Python：仅7项
```

### 2.2 Manifest仍使用泛目录全部ACTIVE规则

以下路径被统一分类为 `LAB / ACTIVE`：

```text
lab/**
experiments/**
validation/**
reference/python/tests/**
examples/**
tools/**
packages/*/tests/**
```

当前数量大致为：

```text
reference/**        300
examples/**          88
experiments/**       60
packages tests       48
validation/**        36
lab/**               10
tools/**               5
其他                  1
```

其中包含：

```text
旧V1测试；
MT1测试；
旧V2模块验证；
GRF7/GRF8历史实验和结果；
旧OpenClaw示例；
历史Evidence结果；
当前包测试；
当前治理工具；
当前Lab编译器和能力验证。
```

这些资产用途和生命周期显然不同，不能继续共享一个笼统的：

```text
LAB / ACTIVE /
test, experiment, fixture, benchmark, or repository tool
```

### 2.3 全Manifest静态扫描仍发现未受Gate约束的冲突

按任务书原要求，对全部：

```text
owner=LAB
lifecycle_status=ACTIVE
file_type=py
```

执行同等静态扫描，发现：

```text
30项违规
涉及23个文件
```

包括：

```text
3项Core私有子模块/缺失根符号导入；
26项动态导入；
1项其他私有导入。
```

部分是包内部测试的合理实现细节，部分是旧验证脚本。它们不应被简单判定为活动工具违规，而应先被正确分类为：

```text
ACTIVE_TEST
ACTIVE_VALIDATION
LEGACY_REGRESSION
LEGACY_REFERENCE
```

### 2.4 当前任务向量在持续进度账中写错

任务预计向量是：

```text
CORE 0% | ... | LAB +5% | DISTRIBUTIONS +5%
```

`LD_ACTIVE_TOOL_TRUTH_REPORT.md`也如此记录。

但持续进度账写成：

```text
CORE +5% | ... | LAB +5% | DISTRIBUTIONS +5%
```

这与任务范围、代码改动和报告均冲突。

### 2.5 完成度被提前提升

当前报告将：

```text
LAB 55%
DISTRIBUTIONS 45%
```

并声称所有偏差为零。

在全部ACTIVE资产类别和Gate尚不真实前，本次外部审核不接受该提升。

---

## 3. 本轮外部复算

### 3.1 输入任务预计向量

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% |
LAB +5% | DISTRIBUTIONS +5%
```

### 3.2 外部复算实际向量

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% |
LAB +0~5% | DISTRIBUTIONS +0~5%
```

偏差原因：

- 两份明确失效的历史脚本已正确降级，属于实质推进。
- `lab/nollm-lab/**`当前活动工具Gate成立。
- 但Manifest仍把大量用途不同、未被当前Gate覆盖的资产统称ACTIVE。
- 持续进度账错误增加了 `CORE +5%`。
- 因此Lab和Distributions不能无条件确认完整 `+5%`。

---

## 4. 任务开始前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 80% | 高 | 39项测试；9/9 parity；25维能力；公共API未扩张 | 跨进程、规模、真实LLM未验证 | 是，仅回归，预计0% |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 7项测试；SnapshotDiff；原子恢复 | 版本迁移、增量快照未验证 | 是，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 3项测试；多Sink与状态隔离 | 深度性能可视化有限 | 是，仅回归 |
| ACCESS | `ACTIVE_BASELINE`候选 | 60% | 中高 | 32项测试；严格绑定；普通失败矩阵 | 真实Host决策、多进程协调未验证 | 是，仅回归 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程和边界存在 | 未实现 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程和边界存在 | 未实现 | 否 |
| OPENCLAW | `LEGACY_REFERENCE` | 25% | 中低 | 迁移资产保留；Live暂停 | 无当前Access/LLM E2E | 否 |
| LAB | `IMPLEMENTED`，分类真值不足 | 50% | 中 | 当前编译器/Parity/能力工具可用；两份历史脚本已降级 | 548项ACTIVE资产用途混杂；Gate仅覆盖7个Python文件；类别与Gate未绑定 | 是，直接修改 |
| DISTRIBUTIONS | `IMPLEMENTED`，Manifest真值不足 | 40% | 中 | 活动Basis、治理文件和基础Manifest可用 | 泛目录全部ACTIVE；向量记录错误；完成度提前提升 | 是，直接修改 |

---

## 5. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 80% | 80% | 0% | 无变化；公共API不为旧资产扩张 | Core独立Gate；9/9；25维能力 | 跨进程、规模、真实LLM |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | 7项测试 | 版本迁移、增量快照 |
| TRACE | 40% | 40% | 0% | 无变化 | 3项测试 | 深度可视化 |
| ACCESS | 60% | 60% | 0% | 无变化 | 32项测试；E2E | Host/LLM、多进程 |
| HISTORY | 10% | 10% | 0% | 无变化 | 边界检查 | 未实现 |
| AUDIT | 10% | 10% | 0% | 无变化 | 边界检查 | 未实现 |
| OPENCLAW | 25% | 25% | 0% | 无变化 | 活动路径确认 | Live E2E |
| LAB | 50% | 55% | +5% | 全部Lab资产具有真实类别、生命周期和明确Gate；活动工具可用，Legacy回归可追溯 | 资产分类测试；Gate覆盖测试；活动工具Import；兼容回归登记 | Corpus、长压测 |
| DISTRIBUTIONS | 40% | 45% | +5% | Manifest不再使用泛目录全部ACTIVE；报告、进度账和机器清单一致 | Manifest truth；向量一致性；Basis/ledger/report测试 | 安装器、版本协商 |

---

## 6. 结果闸门：Lab资产类别模型

### 必须建立的资产类别

在Manifest中增加稳定的 `asset_class`，或以同等明确、单一权威的字段表达：

```text
ACTIVE_LIBRARY
ACTIVE_TOOL
ACTIVE_FIXTURE
ACTIVE_TEST
ACTIVE_VALIDATION
ACTIVE_REPOSITORY_TOOL
LEGACY_REGRESSION
LEGACY_REFERENCE
HISTORICAL_RESULT
```

### 生命周期映射

建议：

```text
ACTIVE_*            -> lifecycle_status=ACTIVE
LEGACY_REGRESSION   -> lifecycle_status=MIGRATION_ASSET
LEGACY_REFERENCE    -> lifecycle_status=HISTORICAL或MIGRATION_ASSET
HISTORICAL_RESULT   -> lifecycle_status=HISTORICAL
```

不得仅通过历史阶段编号、文件名中的 `M1/GRF7/GRF8` 或顶层目录名决定类别。

### 每类的含义

- `ACTIVE_LIBRARY`：当前开发库，被当前活动工具或Gate使用。
- `ACTIVE_TOOL`：当前可执行工具，必须可导入、可运行基础Smoke。
- `ACTIVE_FIXTURE`：当前Gate使用的稳定输入，不要求执行。
- `ACTIVE_TEST`：当前包或治理测试，必须属于明确测试命令。
- `ACTIVE_VALIDATION`：当前验证入口，必须属于明确验证Gate。
- `ACTIVE_REPOSITORY_TOOL`：Manifest、边界、构建等当前仓库工具。
- `LEGACY_REGRESSION`：不代表当前能力，但仍由明确兼容回归运行。
- `LEGACY_REFERENCE`：只供迁移/研究追溯，不要求当前API兼容。
- `HISTORICAL_RESULT`：冻结结果、报告、收据或输出，不可执行。

### 通过条件

```text
所有LAB资产都有asset_class；
类别与生命周期组合合法；
无笼统“test, experiment, fixture, benchmark, or repository tool”作为最终分类；
任务推进向量不变。
```

---

## 7. 结果闸门：泛目录默认ACTIVE清零

### 必须删除的旧规则

不得继续：

```python
if path.startswith(("lab/", "experiments/", "validation/",
                    "reference/python/tests/", "examples/", "tools/")):
    lifecycle = "ACTIVE"
```

### 分类要求

#### package tests

```text
packages/*/tests/** -> ACTIVE_TEST
```

允许测试自身包的内部实现，但：

- 只能由对应独立包Gate运行；
- 不得被称为活动工具；
- 不得成为其他生产模块依赖。

#### 当前M0/架构测试

```text
当前Final Gate明确运行的治理测试 -> ACTIVE_TEST
```

必须记录对应测试命令或suite。

#### GRF兼容测试

```text
当前明确运行的GRF兼容测试 -> LEGACY_REGRESSION
```

它们可依赖Legacy，但不能作为当前Core/Lab能力完成度。

#### 旧V1、MT1、V2、OpenClaw测试

未属于当前Gate者默认：

```text
LEGACY_REFERENCE
```

只有存在明确当前Gate和继续维护理由时才可标 `LEGACY_REGRESSION`。

#### experiments

- 当前被活动Gate执行的实验/验证：`ACTIVE_VALIDATION`。
- 冻结结果目录：`HISTORICAL_RESULT`。
- 旧产品化、旧规模和已撤回路线：`LEGACY_REFERENCE`或`LEGACY_REGRESSION`。
- 不得因位于 `experiments/` 就ACTIVE。

#### validation

- 当前活动验证入口：`ACTIVE_VALIDATION`。
- 旧模块验证：`LEGACY_REGRESSION`或`LEGACY_REFERENCE`。
- 报告和固定输出：`HISTORICAL_RESULT`。

#### examples

- 当前发行组合或公共API使用的示例：`ACTIVE_FIXTURE`。
- 旧V1/OpenClaw/Dream示例：`LEGACY_REFERENCE`。
- 示例不得默认ACTIVE。

#### tools

- 当前Manifest/边界/测试矩阵工具：`ACTIVE_REPOSITORY_TOOL`。
- 旧Tool Manifest或旧CLI辅助：`LEGACY_REFERENCE`。

### 通过条件

```text
LAB ACTIVE数量有可解释来源；
每个ACTIVE资产存在明确Gate或当前消费者；
历史结果和旧路线不再ACTIVE；
不删除历史内容；
不扩大任何生产公共API。
```

---

## 8. 结果闸门：Gate覆盖字段与机器验证

每个 `ACTIVE_*` 或 `LEGACY_REGRESSION` 资产必须记录：

```text
validation_gate
```

示例：

```text
package:core
package:snapshot
package:trace
package:access
governance:m0
governance:architecture
compatibility:grf
lab:geometry-parity
lab:core-capability
lab:minimal-e2e
repository:manifest
repository:boundary
```

### 机器规则

1. `ACTIVE_LIBRARY / ACTIVE_TOOL / ACTIVE_FIXTURE / ACTIVE_VALIDATION / ACTIVE_REPOSITORY_TOOL`
   必须有当前消费者或明确Gate。
2. `ACTIVE_TEST` 必须属于实际执行的测试命令。
3. `LEGACY_REGRESSION` 必须属于显式兼容回归。
4. `LEGACY_REFERENCE / HISTORICAL_RESULT` 不得出现在活动Gate输入列表。
5. 当前Final Gate未执行的文件不得仅因历史上曾运行而标ACTIVE。
6. 任何Gate引用不存在文件时Manifest验证失败。
7. 任何ACTIVE资产没有 `validation_gate` 时Manifest验证失败。

### 通过条件

```text
ACTIVE资产Gate覆盖率=100%；
LEGACY_REGRESSION兼容Gate覆盖率=100%；
无Gate的历史资产均非ACTIVE；
Manifest --check只读。
```

---

## 9. 结果闸门：公共合同验证按资产类别执行

### 活动库、工具和验证

对：

```text
ACTIVE_LIBRARY
ACTIVE_TOOL
ACTIVE_VALIDATION
ACTIVE_REPOSITORY_TOOL
```

执行：

- 禁止导入当前模块私有子模块，除非模块章程明确允许；
- 根公共符号必须存在；
- 导入Smoke无副作用；
- CLI工具可加 `--help` Smoke；
- 不允许动态导入绕过公共合同。

### 活动测试

`ACTIVE_TEST` 不使用活动工具的统一规则。

允许：

- 测试自身包私有实现；
- 为边界测试使用受控动态导入；
- monkeypatch测试内部原子写入。

但必须：

- 归属明确的测试Gate；
- 不被生产或活动工具导入；
- 不改变公共API；
- 独立Gate通过。

### Legacy回归

`LEGACY_REGRESSION`：

- 允许依赖Legacy；
- 只在兼容回归环境运行；
- 不计入当前模块能力完成度；
- 失败必须区分代码回归与环境依赖。

### 历史与参考资产

不导入、不执行，只检查：

```text
文件存在
分类稳定
未进入活动Gate
未被生产依赖
```

### 通过条件

```text
公共合同规则不再误伤包内部测试；
活动工具不能通过目录过滤逃避检查；
所有类别均有适配的机器Gate。
```

---

## 10. 结果闸门：持续进度账与报告真值

修正：

```text
docs/project/LD_ACTIVE_TOOL_TRUTH_REPORT.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/ACTIVE_PROJECT.md
```

### 必须记录的上一任务实际向量

```text
CORE 0%
SNAPSHOT 0%
TRACE 0%
ACCESS 0%
HISTORY 0%
AUDIT 0%
OPENCLAW 0%
LAB +0~5%
DISTRIBUTIONS +0~5%
```

不得写成 `CORE +5%`。

### 当前完成度

在本任务完成前保持：

```text
CORE 80%
SNAPSHOT 50%
TRACE 40%
ACCESS 60%
HISTORY 10%
AUDIT 10%
OPENCLAW 25%
LAB 50%
DISTRIBUTIONS 40%
```

完成后根据真实结果复算，不得自动复制目标：

```text
LAB 55%
DISTRIBUTIONS 45%
```

### 表格要求

当前任务进度表必须使用本任务自己的：

```text
Before
Target
Actual
```

不得继续沿用上一任务的 `CORE 75 -> 80` 等列值。

### 通过条件

```text
报告、进度账、任务书和Manifest向量一致；
全部完成度以5%粒度记录；
没有“全部偏差为零”的无证据结论；
活动Basis链接最新真实报告。
```

---

## 11. 结果闸门：模块章程与发行组合一致性

更新：

```text
NOLLM_LAB_CHARTER.md
NOLLM_DISTRIBUTIONS_CHARTER.md
MODULE_OWNERSHIP_MANIFEST.json/.csv
边界报告
README / ARCHITECTURE / ROADMAP（仅必要差异）
```

章程应明确：

- Lab拥有不同生命周期的开发、验证、Legacy和历史资产。
- `ACTIVE`不等于“位于Lab目录”。
- Legacy回归可被执行，但不构成活动产品能力。
- Distribution只组合模块与治理元数据，不实现Lab分类逻辑之外的业务。
- Core/Snapshot/Trace/Access不依赖Lab。

---

## 12. 独立包与项目回归

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

### 机器治理

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
  docs/architecture/module-ownership/LD_ASSET_TAXONOMY_TRUTH_BOUNDARY_REPORT.json

python -m pytest -q reference/python/tests/m0
python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py
```

### 能力与兼容回归

```powershell
python -m pytest -q reference/python/tests/grf
python lab/nollm-lab/geometry/generate_compiled_templates.py --check
python lab/nollm-lab/m1/run_geometry_parity.py
python lab/nollm-lab/m1/run_core_capability_validation.py --check
python lab/nollm-lab/m1/run_m1_minimal_e2e.py
```

若仅缺 `zstandard`，只允许精确排除既有两项历史压缩测试并记录环境依赖。

### 代码与工作树

```powershell
python -m compileall -q `
  packages/nollm-core/src `
  packages/nollm-snapshot/src `
  packages/nollm-trace/src `
  packages/nollm-access/src `
  lab/nollm-lab `
  tools

git diff --check
git status --short
```

---

## 13. Final Gate必须满足

```text
Manifest tracked = git ls-files；
unclassified = 0；
production violations = 0；
production cycles = []；

所有LAB资产asset_class合法；
ACTIVE资产validation_gate覆盖率 = 100%；
LEGACY_REGRESSION gate覆盖率 = 100%；
无泛目录默认ACTIVE规则；

活动工具/库/验证公共合同错误 = 0；
活动工具导入失败 = 0；
ACTIVE_TEST对应包/治理Gate全部通过；
历史结果不进入活动Gate；
Legacy回归不计入当前能力完成度；

9/9 Geometry parity；
25/25 Core capability；
Snapshot / Trace / Access不回退；
Minimal E2E通过；
所有--check只读；
Final Gate后工作树干净；
完整历史Bundle验证通过。
```

---

## 14. 实际推进向量与模块完成度回填

生成或更新：

```text
docs/project/LD_ASSET_TAXONOMY_TRUTH_REPORT.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
docs/project/NOLLM_CURRENT_STATUS.md
```

必须记录：

```text
预计向量
实际向量
各模块偏差
资产类别数量
每类Gate覆盖数量
任务前/目标/实际完成度
最近验证代码提交和代码树摘要
已知限制
下一候选动作
```

允许：

```text
CAPABILITY_VALIDATED_AT_<validated_code_commit>
ACTIVE_BASELINE_AT_<final_head>
```

前提：

- Manifest分类真值通过；
- 进度账向量无矛盾；
- Final Gate后工作树干净；
- 最终HEAD之后无未验证代码修改。

禁止：

```text
sealed
final closure
永不修改
自动进入下一阶段
```

---

## 15. 真实停止条件

只在以下情况停止：

```text
1. 当前活动能力无法与Legacy回归资产区分；
2. 现有Final Gate无法追溯到具体资产；
3. 大量资产只能通过扩大Core公共API才能保持ACTIVE；
4. 重新分类会删除尚无替代的验证能力；
5. production cycle或边界违规无法清零；
6. 模块章程必须发生超出L/D范围的实质变化；
7. 大规模环境失败无法定位。
```

不要因以下问题停止：

```text
Manifest行数变化；
ACTIVE数量显著下降；
历史测试或实验降级；
旧阶段编号保留在Legacy目录；
测试命令拆分；
两项zstandard环境依赖；
进度完成度下调。
```

---

## 16. 交付要求

必须：

```text
全部修改提交；
工作树干净；
仓库外生成一个完整历史Git Bundle；
验证Bundle；
只交一个Bundle。
```

建议Bundle名：

```text
nollm_ld_asset_taxonomy_truth_20260712_<shorthead>.bundle
```

Codex最终回复只报告：

```text
branch / final HEAD / validated code commit / code tree digest
预计推进向量 / 实际推进向量 / 偏差
全部模块任务前后实际完成度
各asset_class数量和Gate覆盖率
Manifest / boundary / cycles
package tests / M0 / architecture / GRF
9/9 parity / 25维能力 / Minimal E2E
历史资产保留情况
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
