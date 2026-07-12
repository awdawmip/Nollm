# Nollm ALD MemoryStatement 形成合同与语料任务书

**模块缩写**：`A=Access | L=Lab | D=Distributions`
**日期**：2026-07-12
**任务文件名**：`NOLLM_ALD_STATEMENT_FORMATION_CONTRACT_CORPUS_TASK_20260712.md`
**性质**：Access 公共合同扩展、Evidence-preserving Statement Formation 基础与 Lab 语料验证
**输入 Bundle**：`nollm_ld_asset_taxonomy_truth_20260712_3528c01.bundle`
**输入 Bundle SHA-256**：`b7aca3ffba669069e5e74d5fabdecd59dce6d746099b1b6d2dd016c2b9e2a459`
**输入分支**：`codex/ld-asset-taxonomy-truth`
**输入 HEAD**：`3528c0130a2f29987e06105753310d3b2a592a2a`
**已验证代码提交**：`7ff9690edeca71806bf5783787ef81367b9eb167`
**已验证代码树摘要**：`b8a17134c494d3610c306723281bcdede7c130de41ec010d290a02e093ecbd27`
**建议分支**：`codex/ald-statement-formation-contract-corpus`
**主环境**：Windows 10/11 + PowerShell
**交付形式**：全部修改提交、工作树干净、仓库外单一完整历史 Git bundle
**结论边界**：只形成绑定具体 HEAD 的 Access/Lab 能力记录或活动基线；不宣称封版，不自动启动 Placement、OpenClaw 或真实模型阶段。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% | LAB +10% | DISTRIBUTIONS +5%

主方向：
在 Access 中建立由外部 Host/LLM/人工提供语义边界的
Evidence-preserving MemoryStatement Formation 公共合同；
在 Lab 中建立可复现语料、负例和确定性评测工具。
Python 只做类型、边界、Evidence span 和 canonical contract 验证，
不自行理解、摘要、改写或决定 Placement。

范围变化：
无。Access 和 Lab 的模块章程目标不扩大；本任务只实现项目书已规划的
MemoryStatement Formation 合同与新语料基础。
```

### 0.1 向量解释

- `ACCESS +10%`：补齐 Raw Evidence → Statement Formation Request/Decision → MemoryStatement 的公共合同、验证和组装能力。
- `LAB +10%`：建立版本化 Gold Corpus、错误提案集、评测器和报告。
- `DISTRIBUTIONS +5%`：登记 Formation Corpus/Fixture/Gate 资产，保持 Manifest、活动 Basis、报告和进度账真值。
- `CORE / SNAPSHOT / TRACE / HISTORY / AUDIT / OPENCLAW 0%`：不修改能力，只做必要回归。
- 本任务不包含真实模型效果，因此 Access/Lab 完成度提升只表示合同与验证基础，不表示语义质量已经证明。

### 0.2 执行纪律

1. 每个结果闸门开始和结束时复述推进向量。
2. 若新增受影响模块，或任何模块实际偏差超过 `5%`，必须更新任务范围、任务名称建议、向量和持续进度账。
3. 不得以语料数量、测试数量或 schema 数量替代能力推进说明。
4. 不得自动进入 Placement、OpenClaw 或真实模型调用。

---

## 1. 输入活动基线

### 1.1 Bundle 审核事实

```text
Bundle verify：通过
完整历史：通过
输入 HEAD：3528c0130a2f29987e06105753310d3b2a592a2a
输入工作树：clean

Manifest = 1489 / 1489
unclassified = 0
production violations = 0
production cycles = []
migration findings = 7
```

### 1.2 已验证模块能力

```text
Core = 39 passed
Snapshot = 7 passed
Trace = 3 passed
Access = 32 passed
M0 governance = 43 passed
architecture / hygiene = 8 passed

