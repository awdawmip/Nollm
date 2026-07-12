# Nollm AOLD 隐形 Dream Agent 任务书

**模块缩写**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**日期**：2026-07-12
**任务文件名**：`NOLLM_AOLD_INVISIBLE_DREAM_AGENT_TASK_20260712.md`
**性质**：Access语义Formation合同迁移、OpenClaw后台子代理接入、无感运行和真实迭代
**输入工程checkpoint**：`bac2c7f06017f90adbc24ae3b71a99cae1581e85`
**当前已接受活动基线**：`3528c0130a2f29987e06105753310d3b2a592a2a`
**Access exact-span实现checkpoint**：`1cad3f756528d91e1d88dc443357cc46ae2dac52`
**建议分支**：`codex/aold-invisible-dream-agent`
**主环境**：Windows 10/11 + PowerShell
**交付形式**：所有修改提交、工作树干净、仓库外单一完整历史Git Bundle
**结论边界**：形成后台Dream Formation和StatementStore能力记录；不宣称模型语义质量有保证，不实现完整Placement或Recall。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% | LAB +5% | DISTRIBUTIONS +5%

主方向：
把exact-span／原始Evidence路线替换为OpenClaw后台Dream Agent；
MemoryStatement允许LLM改写、拆分和合并；
默认继承OpenClaw模型与认证，不要求用户填写第二套API；
Nollm只保证工具、结构和状态边界，不保证模型语义准确。

