# Nollm 架构修订 V3.11 Rev4：无碰撞入口身份、上下文命题形成与共享召回路径生长

**版本**：V3.11 Rev4  
**日期**：2026-07-21  
**性质**：对 V3.11 Rev3 Live 失败的根因纠偏；不废止 Prompt-bounded Atlas、realized Junction、即时 Capture、异步吸收、V3.9 Coverage 或单入口 Recall  
**输入检查点**：`c40f8bf6a5be6184e5e56236c96d2817fed4bee5`  
**输入 Bundle**：`nollm_caold_runtime_integrity_atomic_proposition_growth_20260721_c40f8bf.bundle`  
**输入 Bundle SHA-256**：`16a77df3eabac4a135c3e20f3bf109d56afab8dad19011817a5d46d5feeba771`  
**输入状态**：`CAOLD_RUNTIME_INTEGRITY_ATOMIC_GROWTH_IN_PROGRESS_AT_<HEAD>`  
**检查点重新定性**：`RUNTIME_INTEGRITY_AND_RELATION_ENTRY_COLLISION_CHECKPOINT_AT_c40f8bf`  
**状态**：活动架构修订；不表示已经实现

---

# 0. 修订结论

`c40f8bf` 已经真实完成：

```text
Core trace callback 重入拒绝；
operation 中 close/import 拒绝；
旧 Junction 完整评分后再截输出；
Access fatal rollback 诊断与 FAILED 状态；
commit/readback 状态显式化；
损坏 Statement item 级降级；
confirmed revision Atlas 新鲜度；
live/frozen Evidence 分离；
Provider identity 实取；
九条原子 Capture 均 durable Admission。
```

但其“one-cell Provider 反例”不成立，因为 Live Recall 受一个确定性入口身份碰撞影响：

```text
每个 Progressive Atlas region 内的第一 support entry
都被命名为 progressive-entry:0；

fast Recall 将所有 region entries 按 entry_id 放进字典；

相同 entry_id 相互覆盖；

最终 Reader 实际只剩最后一个 region 的 entry。
```

因此：

```text
东京、日期、天气和无关查询
→ 全部只能选择同一个会议记录 Cell (4,0)
```

这不是 one-cell 几何失败，而是 Reader 入口身份丢失。

同时，八条事实被放成 independent_seed 还暴露两个 LLM 教学缺口：

```text
1. Proposition Writer 只看当前 Capture，
   无法可靠解析“那天”“同一天”“之后”等叙事指代，
   并已将东京雨停日期错误写成 2026-07-20。

2. Cartographer 被提示去寻找“已经支持/包含新命题答案”的区域，
   而不是寻找“未来读者会先进入、并可沿此路径发现新事实”的共享召回邻域。
```

本修订确立：

> **Atlas entry 身份必须在一次操作内全局无碰撞；Writer 必须在不重放旧事实的前提下获得有界、按时间排列的叙事上下文；Recall Lens 必须区分“直接回答新事实的问题”和“用于进入共享关系场的入口问题”。Cartographer 解析的是共享召回路径，不要求旧 Locality 已经包含新答案。**

---

# 1. 能力重新定性

`c40f8bf` 可以证明：

```text
运行时重入和事务可靠性明显提高；
Evidence 生命周期已改正；
原文即时 Capture 和异步吸收成立；
Writer/Cartographer 可产生九条 durable Statements；
每条 Statement 仍为一个 Atom、Handle、Cell；
一个东京 related_growth 边成立。
```

它没有证明：

```text
生产 Reader 看见了完整 Atlas entry 集合；
one-cell 模型无法形成关系臂；
Cartographer 会识别共享召回关系；
Writer 能正确解析跨轮时间和代词；
东京/时间/天气三关系入口失败；
原子命题场生长被几何证伪。
```

禁止继续使用：

```text
true one-cell Provider counterexample
```

描述该检查点。

---

# 2. 无碰撞 Atlas Entry Identity

## 2.1 当前错误

当前 entry ID 在 region 内局部生成：

```text
progressive-entry:0
progressive-entry:1
...
```

不同 region 可拥有相同 ID。

Cartographer Wire 同时携带：

```text
region_id + entry_id
```

所以局部 ID 尚可消歧。

fast Recall Wire 只返回：

```text
entry_id
```