Geometry parity = 9 / 9
Core capability validation = 25 / 25
Minimal E2E = passed
```

外部 GRF 审核：

```text
109 passed
1 skipped
2 failed only because zstandard was unavailable
```

### 1.3 当前活动基线结论

允许记录：

```text
CAPABILITY_VALIDATED_AT_7ff9690edeca71806bf5783787ef81367b9eb167
ACTIVE_BASELINE_AT_3528c0130a2f29987e06105753310d3b2a592a2a
```

含义：

- Core/Snapshot/Trace/Access 的既有能力绑定已验证代码提交和代码树摘要。
- 最终 HEAD 仅增加经 Gate 验证的治理、Manifest 和 Lab 资产分类。
- 该基线可以继续演进，不是 sealed 或 final。

---

## 2. 上一任务实际推进向量与完成度

上一任务预计：

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% |
LAB +5% | DISTRIBUTIONS +5%
```

本次审核确认实际：

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW 0% |
LAB +5% | DISTRIBUTIONS +5%
```

模块完成度基线：

| 模块 | 生命周期状态 | 实际完成度 | 置信度 | 最近验证依据 | 主要缺口 |
|---|---|---:|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 80% | 高 | code `7ff9690e`; tree `b8a17134`; 39 tests; 9/9; 25维验证 | 跨进程恢复、规模、真实语义 Host 未验证 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 7 tests；SnapshotDiff；原子恢复 | 跨版本迁移、增量快照 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 3 tests；多 Sink 与状态隔离 | 深度性能工具和可视化 |
| ACCESS | `ACTIVE_BASELINE` | 60% | 中高 | 32 tests；严格 Binding；动作映射；Evidence fallback | Statement Formation 合同、真实 Host/LLM、多进程协调 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程与边界 | 未实现 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程与边界 | 未实现 |
| OPENCLAW | `LEGACY_REFERENCE` | 25% | 中低 | 迁移资产保留；Live 暂停 | 当前 Access/LLM E2E 未实现 |
| LAB | `IMPLEMENTED` | 55% | 高 | 562项分类；132项 Gate；9/9；25维验证 | Statement Formation Corpus、真实模型评测、长压测 |
| DISTRIBUTIONS | `IMPLEMENTED` | 45% | 高 | Manifest 分类与 Gate 真值；Bare/Minimal/Debug | 安装器、版本协商 |

### 2.1 已知非阻断事项

`NOLLM_LAB_CHARTER.md` 当前在 Manifest 中归为 `ACTIVE_REPOSITORY_TOOL`，其语义更接近活动治理输入。若本任务触及相关分类，应在不新增类别的前提下改为更准确的 `ACTIVE_FIXTURE`，并由 `repository:manifest` Gate 覆盖。

---

## 3. 任务开始前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 80% | 高 | 39 tests；9/9；25维验证；显式入口 Recall | 真实 Host/LLM 和规模未验证 | 是，仅高风险回归，预计0% |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 7 tests；原子 Snapshot 服务 | 迁移、增量快照 | 是，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 3 tests；多 Sink | 深度工具有限 | 是，仅回归 |
| ACCESS | `ACTIVE_BASELINE` | 60% | 中高 | Statement、Evidence、Decision、Binding、Recall 基础存在 | Raw Evidence 与 formed statement 缺少明确形成合同、span provenance 和 defer 语义 | 是，直接修改 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程存在 | 未实现 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程存在 | 未实现 | 否 |
| OPENCLAW | `LEGACY_REFERENCE` | 25% | 中低 | Host 迁移资产保留 | 无真实 Statement Formation E2E | 否，只确认未启动 |
| LAB | `IMPLEMENTED` | 55% | 高 | 分类真值、编译器、Parity、能力验证 | 无 Statement Formation 语料、Gold schema、错误提案和评测器 | 是，直接修改 |
| DISTRIBUTIONS | `IMPLEMENTED` | 45% | 高 | 组合和 Manifest 真值 | 安装器、版本协商 | 否，只做回归 |

---

## 4. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 80% | 80% | 0% | 无变化；确认 Formation 不进入 Core | Core tests；public allowlist；boundary | 真实模型、规模仍未验证 |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | Snapshot tests | 迁移、增量快照 |
| TRACE | 40% | 40% | 0% | 无变化 | Trace tests | 深度工具有限 |
| ACCESS | 60% | 70% | +10% | Raw Evidence、span、Formation Request/Decision/Result、deterministic assembly 和 defer 合同 | 独立 Access tests；canonical round-trip；负例矩阵；无语义推理扫描 | 真实模型质量、产品策略和持久化工作流集成仍未验证 |
| HISTORY | 10% | 10% | 0% | 无变化 | boundary | 未实现 |
| AUDIT | 10% | 10% | 0% | 无变化 | boundary | 未实现 |
| OPENCLAW | 25% | 25% | 0% | 无变化 | 活动路径确认 | 无 Live E2E |
| LAB | 55% | 65% | +10% | Corpus v1、Gold spans、错误提案集、schema validator、self-check 和 evaluator | Corpus coverage；Gold self-check；fixture metrics；报告 | 无真实模型调用、无跨模型比较、语义质量未验证 |
| DISTRIBUTIONS | 45% | 50% | +5% | Formation Corpus/Fixture/Gate 分类进入机器治理；活动 Basis、报告和进度账同步 | Manifest truth；Gate覆盖；Basis/ledger一致性 | 安装器、版本协商 |

---

## 5. 本任务的核心设计决定

### 5.1 Formation 是外部语义决定，不是 Python NLP

正确流程：

```text
Raw Evidence
→ Host / LLM / Human 选择独立意义片段的边界
→ StatementFormationDecision
→ Access 验证 Evidence 引用、span、顺序和 canonical contract
→ Access 确定性组装 FormedMemoryStatement
→ 后续独立任务再决定 PlacementDecision
```

禁止：

```text
Python 自动摘要；
关键词切句作为产品主路径；
固定规则判断独立意义；
hash/embedding/vector 形成 statement；
自动 duplicate/revision/stitch；
形成时选择 GeometryAddress；
形成时写入 Core。
```

### 5.2 v1 使用 Evidence-preserving exact spans

Statement Formation v1 只允许：

```text
一个 formed statement
= 一个 RawEvidenceRecord 中的一个连续 Unicode code-point span
```

Access 可以确定性验证：

```text
statement.content_utf8
==
evidence.content_utf8[start_codepoint:end_codepoint]
```

不允许：

```text
改写；
摘要；
翻译；
纠错；
合并多个离散 span；
跨 Evidence 拼接；
模型新增未出现文本。
```

理由：

- Evidence 始终是事实源；
- Python 可以验证零幻觉；
- 分散事实先形成多个 statement，后续由 Placement/Stitch 处理；
- 更复杂的多 span 或语义重写必须另立任务，并有独立证据。

### 5.3 Formation 与 Placement 严格分离

Formation 合同不得包含：

```text
GeometryAddress
AtomHandle
BridgeSpec
reuse / new / revision / stitch / forget
importance
truth
confidence score
similarity
topic / entity
embedding
```

`StatementFormationDecision` 只回答：

```text
哪些 Evidence span 构成独立、有意义的 MemoryStatement；
或者当前证据应 defer。
```

---

## 6. 结果闸门：Access Formation 公共对象

在 `nollm-access` 中建立公共合同。具体文件可按包结构决定，但对象职责必须清晰。

### 6.1 RawEvidenceRecord

建议字段：

```text
evidence_id: str
content_utf8: str
source_handle: str | None
context_refs: tuple[str, ...]
```

要求：

- exact types；
- 非空 `evidence_id` 和 `content_utf8`；
- `context_refs` tuple、排序、唯一；
- canonical mapping/bytes；
- 不做 `str()`、数字、布尔或对象强转；
- RawEvidenceRecord 与 MemoryStatement 不同，不进入 Core。

### 6.2 EvidenceSpan

建议字段：

```text
evidence_id: str
start_codepoint: int
end_codepoint: int
```

要求：

- exact int，拒绝 bool/float；
- `0 <= start < end`；
- span 不在对象构造时假设 Evidence 存在；
- 在 Formation assembly 时核对范围；
- v1 明确使用 Unicode code-point offset，不使用 UTF-8 byte offset；
- 报告中说明 Python 字符索引语义和限制。

### 6.3 StatementSelection

建议字段：

```text
statement_id: str
span: EvidenceSpan
```

要求：

- exact `EvidenceSpan`；
- statement_id 非空；
- 同一 decision 中 statement_id 唯一；
- selection 按 `(evidence_id, start, end, statement_id)` canonical 排序；
- 默认禁止 span 重叠；
- gaps 允许；
- 不自动合并相邻 span。

### 6.4 StatementFormationRequest

建议字段：

```text
request_id: str
evidence: tuple[RawEvidenceRecord, ...]
max_statements: int
```

要求：

- evidence_id 唯一；
- evidence tuple canonical 排序；
- `max_statements` 为有限正整数并有合理硬上限；
- 不含 Geometry、Placement、model configuration 或 prompt。

### 6.5 StatementFormationDecision

建议字段：

```text
decision_id: str
request_id: str
outcome: formed | defer
selections: tuple[StatementSelection, ...]
defer_reason: str | None
decided_by: host | llm | human | fixture
```

要求：

- `formed`：至少一个 selection，`defer_reason=None`；
- `defer`：无 selection，defer_reason 非空；
- exact fields，拒绝未知字段；
- 不允许 confidence、score、target_cell、existing_handle 或 bridge；
- Access 不检查 reason 的语义正确性，只检查类型和状态互斥。

### 6.6 FormedMemoryStatement

建议字段：

```text
statement: MemoryStatement
provenance: EvidenceSpan
formation_decision_id: str
```

要求：

- `MemoryStatement.content_utf8` 由 Evidence span 确定性提取；
- source_handle 与 context_refs 从 RawEvidenceRecord 继承；
- statement_id 来自 selection；
- provenance 不进入 Core；
- FormedMemoryStatement 具有 canonical mapping；
- 不替代 Raw Evidence。

### 6.7 StatementFormer Protocol

Access 可定义极小 Protocol：

```text
form(request: StatementFormationRequest) -> StatementFormationDecision
```

只定义边界，不实现模型、不加载 Prompt、不依赖 OpenClaw。

### 通过条件

```text
全部对象严格类型和 canonical round-trip；
Access package root导出明确；
Core/Snapshot/Trace不新增依赖；
Formation schema不包含Placement字段；
ACCESS推进方向保持+10%。
```

---

## 7. 结果闸门：确定性 Formation 验证与组装

建立纯函数或无状态服务，例如：

```text
validate_formation_decision(request, decision)
assemble_formed_statements(request, decision)
```

### 必须验证

```text
request_id匹配；
Evidence引用存在；
span范围合法；
selection数量不超过max_statements；
statement_id唯一；
canonical顺序；
span不重叠；
formed/defer互斥；
提取文本非空；
提取文本逐字符等于原Evidence span；
source_handle/context_refs正确继承；
输出顺序确定；
重复运行bytes相同。
```

### 必须拒绝

```text
未知Evidence；
越界；
零长度；
负数；
bool/float offset；
重叠span；
重复statement_id；
非canonical顺序；
formed无selection；
defer带selection；
空defer_reason；
任何Placement字段；
任何改写或额外文本；
跨Evidence拼接为单条statement。
```

### 明确不验证

```text
span是否真的“有意义”；
是否应该拆成一条还是多条；
是否遗漏重要事实；
是否应该defer；
模型理由是否正确。
```

这些属于外部语义 actor 和后续模型评测。

---

## 8. 结果闸门：现有 MemoryStatement 与 Formation 合同兼容

不得直接推翻当前 `MemoryStatement`、EvidenceStore 和 AccessRuntime。

### 必须完成

1. 明确当前 `MemoryStatement` 继续作为 Access/Placement 使用的语义盲 statement payload。
2. Formation 输出通过 `FormedMemoryStatement.statement` 产生当前 MemoryStatement。
3. 当前 `AccessRuntime.capture()` 仍可接受显式、已经形成的 MemoryStatement。
4. 本任务默认不自动把 Formation Result 写入 EvidenceStore 或 Core。
5. 如增加便捷方法，只能是显式调用，例如：

```text
capture_formed(form_result)
```

且必须：
- 只写 Access Evidence；
- 不做 Placement；
- 不调用 Core；
- 保留 Raw Evidence 或其外部引用合同；
- 不替代现有 `capture()`。

6. 现有 Access 32项测试全部保持。

### 通过条件

```text
旧Access调用不回退；
Formation是前置可组合合同，不是隐式自动流程；
不引入第二套竞争的MemoryStatement；
不启动Placement。
```

---

## 9. 结果闸门：Statement Formation Corpus v1

建立：

```text
lab/nollm-lab/statement_formation/
  README.md
  schema/
  datasets/
  fixtures/
  reports/
  validate_corpus.py
  evaluate_fixture_decisions.py
