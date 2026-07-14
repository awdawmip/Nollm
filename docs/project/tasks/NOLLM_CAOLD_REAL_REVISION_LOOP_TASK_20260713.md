# Nollm CAOLD 真实修订闭环任务书

**模块缩写**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**日期**：2026-07-13  
**任务文件名**：`NOLLM_CAOLD_REAL_REVISION_LOOP_TASK_20260713.md`  
**性质**：“工作得对”阶段的第一个真实端到端能力  
**输入Bundle**：`nollm_caold_cross_session_memory_loop_20260713_c3354743_validated.bundle`  
**输入Bundle SHA-256**：`bfcc55e87b126fca9e46bf72a5203d3b5d359a2d4b0f6248a776316f4308d485`  
**输入分支**：`codex/cstaold-real-memory-loop`  
**输入HEAD**：`c3354743482e50477052c5095b0b8a30e1bbd1ee`  
**已验证能力**：`REAL_OPENCLAW_CROSS_SESSION_MEMORY_LOOP_VALIDATED_AT_c3354743482e50477052c5095b0b8a30e1bbd1ee`  
**建议分支**：`codex/caold-real-revision-loop`  
**主环境**：真实Windows 10/11 + 当前OpenClaw  
**交付形式**：所有修改提交、工作树干净、仓库外单一完整历史Git Bundle  
**成功后环境**：插件保持安装和启用，已有Nollm数据保留，交给用户继续正常聊天测试  
**结论边界**：验证一个真实修订能力；不宣称全部语义质量、长期稳定、发布或完整安全。

---

## 0. 任务推进向量

```text
任务推进向量：
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5%

主方向：
用户先形成一条真实记忆；
后续新会话自然纠正；
真实LLM在局部几何现场中选择revision而不是new；
Access原子更新；
重启后的第三个新会话只召回当前事实。

同时：
把OpenClaw中的Core构造、Core类型和Placement/Recall编排
收回Access公共服务，使依赖恢复为OpenClaw→Access→Core。

范围变化：
进入“工作得对”阶段；
不新增安全、审计、发布或历史产品；
不引入Python语义判断、向量、图或外置关系索引。
```

### 0.1 为什么选择revision

真实跨会话闭环已经证明“能工作”。

下一步最直接的正确性能力是：

```text
用户改变或纠正了一条已经存储的事实时，
系统不能把新旧两条都当成当前事实召回。
```

这同时检验：

```text
Formation；
局部Memory context；
LLM PlacementDecision；
revision动作；
Handle绑定；
Core replace/move；
重启；
跨session Recall；
主代理自然使用。
```

---

## 1. 任务前模块完成度

| 模块 | 生命周期状态 | 当前完成度 | 置信度 | 已验证能力 | 主要缺口 | 本任务影响 |
|---|---|---:|---|---|---|---|
| CORE | `CAPABILITY_VALIDATED` | 85% | 高 | 真实写入、重启、跨session有界Recall | 真实revision覆盖和当前状态召回 | 是 |
| SNAPSHOT | `IMPLEMENTED` | 50% | 中 | 最小备份 | 本任务不扩展 | 否 |
| TRACE | `IMPLEMENTED` | 40% | 中 | 最小事件 | 本任务不扩展 | 否 |
| ACCESS | `CAPABILITY_VALIDATED` | 90% | 高 | Statement、Placement、Handle、Recall真实编排 | Host仍直接依赖Core；revision原子闭环未验证 | 是 |
| HISTORY | `PROPOSED` | 10% | 低 | 章程 | 当前暂停 | 否 |
| AUDIT | `PROPOSED` | 10% | 低 | 章程 | 当前暂停 | 否 |
| OPENCLAW | `CAPABILITY_VALIDATED` | 70% | 中高 | 隐形Dream、真实Placement、跨session Recall和注入 | 修订识别、Access-only边界 | 是 |
| LAB | `IMPLEMENTED` | 80% | 中 | 最小Live报告 | 缺真实revision对照 | 是 |
| DISTRIBUTIONS | `IMPLEMENTED` | 60% | 中 | 插件安装和保持启用 | 活动状态、Manifest和Access-only组合未同步 | 是 |

---

## 2. 任务后目标完成度

