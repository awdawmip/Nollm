# Nollm AOLD：单一活动内容中立管线、Tool Evidence、逐 Capture Continuation 与 Provider Live 任务书

**任务文件名**：`NOLLM_A_O_L_D_SINGLE_ACTIVE_CONTENT_NEUTRAL_PIPELINE_TOOL_EVIDENCE_PER_CAPTURE_CONTINUATION_PROVIDER_LIVE_TASK_20260724.md`  
**日期**：2026-07-24  
**受影响模块**：`A=Access | O=OpenClaw | L=Lab | D=Distributions`  
**输入 Bundle**：`nollm_aold_content_neutral_memory_20260723_a6551fe.bundle`  
**输入 SHA-256**：`50d7602dd742acb4c79fd7b4217382b3026eecb45697f1f01b034321e3d63e63`  
**输入 HEAD**：`a6551feb89322826f4faa3b0c98c8b8c6152d5d4`  
**输入分支**：`codex/aold-content-neutral-formation-recoverable-absorption-routing`  
**建议分支**：`codex/aold-single-content-neutral-tool-evidence-capture-continuation`  
**交付**：Windows-first；内部Gate；全部进展commit；clean tree；仓库外单一完整历史Bundle  
**非目标**：Core修改、multi-cell、多层Placement、Stitch、Topic/Entity、vector/graph、multi-entry、Provider更换、PB、正式发布

---

# 0. 任务推进向量

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +15% |
HISTORY 0% | AUDIT 0% | OPENCLAW +15% |
LAB +15% | DISTRIBUTIONS +5%

主方向：
关闭活动Legacy内容过滤旁路；
建立immutable Tool Evidence；
将batch continuation改为逐Capture完整覆盖；
修正zero-delta终态和诊断；
建立全活动import/action Gate；
运行真实Provider内容多样性与continuation Live。

