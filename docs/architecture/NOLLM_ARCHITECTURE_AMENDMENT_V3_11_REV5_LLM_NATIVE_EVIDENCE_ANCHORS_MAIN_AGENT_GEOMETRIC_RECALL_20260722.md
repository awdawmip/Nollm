# Nollm 架构修订 V3.11 Rev5：LLM 原生 Evidence Anchor、陈旧计划拒绝与主代理几何 Recall

**版本**：V3.11 Rev5
**日期**：2026-07-22
**性质**：对 V3.11 Rev4 的生产可用性纠偏；不废止上下文 Writer、Direct/Entry Query、Prompt-bounded Cartography、realized Junction、即时 Capture、异步吸收或单入口 Recall
**输入检查点**：`a4d8e3135ef894453e1d01dc5c19139d23d9c71f`
**输入 Bundle**：`nollm_aold_contextual_writer_shared_retrieval_growth_20260721_a4d8e31.bundle`
**输入 Bundle SHA-256**：`9bc3cbe6a8952461c555f9b4bd5fba283a194a4d0f764dd1c2d2c3cc7b9c66aa`
**检查点重新定性**：`CONTEXTUAL_WRITER_SHARED_RETRIEVAL_GROWTH_CHECKPOINT_AT_a4d8e31`
**状态**：活动架构修订；不表示已经实现

---

## 0. 修订结论

`a4d8e31` 已经真实证明：

```text
Progressive Atlas entry identity 无碰撞；
上下文 Writer 可以使用有界前序 Capture；
Direct Query 与 Entry Query 分离；
9 条 Capture → 9 条 durable Statements；
6 related growth + 3 independent seeds；
东京、会议、天气选择三个不同入口；
T0 可从多个关系入口以非空路径到达；
无关 seed 不到达；
Gateway restart 与 NONE；
Core/Access 可靠性修复保持。
```

但它仍不适合作为生产完成基线：

```text
1. 活动 parser 仍接受 legacy Writer v1，
   可以绕过绝对日期、resolved reference、Direct/Entry Query 等 Rev4 约束。

2. Writer 被要求手算 Unicode start/end 和 basis_span_indexes。
   9 条成功 Capture 的 attempt 总数为 31；
   Trace 中至少 8 次正式校验失败：
   span 不匹配、index 被误作字符偏移、outer text、错误 outcome、无日期 basis。
   这把确定性字符串定位错误交给了 LLM。

3. resolved_reference 的 basis_capture_ids 与 basis_span_indexes
   没有被机械交叉绑定；
   声称的精确 provenance 可以引用互不对应的 Capture 和 span。

4. Cartographer 在 20～100 秒 Provider 调用期间使用的 page/Atlas 状态，
   在 apply 时没有与当前 Core state 做强一致比对。
   只要所选 Cell 仍存在，陈旧语义关系仍可能写入。

5. Common Recall 仍需一个独立隐藏 Reader 子代理：
   真实样本约 19.7～33.7 秒。
   用户主代理随后还要再生成回答。

6. 单入口 Core Recall 在 9 事实簇中每次注入 6～7 条相关簇事实。
   它证明可达，但尚未证明规模增长后的几何选择性。
```

本修订确立：

> **不要让 LLM 计算字符位置和数组索引。LLM 只输出自然语言 Evidence 引用；Access 负责确定性定位和持久 provenance。Cartographer 计划必须绑定当前 Atlas/Core 状态，陈旧即零写入重算。读取时由正在回答用户的主代理直接使用 Nollm 几何工具，不再先启动一个独立 Reader LLM；一个入口返回小型、按几何得分排序的 Locality，主代理可在同一 run 中请求有界扩展。**

---

## 1. 能力重新定性

`a4d8e31` 可记录为：

```text
CONTEXTUAL_WRITER_SHARED_RETRIEVAL_GROWTH_CHECKPOINT_AT_a4d8e31
```

它证明：

```text
上下文命题形成；
Entry Query 引导关系生长；
多方向单入口可达；
operation-local Atlas entry identity；
独立 seed 与 related growth 可以共存；
Core 中仍为 one Statement / one Atom / one Handle / one Cell。
```

它没有证明：

```text
活动 Writer 无法绕过 Rev4；
命题 Evidence 可从 canonical state 精确重建；
Writer 在普通 Capture 上低重试稳定工作；
Cartography apply 只使用新鲜字段；
用户查询无需额外隐藏子代理；
几何 Locality 在 50～100 事实规模具有选择性；
冻结 Evidence 对 raw Writer/Cartographer events 完整绑定。
```

---

