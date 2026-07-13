# Nollm CAOLD 跨会话真实记忆闭环任务书

**模块缩写**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**日期**：2026-07-13  
**任务文件名**：`NOLLM_CAOLD_CROSS_SESSION_MEMORY_LOOP_TASK_20260713.md`  
**性质**：核心功能优先期的单一真实端到端能力任务  
**输入Bundle**：`nollm_aold_formation_json_resilience_20260713_9c0e1b6d.bundle`  
**输入Bundle SHA-256**：`720efcf3c9f072d88f6432e959fdad732fe7763a56c4858f5e15679bee718498`  
**输入分支**：`codex/cstaold-real-memory-loop`  
**输入HEAD**：`9c0e1b6d7e507de6240baae637a2bd0029950d76`  
**建议继续分支**：`codex/cstaold-real-memory-loop`  
**主环境**：真实Windows 10/11 + 当前实际OpenClaw  
**交付形式**：所有修改提交、工作树干净、仓库外单一完整历史Git Bundle  
**成功后环境**：插件保持安装和启用，现有Statement/Core/Handle/Cursor数据保留，交给用户正常聊天手动测试  
**结论边界**：只验证指定HEAD和真实环境中的跨会话记忆闭环；不宣称语义准确、长期稳定、发布就绪或完整安全。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
补齐最小JSON策略真值后，直接完成：
真实聊天→Formation→Placement→Core写入→OpenClaw重启→
独立新会话Recall→隐藏注入→主代理自然使用。

范围变化：
无。继续V3.4核心功能优先期；
不新增审计、安全、发布、兼容或治理主线；
不使用Python语义模拟；
不引入额外LLM Provider。
```

### 0.1 Gate纪律

```text
所有修正必须直接服务真实闭环；
外围问题就地修复，不单独立项；
旧接口或旧测试阻碍正确实现时允许删除；
一个JSON失败继续下一个turn；
有效结果必须继续Placement/Core；
成功后不卸载、不回退、不清空；
不以单元测试、汇总报告或Tag替代真实跨会话能力。
```

---

## 1. 任务前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已有能力 | 当前主缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 80% | 高 | 几何状态、Coverage、Bridge、有界Recall | 未验证独立新会话真实入口和Recall使用 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中 | 最小备份 | 只复用，不扩展 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 最小诊断 | 只复用，不扩展 | 否 |
| ACCESS | CSTAOLD checkpoint | 80% | 中高 | StatementStore、Placement编排、Handle、move binding、Recall映射 | 跨会话入口和Placement失败后的可继续状态 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | CSTAOLD checkpoint | 55% | 中 | Dream、JSON重试、Placement/Recall代码、插件启用 | P1默认不一致；新会话Recall未成立 | 是 |
| LAB | `IMPLEMENTED` | 75% | 中 | Prompt矩阵汇总、真实运行基础 | 缺逐attempt最小机器记录和跨会话证据 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 55% | 中 | 插件与配置基础 | P1未成为交付默认；活动Basis/Manifest陈旧 | 是 |

---

## 2. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 交付能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 80% | 85% | +5% | 真实重启和独立新会话有界Recall | Core文件、重开、Recall结果 | 规模和长期稳定性 |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | 最小备份smoke | 增量/版本迁移 |
| TRACE | 40% | 40% | 0% | 无变化 | 最小错误摘要 | 产品观察 |
| ACCESS | 80% | 85% | +5% | Formation→Placement→Handle→跨会话Recall完整编排 | 真实写入、映射、失败继续 | revision/forget质量 |
| HISTORY | 10% | 10% | 0% | 无变化 | 无 | 暂停 |
| AUDIT | 10% | 10% | 0% | 无变化 | 无 | 暂停 |
| OPENCLAW | 55% | 65% | +10% | 新会话Recall和隐藏注入，主代理自然使用 | 真实多会话E2E | 长期稳定性 |
| LAB | 75% | 80% | +5% | 最小可重算JSON策略和跨会话证据 | compact JSONL + 单一报告 | 完整质量评测暂停 |
| DISTRIBUTIONS | 55% | 60% | +5% | P1默认、V3.4活动Basis、插件保持启用 | 配置和手测交接 | 正式发布暂停 |

---

## 3. 直接保留的实现

不得重写：

```text
Hook阶段和后台Dream；
ConversationMaterial；
StatementStore；
Formation JSON轻修复；
同模型format repair；
P1/P2重做；
shadow零写入保护；
Placement Prompt；
AccessDecision/Core桥；
move binding；
MemoryCursor；
Recall Agent；
隐藏注入；
失败不阻断聊天。
```

当前任务只修真实闭环所需缺口。

---

## 4. JSON韧性的最小闭合修正

### 4.1 P1成为真实默认

统一以下默认：

```text
openclaw.plugin.json；
install.ps1；
index.ts fallback；
用户活动插件配置。
```

目标：

```text
prompt_version = dream-json-p1
```

保留P0/P2/P3作为Lab比较策略，不作为默认。

不得增加新Provider或API配置。

### 4.2 invalid_input不请求模型

对解析结果分类：

```text
invalid_json / invalid_schema：
  可执行同模型format repair或完整重做。