范围变化：
Access Formation公共合同和持久Store语义发生调整；
OpenClaw由主代理显式工具切换为插件Hook+后台子代理；
Core、Snapshot、Trace、History、Audit章程范围不变。
```

### 0.1 向量解释

- `ACCESS +10%`：建立Dream Formation活动合同、StatementStore及exact-span兼容迁移。
- `OPENCLAW +10%`：实现主回复后的无感后台子代理，不再暴露Formation工具给主代理。
- `LAB +5%`：建立真实后台运行记录、模型/Prompt比较和诚实质量观察。
- `DISTRIBUTIONS +5%`：默认继承模型、可选专用模型、安装与诊断组合。
- 其余模块`0%`：只做高风险回归。

### 0.2 Gate纪律

1. 每个内部Gate开始和结束时复述推进向量。
2. 新增受影响模块或任一模块实际偏差超过5%时，更新任务名称、范围、向量和状态。
3. 不以语义准确率作为工程停止条件。
4. 不通过Python规则提高Formation质量。
5. 不自动启动Placement或Recall任务。

---

## 1. 开工依据与撤回项

### 1.1 必须读取

```text
最新第一性原理；
V3.1稳定模块架构；
NOLLM_ARCHITECTURE_AMENDMENT_V3_3_SEMANTIC_MEMORY_TOOL_20260712.md；
当前状态和模块进度账；
本任务书；
Access/OpenClaw/Lab/Distributions章程；
根目录AGENTS.md。
```

### 1.2 正式撤回

退出活动执行入口：

```text
V3.2 exact-span Formation路线；
NOLLM_AOLD_RAW_EVIDENCE_CHAT_TRUTH_TASK_20260712.md；
用户原始聊天逐字保全Gate；
主代理可见nollm_form_statement工具路线。
```

### 1.3 保留为迁移资产

```text
RawEvidenceRecord；
EvidenceSpan；
StatementSelection；
exact-span验证和assemble；
FileEvidenceStore；
旧Formation Corpus与Live记录；
旧插件安装和Windows Launcher代码。
```

不得直接删除，须先建立替代合同、迁移测试和兼容读取。

---

## 2. 任务前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 80% | 高 | 9/9 Geometry；25维能力；有界Recall | Placement、规模、跨进程 | 否，仅回归 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 原子恢复与SnapshotDiff | 版本迁移、增量快照 | 否，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 多Sink和状态隔离 | Host级观测未组合 | 否，仅回归 |
| ACCESS | `CAPABILITY_VALIDATED` checkpoint | 65% | 中高 | MemoryStatement、exact-span Formation、Store和AccessRuntime | 合同错误绑定原文Evidence；Store命名与语义过时 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程存在 | 未实施 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程存在 | 未实施 | 否 |
| OPENCLAW | 正常聊天插件checkpoint | 35% | 中 | 实际模型、插件生命周期、正常聊天触发经验 | 主代理工具显性；Formation阻塞/嵌套；无后台Dream Hook | 是 |
| LAB | `IMPLEMENTED` | 65% | 中 | Live记录、Prompt、验证基础 | 评测仍围绕exact span；缺后台运行比较 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 50% | 中 | OpenClaw组合和脚本 | 默认模型策略、静默模式和新合同未登记 | 是 |

---

## 3. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 80% | 80% | 0% | 无变化 | Core回归、9/9、25维 | Placement和规模 |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | Snapshot回归 | 版本迁移 |
| TRACE | 40% | 40% | 0% | 无变化 | Trace回归 | 产品观测 |
| ACCESS | 65% | 75% | +10% | Dream Formation合同；StatementStore；exact-span兼容迁移 | 公共API、Store迁移、canonical tests | Placement、修订策略 |
| HISTORY | 10% | 10% | 0% | 无变化 | boundary | 未实施 |
| AUDIT | 10% | 10% | 0% | 无变化 | boundary | 未实施 |
| OPENCLAW | 35% | 45% | +10% | after-reply Hook；后台subagent；inherit/dedicated模型；无可见消息 | Runtime证据、live runs、latency ordering | Recall、长期产品稳定性 |
| LAB | 65% | 70% | +5% | 三轮后台真实运行、模型/Prompt/上下文比较、质量观察 | live records、metrics、failure classes | 样本小，无广泛用户数据 |
| DISTRIBUTIONS | 50% | 55% | +5% | 无额外API的默认安装；高级模型配置；静默诊断 | manifest、install/doctor、config tests | 正式发布、跨平台 |

---

## 4. 活动架构与文档真值

加入并启用：

```text
NOLLM_ARCHITECTURE_AMENDMENT_V3_3_SEMANTIC_MEMORY_TOOL_20260712.md
```

更新活动Basis，明确：

```text
V3.1：稳定模块边界和基线治理；
V3.3：当前语义记忆工具和Dream Agent路线；
当前任务：AOLD invisible Dream Agent；
V3.2 exact-span路线：SUPERSEDED；
Raw Evidence Chat Truth任务：WITHDRAWN。
```

同步更新：

```text
第一性原理中原始Evidence永久保全条款；
Access/OpenClaw/Lab/Distributions章程；
README/ARCHITECTURE/ROADMAP必要差异；
CURRENT_STATUS；
MODULE_PROGRESS_LEDGER。
```

同一要求只保留一个活动权威来源。

---

## 5. Access Dream Formation 公共合同

### 5.1 新增对象

建议名称可按代码风格调整，但职责必须成立：

```text
ConversationMaterial
DreamFormationRequest
DreamMemoryDraft
DreamFormationResult
DreamFormer
StatementStore
FileStatementStore
```

#### ConversationMaterial

临时输入，最低字段：

```text
material_id
turns: tuple[ConversationTurn, ...]
```

ConversationTurn最低字段：

```text
role
content_utf8
```

性质：

```text
不可持久化为Nollm默认状态；
只供Dream Agent运行；
不要求逐字映射到最终statement。
```

#### DreamMemoryDraft

最低字段：

```text
draft_id
content_utf8
```

可选提示字段：

```text
stability_hint
uncertainty_hint
scope_hint
```

这些只是模型输出提示，不是Core事实或产品保证。

#### DreamFormationResult

```text
result_id
request_id
outcome: emit | defer
drafts
defer_reason
decided_by = llm | human | fixture
```

### 5.2 结构验证

Access只验证：

```text
exact类型；
非空UTF-8；
canonical顺序；
ID唯一；
数量；
单条和总字符预算；
emit/defer互斥；
Schema version。
```

Access不得验证：

```text
是否原文span；
是否语义正确；
是否与原聊天逐字一致；
是否应长期保存；
```

### 5.3 MemoryStatement生成

确定性地将通过结构验证的Draft转为：

```text
MemoryStatement
```

可以生成稳定statement ID；ID算法不得用来判断语义重复。

---

## 6. StatementStore迁移

### 6.1 新合同

```text
StatementStore.put(statement)
StatementStore.get(statement_id)
StatementStore.exists(statement_id)
```

`FileStatementStore`保存canonical MemoryStatement。

### 6.2 旧合同兼容

```text
EvidenceStore
FileEvidenceStore
put_original
get_original
```

处理为：

```text
compatibility re-export或wrapper；
调用发出deprecation说明；
旧nollm_access_evidence_v1文件可读取；
新写入使用statement schema；
迁移测试覆盖旧workspace重开。
```

不得在替代未完成前删除旧文件。

### 6.3 AccessRuntime

更新命名和文档：

```text
capture → stage_statement或put_statement
evidence_store → statement_store
```

可保留旧方法兼容层。

当前任务只把MemoryStatement写入StatementStore，不执行Placement。

---

## 7. OpenClaw官方Hook和subagent能力发现

必须在实际OpenClaw 2026.6.11或当前环境确认：

```text
可用于主回复交付后的插件Hook；
message/session生命周期字段；
目标agent/session信息；
后台subagent runtime；
deliver=false；
继承当前模型的行为；
专用模型override配置；
run状态、超时和取消；
Gateway重载；
```

生成：

```text
docs/integration/openclaw/DREAM_AGENT_RUNTIME_DISCOVERY.md
```

不得假设旧工具插件结构自动适用。

若没有真正的post-delivery Hook：

```text
选择最接近的官方消息生命周期Hook；
必须证明主回复不等待Dream；
不得退回主代理可见Tool；
不得通过聊天命令触发。
```

若无法实现不阻塞且无可见消息：

```text
停止并记录OPENCLAW_INVISIBLE_DREAM_UNAVAILABLE。
```

---

## 8. 后台Dream Agent实现

### 8.1 插件形态

将主代理可见的：

```text
nollm_form_statement
```

从默认工具表移除或默认禁用。

插件通过官方Hook：

```text
主回复已交付
→ 收集bounded ConversationMaterial
→ api.runtime.subagent.run(...)
```

要求：

```text
deliver = false；
不向parent/requester产生可见announce；
主回复不waitForRun；
后台任务有超时；
失败不发送用户消息；
同一session限并发；
重复事件有幂等键。
```

### 8.2 ConversationMaterial范围

默认：

```text
当前用户turn；
当前主代理reply；
最近最多2个用户turn；
最近最多1个assistant turn；
总字符预算。
```

这些是Prompt输入策略，可配置，不是持久状态。

不得默认复制完整会话。

### 8.3 Formation输出

后台子代理只输出：

```text
DreamFormationResult JSON
```

不得：

```text
调用message；
向用户回复；
决定GeometryAddress；
直接写Core；
调用Placement；
生成工具命令。
```

---

## 9. 模型配置

### 9.1 默认配置

```text
memoryModel.mode = inherit
```

不要求：

```text
新API Key；
Base URL；
Provider；
额外模型选择。
```

### 9.2 专用模型

可选：

```text
memoryModel.mode = dedicated
memoryModel.model = provider/model
```

必须使用OpenClaw正式subagent model override和allowedModels配置。

插件不得直连Provider HTTP。

### 9.3 Fallback

```text
inherit解析失败
→ configured modelFallback
→ 仍失败则本轮defer
```

不得切换到Python semantic splitter。

### 9.4 外部API

`external`只预留接口或文档，不在本任务实现，也不进入默认安装UI。

---

## 10. Dream Prompt

建立版本化Prompt，例如：

```text
dream-v1
dream-v2
dream-v3
```

Prompt允许：

```text
改写；
合并；
拆分；
补全指代；
删除交互性措辞；
defer。
```

Prompt要求：

```text
形成自足、可长期使用的表达；
保留重要否定、条件、时间和不确定性；
不要无依据增加事实；
不确定时defer；
不输出隐藏推理；
只输出Schema。
```

不得要求exact span。

Prompt/Schema位于OpenClaw Adapter或Lab的单一权威位置，插件和测试不得各自维护一套。

---

## 11. Shadow到StatementStore的三轮Live迭代

至少三轮真实OpenClaw运行，每轮不少于15个eligible turns，总数不少于45。

### 第1轮：shadow

```text
后台子代理真实运行；
不持久化；
记录emit/defer和结构错误；
确认用户无可见变化。
```

### 第2轮：shadow + Prompt调整

```text
根据第1轮真实输出调整Prompt或上下文预算；
不增加Python语义规则；
回归第1轮代表案例；
仍不持久化。
```

### 第3轮：StatementStore写入

```text
结构验证通过的MemoryStatement写入FileStatementStore；
不Placement；
不Core写入；
不向用户确认已记住；
记录statement IDs和Store结果。
```

Live输入必须来自普通真实聊天，不在聊天中使用命令、工具名、JSON或调用指令。

---

## 12. 无感性Gate

必须从运行轨迹证明：

```text
main_reply_delivered_at < dream_started_at；
主回复不等待subagent completion；
额外用户可见消息 = 0；
主代理模型可见工具表中默认无Formation工具；
Dream Agent无message工具；
Dream失败时主回复仍正常；
插件disabled时普通聊天行为保持正常；
安装默认不要求第二套API；
```

观察指标：

```text
hook scheduling overhead；
Dream后台延迟；
成功/超时/失败；
emit/defer；
每轮statement数量；
主回复可见消息数量；
```

不要求主回复文本与未安装时逐字相同；模型本身非确定性。要求交互形态和可见流程无明显变化。

---

## 13. 质量观察而非准确性硬保证

每轮人工或assistant抽样标记：

```text
useful
harmless
wrong
overstored
missed
uncertain
```

记录：

```text
review_type；
reviewer；
note；
model；
prompt；
context mode。
```

不得：

```text
把assistant review称为human review；
以固定accept rate决定工程是否通过；
为提高分数添加Python语义特判；
把模型输出自动当Gold。
```

质量较差时允许：

```text
换模型；
改Prompt；
改上下文预算；
增加defer倾向；
后续通过revision/forget修正。
```

---

## 14. Lab资产与Trace

新目录建议：

```text
lab/nollm-lab/dream_agent/
  prompts/
  schemas/
  runs/
  reviews/
  reports/