## 2. LLM 原生 Evidence Anchor

### 2.1 正确边界

LLM 适合：

```text
理解一句话表达了什么；
选择哪些原文片段支撑命题；
判断“那天”“之后”“那里”指向什么；
提出 Direct Query 与 Entry Query。
```

LLM 不适合：

```text
计算 UTF-8/Unicode 字符偏移；
计算 Python slice；
维护 span 数组下标；
手工保证 basis_span_indexes 与 capture IDs 对应。
```

因此活动 Writer 不得再输出：

```text
start；
end；
basis_span_indexes。
```

### 2.2 EvidenceQuoteRef

活动 Writer 输出 operation-local 引用：

```text
evidence_ref_id；
capture_id；
role；
quote_utf8；
occurrence_hint（可选）；
left_context_utf8（可选，短）；
right_context_utf8（可选，短）。
```

Access 确定性处理：

```text
1. 读取指定 Capture 和 role 原文；
2. 精确寻找 quote_utf8；
3. 唯一命中：
   生成 canonical start/end；
4. 多次命中：
   使用 occurrence 或左右文消歧；
5. 仍歧义：
   返回 evidence_quote_ambiguous；
6. 零命中：
   返回 evidence_quote_not_found。
```

Access 只做精确字符串定位，不理解语义。

### 2.3 Unicode 和规范化

Canonical Evidence bytes 以 Capture 中保存的 UTF-8 原文为准。

不得在定位前静默进行：

```text
大小写折叠；
全角半角替换；
Unicode NFC/NFKC 改写；
空白压缩；
标点替换；
翻译；
摘要。
```

如 Host 在 Capture 前已经进行明确、版本化的规范化：

```text
Capture metadata 必须记录；
quote resolver 按同一版本处理。
```

### 2.4 ResolvedReference

每个 resolved reference 使用：

```text
reference_id；
kind：
  temporal | coreference | location | event | other；
normalized_value；
basis_evidence_ref_ids；
timestamp_basis_capture_ids（可选）。
```

禁止：

```text
basis_span_indexes。
```

机械验证：

```text
所有 Evidence ref 存在；
每个 ref 的 capture_id/role/quote 可定位；
timestamp basis 指向真实 Capture 时间；
absolute date 必须有 quote basis 或 timestamp basis；
不同 scope/workspace 的 Capture 不可引用；
未来 Capture 不可引用；
同一 basis ref 不可对应多个不一致 normalized value。
```

Access 不判断 normalized value 的开放式语义正确性，只验证它拥有声明的 Evidence 基础。

### 2.5 Statement Provenance

每条 durable Statement 必须有 canonical provenance：

```text
statement_id；
writer_schema_version；
source_capture_ids；
context_capture_ids；
exact evidence spans；
resolved references；
content digest；
created_at；
revision predecessor（若有）。
```

Codex 可选择：

```text
扩展 Statement schema；
Access-owned StatementProvenance sidecar；
按 statement_id 命名的 canonical provenance document。
```

必须成立：

```text
重开后可读取；
不依赖 debug trace；
revision 新旧 Statement 各有自己的 provenance；
不进入 Core；
不用于 query/Topic/Entry 路由；
删除 provenance 后不能继续声称 Evidence chain 完整。
```

旧 Statement：

```text
允许 provenance_version=legacy；
只记录可验证的粗粒度 Capture refs；
不得补造 exact spans。
```

---

## 3. 活动 Writer 与 Legacy 隔离

### 3.1 当前漏洞

活动 `parse_proposition_writer_result` 同时接受：

```text
contextual v2；
legacy v1。
```

Legacy v1 不要求：

```text
resolved references；
绝对日期 basis；
Direct/Entry Query 区分；
context provenance。
```

因此可以绕过 Rev4。

### 3.2 新合同

生产 Host 只接受最新活动 schema，例如：

```text
nollm_openclaw_contextual_proposition_writer_v3
```

Legacy 解析只允许：

```text
offline migration；
historical fixture；
显式 migration command。
```

普通 Provider response 不能自动降级成 legacy。

### 3.3 Migration

Migration 结果必须明确：

```text
migrated_from_version；
provenance_precision=coarse|exact；
无法验证的字段为空或 unknown；
不得将 legacy 推测成 Rev5 exact provenance。
```

---

## 4. Cartography Plan 新鲜度

### 4.1 为什么陈旧

Writer/Cartographer Provider 调用可能持续：

```text
20～100 秒或更长。
```

期间字段可能发生：

```text
新的 Statement Admission；
Cell occupancy 改变；
Handle revision；
forget；
Core reopen/import；
Atlas derived state 变化。
```

