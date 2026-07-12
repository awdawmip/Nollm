# Nollm AOLD 隐形 Dream Runtime 真值任务书（Rev.1）

**模块缩写**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`
**日期**：2026-07-12
**任务文件名**：`NOLLM_AOLD_INVISIBLE_RUNTIME_TRUTH_REV1_TASK_20260712.md`
**性质**：Hook阶段语义、ConversationMaterial来源、子代理模型继承、无感性证据与治理记录修正
**输入Bundle**：`nollm_aold_invisible_dream_agent_20260712_e2ac451e.bundle`
**输入Bundle SHA-256**：`274669377d675b94dc2eebb89b8f66a8ba1beb152b7bbcfd56c9bc6f81a8db34`
**输入分支**：`codex/aold-invisible-dream-agent`
**输入HEAD**：`e2ac451ec39befc5cfd539f1260268126ec072f7`
**当前已接受活动基线**：`3528c0130a2f29987e06105753310d3b2a592a2a`
**建议分支**：`codex/aold-invisible-runtime-truth`
**主环境**：Windows 10/11 + PowerShell
**交付形式**：全部修改提交、工作树干净、仓库外单一完整历史Git Bundle
**结论边界**：只验证运行时隐形性、材料来源和模型绑定；不验证MemoryStatement语义准确率，不进入Placement或Recall。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS 0% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
修正Dream Hook的真实阶段语义、ConversationMaterial采集、
子代理模型继承和无感性证据；
不再追求语义准确率，也不改Access/Core合同。

范围变化：
无。V3.3语义记忆工具路线保持；
不进入Placement、Recall、History或Audit实现。
```

### 0.1 向量解释

- `ACCESS 0%`：Dream公共合同和StatementStore保持不变，只做高风险回归。
- `OPENCLAW +10%`：真实区分after-turn/after-delivery，消除重复Hook，证明子代理模型绑定和非阻塞运行。
- `LAB +5%`：Live证据可从主回复、Hook和subagent原始记录重算。
- `DISTRIBUTIONS +5%`：状态、完成度、Manifest和模型策略配置形成机器真值。
- 其余模块`0%`：不修改能力。

### 0.2 非目标

```text
MemoryStatement语义准确率；
固定人工接受率；
原始聊天长期保存；
exact-span恢复；
Placement；
Recall；
revision/forget产品化；
Python语义fallback；
额外LLM API。
```

### 0.3 成功接入后的保留原则

一旦在用户实际 OpenClaw 环境中确认：

```text
插件已加载；
后台 Dream 可运行；
主聊天不受阻断；
StatementStore 可用；
运行时诊断通过；
```

后续不得为了“测试收尾”执行：

```text
卸载插件；
恢复安装前配置；
禁用已经验证成功的集成；
删除 StatementStore；
清空 Nollm workspace；
删除已有 MemoryStatement；
重置 Core / Access / Snapshot 状态；
覆盖用户现有 Nollm 配置；
把用户环境恢复成空白测试环境。
```

允许的破坏性测试必须在：

```text
独立临时 profile；
临时 workspace；
独立测试配置；
临时 StatementStore；
```

中完成，不得作用于用户正在使用的 Nollm/OpenClaw 实例。

只有以下情况允许对用户环境回退：

```text
用户明确要求；
发现不可恢复的数据损坏风险；
插件导致 OpenClaw 无法正常聊天且无法就地修复；
活动架构方向发生明确冲突。
```

即便发生上述情况，也应优先：

```text
就地修复；
暂停后台 Dream；
保留 StatementStore 和现有记忆数据；
记录可恢复状态；
```

不得默认清空 Nollm。

### 0.4 手动测试交接

自动 Gate 完成后，系统应保持：

```text
插件已安装；
插件已启用；
最终验证配置保持不变；
StatementStore 和既有数据保留；
Nollm workspace 保留；
诊断入口可用；
正常聊天可继续。
```

生成：

```text
docs/integration/openclaw/NOLLM_MANUAL_TEST_HANDOFF.md
```

内容仅包括：

```text
当前插件版本；
当前配置模式；
当前模型模式；
StatementStore位置；
如何通过正常聊天观察后台 Dream；
如何查看只读状态和诊断；
已知限制；
出现问题时如何暂停 Dream 而不删除数据。
```

用户手动测试只使用正常聊天，不要求在聊天中输入命令、工具名、JSON 或调用指令。

---

## 1. 输入审核基线