```

生产默认：

```text
persistSubagentTranscripts = false
debugTrace = false
```

验证时可临时开启受控记录，但不得默认保存完整聊天。

Manifest分类：

```text
Prompt/Schema → ACTIVE_LIBRARY或ACTIVE_FIXTURE
Live验证入口 → ACTIVE_VALIDATION
固定运行输出 → HISTORICAL_RESULT
旧exact-span Corpus → LEGACY_REGRESSION或LEGACY_REFERENCE
```

---

## 15. Distribution和安装

`nollm-openclaw`默认：

```text
dreamAgent.enabled = true
dreamAgent.mode = background
dreamAgent.modelMode = inherit
dreamAgent.persistTranscripts = false
dreamAgent.writeMode = shadow（初始）
formationTool.visible = false
externalApi.required = false
```

开发验证后可把：

```text
writeMode = statement-store
```

设为显式配置，是否成为长期默认由后续审核决定。

脚本必须支持：

```text
install
enable
disable
uninstall
diagnose
shadow status
statement-store status
```

普通用户无需运行聊天命令。

---

## 16. 独立测试

### Access

新增或更新：

```text
DreamFormationRequest/Result canonical；
MemoryDraft预算；
emit/defer；
Draft→MemoryStatement；
StatementStore写入/重开；
旧EvidenceStore兼容；
旧workspace迁移；
AccessRuntime旧方法兼容；
无exact-span活动依赖。
```

### OpenClaw

```text
Hook注册；
post-delivery时间顺序；
subagent deliver=false；
inherit模型；
dedicated模型配置；
allowedModels；
timeout/failure fail-open；
幂等；
session并发；
无Formation主代理工具；
无可见announce；
StatementStore桥。
```

Mock只用于单元测试，Live Gate必须使用真实OpenClaw subagent。

---

## 17. 项目回归

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py

python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests
python -m pytest -q packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests
python -m pytest -q integrations/openclaw/formation-loop/tests
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

Node/OpenClaw插件按实际版本执行：

```text
npm ci
npm test
plugin build/validate
runtime inspect
真实background subagent live gate
```

GRF兼容回归继续运行；环境缺`zstandard`时只记录既有两项依赖。

---

## 18. Final Gate

必须满足：

```text
V3.3进入活动Basis；
V3.2 exact-span路线降级；
Raw Evidence任务撤回；
Access活动API不再要求原文span；
StatementStore成为活动持久合同；
旧EvidenceStore可兼容读取和迁移；