即使 selected Cell 仍存在：

```text
该 Locality 的语义背景可能已经改变。
```

### 4.2 CartographyPlanToken

Cartographer 结果必须绑定：

```text
request_id；
writer_proposition_digest；
atlas_fingerprint；
page_fingerprint；
core_state_sha256；
selected region_id；
selected entry identities；
selected Cell stable keys；
visible current Handle digests；
cartographer schema/prompt version。
```

它不是安全 token，只是确定性状态身份。

### 4.3 Apply Gate

Access apply 前重新读取：

```text
Core state SHA；
Atlas fingerprint；
selected Cell occupancy；
相关 current Handles/Statements；
existing Handle（reuse/revision）。
```

允许写入的最低条件：

```text
token 与当前状态一致；
selected entry 仍属于同一 region；
relation groups 仍 realized；
visible Handle digests 未变；
Writer proposition digest 未变。
```

不一致：

```text
stale_cartography_plan；
zero write；
worker 重新构建 Atlas/Cartography；
不得仅因 selected Cell 仍存在而继续。
```

### 4.4 Narrow freshness

Codex 可以设计更窄的受影响范围指纹，避免字段中完全无关的变化使所有计划失效。

但必须通过：

```text
selected Locality 变化 → 拒绝；
existing Handle 变化 → 拒绝；
无关远 Cell 变化 → 明确允许或拒绝，并有测试/文档；
状态身份不能依赖语义索引。
```

---

## 5. 主代理原生几何 Recall

### 5.1 当前调用拓扑

当前用户查询：

```text
query
→ 独立隐藏 Reader child-agent
→ entry
→ Core Recall
→ hidden context
→ main agent 生成回答。
```

Reader child-agent 实测增加：

```text
约 20～34 秒。
```

用户主代理本身已经是 LLM，重复调用另一个 LLM 完成入口选择没有必要。

### 5.2 新拓扑

```text
query
→ main agent 当前 run 获得内部 Nollm 几何工具
→ main agent 查看 Prompt-bounded Atlas candidates
→ 选择一个 operation-local entry 或 NONE
→ Access/Core 返回 bounded Locality
→ main agent 在同一 run 中自然回答。
```

Common path：

```text
独立 hidden child-agent calls = 0。
```

### 5.3 工具合同

工具可以由 Codex 按 OpenClaw 实际能力实现，最低动作：

```text
nollm_memory_surface：
  返回 top-level Prompt-bounded Atlas page；

nollm_memory_open_region：
  在同一 operation 展开一个 region；

nollm_memory_recall：
  选择一个 entry，返回默认 bounded Locality；

nollm_memory_expand：
  对同一个 entry 扩大有界预算；

nollm_memory_none：
  结束不注入。
```

可以合并为一个多动作工具。

不可协商：

```text
工具只对主代理内部可见；
用户不看到内部 JSON/地址；
主代理不能提交任意 q/r；
entry ID operation-local；
一次 Recall 只有一个最终 entry；
query→entry 不持久化；
工具失败开放；
Pending Capture context 可同时存在。
```

### 5.4 小场 fast path

如果 top-level Atlas 页面在 Prompt 预算内：

```text
一次工具结果展示全部 region/support entries；
main agent 直接 select_entry。
```

### 5.5 大场 progressive path

如果需要下降：

```text
main agent 在同一个 run 中调用 open_region；
没有新的模型 session；
最多固定工具调用次数；
超限返回 overflow/defer，而不是 stable-key 抽样。
```

### 5.6 旧 Reader

独立 Reader child-agent：

```text
退出 active distribution；
保留为 Lab A/B baseline 或 Legacy Reference；
不得在用户默认链路被调用。
```

---

## 6. Locality 选择性与有界扩展

### 6.1 当前现象

在 9 条事实的小簇中：

```text
东京 query：返回 7 条；
会议 query：返回 6 条；
天气 query：返回 6 条；
target-hidden：返回 7 条。
```

这证明目标可达，但 Locality 过宽。

### 6.2 默认 Locality

Access 基于 Core 返回的稳定几何得分和 path 排序，默认返回：

```text
entry direct items；
最优 geometry-ranked items；
默认 statement_count 3～5；
默认 chars <= 3000；
has_more；
budget_exhausted；
next_budget_options；
每条 Handle/path/score。
```

禁止：

```text
Python 关键词过滤；
LLM 预筛；
Topic/Entity；
query relevance score；
第二个语义筛选模型。
```

### 6.3 Expand

主代理需要更多时：

