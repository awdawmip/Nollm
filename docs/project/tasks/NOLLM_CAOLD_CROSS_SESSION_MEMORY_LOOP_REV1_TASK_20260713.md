# Nollm CAOLD 跨会话真实记忆闭环任务书（Rev.1：交付优先）

**模块缩写**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`
**日期**：2026-07-13
**任务文件名**：`NOLLM_CAOLD_CROSS_SESSION_MEMORY_LOOP_REV1_TASK_20260713.md`
**性质**：核心功能优先期的真实端到端续跑任务；允许阶段性交付
**当前分支**：`codex/cstaold-real-memory-loop`
**当前已提交HEAD**：`9c0e1b6d7e507de6240baae637a2bd0029950d76`
**当前工作区**：在上述HEAD之上存在未提交的CAOLD实现与真实Windows/OpenClaw验证结果
**已知已完成**：

```text
P1仓库默认；
受限JSON外壳修复；
invalid_input不重试；
Placement共用JSON修复与有限重试；
agent/profile有界Cursor；
跨session Cursor测试；
Placement失败清理本次孤立Statement；
Python 32 passed；
Node 14 passed；
10个真实写入回合；
Gateway重启；
两个新session查询；
真实Placement/Core写入；
Placement失败后主聊天继续。
```

**当前阻塞**：

```text
部分有效Formation结果在桥接序列化层被误分类为invalid_input；
P2/P3历史直接矩阵缺少可回溯Prompt哈希；
完整跨会话Recall和主代理自然使用尚未形成可验收证据。
```

**主环境**：真实Windows 10/11 + 当前OpenClaw
**交付形式**：所有真实进展必须commit；工作树干净；仓库外单一完整历史Git Bundle
**成功后环境**：插件保持安装和启用，Nollm数据不清空，交给用户继续正常聊天测试
**结论边界**：允许交付`IN_PROGRESS` Bundle；缺失证据如实记录，不补造，不因未完成闭环阻止交付。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
先保存并交付当前真实进展；
再修复Formation桥接序列化误判；
继续真实Placement→Core→跨session Recall；
证据不完整时如实标记，不阻止commit和Bundle。

范围变化：
无。继续V3.4核心功能优先期；
不新增审计、安全、发布或兼容建设；
不引入额外LLM Provider；
不使用Python模拟语义。
```

### 0.1 交付优先原则

以下规则优先于旧任务中的完整矩阵、完整Gate和最终验收要求：

```text
真实代码进展必须及时commit；
真实运行结果必须及时记录；
未完成也必须能生成Bundle；
缺失数据标记NOT_AVAILABLE / NOT_VERIFIED；
不可回溯Prompt哈希不得补造；
没有原始attempt记录时不得根据汇总反推伪造；
Bundle可以是工程checkpoint，不必冒充最终验收。
```

不得出现：

```text
因为P2/P3不完整而不提交；
因为跨会话Recall未完成而不打Bundle；
为了满足任务格式伪造Prompt哈希；
为了凑够48条重新篡改历史统计；
把IN_PROGRESS写成VALIDATED。
```

---

## 1. 第一动作：提交当前工作区

开始任何新修复前：

```text
1. 记录git status和diff；
2. 运行当前定向回归；
3. 确认Gateway健康；
4. 提交当前未提交修改；
5. 生成一次阶段性完整历史Bundle。
```

建议提交信息：

```text
checkpoint(caold): preserve cross-session loop progress and live results
```

建议阶段Bundle：

```text
nollm_caold_cross_session_checkpoint_20260713_<shorthead>.bundle
```

阶段Bundle允许状态：

```text
CAOLD_CROSS_SESSION_LOOP_IN_PROGRESS_AT_<HEAD>
```

不得写：

```text
REAL_OPENCLAW_CROSS_SESSION_MEMORY_LOOP_VALIDATED
```

阶段Bundle生成后继续同一分支修复，不需要等待外部审核。

---

## 2. 证据要求降级为最小真实记录

### 必须保留

```text
当前Provider/model；
实际Prompt版本；
已完成P0/P1真实统计；
P2/P3完成到什么程度；
有效Formation数量；
invalid_json / invalid_schema / invalid_input数量；
Placement尝试/成功/失败；
Core写入；
Gateway重启；
新session查询；
插件最终启用状态；
数据保留状态。
```

### 缺失数据的写法

P2/P3原始Prompt哈希缺失时：

```text
prompt_sha256 = null
evidence_status = "not_available"
reason = "historical live run did not persist prompt hash"
```