范围变化：
Capture Evidence合同增加tool items；
Core与几何合同不变。
```

---

# 1. 任务前全部模块完成度

| 模块 | 生命周期 | 当前完成度 | 置信度 | 主要缺口 | 影响 |
|---|---|---:|---|---|---|
| CORE | CAPABILITY_VALIDATED | 93% | 中高 | 本任务回归 | 否 |
| SNAPSHOT | IMPLEMENTED | 50% | 中高 | 增量 | 否 |
| TRACE | IMPLEMENTED | 40% | 中 | metrics | 否 |
| ACCESS | IMPLEMENTED | 91% | 中 | Tool provenance、逐Capture状态 | 是 |
| HISTORY | PROPOSED | 10% | 低 | 暂停 | 否 |
| AUDIT | PROPOSED | 10% | 低 | 暂停 | 否 |
| OPENCLAW | IMPLEMENTED | 90% | 中 | Legacy旁路、Tool Capture、Live | 是 |
| LAB | IMPLEMENTED | 86% | 中 | 静态Gate漏检、无Provider | 是 |
| DISTRIBUTIONS | IMPLEMENTED | 92% | 中 | 活动入口/Profile真值 | 是 |

---

# 2. 任务后目标完成度

| 模块 | 前 | 目标 | 交付 |
|---|---:|---:|---|
| CORE | 93 | 93 | 回归 |
| SNAPSHOT | 50 | 50 | 回归 |
| TRACE | 40 | 40 | 回归 |
| ACCESS | 91 | 97 | Tool provenance、逐Capture continuation |
| HISTORY | 10 | 10 | 无 |
| AUDIT | 10 | 10 | 无 |
| OPENCLAW | 90 | 97 | 单一管线、Tool Evidence、Provider Live |
| LAB | 86 | 96 | 全活动Gate、真实多样性 |
| DISTRIBUTIONS | 92 | 96 | Profile/入口一致 |

不写永久100%。

---

# 3. Gate 0：状态与反例

必须固化反例：

```text
默认/缺workspace配置启用legacyFormation；
旧Prompt含tool noise/no_memory/question defer；
静态scanner漏检；
multi-Capture prior IDs污染；
final zero覆盖先前admission；
tool标签无tool bytes；
diagnose旧状态；
Provider禁令不存在。
```

更新：

```text
AGENTS；
ACTIVE_PROJECT；
STATUS；
Ledger；
Rev6.1 architecture；
审核报告。
```

---

# 4. Gate A：单一活动语义入口

## 4.1 删除自动fallback

正常register：

```text
CaptureStore不存在
→ 不启动legacy launch；
→ Capture/absorption配置错误诊断；
→ 若无法Capture则插件记忆功能fail-closed。
```

不得在message_sent/agent_end调用旧launch。

## 4.2 Bridge allowlist

活动插件仅可调用：

```text
read_memory_evaluation_fingerprint；
Writer v4+；
Cartographer v2+；
apply；
main-agent progressive Recall；
revision confirmation；
必要的Access mechanical actions。
```

以下只能offline migration：

```text
build_dream_prompt；
parse_dream_result；
Dream Sculptor；
旧Formation selector；
旧placement/reader。
```

建议：

```text
独立legacy_bridge.py；
或action必须携带offline_migration=true，
且活动TS从不生成。
```

## 4.3 历史资产分类

逐项登记：

```text
formation-loop/adapter.py；
dream_adapter.py；
sculptor.py；
nollm-memory-provider；
nollm-memory-companion；
grf-adapter。
```

活动import graph到这些资产必须为0，除显式migration模块。

Gate A PASS：

```text
任何允许配置都不会进入旧内容过滤Prompt；
缺配置只retry/diagnose；
活动action集合唯一。
```

---

# 5. Gate B：Immutable Tool Evidence

## 5.1 Host Hook

从真实OpenClaw tool事件记录：

```text
tool_call_id；
tool name；
exact result bytes/canonical JSON；
失败/成功；
scope/workspace/session/run；
时间；
visibility。
```

不得记录隐藏推理，只记录Host实际工具输入输出合同允许的结果。

## 5.2 文件

建议：

```text
captureRoot/tool-evidence/<tool_evidence_id>.json
```

要求：

```text
wx/atomic publish；
fsync；
content hash；
idempotent replay；
conflict拒绝；
scope隔离；
corrupt diagnostic。
```

## 5.3 Writer wire

Evidence ref role：

```text
user | assistant | tool。
```

Tool quote resolver按canonical tool result定位。

## 5.4 不分类

测试内容包括：

```text
密码形态；
医疗；
错误日志；
长JSON；
空结果；
二进制不可表示结果的明确编码。
```

同一合同，不做关键词拒绝或遮蔽。

Gate B PASS：

```text
Tool Statement可reopen回exact Tool Evidence；
仅有tool action标签但无bytes时不得伪造exact tool origin。
```

---

# 6. Gate C：逐 Capture Work State

## 6.1 数据结构

引入：

```text
CaptureAbsorptionProgress v1
或等价append-only state。
```

每Capture保存：

```text
own statement IDs；
own source windows；
own covered/uncovered ranges；
own continuation pass；
own prior proposition digests；
own evaluation identity。
```

## 6.2 Batch

batch Provider调用可共享，但返回后：

```text
按source_capture_ids拆分；
每Capture独立状态；
不把union IDs写回所有Capture；
不共享第一个continuation。
```

## 6.3 测试

至少：

```text
A产生Statement，B zero；
A complete，B continue；
A retry，B admitted；
A 20 propositions，B 1；
restart；
batch重排；
partial Admission；
revision/reuse。
```

硬Gate：

```text
Capture B statement_ids不含A；
coverage只含自己；
evaluation hash可按自己重算；
各自状态独立。
```

---

# 7. Gate D：Continuation 完整性

## 7.1 prior proposition context

下一pass输入：

```text
prior Statement ID；
content digest；
必要时content；
source ranges；
pass。
```

不得仅给opaque IDs。

## 7.2 终态

规则：

```text
从未产生delta + 全覆盖 + zero
→ evaluated_no_new_propositions；

已产生Statement + 全覆盖 + zero
→ completed_with_statements/admitted等成功态；

