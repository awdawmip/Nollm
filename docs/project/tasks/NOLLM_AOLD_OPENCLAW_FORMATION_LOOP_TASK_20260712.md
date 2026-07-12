# Nollm AOLD OpenClaw Statement Formation 真实闭环任务书

**模块缩写**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**日期**：2026-07-12
**任务文件名**：`NOLLM_AOLD_OPENCLAW_FORMATION_LOOP_TASK_20260712.md`
**性质**：真实 OpenClaw LLM 接入、Statement Formation 小批次迭代、运行数据沉淀
**活动基线**：`ACTIVE_BASELINE_AT_3528c0130a2f29987e06105753310d3b2a592a2a`
**可复用实现 checkpoint**：`018858582207e4af6f04f35f5bd41d4143897466`
**可复用 Formation 实现提交**：`1cad3f756528d91e1d88dc443357cc46ae2dac52`
**建议分支**：`codex/aold-openclaw-formation-loop`
**主环境**：Windows 10/11 + PowerShell
**交付形式**：所有修改提交、工作树干净、仓库外单一完整历史 Git Bundle
**结论边界**：只形成真实 OpenClaw Formation 能力记录和活动候选；不宣称 Placement、Recall 质量、OpenClaw 全产品集成或封版。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% | LAB +5% | DISTRIBUTIONS +5%

主方向：
把真实 OpenClaw LLM 接入 Statement Formation；
让语义拆分、保留和 defer 由真实模型完成；
Python 只做 Schema、span、Evidence 和 canonical 验证；
根据真实运行失败迭代 Prompt、Access合同和Lab案例。