| 模块 | 任务前 | 目标 | 预计增量 | 本任务能力 | 验收证据 | 剩余限制 |
|---|---:|---:|---:|---|---|---|
| CORE | 85% | 90% | +5% | 真实replace/move后只Recall当前Atom | 写入、重开、Recall | 规模和长期稳定 |
| SNAPSHOT | 50% | 50% | 0% | 无变化 | 最小备份smoke | 版本迁移 |
| TRACE | 40% | 40% | 0% | 无变化 | 最小错误摘要 | 产品观察 |
| ACCESS | 90% | 100% | +10% | Access-owned MemoryLoop服务；revision原子更新；无旧当前绑定 | 真实revision与失败回滚 | 后续章程扩展时重算基线 |
| HISTORY | 10% | 10% | 0% | 无变化 | 无 | 未实现 |
| AUDIT | 10% | 10% | 0% | 无变化 | 无 | 未实现 |
| OPENCLAW | 70% | 80% | +10% | 正常聊天纠正、局部revision决策和当前事实召回 | 三个独立session真实E2E | 其他模型和长期质量 |
| LAB | 80% | 85% | +5% | 最小revision/duplicate/similar对照 | 单一报告 | 大规模质量暂停 |
| DISTRIBUTIONS | 60% | 65% | +5% | Access-only依赖、活动Basis和Manifest一致 | machine check与插件保持启用 | 正式发布暂停 |

目标值只作预测，实际值按交付回填。Access达到100%只表示当前章程能力被验证，不代表永久封版。

---

## 3. 单一主验收场景

使用三个独立OpenClaw session。

### Session A：形成旧事实

用户自然表达一个适合后续纠正的长期信息，例如：

```text
项目周会固定在每周二上午九点。
```

要求：

```text
后台Formation；
真实LLM Placement选择new；
Core写入；
Handle binding；
agent/profile Cursor更新。
```

### Session B：自然纠正

用户在新session自然表达：

```text
项目周会以后改到每周四下午三点，周二上午的安排取消。
```

要求真实LLM读取局部几何现场并选择：

```text
revision_current
或符合现有合同的等价replace/move revision动作。
```

不得：

```text
Python关键词判断“改到/取消”；
简单创建第二条当前事实；
删除整个workspace；
依赖source/topic/entity索引。
```

### Session C：验证当前事实

Gateway重启后创建第三个新session，自然询问：

```text
项目周会现在什么时候开？
```

必须：

```text
Core从agent/profile Cursor进入真实Recall；
Recall Agent选择当前Statement；
旧时间不被注入主代理；
主代理自然回答周四下午三点；
不提Nollm、Geometry、工具或内部记忆。
```

---

## 4. 两个最小对照

对照不扩大为独立评测项目。

### 4.1 完全重复

新session再次表达当前事实：

```text
项目周会现在是每周四下午三点。
```

允许：

```text
reuse；
defer；
等价的无新当前事实动作。
```

不得形成第二个活动当前事实。

### 4.2 相似但不同

表达一个相关但独立的信息：

```text
项目技术评审会仍在每周二上午九点。
```

要求：

```text
new；
不得错误revision项目周会。
```

这两个对照只验证revision不过度和不不足。

---

## 5. Access-owned MemoryLoop

### 5.1 当前问题

OpenClaw适配器直接import：

```text
CoreRuntime；
GeometryAddress；
AtomHandle；
BridgeSpec；
RecallBudget。
```

并直接承担：

```text
Core打开；
Placement对象解析；
Core/Access组合；
有界Recall；
Handle/Core一致性；
Cursor地址序列化。
```

### 5.2 目标

在`nollm-access`建立一个最小公共编排对象，名称可按代码风格选择，例如：

```text
AccessMemoryLoop
AccessMemoryWorkspace
MemoryLoopRuntime
```

它拥有：

```text
CoreRuntime生命周期；
StatementStore；
HandleStore；
PlacementDecision解析后的AccessDecision执行；
有界局部Recall；
Handle/Core一致性；
revision原子更新；
Cursor使用所需的公开地址视图。
```

OpenClaw只依赖：

```text
nollm_access
```

OpenClaw不得import：

```text
nollm_core
```

### 5.3 OpenClaw仍负责

```text
ConversationMaterial；
Prompt；
调用真实LLM；
session/profile Cursor策略；
隐藏上下文注入；
用户无感运行。
```

Cursor可保存Access返回的opaque/public address mapping，不直接构造Core对象。

### 5.4 不新增兼容层

当前代码未正式发布。

直接迁移：

```text
memory_loop.py删除Core imports；
旧OpenClaw/Core直接路径删除；
测试同步更新；
不保留双路径或compatibility wrapper。
```

---

## 6. revision原子语义

修订成功后必须成立：

```text
旧当前Statement不再是当前绑定；
当前Handle指向新Statement；
Core cell中当前Atom内容为新事实；
Cursor仍可进入该局部现场；
重开后状态一致。
```

若现有动作使用同一Handle：

```text
优先复用现有GeometryAddress；
替换当前Atom；
更新Handle binding。
```

若需要move：

```text
先完成Core原子move/replace；
再更新binding；
失败回到旧状态。
```

不得留下：

```text
两个活动当前Handle；
新Statement无Handle；
旧Core Atom仍被当前Recall返回；
Cursor指向不存在的地址。
```