并将 entries 以该 ID 建字典，导致跨 region 覆盖。

## 2.2 新身份合同

每个可选择 entry 必须拥有一个在当前 Atlas operation 内唯一的身份。

推荐：

```text
entry_id =
  hash(
    atlas_fingerprint,
    region_id,
    GeometryAddress.stable_key
  )
```

或等价 canonical identity。

必须满足：

```text
同一 Atlas page 全局唯一；
同一 Atlas state 可复现；
不同 region 同一局部 index 不碰撞；
mutation/fingerprint 变化后旧 ID 失效；
不包含 Statement、Topic、query 或语义。
```

## 2.3 Wire

活动 Reader/Cartographer 可选择以下任一方案：

### 方案 A

```json
{
  "region_id": "...",
  "entry_id": "..."
}
```

以二元组校验。

### 方案 B

```json
{
  "entry_id": "globally unique operation-local ID"
}
```

但必须在 page 构造时机器验证全局唯一。

Codex 可选择兼容成本最低的方案。

## 2.4 Page 不变量

`ProgressiveAtlasPage` 或 Access validator 必须拒绝：

```text
duplicate region_id；
duplicate selectable entry identity；
entry 指向不在 region support 中的 Cell；
同一 entry identity 对应多个 Cell。
```

不得继续通过 dict overwrite 隐式消歧。

## 2.5 Recall 不变量

fast Recall：

```text
entries 输入数量
=
Atlas 中全部 selectable support entries 数量。
```

构建 Prompt 前、模型返回后均验证。

---

# 3. Contextual Proposition Writer

## 3.1 为什么需要上下文

当前 Capture-only Writer 对以下表达无法可靠独立解释：

```text
那天晚上；
同一天；
之后；
那里；
这次行程；
这个会议。
```

只用 Capture 时间戳不能解决：

```text
“同一天”究竟指哪一天；
“会议记录”指哪场会议；
“雨停了”属于东京哪次降雨。
```

上下文缺失已经导致：

```text
2026年7月21日东京的雨
→ 错误写成 2026年7月20日雨停。
```

## 3.2 Narrative Context Window

Writer 输入分为：

### Absorption sources

```text
当前待吸收 Capture(s)；
决定本批 Capture 状态；
新 Statement 的主要来源。
```

### Context-only evidence

```text
同一 session / user / workspace；
时间上紧邻；
已 Capture 的前序 user/assistant turns；
可包括少量已 admitted current Statements；
只用于解析代词、时间、事件连续性；
不因被再次展示而重新 Admission。
```

建议初始预算：

```text
preceding Captures <= 4；
context current Statements <= 4；
total context chars <= 6000；
严格按时间排列。
```

这些是 Policy，可实测调整。

## 3.3 Provenance

每条 Proposition 必须分别记录：

```text
source_capture_ids：
  本批次需要推进状态的 Capture；

evidence_spans：
  支撑命题内容的 exact spans；
  可来自 source Capture 或 context-only Capture；

context_statement_refs：
  若使用已 admitted Statement 解析指代，
  记录 Statement ID 和引用用途。
```

不得把 context-only Capture 自动标记 admitted/no-memory。

## 3.4 Temporal resolution

命题中出现的绝对日期、时间或地点，如果不是当前源文本的原样内容，必须有可验证来源：

```text
capture timestamp；
exact context span；
已有 current Statement。
```

建议输出：

```text
resolved_references:
  kind: temporal|coreference|location
  normalized_value
  basis_refs
```

Access 只验证引用存在、时间规则和身份，不做开放式语义推理。

至少必须机械阻止：

```text
没有任何 2026-07-20 basis
→ Writer 生成 2026-07-20。
```

## 3.5 不允许上下文污染

```text
旧 context facts 不得被复制成新 Statements；
generic assistant advice 不得自动成为用户事实；
context 只用于完成当前命题；
provenance 不完整则 retry/defer；
不得用 embedding、Topic、Entity 选上下文。
```

上下文选择只依据：

```text
同 session；
固定时间邻近；
固定条数/字符预算；
当前 admitted chain 的显式 handle relation（若已有）。
```

---

# 4. Direct Lens 与 Entry Lens

## 4.1 当前单一 Lens 的歧义

当前 `future_query` 同时承担：

```text
“什么问题直接由新命题回答”
和
“未来读者可能从哪个已有局部进入”。
```