不得：

```text
重新计算一个不对应当时调用的Prompt哈希；
根据当前Prompt冒充历史Prompt；
因为缺哈希而否定真实运行本身；
因为缺哈希而阻止Bundle。
```

### 不再强制

当前任务不再强制补齐：

```text
完整48条历史逐attempt记录；
所有P2/P3原始输出；
完整Prompt哈希矩阵；
大型JSONL审计集；
每个统计字段均可独立重算。
```

后续新attempt应记录Prompt版本/哈希，但不追溯伪造旧记录。

---

## 3. 当前唯一代码阻塞：Formation桥接误分类

### 3.1 目标

定位为何部分结构上有效的Formation结果在桥接层被分类为：

```text
invalid_input
```

必须区分：

```text
模型输出无效；
JSON解析无效；
Schema无效；
桥接传输或序列化错误；
字段映射错误；
版本不一致；
Python/Node边界类型错误。
```

### 3.2 调试顺序

对一个已知“模型输出看似有效但最终invalid_input”的真实case，逐层保存最小脱敏值：

```text
raw model visible output；
JSON repair后文本；
JSON parse结果；
Schema validate结果；
Node→Python bridge payload；
Python收到的payload；
DreamFormationRequest；
DreamFormationResult或异常；
最终error_class。
```

只需要一个可复现case即可定位，不要求重建全部历史矩阵。

### 3.3 修复原则

允许修复：

```text
字段命名不一致；
JSON envelope解包；
UTF-8/换行；
null/undefined差异；
Node/Python类型转换；
Schema版本；
请求ID/结果ID映射；
枚举序列化；
数组/tuple转换。
```

不得：

```text
用Python猜MemoryStatement；
自动生成缺失语义字段；
把无效Schema强制当成功；
通过Prompt掩盖确定性桥接错误；
对invalid_input继续请求模型。
```

### 3.4 invalid_input规则

```text
invalid_input / engineering_error：
  不调用format repair；
  不调用Formation重做；
  记录并继续下一个turn。

invalid_json / invalid_schema：
  才允许有限修复和同模型重做。
```

---

## 4. 一个失败继续下一个

运行时必须保证：

```text
turn A发生invalid_input
→ 记录engineering_error
→ 不写Statement/Placement/Core
→ 不重启Gateway
→ 不禁用插件
→ 继续turn B
```

批次结束必须报告：

```text
total turns
completed turns
formation success
formation failed
engineering errors
placement attempted
placement succeeded
placement failed
unprocessed turns = 0
```

硬条件：

```text
一个JSON或桥接失败不能中断后续正常聊天。
```

---

## 5. 修复后最小真实续跑

桥接问题修复后，不再先补大矩阵，直接运行：

```text
不少于10个普通聊天turn；
失败继续下一个；
至少2个有效MemoryStatement；
至少1个真实Placement/Core binding；
至少1个Placement失败后继续；
Gateway保持健康。
```

如果10个turn仍无有效Statement：

```text
如实提交和打Bundle；
状态保持IN_PROGRESS；
报告最常见错误；
插件保持启用；
不清空数据；
继续同一任务。
```

---

## 6. 跨session闭环

一旦存在有效Core写入：

```text
1. 确认Statement/Handle/Core/Cursor已持久化；
2. Gateway reload或OpenClaw重启；
3. 创建两个新的session；
4. 通过agent/profile有界Cursor进入Core Recall；
5. 至少一个新session取得相关Recall；
6. Recall结果隐藏注入主代理；
7. 主代理自然使用，不提Nollm；
8. 至少一个无相关记忆问题返回NONE或不注入。
```

最低通过能力：

```text
1次真实写入；
1次重启；
1次独立新session Recall；
1次隐藏注入；
1次主代理自然使用。
```

该最低能力完成后即可记录真实闭环checkpoint；无需等待大规模质量统计。

---

## 7. agent/profile Cursor边界

继续使用有界Cursor：

```text
最近成功Placement的少量GeometryAddress；
最近成功Recall的少量entry cells；
固定上限。
```

不得添加：

```text
source/topic/entity路由；
statement关系表；
向量；
graph；
全局语义索引。
```

Cursor丢失时允许返回NONE，不得用Python语义搜索替代。

---

## 8. Placement失败与孤立Statement

保持已实现规则：

```text
本次新建Statement在Placement失败时删除；
不得删除已有Statement；
失败不写Handle；
失败不更新Cursor；
后续turn继续。
```