默认安装不要求额外LLM API；
OpenClaw后台subagent继承会话模型；
可选dedicated模型使用正式配置；
插件不直连Provider HTTP；

Formation不作为主代理可见工具；
普通聊天无命令和显式Nollm调用；
主回复先交付，Dream后启动；
Dream deliver=false；
额外用户可见消息=0；
Dream失败不影响聊天；
Python semantic fallback=0；

真实Live turns >= 45；
第3轮StatementStore写入通过；
无Core写入、无Placement；
production violations=0；
production cycles=[]；
所有普通--check只读；
Final Gate后工作树干净；
完整历史Bundle验证通过。
```

语义准确率、人工接受率和每轮emit率只记录，不作为硬Gate。

---

## 19. 实际向量和完成度回填

必须更新：

```text
ACTIVE_PROJECT；
CURRENT_STATUS；
MODULE_PROGRESS_LEDGER；
Dream Agent runtime discovery；
三轮Live报告；
Manifest/Boundary报告；
兼容迁移报告。
```

记录：

```text
预计推进向量；
实际推进向量；
各模块偏差；
模型模式；
Prompt版本；
Live turn数；
emit/defer；
后台成功/超时/失败；
用户可见额外消息；
StatementStore写入；
质量观察；
实际完成度；
已知限制；
下一候选动作。
```

允许：

```text
ACCESS_DREAM_FORMATION_CAPABILITY_VALIDATED_AT_<commit>
OPENCLAW_INVISIBLE_DREAM_AGENT_VALIDATED_AT_<commit>
ACTIVE_BASELINE_AT_<final_head>
```

不得声称：

```text
模型记忆准确性得到保证；
Placement已完成；
Recall质量已验证；
用户原文被永久保存；
OpenClaw完整产品集成已封版。
```

---

## 20. 真实停止条件

只在以下情况停止：

```text
1. OpenClaw没有可用的插件Hook或后台subagent API；
2. 无法保证主回复不等待Dream；
3. subagent无法deliver=false或会强制产生可见消息；
4. 必须使用Python语义规则才能形成MemoryStatement；
5. 旧Store无法迁移且会造成真实数据丢失；
6. 必须修改Core或提前实现Placement；
7. production cycle无法清零；
8. 实际Windows环境失败无法定位。
```

不要因以下问题停止：

```text
模型形成内容不够好；
部分turn全部defer；
不同模型结果不一致；
Prompt需要多轮调整；
质量指标不漂亮；
旧exact-span测试需要迁移；
Manifest行数变化；
两项zstandard环境依赖。
```

---

## 21. 交付要求

必须：

```text
全部修改commit；
工作树干净；
仓库外生成一个完整历史Git Bundle；
验证Bundle；
只交一个Bundle。
```

建议Bundle名称：

```text
nollm_aold_invisible_dream_agent_20260712_<shorthead>.bundle
```

Codex最终回复只报告：

```text
branch / final HEAD
预计推进向量 / 实际推进向量 / 偏差
全部模块任务前后实际完成度
Access Dream Formation与StatementStore
exact-span/EvidenceStore迁移
OpenClaw Hook与subagent runtime
inherit/dedicated模型配置
三轮Live统计
无感性指标
StatementStore写入
质量观察与已知限制
package tests / boundary / cycles
Bundle filename / SHA-256
```