仍有source/命题
→ incomplete_continuation。
```

## 7.3 Pass预算

每worker invocation最多N个连续pass；达到后：

```text
持久cursor；
有界退避；
下一次继续；
不清空prior；
不静默完成。
```

## 7.4 Provider测试

至少：

```text
20+命题；
跨3 pass；
真实Provider；
重复命题检测；
restart；
timeout；
format repair；
最终全覆盖。
```

---

# 8. Gate E：Zero-delta与诊断

## 8.1 evaluation

每Capture独立：

```text
source coverage；
context；
Writer版本；
provenance directive；
memory observation。
```

## 8.2 re-evaluate

提供明确命令或Host管理动作：

```text
requestReevaluation(capture_id, reason)。
```

diagnose显示可用性。

## 8.3 diagnose.ps1

更新全部新状态、continuation和legacy count。

不得再将no_memory/deferred作为活动terminal。

---

# 9. Gate F：全活动内容过滤审计

建立真正的Gate：

```text
从插件register入口构建TS/Python action/import reachability；
列出所有活动Prompt builders；
活动路径不得到达Legacy过滤函数；
扫描条件分支、Prompt和配置；
区分内容中立正面说明与条件拒绝逻辑；
检查历史资产public_api=none；
检查export-only redaction不被Formation import。
```

不得只扫描一个文件的if行。

Evidence必须列：

```text
active semantic entrypoints；
active prompts；
legacy reachable count；
content-category branch count；
source-role gate count；
tool exact Evidence support；
diagnose status set。
```

---

# 10. Gate G：真实 Provider 内容多样性 Live

## 10.1 环境

明确：

```text
active-memory；
statement-store；
Capture/Tool Evidence workspace；
真实Provider/model；
run-scoped mutable Evidence。
```

当前权威不禁止Live。

## 10.2 场景

至少：

```text
24自然turn；
内容类别覆盖架构列出的全部；
assistant推论；
recalled-derived推论；
tool success/failure；
长Capture；
20命题Capture；
多Capture batch；
reuse/revision/zero/retry。
```

## 10.3 指标

```text
Provider calls；
first attempt；
format/semantic retry；
各内容类别不是资格分类，仅作为测试覆盖标签；
durable Statements；
tool provenance；
per-Capture coverage；
continuation passes；
duplicate/orphan；
visible answer；
restart。
```

测试标签只用于Lab覆盖统计，不进入生产判断。

---

# 11. Gate H：Routing与主代理回归

保持统一preview：

```text
无category redaction；
同一字符预算；
字段完整；
Prompt有界；
surface/open_region/recall/expand/none；
one final entry。
```

Provider主代理至少验证：

```text
短凭证形态Statement；
医疗；
天气；
工具错误；
普通事实；
均可通过同一路由读取。
```

不检查“是否敏感”，只检查同一合同和scope隔离。

---

# 12. Gate I：回归、Evidence与交付

分组执行：

```text
Core/Snapshot/Trace；
Access；
OpenClaw Python；
OpenClaw Node；
Lab；
M0/Manifest/boundary。
```

主Evidence：

```text
validation/aold_single_content_neutral_pipeline_20260724.jsonl
validation/aold_single_content_neutral_pipeline_summary_20260724.json
```

主报告：

```text
docs/project/AOLD_SINGLE_CONTENT_NEUTRAL_PIPELINE_REPORT.md
```

Freeze后从Git blob复算。

最终记录：

```text
implementation HEAD；
evidence HEAD；
delivery HEAD；
Bundle HEAD/SHA。
```

---

# 13. 完成Gate

全部满足才允许：

```text
SINGLE_ACTIVE_CONTENT_NEUTRAL_MEMORY_PIPELINE_VALIDATED_AT_<HEAD>
```

必须同时有：

```text
legacy active reachability=0；
content-category production branch=0；
source-role admission gate=0；
tool exact Evidence；
per-Capture continuation isolation；
20+ proposition Provider continuation；
zero terminal正确；
diagnose正确；
Provider Live；
routing/main-agent；
Core unchanged；
tests/Manifest/boundary；
clean Bundle。
```

否则：

```text
AOLD_SINGLE_CONTENT_NEUTRAL_PIPELINE_IN_PROGRESS_AT_<HEAD>
```

---

# 14. 建议提交

```text
checkpoint(aold): record remaining content-neutral bypasses
fix(openclaw): remove automatic legacy Formation fallback
feat(openclaw): persist immutable tool Evidence
fix(openclaw): isolate continuation state per Capture
fix(aold): preserve successful terminal state after continuation zero
fix(openclaw): update content-neutral diagnostics
test(lab): validate full active semantic reachability
test(aold): run Provider content-neutral continuation Live
docs(aold): record single active pipeline capability
```

---

# 15. Bundle

建议：

```text
nollm_aold_single_content_neutral_pipeline_20260724_<shorthead>.bundle
```