invalid_input / engineering_error：
  不请求模型；
  记录错误；
  清理本turn临时状态；
  继续下一个turn。
```

新增测试证明：

```text
invalid_input模型调用增量 = 0
后续case仍运行
```

### 4.3 收缩对象外文字修复

只允许：

```text
空白；
单层代码围栏；
有限明确前缀：
  JSON:
  Here is the JSON:
  Here is the requested JSON:
有限明确后缀空白。
```

任何其他自然语言、矛盾说明或第二个语义结论：

```text
拒绝；
交同模型重做。
```

### 4.4 最小策略记录

不重建大型审计体系。

建立一个紧凑文件：

```text
lab/nollm-lab/dream_agent/json_resilience/formation_attempts.jsonl
```

每次attempt仅记录：

```text
case_id
strategy_id
prompt_sha256
provider/model
attempt_kind
raw_output_sha256
parse/schema状态
error_class
repair_type
latency
final_case_status
下游Placement/Core/Recall状态
```

不保存完整用户聊天，不保存隐藏推理。

若本轮48次原始记录仍存在于本机测试profile：

```text
规范化后导入；
核对汇总；
不必重新调用模型。
```

若不存在：

```text
重新完成相同48次矩阵。
```

---

## 5. Placement JSON共用同一韧性机制

Placement模型输出若出现JSON问题：

```text
使用同一个strict parse / finite repair / same-model retry框架；
换用Placement Schema和Prompt；
单条失败继续后续Statement/turn；
不得Python决定Placement。
```

Placement的`invalid_input`同样不得触发模型重做。

不再建设第二套JSON基础设施。

---

## 6. 跨会话MemoryCursor

当前Cursor只按`session_key`保存，独立新会话无法进入旧几何现场。

增加一个有界Host入口层：

```text
session cursor；
agent/profile cursor。
```

### agent/profile cursor

只保存：

```text
最近成功Placement的少量GeometryAddress；
最近成功Recall使用的少量entry cells；
固定上限，建议8或16。
```

不得保存：

```text
source/topic/entity映射；
statement→statement关系；
语义标签；
object route；
全局关系索引；
向量或graph数据。
```

更新规则：

```text
成功Placement后更新session cursor和agent cursor；
成功Recall后可把实际使用entry cells移到cursor尾部；
失败不更新；
文件写入使用原子replace。
```

新会话Recall入口顺序：

```text
session cursor
→ agent/profile cursor
→ 明确的预设anchor或NONE
```

这是可丢弃的有界入口提示，不承担语义正确性。

---

## 7. 真实跨会话闭环

在用户实际OpenClaw环境完成：

### 7.1 写入

不少于：

```text
10个普通聊天turn；
至少3个有效MemoryStatement；
至少2个成功Placement/Core binding；
至少1个Placement失败并继续后续turn。
```

### 7.2 重启

```text
重启或reload OpenClaw；
重新打开Core/Statement/Handle/Cursor；
确认成功写入仍存在。
```

### 7.3 独立新会话

创建至少2个新的session key。

不得复用原写入session cursor。

在新会话中自然提问，至少覆盖：

```text
直接相关问题；
间接表达问题；
无相关记忆的NONE。
```

### 7.4 Recall与注入

必须证明：

```text
使用agent/profile cursor作为有限entry；
Core真实有界Recall；
Recall Agent真实选择；
隐藏上下文进入主代理；
主代理自然使用；
可见回答不提Nollm、Geometry或内部工具。
```

至少：

```text
2次独立新会话成功Recall；
1次NONE；
1次主代理自然使用已存记忆。
```

---

## 8. 写入失败和孤立Statement

Formation成功但Placement失败时，不允许形成不可见的永久垃圾。

采用最小方案之一：

### 方案A：Pending Statement

StatementStore记录：

```text
pending_placement
placed
```

Placement失败保持pending，后续可重试。

### 方案B：失败删除

若Statement只为当前Placement形成：

```text
Placement失败时删除本次新Statement；
不得删除已有Statement。
```

选择更符合现有Store的最小方案。

不得新增History/Audit系统。

报告必须统计：

```text
formed
placed
pending/deleted
binding
orphan count
```

硬条件：

```text
untracked orphan statement count = 0
```

---

## 9. 活动Basis与Manifest最小同步

就地完成：

```text
加入V3.4项目修订；
加入当前任务书；
ACTIVE_PROJECT指向V3.4和当前任务；
Current Status不再称V3.3为当前路线；
修正Placement/Recall前后矛盾；
Manifest生成一次并提交3个新增文件。
```

不扩大Manifest分类体系，不单独建立治理Gate。

---

## 10. 最小自动测试

只新增直接保护闭环的测试：

```text
P1默认一致；
invalid_input不模型重做；
外文字有限allowlist；
Placement JSON共用韧性机制；
agent cursor原子写入/重开；
新session使用agent cursor；
无cursor返回NONE；
Placement失败无孤立Statement；
成功写入后跨session Recall；
隐藏注入不出现Nollm字样。
```

旧外围测试阻碍正确实现时允许删除。

---

## 11. 最小真实记录

提交：

```text
formation_attempts.jsonl；
cross_session_loop_summary.json；
CSTAOLD_REAL_MEMORY_LOOP_REPORT.md。
```

`cross_session_loop_summary.json`只记录：

```text
OpenClaw/provider/model；
插件版本；
写入session；
新Recall sessions；
Statement IDs；
Placement actions；
GeometryAddress；
Core reopen；
Recall selected IDs；
主代理是否使用；
失败与继续；
插件最终状态；
数据保留状态。
```

不保存完整聊天，不新增receipt或审计包。

---

## 12. Final验收

必须同时满足：

```text
P1为仓库和用户实例默认；
invalid_input不触发模型重做；
有限JSON修复无语义抽取；
一个失败继续下一个；
无额外Provider/API；
真实Formation；
真实LLM Placement；
真实Core写入；
OpenClaw重启；
独立新会话Recall；
隐藏注入；
主代理自然使用；
NONE正常；
无Python语义fallback；
无graph/vector/embedding或外置关系索引；
无孤立Statement；
写入失败不污染；
插件最终保持启用；
Nollm数据保留；
工作树干净；
完整历史Bundle验证通过。
```

通过后允许：

```text
REAL_OPENCLAW_CROSS_SESSION_MEMORY_LOOP_VALIDATED_AT_<HEAD>
```

仍不得声称：

```text
记忆语义准确；
长期稳定；
发布就绪；
安全建设完成；
项目封板。
```

---

## 13. 实际向量与完成度回填

更新单一报告和进度账，记录：

```text
预计/实际向量；
模块实际完成度；
JSON策略结果；
Placement结果；
Core写入；
重启；
跨session Recall；
隐藏注入；
主代理自然使用；
失败case；
孤立Statement；
插件/数据最终状态。
```

不得因单元测试或同session Recall提升Core/OpenClaw完成度。

---

## 14. 真实停止条件

只在以下情况停止：

```text
1. agent/profile cursor仍无法让新会话进入真实几何现场；
2. Core Recall必须引入外置关系索引才能工作；
3. Placement必须用Python语义模拟；
4. 写入失败无法避免状态污染；
5. OpenClaw无法进行回复前隐藏注入；
6. 真实Windows环境故障无法定位。
```

不要因以下问题停止：

```text
某个JSON失败；
某个Placement失败；
Recall偶尔不相关；
模型质量不漂亮；
Manifest或旧测试问题；
未完成发布/安全设施；
两项zstandard依赖。
```

---

## 15. 交付要求

```text
所有修改commit；
工作树干净；
仓库外生成并验证一个完整历史Git Bundle；
只交一个Bundle；
插件保持安装和启用；
Statement/Core/Handle/Cursor数据不清空；
更新手动测试交接。
```

建议Bundle：

```text
nollm_caold_cross_session_memory_loop_20260713_<shorthead>.bundle
```

最终只报告：

```text
branch / final HEAD
预计/实际向量
全部模块实际完成度
P1与JSON韧性修正
Formation / Placement统计
Core写入和重启
跨session Recall
隐藏注入和主代理使用
失败继续与孤立Statement
插件最终状态
Nollm数据保留状态
known limitations
Bundle filename / SHA-256
```