### 1.1 Git和Gate

```text
Bundle verify：通过
完整历史：通过
HEAD：e2ac451ec39befc5cfd539f1260268126ec072f7
工作树：clean

Core 39 passed
Snapshot 7 passed
Trace 3 passed
Access 55 passed
OpenClaw Python 19 passed
OpenClaw Node 6 passed
M0 45 passed
architecture/hygiene 8 passed
Geometry 9/9
Core capability 25/25
Minimal E2E passed
GRF 109 passed / 1 skipped / 2 zstandard unavailable
production violations=0
production cycles=[]
```

### 1.2 必须保留

```text
V3.3架构；
ConversationMaterial和Dream Formation合同；
StatementStore；
EvidenceStore兼容；
无主代理Formation工具；
api.runtime.subagent.run；
deliver=false；
Prompt v1/v2；
shadow/statement-store；
三轮Live历史记录；
Core/Snapshot/Trace不变。
```

---

## 2. 输入任务实际向量回填

先纠正上一任务：

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +0~5% | DISTRIBUTIONS +0~5%
```

不得继续记录：

```text
全部模块零偏差；
OPENCLAW +10已完全成立；
LAB/DISTRIBUTIONS目标值自动完成。
```

---

## 3. 任务前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 证据 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 80% | 高 | 39 tests；9/9；25维能力 | Placement、规模、跨进程 | 否，仅回归 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中高 | 7 tests | 版本迁移、增量快照 | 否，仅回归 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 3 tests | Host产品级观察 | 否，仅回归 |
| ACCESS | `CAPABILITY_VALIDATED` | 75% | 高 | Dream合同、StatementStore、兼容迁移 | Placement、修订、跨进程 | 是，仅回归 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程存在 | 未实现 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程存在 | 未实现 | 否 |
| OPENCLAW | Dream Agent工程checkpoint | 40% | 中 | subagent、deliver=false、45-turn记录 | 阶段语义、材料来源、模型继承、channel去重未验证 | 是 |
| LAB | `IMPLEMENTED` | 65% | 中 | 三轮记录和verifier | verifier依赖自报字段；无raw主回复 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 50% | 中 | V3.3和插件配置 | 状态placeholder、完成度和Manifest说明错误 | 是 |

---

## 4. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 80% | 80% | 0% | 无变化 | Core回归 | Placement和规模 |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | Snapshot回归 | 版本迁移 |
| TRACE | 40% | 40% | 0% | 无变化 | Trace回归 | 产品观察 |
| ACCESS | 75% | 75% | 0% | 合同不变 | 55+ tests | Placement和修订 |
| HISTORY | 10% | 10% | 0% | 无变化 | boundary | 未实现 |
| AUDIT | 10% | 10% | 0% | 无变化 | boundary | 未实现 |
| OPENCLAW | 40% | 50% | +10% | Hook阶段真实、材料去重、实际模型绑定、非阻塞Live | channel/CLI Live、subagent events、A/B记录 | 其他Provider和长期稳定性 |
| LAB | 65% | 70% | +5% | raw输出、Hook、subagent、Store证据可重算 | verifier mutation tests | 广泛真实用户数据 |
| DISTRIBUTIONS | 50% | 55% | +5% | 状态、Manifest、模型override策略和诊断一致 | machine truth | 正式发布、跨平台 |

---

## 5. Hook阶段语义修正

建立明确枚举：

```text
AFTER_DELIVERY
AFTER_TURN
```

规则：

```text
message_sent success -> AFTER_DELIVERY
agent_end -> AFTER_TURN
```

禁止：

```text
把agent_end写成main_reply_delivered；
用插件内部Date.now()伪造delivery时间；
在报告中混用after-turn和after-delivery。
```

Trace至少记录：

```text
source_hook
trigger_phase
hook_observed_at
hook_handler_returned_at
background_scheduled_at
prompt_build_started_at
subagent_started_at
main_command_returned_at（Live runner）
```

### Gateway/channel

优先使用：

```text
message_sent success
```

### CLI/webchat fallback

可以使用：

```text
agent_end
```

但必须标为：

```text
AFTER_TURN
```

只证明：

```text
主agent已完成；
后台工作不影响主agent结果。
```

不得声称已经外发。

---

## 6. Hook必须立即返回

当前Hook中调用：

```text
void launch(...)
```

launch会在第一次await前执行部分同步逻辑并启动Python bridge。

修改为明确后台调度：

```text
queueMicrotask / setImmediate / plugin-owned scheduler
```

Hook handler本身只：

```text
提取最小metadata；
登记一次性任务；
立即返回。
```

### 单元Gate

```text
message_sent handler同步返回；
agent_end handler同步返回；
handler不调用bridge；
handler不等待subagent；
handler不打开StatementStore；
```

### Live Gate

记录：

```text
hook_handler_duration_ms
```

硬条件：

```text
p95 <= 20ms
max <= 50ms
```

环境异常时可调整，但必须先证明不是Python/IO/模型操作发生在Hook中。

---

## 7. ConversationMaterial来源修正

### 禁止

不得再把：

```text
before_agent_run.event.prompt
```

直接作为`role=user`写入ConversationMaterial。

`before_agent_run`可以用于：

```text
run correlation；
父模型metadata；
run id；
session messages只读检查。
```

### 优先来源

#### Channel

```text
message_received.content
messageId
threadId
sessionKey
```

#### CLI/webchat fallback

从：

```text
agent_end.event.messages
```

提取真实：

```text
role=user
role=assistant
```

### 去重

建立统一Turn identity：

```text
messageId（优先）
runId + role + stable content digest（fallback）
```

同一turn经：

```text
message_received
before_agent_run
agent_end
```

观察多次时只保留一次。

### Material窗口

默认：

```text
当前user turn；
当前assistant reply；
前一个user turn（可选）；
最多一个历史assistant turn（可选）；
字符预算。
```

不得包含：

```text
system prompt；
skills/bootstrap内容；
隐藏工具定义；
Host注入上下文；
整个final prompt；
Dream Agent自身消息。
```

### 测试

```text
channel单turn；
CLI agent_end fallback；
message_received + before_agent_run不重复；
message_sent + agent_end不重复Dream；
多轮窗口；
system内容不进入；
assistant回复只出现一次；
Unicode和换行；
session隔离；
subagent自身被排除。
```

---

## 8. 同一turn只启动一次Dream

建立统一`TurnKey`：

```text
sessionKey
runId（优先）
messageId
fallback content/time digest
```

`message_sent`和`agent_end`必须共享同一个TurnKey。

规则：

```text
message_sent存在时，AFTER_DELIVERY胜出；
agent_end只作为fallback；
同一turn不允许两个request_id；
同一turn不允许两个subagent run；
```

增加：

```text
duplicate_hook_observation_count
duplicate_dream_suppressed_count
```

Live channel测试必须覆盖两个Hook均出现。

---

## 9. 模型继承真值

### 当前要求

`inherit`必须表示：

```text
Dream子代理实际使用当前父run解析出的provider/model。
```

不能只表示：

```text
插件不传model；
假定OpenClaw会自动继承；
trace写host-inherit。
```

### 必须监听

```text
subagent_spawned
subagent_ended
```

记录：

```text
parent_run_id
child_run_id
child_session_key
resolvedProvider
resolvedModel
outcome
endedAt
```

### 实现选择

#### 方案A：Host提供真实父模型继承

若官方runtime支持父session绑定继承，使用正式API并以`subagent_spawned`证据确认。

#### 方案B：显式同模型override

将父run的resolved provider/model传给subagent，并在安装时配置：

```text
plugins.entries.nollm-formation.subagent.allowModelOverride = true
plugins.entries.nollm-formation.subagent.allowedModels = [...]
```

这复用现有OpenClaw认证，不要求第二套API。

#### 方案C：无法保证

将配置名改为：

```text
host-default
```

不得继续称为inherit。

### Dedicated

必须：

```text
明确model；
Host allowModelOverride；
Host allowedModels；
插件allowed_models；
resolved child model一致。
```

### 诊断

`diagnose.ps1`必须显示：

```text
requested model mode
parent resolved model
child resolved model
Host override policy
allowed model set
```

---

## 10. 实际无感性Live Gate

本任务不评测语义准确率。

### 10.1 Controlled输入

至少：

```text
15个用户实际环境中的plugin enabled普通turn；
15个独立临时profile中的plugin disabled对照turn；
5个多轮session；
5个channel/message_sent案例（若目标环境可用）；
5个CLI/webchat AFTER_TURN案例。
```

要求：

```text
disabled对照不得在用户已成功接入的活动实例上执行；
不得为了对照测试禁用、卸载或清空用户的Nollm；
破坏性生命周期测试只使用独立临时profile和临时StatementStore。
```

消息保持普通聊天，不含：

```text
Nollm；
Dream；
工具名；
命令；
JSON；
调用指令。
```

### 10.2 保存受控原始输出

Lab验证模式允许保存：

```text
主agent CLI/官方chat返回JSON；
主agent可见assistant消息；
turn receipt；
Hook trace；
subagent spawned/ended；
Dream terminal result；
Store写入。
```

这是受控测试证据，不改变生产默认：

```text
persistSubagentTranscripts=false
debugTrace=false
```

### 10.3 硬条件

```text
主agent exit success = 100%
每个turn可见主assistant回复 = 1
Dream额外可见回复 = 0
Hook同步返回满足预算
主agent不等待Dream completion
Python semantic fallback = 0
duplicate Dream per turn = 0
```

CLI fallback不要求Dream在CLI return之后才启动，但必须如实记录：

```text
AFTER_TURN
```

同时证明：

```text
Dream terminal completion发生在主agent return之后
```

至少：

```text
90%的Dream completion在main return之后
```

若不满足，说明主流程可能等待后台任务。

### 10.4 延迟

报告enabled/disabled：

```text
median
p95
sample count
model/provider
```

不设固定产品通过率，但不得把无对照数据称为“无明显影响”。

---

## 11. Live Evidence verifier重写

从原始文件重算：

```text
turn数量；
主agent回复数量；
main return时间；
Hook阶段；
Hook返回耗时；
Dream start/completion；
subagent resolved model；
duplicate Hook；
duplicate Dream；
额外可见消息；
Store写入；
fallback计数。
```

不得信任：

```text
main_reply_delivered_at字段；
visible_message_count字段；
summary.json最终计数；
host-inherit字符串；
手工写入的verified=true。
```

### 变异测试

必须拒绝：

```text
把AFTER_TURN改成AFTER_DELIVERY；
删除主agent输出；
增加第二条可见回复；
同一turn添加第二个Dream；
篡改resolved child model；
Dream completion早于全部主return且报告无等待；
summary与raw记录不一致；
ConversationMaterial含system prompt；
重复user turn。
```

`--check`只读，不调用模型。

---

## 12. Statement写入幂等

同一turn重复观察或Gateway重载不得产生两个Statement批次。

调整：

```text
request_id
result_id
statement identity
```

使其稳定绑定：

```text
TurnKey + prompt/schema version + draft_id
```

而不是仅绑定随机：

```text
subagent runId
```

模型输出内容变化时：

```text
拒绝覆盖已有同ID不同内容；
记录冲突；
不静默last-writer-wins。
```

这不做语义去重；语义重复留给后续Placement。

---

## 13. 活动治理与进度账修正

更新：

```text
ACTIVE_PROJECT.md
NOLLM_CURRENT_STATUS.md
NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md
Manifest
AOLD runtime truth report
```

必须：

```text
替换PENDING_FINAL_COMMIT；
删除final closure措辞；
记录e2ac451为checkpoint而非active baseline；
修正任务前完成度；
修正上一任务实际向量；
Manifest reason不再写exact-span；
区分AFTER_TURN和AFTER_DELIVERY。
```

本任务完成后再计算：

```text
实际向量；
实际完成度；
置信度；
下一候选动作。
```

不得直接复制目标值。

当前状态必须记录：

```text
用户实际OpenClaw实例保持已安装、已启用；
最终验证配置未回退；
StatementStore未清空；
Nollm workspace未重置；
破坏性对照仅在临时profile执行；
已生成手动测试交接文件。
```

---

## 14. Manifest与章程

更新：

```text
OpenClaw Charter
Lab Charter
Distributions Charter
MODULE_OWNERSHIP_MANIFEST
```

Manifest分类：

```text
插件代码 -> OPENCLAW / ACTIVE
runtime truth validator -> LAB / ACTIVE_VALIDATION
受控Live raw输出 -> LAB / HISTORICAL_RESULT
当前任务/报告 -> DISTRIBUTION / ACTIVE governance
旧e2ac三轮证据 -> HISTORICAL_RESULT / superseded runtime evidence
```

不得把历史exact-span理由复制到当前Dream Agent资产。

---

## 15. 独立测试与项目回归

### Python

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

python -m pytest -q packages/nollm-core/tests
python -m pytest -q packages/nollm-snapshot/tests
python -m pytest -q packages/nollm-trace/tests
python -m pytest -q packages/nollm-access/tests
python -m pytest -q integrations/openclaw/formation-loop/tests/test_adapter.py
```