范围变化：
项目路线调整。OpenClaw 从“Formation/Placement合同之后再接入”
提前到 Formation 语义验证阶段。
Core、Snapshot、Trace、History、Audit 的章程范围不变。
```

### 0.1 向量解释

- `ACCESS +5%`：现有 exact-span Formation 合同接入真实 Host，并根据真实错误补正最小公共合同。
- `OPENCLAW +10%`：从迁移资产推进到真实 LLM Formation 可运行闭环。
- `LAB +5%`：从合成 Gold 为主转为真实运行案例、人工复核和失败分类。
- `DISTRIBUTIONS +5%`：建立 OpenClaw Formation 开发组合、配置、运行和诊断入口。
- 其他模块 `0%`：不修改能力，只做高风险回归。

若执行中需要修改 Core、Snapshot、Trace、History 或 Audit 公共合同，必须停止当前范围、更新任务名称和推进向量，不得静默扩张。

---

## 1. 撤回与保留

### 1.1 撤回

停止执行：

```text
NOLLM_ALD_FORMATION_CORPUS_TRUTH_TASK_20260712.md
```

不再把以下内容作为下一阶段主线：

```text
先重写大规模合成 Corpus；
先达到模板多样性硬指标；
先用 Perfect Fixture 证明 Formation 语义正确；
先用 Python Evaluator 代替真实模型运行。
```

### 1.2 保留

保留 `0188585 / 1cad3f7` 中经过复核的确定性部分：

```text
RawEvidenceRecord；
EvidenceSpan；
StatementSelection；
StatementFormationRequest；
StatementFormationDecision；
FormedMemoryStatement；
exact-span验证；
Evidence引用验证；
canonical编码；
formed/defer互斥；
Formation与Placement/Core分离。
```

合成 Corpus 和 Evaluator：

```text
保留历史；
降级为parser/schema regression或LEGACY_REFERENCE；
不得作为真实语义能力验收依据。
```

---

## 2. 任务开始前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 80% | 高 | 9/9 Geometry；25维能力；显式入口Recall | 真实LLM Placement、规模与跨进程未验证 | 否，仅回归 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 原子create/restore/clone/diff | 版本迁移、增量快照 | 否，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 多Sink与状态隔离 | OpenClaw运行观察尚未组合 | 否，仅回归 |
| ACCESS | `IMPLEMENTED` / Formation checkpoint | 65% | 中高 | exact-span Formation对象与验证；50项历史测试 | 未接真实Host；真实模型输出、错误恢复和版本化未验证 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程存在 | 未实施 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程存在 | 未实施 | 否 |
| OPENCLAW | `LEGACY_REFERENCE` / Adapter迁移资产 | 25% | 中低 | Hook、session、安装、配置、OCA1等历史资产 | 当前真实Runtime/LLM接口未确认；无Formation Live E2E | 是 |
| LAB | `IMPLEMENTED` | 60% | 中 | 现有Corpus、Fixture、Gate与资产分类 | 数据主要为合成；没有真实模型运行和人工复核闭环 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 50% | 中高 | Bare/Minimal/Debug与治理Manifest | OpenClaw Formation开发组合、安装和诊断入口未形成 | 是 |

---

## 3. 任务执行后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 80% | 80% | 0% | 无变化 | Core回归、9/9、25维能力 | Placement与真实Recall质量未验证 |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | Snapshot回归 | OpenClaw恢复组合未验证 |
| TRACE | 40% | 40% | 0% | 无变化 | Trace回归 | OpenClaw产品级观测未完整实现 |
| ACCESS | 65% | 70% | +5% | 真实Host Formation请求/结果合同；模型输出验证；无语义fallback | Access测试；Live回放；错误分类 | Placement与长期产品策略未验证 |
| HISTORY | 10% | 10% | 0% | 无变化 | 边界检查 | 未实施 |
| AUDIT | 10% | 10% | 0% | 无变化 | 边界检查 | 未实施 |
| OPENCLAW | 25% | 35% | +10% | 真实Runtime发现；真实LLM调用；Formation插件/适配器；安装诊断与Live E2E | 真实调用日志；版本/接口报告；三轮Live运行 | Placement、Recall注入和长期稳定性未验证 |
| LAB | 60% | 65% | +5% | 真实运行案例集、人工复核、失败分类、Prompt/Schema版本回归 | Live run records；review labels；metrics | 样本仍小；无广泛真实用户数据 |
| DISTRIBUTIONS | 50% | 55% | +5% | OpenClaw Formation开发组合、配置和诊断清单 | manifest、install/doctor smoke、E2E入口 | 正式发布与版本协商未完成 |

---

## 4. 活动依据与项目路线更新

更新当前活动项目书和状态，采用：

```text
NOLLM_PROJECT_BOOK_V3_2_OPENCLAW_FIRST_SEMANTIC_LOOP_20260712.md
```

必须记录：

```text
OpenClaw提前进入Formation语义验证；
合成Corpus只作解析/Schema回归；
真实模型输出是Formation迭代依据；
Placement仍是后续独立任务；
不自动进入Placement。
```

旧“先Corpus/模型验证，再OpenClaw”的路线降级为历史记录。

---

## 5. 真实 OpenClaw 运行面发现

不得假设历史接口仍然有效。

Codex必须在实际Windows环境中确认：

```text
OpenClaw实际安装位置；
实际版本；
插件/扩展目录；
当前可用Hook或事件入口；
真实LLM调用接口；
配置文件位置；
启用/禁用/重载方式；
日志和诊断入口；
会话/turn标识；
调用超时和错误形式。
```

可读取旧OpenClaw资产获取经验，但不得直接复活旧：

```text
legacy memory-core；
native-memory store；
旧deterministic lexical search；
旧geometry navigation tool；
旧自动promotion逻辑。
```

生成：

```text
docs/integration/openclaw/OPENCLAW_RUNTIME_DISCOVERY.md
docs/integration/openclaw/OPENCLAW_ASSET_MIGRATION_MAP.md
```

### 通过条件

```text
真实OpenClaw Runtime存在；
真实LLM调用接口被一次最小探针成功调用；
版本、路径和接口来自实际环境；
不是Mock、Fixture或Python假模型；
若真实Runtime/LLM不可用，停止并报告环境阻断。
```

---

## 6. OpenClaw Formation Adapter

建立或更新实际适配器，目录以真实OpenClaw规范为准，不硬编码历史结构。

最小组件：

```text
OpenClawEventTranslator
OpenClawSessionMapper
OpenClawLLMClient
FormationPromptBuilder
FormationDecisionParser
AccessFormationClient
FormationResultRenderer
OpenClawFormationConfig
```

依赖方向：

```text
OpenClaw Runtime
  → OpenClaw Adapter
  → Access Formation public contract
```

禁止：

```text
Core import OpenClaw；
Adapter直接写Core私有状态；
Adapter决定GeometryAddress；
Adapter保存唯一Evidence真值；
Adapter内Python语义拆分；
Adapter用Mock结果通过Live Gate。
```

---

## 7. 真实 LLM Formation Prompt 与 Schema

输入至少包含：

```text
Evidence ID；
原始Evidence全文；
source/context的opaque引用；
任务：选择独立有意义的原文连续span，或defer；
禁止摘要、改写、翻译和新增文字；
输出Schema版本；
最大statement数量；
必要的歧义说明。
```

模型输出只允许：

```text
formed:
  selections:
    evidence_id
    start
    end
    statement_id
  reason_summary（仅诊断，不进入Core事实）