```

目录可按仓库习惯调整，但必须通过 Manifest 资产分类和 Gate 真值。

### 9.1 Gold Corpus

建议文件：

```text
datasets/statement_formation_v1.jsonl
```

最低要求：

```text
不少于120条case；
不少于12个类别；
中文、英文、混合语言均有；
Unicode、emoji、标点和换行有覆盖；
每条Raw Evidence保留原文；
Gold只给exact spans或defer；
不含Placement答案。
```

类别至少覆盖：

1. 单一独立陈述；
2. 多句、应拆多条；
3. 一个长句中的两个独立分句；
4. 否定、例外和限定条件；
5. 时间、数量、主体限定；
6. 相似但不同的两条事实；
7. 重复表达；
8. 指令、问题、事实混合；
9. 工具输出和日志；
10. 代码块、表格或键值数据；
11. 中文、英文及混合文本；
12. 不足以形成独立 statement，应 defer；
13. Source/context 元数据继承；
14. Unicode code-point 边界。

Gold 设计原则：

- statement content 必须是原文连续 span；
- 不进行事实判断；
- 不做 placement/revision/stitch；
- 同一 Evidence 内 selections 排序且不重叠；
- 争议案例可标 defer，不强造答案。

### 9.2 Split

至少提供：

```text
development
held_out
```

Gold 自检可以读取全部；未来模型调参不得读取 held_out Gold。

本任务不调用模型，但必须为后续隔离预留明确字段或文件边界。

### 9.3 错误提案集

建立确定性 fixture proposals，至少包括：

```text
perfect
off_by_one
unknown_evidence
overlap
duplicate_statement_id
noncanonical_order
paraphrased_text
invented_text
formed_empty
defer_with_selection
placement_field_injection
```

错误提案只用于验证 Access validator 和 Lab evaluator，不是安全攻击矩阵。

---

## 10. 结果闸门：Corpus 与 Fixture 评测

### 10.1 Corpus self-check

输出：

```text
case_count
category_counts
language_counts
formed_count
defer_count
statement_count
span_boundary_valid_rate
overlap_violation_count
gold_text_mismatch_count
unknown_field_count
```

硬条件：

```text
span_boundary_valid_rate = 1.0
overlap_violation_count = 0
gold_text_mismatch_count = 0
unknown_field_count = 0
```

### 10.2 Fixture evaluator

至少输出：

```text
schema_valid_rate
decision_state_accuracy
exact_statement_count_accuracy
exact_span_precision
exact_span_recall
exact_span_f1
text_faithfulness_rate
hallucinated_text_count
defer_accuracy
source_inheritance_accuracy
context_inheritance_accuracy
```

对 `perfect` fixture：

```text
全部适用指标 = 1.0
hallucinated_text_count = 0
```

对错误 fixture：

- 对应错误必须被 validator 拒绝或指标明确下降；
- 不得静默修复 off-by-one、排序、重叠或 paraphrase；
- 报告必须区分 schema rejection 和 semantic mismatch。

### 10.3 报告

生成：

```text
docs/validation/AL_STATEMENT_FORMATION_CONTRACT_REPORT.md
docs/validation/AL_STATEMENT_FORMATION_CORPUS_REPORT.md
docs/validation/AL_STATEMENT_FORMATION_CORPUS_METRICS.json
```

报告必须写明：

```text
这是合同与Gold Corpus验证；
不是实际LLM运行；
不证明模型能够正确形成statement；
不证明Placement、Recall质量或产品效果。
```

---

## 11. 结果闸门：禁止语义与边界扫描

新增机器测试，确保 `nollm-access` Formation 活动代码不包含：

```text
embedding
vector
graph
semantic similarity
keyword score
importance score
truth score
target_cell
GeometryAddress
AtomHandle
BridgeSpec
reuse
revision
stitch
placement
OpenClaw
model SDK
network call
```

允许文档在“禁止列表”和说明中出现这些词；代码扫描应基于 AST、字段和导入，避免简单字符串误报。

必须验证：

```text
Access Formation代码只依赖stdlib和Access自身对象；
Core不import Formation；
Lab只依赖Access公共合同；
OpenClaw不变化；
production violations=0；
production cycles=[]。
```

---

## 12. 结果闸门：Lab 资产与 Distribution 治理 Gate

新增稳定 Gate：

```text
lab:statement-formation-corpus
lab:statement-formation-fixtures
```

同步更新 Distribution 所有的 Manifest、活动 Basis、当前报告和持续进度账。

Manifest 分类建议：

```text
Formation schema/library -> ACTIVE_LIBRARY
Corpus validator/evaluator -> ACTIVE_TOOL或ACTIVE_VALIDATION
Gold corpus / fixture proposals -> ACTIVE_FIXTURE
生成报告 -> HISTORICAL_RESULT或GENERATED治理记录
```

所有 ACTIVE 资产必须有 `validation_gate`。

Distribution 只登记组合与治理元数据，不得实现 Formation 业务逻辑。

不得：

- 将整个新目录按路径默认 ACTIVE；
- 将 held_out Gold 暴露给未来调参工具的活动输入；
- 将报告当成模型质量证据；
- 将 Corpus 放入 Core、Access runtime package或Distribution runtime。

---

## 13. 模块独立测试

### Access 独立 Gate

新增测试至少覆盖：

```text
RawEvidenceRecord严格类型和canonical mapping；
EvidenceSpan边界类型；
Request evidence唯一和max_statements；
Decision formed/defer互斥；
Selection canonical order、唯一和不重叠；
exact-span assembly；
Unicode/emoji code-point slice；
source/context inheritance；
unknown evidence；
out-of-range；
paraphrase/invented text拒绝；
无Placement字段；
StatementFormer Protocol import；
现有AccessRuntime回归。
```

执行：

```powershell
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-access/src"
) -join ";"