模型因此倾向：

```text
旧 region 必须已经能回答 future_query
→ 才 resolve；
否则 independent_seed。
```

这会阻止自然场生长。

## 4.2 Direct Query

每条 Proposition 有 1～4 个：

```text
direct_queries
```

它们由新命题直接回答。

例：

```text
用户取消浅草后去了哪里？
→ 东京站。
```

Direct Query 用于未来 Recall 测试，不直接映射已有 region。

## 4.3 Entry Query

每条 Proposition 有 1～4 个：

```text
entry_queries
```

含义：

> 如果未来读者尚不知道这条新事实，他可能先进入哪个较宽的关系邻域，再沿字段找到它？

例：

```text
新命题：
取消浅草后去了东京站。

direct query：
取消浅草后去了哪里？

entry query：
用户这次东京行程发生了什么？
```

旧东京/浅草 Locality 不需要已经包含“东京站”答案，只需是未来读者合理进入的共同关系场。

## 4.4 Cartographer 的解析标准

Cartographer 对 Entry Query 判断：

```text
该 region 是否是未来读者查找这类经历时合理的第一站；
新事实放在该 region 附近后，是否能扩展其关系场；
是否存在真实共享的地点、时间、事件延续、比较或因果上下文。
```

不得要求：

```text
region 已经包含新命题答案；
representative Statement 与 direct query 精确匹配。
```

也不得仅凭：

```text
一个泛化词；
语言表面相似；
任意日期；
任意地点。
```

强行 resolve。

## 4.5 Relation 类型不持久化

Prompt 可以用自然语言说明：

```text
shared place；
shared time；
event continuation；
contrast/comparison；
cause/consequence。
```

这些只是 LLM 的临时思考示例。

不保存：

```text
relation_type；
Topic；
Entity；
edge label；
face meaning。
```

最终仍只保存几何位置。

---

# 5. Cartographer 的教学方式

## 5.1 正面示例

### 东京行程延续

```text
已有：
用户在东京取消浅草行程。

新：
取消浅草后用户去了东京站。

正确：
resolve 到东京/浅草 Locality；
因为未来读者询问“东京行程发生了什么”会先进入该处。

错误：
因为旧 Locality 不包含“东京站”答案而 unresolved。
```

### 会议延续

```text
已有：
用户在7月21日参加线上会议。

新：
那天晚上用户整理会议记录。

正确：
用上下文解析“那天”和“会议”；
resolve 到会议 Locality。
```

### 天气对照

```text
已有：
7月21日东京下雨。

新：
同一天大阪晴天。

正确：
entry query 可为“7月21日天气情况如何”；
resolve 到东京降雨/日期 Locality，形成对照生长。
```

## 5.2 负面示例

```text
审计日志保留30天
与
东京天气

→ 无共享召回路径；
independent_seed。
```

```text
服务器备份凌晨2点
与
7月21日线上会议

→ 仅都含时间，不足以共享Locality；
independent_seed。
```

## 5.3 局部 detail

若 Atlas representative 不足以判断：

```text
Cartographer 可以 request_local_detail；
同一 session；
有界 current Statements；
不打开全字段；
不创建额外独立模型 session。
```

---

# 6. Reader Entry Identity 与完整性

## 6.1 Fast Recall 修复

构建 Reader candidates 时：

```text
不得用 entry_id 单键 dict 覆盖；
不得静默减少条目；
必须报告：
  atlas_entry_count；
  prompt_entry_count；
  duplicate_entry_count。
```

活动 Gate：

```text
atlas_entry_count = prompt_entry_count；
duplicate_entry_count = 0。
```

## 6.2 选择返回

Reader 必须返回：

```text
唯一可校验的 entry identity；
或 region_id + entry_id。
```

Access 映射到唯一 GeometryAddress。

## 6.3 多 region fixture

至少建立：

```text
9 regions；
每个 region 都只有一个 local index 0 entry；
Reader Prompt 中仍出现9个不同 selectable IDs；
可分别强制选择9个 Cell。
```

这直接锁住本次 bug。

---

# 7. 持久状态

持久状态不变：

```text
Capture；
MemoryStatement；
HandleBinding；
Core Atom/Cell；
worker state。
```

不持久：

```text
Narrative Context Window；
resolved references；
Direct/Entry Query；
Atlas pages；
Cartographer traversal；
entry candidate IDs；
query→entry；
fact→entries。
```