---

## 7. revision失败继续聊天

至少注入一次受控失败：

```text
Core replace/move失败；
或Handle binding失败。
```

要求：

```text
旧事实仍完整可Recall；
新事实不成为当前；
无孤立Statement；
主聊天继续；
后续turn仍能成功修订；
插件不禁用；
数据不清空。
```

只使用最小故障注入，不建设新的故障框架。

---

## 8. 局部LLM语义路径

Placement Prompt只得到：

```text
新MemoryStatement；
当前有限Cursor；
Core有限局部Recall结果；
当前可用Handle；
允许动作Schema。
```

不得得到：

```text
全局Statement列表；
source/topic/entity映射；
倒排表；
embedding；
vector；
graph；
Python相似度分数。
```

真实LLM决定：

```text
new / reuse / revision_current / move / defer。
```

Stitch不作为本任务硬要求。

---

## 9. Recall当前事实

Recall结果中：

```text
只允许当前绑定Statement作为有效注入候选；
旧修订Statement不得作为当前事实注入。
```

若旧Statement文件因调试或迁移仍存在：

```text
不能通过当前Handle/active binding进入正常Recall。
```

本任务不实施History产品，也不要求删除所有旧文件。

---

## 10. 最小Live数量

在真实OpenClaw中至少完成：

```text
1次初始new；
1次真实revision；
1次revision失败后旧事实保留；
1次失败后再次revision成功；
1次duplicate控制；
1次similar-distinct控制；
2次Gateway重启；
3个以上独立session；
2次当前事实相关Recall；
1次旧事实污染检查；
1次NONE或无注入。
```

聊天中不使用Nollm命令或工具名。

插件最终保持启用。

---

## 11. 最小记录

只更新一份：

```text
docs/project/CAOLD_REAL_REVISION_LOOP_REPORT.md
```

记录：

```text
初始Statement ID和Handle；
初始GeometryAddress；
修订Statement ID；
Placement动作；
修订前后binding；
Core重开结果；
相关Recall选择；
旧事实是否被注入；
duplicate结果；
similar-distinct结果；
失败回滚；
主代理可见回答；
插件和数据最终状态。
```

不保存完整聊天，不新增审计包。

---

## 12. 最小自动测试

只保留直接保护真实能力的测试：

```text
OpenClaw不import nollm_core；
AccessMemoryLoop打开/关闭；
revision_current成功；
move revision成功（如实际使用）；
binding失败回滚；
Core失败回滚；
旧事实不进入当前Recall；
duplicate不创建第二当前事实；
similar-distinct不错误revision；
重开；
跨session cursor；
隐藏注入。
```

Manifest最终HEAD：

```text
--check通过；
production violations=0；
production cycles=[]。
```

这不是独立治理目标，而是确认Access-only架构已经真实落地。

---

## 13. 活动状态最小同步

就地修正：

```text
ACTIVE_PROJECT；
CURRENT_STATUS；
MODULE_PROGRESS_LEDGER；
Manifest。
```

必须记录：

```text
c335474真实跨session闭环已验证；
进入“工作得对”阶段；
当前任务是真实revision闭环；
不再写跨session Recall未验证；
不再把OpenClaw→Core依赖标成合法。
```

不增加新的治理设施。

---

## 14. Final验收

必须同时满足：

```text
真实初始记忆；
真实自然纠正；
真实LLM选择revision；
Access原子更新；
Core重启；
第三个新session只Recall当前事实；
主代理自然使用当前事实；
旧事实不污染；
duplicate不重复当前事实；
similar-distinct不被错误覆盖；
失败后旧事实保留且后续可成功；
OpenClaw只依赖Access；
无Python语义判断；
无graph/vector/embedding或外置关系索引；
插件保持启用；
Nollm数据保留；
工作树干净；
完整历史Bundle验证通过。
```

允许记录：

```text
REAL_OPENCLAW_REVISION_LOOP_VALIDATED_AT_<HEAD>
```

不表示：

```text
所有记忆质量得到保证；
History完成；
长期稳定；
发布或完整安全完成。
```

---

## 15. 交付优先

无论revision是否最终成功：

```text
真实进展必须commit；
工作树必须clean；
必须生成并验证Bundle；
未完成项写IN_PROGRESS；
不得因为Live结果不理想拒绝交付；
插件和数据不得清空。
```

建议Bundle：

```text
nollm_caold_real_revision_loop_20260713_<shorthead>.bundle
```

最终只报告：

```text
branch / final HEAD
预计/实际向量
全部模块实际完成度
AccessMemoryLoop与依赖方向
初始new
真实revision
失败回滚
duplicate/similar控制
重启和当前事实Recall
旧事实污染检查
插件最终状态
Nollm数据保留状态
known limitations
Bundle filename / SHA-256
```