必须统计：

```text
formed
placement_attempted
placement_success
placement_failed
new_statement_deleted_after_failure
orphan_statement_count
```

硬条件：

```text
orphan_statement_count = 0
```

---

## 9. 最小测试

只运行和补充直接保护当前链路的测试：

```text
有效Formation桥接不被误判invalid_input；
invalid_input不触发模型重做；
invalid_input后下一个turn继续；
Node/Python序列化一致；
Placement失败删除本次Statement；
agent cursor重开；
新session读取agent cursor；
Recall隐藏注入；
无额外用户可见消息。
```

旧外围测试失败不阻止提交和Bundle；如直接阻碍正确代码，可更新或删除。

---

## 10. 报告

只更新：

```text
docs/project/CSTAOLD_REAL_MEMORY_LOOP_REPORT.md
```

报告分为：

### 已验证事实

```text
commit；
测试；
真实turn；
Gateway；
Formation；
Placement；
Core；
Cursor；
重启；
Recall；
插件和数据状态。
```

### 未验证/缺失

```text
P2/P3哪些记录缺Prompt哈希；
哪些历史attempt不可回溯；
哪些新session尚未成功Recall；
哪些主代理使用尚未观察。
```

不得把缺失信息写成失败，也不得把未知写成通过。

---

## 11. 提交与Bundle节奏

至少在以下节点提交：

```text
A. 当前未提交进展checkpoint；
B. bridge invalid_input修复；
C. 真实跨session闭环结果或最新IN_PROGRESS状态；
D. 报告和交付。
```

每个主要checkpoint都允许生成Bundle，但最终只向用户交付最新一个完整历史Bundle。

若任务仍未闭环，最终Bundle名称可为：

```text
nollm_caold_cross_session_in_progress_20260713_<shorthead>.bundle
```

若闭环真实成立：

```text
nollm_caold_cross_session_memory_loop_20260713_<shorthead>.bundle
```

---

## 12. 验收状态

### 部分交付允许状态

```text
CAOLD_BRIDGE_SERIALIZATION_FIXED_AT_<HEAD>
CAOLD_CROSS_SESSION_LOOP_IN_PROGRESS_AT_<HEAD>
```

### 完整闭环状态

只有以下全部成立时：

```text
真实Formation；
真实Placement；
Core写入；
重启；
独立新session Recall；
隐藏注入；
主代理自然使用；
```

才允许：

```text
REAL_OPENCLAW_CROSS_SESSION_MEMORY_LOOP_VALIDATED_AT_<HEAD>
```

### 任何状态均必须交付

无论是否完整闭环：

```text
修改必须commit；
工作树必须clean；
必须生成并验证Bundle；
插件保持启用；
Nollm数据保留；
报告真实状态。
```

---

## 13. 实际推进向量与完成度

本任务结束时回填：

```text
预计向量；
实际向量；
已实现能力；
未完成能力；
任务前/目标/实际完成度；
下一步仍属于同一闭环的动作。
```

不因缺Prompt哈希下调已真实实现的代码能力；也不因测试通过自动上调未真实完成的跨session能力。

---

## 14. 最低安全底线

```text
不破坏OpenClaw原始数据；
Formation/Placement失败不污染Core；
插件可关闭；
Nollm可备份；
成功接入后不卸载、不清空；
所有修改有commit；
交付单一完整历史Bundle。
```

不新增：

```text
审计系统；
安全子系统；
发布门禁；
内部兼容层；
完整证据基础设施。
```

---

## 15. 真实停止条件

只在以下情况停止继续编码：

```text
1. 桥接序列化无法定位且无法得到任何有效Formation；
2. Placement/Core写入会造成不可恢复污染；
3. 新session Recall必须依赖外置关系索引；
4. OpenClaw无法进行隐藏注入；
5. 实际Windows环境故障无法定位。
```

即便停止继续编码，也必须：

```text
提交当前进展；
生成报告；
工作树clean；
生成Bundle；
保留插件和数据。
```

---

## 16. 最终交付要求

Codex最终只报告：

```text
branch / final HEAD
提交列表
当前闭环状态：IN_PROGRESS或VALIDATED
桥接invalid_input根因和修复
真实turn统计
Formation / Placement / Core结果
重启与跨session Recall
隐藏注入和主代理使用
缺失或不可回溯证据
插件最终启用状态
Nollm数据保留状态
known limitations
Bundle filename / SHA-256
```

不得因为未完成而拒绝生成交付物。