Proposition provenance 是否持久：

```text
只持久必要 Evidence refs；
不持久完整 Prompt 或 LLM reason。
```

---

# 8. 东京—时间—天气重跑标准

使用与 `c40f8bf` 相同九类原子事实，允许修正错误日期文本。

必须形成：

```text
T0：东京下雨；
东京 arm：
  取消浅草；
  改去东京站；

时间/事件 arm：
  7月21日线上会议；
  那天晚上整理会议记录；

天气 arm：
  同日大阪晴天；
  东京雨在当日晚间停止；

unrelated：
  审计日志；
  服务器备份。
```

要求：

```text
T1 related to T0；
T2 related to T1或东京arm；
T3可独立seed或连接日期；
T4 related to T3；
T5 related toT0/日期天气；
T6 related toT0/天气arm；
两个unrelated independent seed。
```

不是每一条都必须多 Lens，关系由真实 Provider决定；但以下硬 Gate 必须满足：

```text
related_growth >= 5；
independent unrelated >= 2；
错误日期 = 0；
duplicate/orphan = 0。
```

---

# 9. Relation-entry Recall

## 9.1 正常产品 Recall

修复 entry identity 后，普通 Reader 应能看到不同 region entries。

至少验证：

```text
东京查询选择东京arm entry；
日期/会议查询选择时间arm entry；
天气查询选择天气arm entry；
无关查询选择无关或NONE；
distinct selected entries >= 3。
```

## 9.2 因果 Gate

隐藏：

```text
T0 target Cell；
T0 preview。
```

从三个 arm 外端分别单入口：

```text
东京 entry → T0；
时间 entry → T0；
天气 entry → T0；
path非空；
三个entry不同；
同一Handle；
unrelated entry不达。
```

路径长度第一版：

```text
>=1 即证明entry identity和relation growth；
目标仍以>=2为优先观察，
不得为长度2强行扭曲自然场。
```

这次不再把“未达到人为arm长度2”直接升级为multi-cell证据。

---

# 10. Writer 语义完整性 Gate

至少包含：

```text
“今天”由Capture timestamp解析；
“同一天”引用前序明确日期；
“那天晚上”引用会议日期；
“之后”引用前序事件；
日本语/中文混合；
assistant paraphrase不得覆盖用户原意。
```

必须拒绝：

```text
无basis的绝对日期；
错误地点；
将assistant建议当成用户事实；
复制context-only旧事实；
多个source Capture归属错误。
```

---

# 11. 模型调用与效率

保持：

```text
Capture前台0 Provider；
Writer common 1 call/batch；
Cartographer 1 session/batch；
每Prompt<=64KB；
Recall common hidden calls<=1；
Core local V3.9数量级。
```

新增上下文不得造成：

```text
Writer Prompt >64KB；
每条Statement单独Writer；
为每个Entry Query单独Cartographer session。
```

记录：

```text
context capture count/chars；
Writer prompt bytes；
Cartographer turns；
entry counts；
Provider seconds；
backlog drain。
```

---

# 12. 禁止路线

```text
用entry_id碰撞后任意保留一个Cell；
用关键词/实体抽取代替Cartographer；
持久relation_type；
Topic/Entity节点；
query/fact entry map；
embedding/vector/graph；
multi-entry Recall；
复制Atom；
multi-cell；
多物理层；
Stitch；
用context窗口重新Admission旧事实；
因一条Live失败扩张Core。
```

---

# 13. 最终架构概括

```text
Writer需要足够的叙事上下文，
才能把“那天”“同一天”“之后”写成正确命题。

Writer提出：
  这条事实直接回答什么问题；
  未来读者会从什么更宽的关系问题进入。

Cartographer不寻找“已经包含答案的Cell”，
而寻找“放进去以后会让这条关系路径继续生长的Locality”。

Atlas中的每一个入口都必须有真正唯一的身份，
否则再好的几何也只会被Reader看到最后一个Cell。

未来Reader从不同关系入口进入，
再由字段找到同一个Atom。
```

> **LLM 使用 LLM 的关键不是增加模型数量，而是让 Writer 负责命题与未来问题，让 Cartographer 负责共享召回路径，并确保 Reader 真的拥有完整、无碰撞的几何入口。**