或

defer:
  reason_class
  reason_summary
```

Python只负责：

```text
JSON/结构解析；
字段类型；
Evidence ID；
code-point span；
canonical顺序；
重叠/数量；
原文逐字符一致；
source/context继承；
错误分类。
```

Python不得：

```text
按句号自动切；
关键词分类；
正则判断事实/问题/指令；
自动修补模型span；
猜测模型原意；
调用备用Python splitter；
针对case硬编码答案。
```

解析失败、非法span或改写文本：

```text
返回结构化拒绝；
允许重新提示真实LLM；
不得转入Python semantic fallback。
```

---

## 8. 小批次真实迭代

至少执行三轮，每轮不少于12个真实LLM调用，总数不少于36。

### 每轮输入建议

```text
中文 >= 5
英文 >= 3
中英混合 >= 2
多Evidence >= 2
```

覆盖：

```text
单一完整陈述；
多个独立句子；
相似但不同；
真实重复表达；
指令/问题/事实混合；
否定和例外；
时间/数量/主体限定；
工具日志；
代码/表格/键值；
Unicode/emoji；
指代不足或残缺；
应defer案例。
```

这些输入可以人工编写，但语义结果必须由真实LLM生成；不得由Python预先生成输出。

### 轮次流程

```text
真实调用
→ Access解析/验证
→ 人工复核
→ 失败归类
→ 调整Prompt/Schema/最小Access合同
→ 回归前轮案例
→ 下一轮
```

每轮生成：

```text
run metadata
input evidence
raw model response
parsed decision
validation result
human review:
  accept / partial / reject
review note
prompt version
schema version
latency
retry count
```

不得存储模型隐藏推理；只保存可见输出和人工复核。

---

## 9. 迭代边界

允许根据真实运行修改：

```text
Prompt措辞；
输出Schema的表达能力；
错误分类；
重试策略；
Access的确定性验证；
OpenClaw适配器；
Lab记录格式。
```

不允许：

```text
新增Python语义规则；
对单个case硬编码；
为提高指标让Python改写模型输出；
修改Core语言理解；
提前实现Placement；
用合成Perfect Fixture替代真实调用。
```

若发现Formation合同本身不足，修改必须来自至少两个真实失败模式，并记录：

```text
原问题；
为何Prompt不足；
为何Schema不足；
修改前后行为；
回归结果；
剩余限制。
```

---

## 10. 真实运行指标

每轮及总计至少报告：

```text
live_call_count
parse_success_rate
valid_exact_span_rate
formed_rate
defer_rate
empty_output_rate
retry_rate
hallucinated_or_rewritten_text_count
invalid_evidence_reference_count
invalid_span_count
human_accept_rate
human_partial_rate
human_reject_rate
source_context_inheritance_rate
median_latency_ms
p95_latency_ms
```

这些指标不要求达到100%。

硬条件：

```text
真实LLM调用数 >= 36；
Python semantic fallback count = 0；
hallucinated/rewritten文本不得被接受；
所有accepted statement可回到原Evidence；
所有指标和失败案例如实记录。
```

---

## 11. Lab真实运行Corpus

新Corpus来源于真实调用，不预先伪造Gold。

建议结构：

```text
lab/nollm-lab/openclaw_formation/
  runs/
  reviewed_cases/
  prompts/
  schemas/
  fixtures/
  reports/