```text
保持同一个 entry；
扩大 max_steps / max_results / chars；
最多固定扩展次数；
返回新增 items 或完整新窗口；
仍然 single-entry。
```

不得：

```text
换成第二入口；
合并多入口；
持久化 query path。
```

### 6.4 Selectivity 不是永久重要性

几何默认窗口小，只表示：

```text
先提供离入口最近的局部现场。
```

不表示：

```text
远处事实不重要；
未返回事实不值得记；
几何分数等于事实相关性或真值。
```

主代理可按需扩展。

---

## 7. 规模验证

### 7.1 字段

建立：

```text
60～100 durable Statements；
6～10 Localities；
至少 20 个 unrelated independent seeds；
至少一个 10+ facts dense Locality；
至少三条有长度的 relation arms；
多个 Capture sessions；
Gateway restart。
```

真实 Provider-backed 子集必须存在；可使用 deterministic fixture 增加压力，但要分开报告。

### 7.2 查询

至少：

```text
20 relevant；
10 relation-entry target-hidden；
10 dense hidden-target；
10 NONE/unrelated；
5 expansion-required；
2 cold restart。
```

### 7.3 指标

当前任务实验 Gate：

```text
target reach >= 90%；
unrelated leakage <= 1 item/query；
default injected statements p95 <= 5；
default injected chars p95 <= 3000；
single-entry rate = 100%；
child-agent calls = 0；
expanded target reach；
NONE false injection；
query→visible latency。
```

这些是当前环境实验阈值，不是永久 SLA。

### 7.4 负对照

必须比较：

```text
旧 hidden Reader；
新 main-agent tool；
默认 Locality；
expanded Locality；
target Cell direct control；
relation-entry path；
unrelated entry。
```

---

## 8. Evidence 与报告真值

### 8.1 当前提交绑定

正确记录：

```text
Rev4 code/evidence commit：
75383c6（或报告中实际固定的证据提交）；

最终文档/绑定 commit：
a4d8e31；

Git-blob verifier passes at：
a4d8e31。
```

不得声称 verifier 在未包含 completion binding 的较早提交通过。

### 8.2 Raw event binding

冻结 Summary 必须包含：

```text
raw events path；
line count；
bytes；
SHA；
record type counts；
Provider/model；
Writer attempts；
validation failure types；
accepted attempt IDs；
Cartographer turns；
main-agent tool events。
```

### 8.3 Live 与 Frozen

继续遵守：

```text
run-scoped mutable live path；
freeze 前停止/旋转 writer；
frozen artifact 不再 append；
Git blob verifier。
```

---

## 9. 模块所有权

### Access

新增/拥有：

```text
Evidence quote resolver；
canonical Statement provenance；
Cartography freshness validation；
bounded Locality projection；
same-entry expansion。
```

不拥有：

```text
语义判断；
query relevance；
Topic/Entity；
Provider。
```

### OpenClaw

拥有：

```text
Writer v3 Prompt/Wire；
main-agent internal geometry tool；
Host tool lifecycle；
legacy Reader active path removal；
visible latency evidence。
```

### Lab

拥有：

```text
legacy bypass negative；
quote resolver fixtures；
stale plan race；
main-agent vs child-agent A/B；
scale/selectivity；
Evidence freeze verifier。
```

### Distributions

只声明：

```text
active Writer schema；
main-agent tool version；
default Locality budgets；
legacy path disabled；
plugin compatibility。
```

Core 不变。

---

## 10. 禁止路线

```text
LLM 手算 offset/index；
活动 legacy 自动转换；
Cartographer 陈旧计划继续写；
独立 hidden Reader child-agent；
Python 语义过滤；
query→entry cache；
Topic/Entity；
vector/graph/embedding；
multi-entry Recall；
multi-cell；
多物理层；
Stitch；
Provider 更换；
为了选择性修改 Core 物理参数。
```

---

## 11. 最终架构概括

```text
Writer 用自然语言引用 Evidence，
Access 把引用编译成精确 span。

Cartographer 选择几何时，
其计划绑定真实字段状态，
字段变化就重新思考。

用户查询时，
不再启动一个 Reader LLM 去帮助另一个 LLM。
正在回答用户的主代理，
直接操作 Nollm 的有界几何工具选择一个入口。

Core 返回一个小而有序的 Locality；
需要更多时，同一主代理、同一入口有界扩展。
```

> **教会 LLM 使用 LLM 的最终形态，不是让模型彼此层层转述，而是让 Writer 负责命题，Cartographer 在后台整理几何，用户面前的主模型直接操作几何记忆。**