python -m pytest -q packages/nollm-access/tests
```

### Lab Gate

```powershell
python lab/nollm-lab/statement_formation/validate_corpus.py --check
python lab/nollm-lab/statement_formation/evaluate_fixture_decisions.py --check
```

`--check` 必须只读，执行后工作树干净。

---

## 14. 全项目回归

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = @(
  "$PWD/packages/nollm-core/src",
  "$PWD/packages/nollm-snapshot/src",
  "$PWD/packages/nollm-trace/src",
  "$PWD/packages/nollm-access/src",
  "$PWD/reference/python"
) -join ";"
```

执行：

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py --report `
  docs/architecture/module-ownership/AL_STATEMENT_FORMATION_BOUNDARY_REPORT.json

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

python lab/nollm-lab/statement_formation/validate_corpus.py --check
python lab/nollm-lab/statement_formation/evaluate_fixture_decisions.py --check

python -m compileall -q `
  packages/nollm-access/src `
  lab/nollm-lab/statement_formation

git diff --check
git status --short
```

若仅缺 `zstandard`，只允许精确排除既有两项历史压缩测试并记录环境依赖。

---

## 15. Final Gate 必须满足

```text
Access Formation public contract完整；
Raw Evidence与Formed Statement分离；
Formation exact-span faithfulness = 100%；
Formation schema无Placement字段；
Python不做语义切分、摘要或改写；
Corpus >= 120 cases；
categories >= 12；
development/held_out边界明确；
Gold self-check全部硬条件通过；
perfect fixture全部适用指标=1.0；
错误fixture被拒绝或指标明确下降；
hallucinated_text_count=0；
Access原32项能力不回退；
Core/Snapshot/Trace不变化；
production violations=0；
production cycles=[]；
Manifest分类和Gate真值通过；
所有--check只读；
Final Gate后工作树干净；
完整历史Bundle验证通过。
```