```

资产分类：

```text
真实运行输入/输出 → ACTIVE_VALIDATION或HISTORICAL_RESULT
人工复核案例 → ACTIVE_FIXTURE
Prompt/Schema → ACTIVE_LIBRARY或ACTIVE_FIXTURE
合成解析负例 → ACTIVE_TEST / ACTIVE_FIXTURE
旧合成语义Corpus → LEGACY_REFERENCE或parser regression
```

人工复核结果可形成后续Gold，但必须记录：

```text
reviewer decision
review note
prompt/schema version
model/runtime identity
```

不把模型输出自动当Gold。

---

## 12. OpenClaw开发组合与运维

`nollm-openclaw`开发组合至少声明：

```text
OpenClaw adapter
nollm-access
formation prompt/schema
local Evidence/Handle stores
trace/logging选择
diagnose入口
```

实现或更新Windows PowerShell脚本：

```text
install
enable
disable
uninstall
diagnose
run formation smoke
```

要求：

```text
不覆盖用户其他配置；
可检测实际OpenClaw安装；
可显示插件加载状态；
可显示LLM调用错误；
可定位最新Formation run记录；
可恢复到未安装状态。
```

正式发布、自动更新和跨平台不是本任务目标。

---

## 13. 真实 E2E

必须在实际OpenClaw中完成：

```text
输入一段Evidence
→ OpenClaw事件/工具入口
→ 真实LLM Formation
→ Access解析和验证
→ canonical formed/defer result
→ Evidence回落显示
→ Lab运行记录
```

至少覆盖：

```text
形成1条statement；
形成多条statement；
多Evidence；
defer；
模型输出非法span后真实LLM重试；
模型改写原文被拒绝；
中英混合；
OpenClaw重载后再次成功。
```

不得：

```text
写入Core；
执行Placement；
用Fixture或Mock替代真实模型；
把OpenClaw日志当Evidence真值。
```

---

## 14. 模块独立与回归

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
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

### OpenClaw Adapter

按实际插件技术栈运行：

```text
unit tests
contract parser tests
installation smoke
diagnose smoke
real LLM probe
real Formation E2E
```

Mock可用于单元测试，但不能满足Live Gate。

### 项目回归

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py

python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests
python -m pytest -q packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests
python -m pytest -q reference/python/tests/m0
python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py

python lab/nollm-lab/m1/run_geometry_parity.py
python lab/nollm-lab/m1/run_core_capability_validation.py --check
python lab/nollm-lab/m1/run_m1_minimal_e2e.py

git diff --check
git status --short
```

GRF兼容回归可继续运行；缺`zstandard`时仅精确排除既有两项历史压缩测试。

---

## 15. 活动状态、向量和完成度回填

更新：

```text
ACTIVE_PROJECT
CURRENT_STATUS
MODULE_PROGRESS_LEDGER
OpenClaw runtime discovery report
Formation live loop report
Manifest / Boundary report
```

必须记录：

```text
预计推进向量；
实际推进向量；
每轮真实调用数；
Prompt/Schema变更；
Access合同变化；
人工复核指标；
失败分类；
实际模块完成度；
已知限制；
下一候选动作。
```

不得直接复制目标完成度。

允许：

```text
OPENCLAW_FORMATION_LIVE_CAPABILITY_VALIDATED_AT_<code_commit>
ACTIVE_BASELINE_AT_<final_head>
```

前提：

```text
真实OpenClaw Runtime与LLM被调用；
不少于36次Live调用；
无Python semantic fallback；
E2E可复现；
最终工作树干净。
```

禁止：

```text
真实模型语义质量已封版；
Formation已最终完成；
Placement已验证；
OpenClaw全产品集成完成；
自动进入下一阶段。
```

---

## 16. 真实停止条件

只在以下情况停止：

```text
1. 实际OpenClaw Runtime不存在或无法访问；
2. 实际LLM调用接口无法工作；
3. 模型输出无法通过任何合理Schema表达连续span或defer；
4. 必须使用Python语义fallback才能运行；
5. Formation必须修改Core或提前实现Placement；
6. OpenClaw适配必须复活旧memory provider/native store；
7. production cycle或边界违规无法清零；
8. 环境失败无法定位。
```

不要因以下问题停止：

```text
模型指标不漂亮；
Prompt需要多轮修改；
Schema字段需要调整；
部分case应defer；
真实调用有少量失败；
Corpus数量较小；
历史合成Corpus降级；
文档和路径调整。
```

---

## 17. 交付要求

必须：

```text
全部修改commit；
工作树干净；
仓库外生成一个完整历史Git Bundle；
验证Bundle；
只交一个Bundle。
```

建议Bundle名：

```text
nollm_aold_openclaw_formation_loop_20260712_<shorthead>.bundle
```

Codex最终回复只报告：

```text
branch / final HEAD
预计推进向量 / 实际推进向量 / 偏差
全部模块任务前后实际完成度
实际OpenClaw版本与LLM接口
Adapter结构与安装/诊断结果
三轮真实运行统计
Prompt/Schema迭代摘要
人工复核和失败分类
Python semantic fallback count
package tests / boundary / cycles
known limitations
Bundle filename / SHA-256
```