### Node

使用满足声明版本的Node：

```powershell
npm ci --ignore-scripts
npm test
npm run plugin:check
```

新增测试覆盖：

```text
Hook phase；
同步返回；
Turn去重；
Material来源；
subagent resolved model；
inherit/dedicated policy；
幂等。
```

### 治理与能力

```powershell
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py

python -m pytest -q reference/python/tests/m0
python -m pytest -q `
  reference/python/tests/test_no_forbidden_features.py `
  reference/python/tests/test_architecture_language.py `
  reference/python/tests/test_repository_hygiene.py

python lab/nollm-lab/m1/run_geometry_parity.py
python lab/nollm-lab/m1/run_core_capability_validation.py --check
python lab/nollm-lab/m1/run_m1_minimal_e2e.py
python lab/nollm-lab/dream_agent/reports/verify_runtime_truth.py --check

git diff --check
git status --short
```

GRF继续运行；仅缺`zstandard`时精确记录两项环境依赖。

---

## 16. Final Gate

```text
agent_end不再称为delivered；
message_sent与agent_end阶段区分；
Hook callback立即返回；
before_agent_run.prompt不作为用户turn；
ConversationMaterial无system/Host prompt；
同一turn只启动一个Dream；
inherit模式有实际resolved child model证据；
dedicated模式Host override policy真实；