---

## 16. 任务报告和持续进度账

生成或更新：

```text
docs/project/AL_STATEMENT_FORMATION_TASK_REPORT.md
docs/project/NOLLM_CURRENT_STATUS.md
docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
docs/project/ACTIVE_PROJECT.md
```

必须记录：

```text
预计推进向量
实际推进向量
各模块偏差
Corpus case/category/language统计
Access合同与公共API变化
验证指标
实际模块完成度
已知限制
未验证事项
下一候选动作
```

任务后实际完成度必须重新计算，不得自动复制目标值。

允许：

```text
ACCESS_STATEMENT_FORMATION_CAPABILITY_VALIDATED_AT_<validated_code_commit>
ACTIVE_BASELINE_AT_<final_head>
```

禁止：

```text
LLM formation quality validated
Placement validated
OpenClaw integrated
sealed
final closure
自动进入下一阶段
```

---

## 17. 真实停止条件

只在以下情况停止：

```text
1. Evidence-preserving exact-span合同无法表达项目最小Statement单位；
2. Formation必须依赖Geometry或Placement才能成立；
3. 当前MemoryStatement无法与formed provenance组合且必须破坏现有Access合同；
4. Corpus Gold无法在不改写原文的前提下形成；
5. Access/Lab拆分必须引入graph/vector/embedding；
6. production cycle或边界违规无法清零；
7. 大规模环境失败无法定位。
```

不要因以下问题停止：

```text
Corpus条目措辞需要修正；
类别数量变化；
Fixture指标不漂亮；
文件名调整；
历史报告移动；
两项zstandard环境依赖；
完成度低于目标。
```

---

## 18. 交付要求

必须：

```text
全部修改commit；
工作树干净；
仓库外生成一个完整历史Git Bundle；
验证Bundle；
只交一个Bundle。
```

建议 Bundle 名称：

```text
nollm_ald_statement_formation_contract_corpus_20260712_<shorthead>.bundle
```

Codex最终回复只报告：

```text
branch / final HEAD / validated code commit / code tree digest
预计推进向量 / 实际推进向量 / 偏差
全部模块任务前后实际完成度
Access Formation公共合同
Corpus规模与类别
Distribution/Manifest Gate真值
Gold self-check与fixture metrics
package tests / M0 / architecture / GRF
9/9 parity / 25维能力 / Minimal E2E
Manifest / boundary / cycles
known limitations
Bundle filename / SHA-256
```

不得声称：

```text
Core或Access已封版
真实LLM Formation质量已验证
Placement已验证
OpenClaw已集成
Memory Quality或PB规模已验证
项目最终闭合