enabled/disabled受控Live完成；
每turn恰好一个主回复；
额外Dream可见消息=0；
Dream completion不阻塞主回复；
无Python semantic fallback；
Statement写入幂等；

用户实际OpenClaw实例保持安装和启用；
最终配置不回退；
StatementStore和Nollm workspace未清空；
破坏性disabled/uninstall测试只在临时profile执行；
手动测试交接文件已生成；
用户可继续通过正常聊天测试；

状态无PENDING_FINAL_COMMIT；
无final closure；
进度账与任务书一致；
Manifest说明与V3.3一致；

Core/Snapshot/Trace/Access不回退；
production violations=0；
production cycles=[]；
所有check只读；
工作树干净；
完整历史Bundle验证通过。
```

---

## 17. 允许状态

通过后可记录：

```text
OPENCLAW_INVISIBLE_DREAM_RUNTIME_VALIDATED_AT_<commit>
ACTIVE_BASELINE_AT_<final_head>
```

只表示：

```text
后台运行时、模型绑定、材料窗口、无感性和Store边界通过。
```

不表示：

```text
MemoryStatement语义准确；
Placement或Recall已实现；
不同模型效果一致；
Nollm保证记忆质量。
```

---

## 18. 真实停止条件

只在以下情况停止：

```text
1. OpenClaw无法提供可区分的after-turn/after-delivery事件；
2. Plugin Hook无法立即返回；
3. 实际父模型无法继承或真实解析；
4. 同一turn无法跨Hook去重；
5. ConversationMaterial只能依赖完整final prompt；
6. 后台Dream必然阻塞主回复；
7. 修正必须修改Core或进入Placement；
8. production cycle无法清零；
9. 实际Windows环境失败无法定位。
```

不要因以下事项停止：

```text
模型语义结果不漂亮；
emit/defer比例变化；
invalid JSON存在；
enabled/disabled延迟有噪声；
历史Live记录降级；
完成度下调；
两项zstandard环境依赖；
用户希望保留当前Nollm数据并自行手动测试。
```

不得以“需要干净测试环境”为理由清空用户Nollm。需要空白环境时创建独立临时profile。

---

## 19. 交付要求

```text
所有修改commit；
工作树干净；
仓库外生成一个完整历史Git Bundle；
验证Bundle；
只交一个Bundle。
```

建议Bundle：

```text
nollm_aold_invisible_runtime_truth_20260712_<shorthead>.bundle
```

Codex最终只报告：

```text
branch / final HEAD
预计向量 / 实际向量 / 偏差
全部模块任务前后实际完成度
Hook阶段语义
ConversationMaterial来源与去重
inherit/dedicated实际resolved model
enabled/disabled无感性统计
主回复与Dream时间关系
可见消息数量
Statement幂等
用户实际实例的安装/启用保留状态
StatementStore与Nollm数据保留状态
临时profile破坏性测试范围
手动测试交接文件
package tests / boundary / cycles
known limitations
Bundle filename / SHA-256
```
