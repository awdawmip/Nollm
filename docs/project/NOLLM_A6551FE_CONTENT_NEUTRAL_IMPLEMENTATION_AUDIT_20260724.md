# `a6551fe` 内容中立实现审核报告

**日期**：2026-07-24  
**Bundle**：`nollm_aold_content_neutral_memory_20260723_a6551fe.bundle`  
**Bundle SHA-256**：`50d7602dd742acb4c79fd7b4217382b3026eecb45697f1f01b034321e3d63e63`  
**HEAD**：`a6551feb89322826f4faa3b0c98c8b8c6152d5d4`  
**Branch**：`codex/aold-content-neutral-formation-recoverable-absorption-routing`  
**Working tree**：clean  
**Exact HEAD tag**：无

---

# 1. 总体结论

方向正确，但只能定性为：

```text
CONTENT_NEUTRAL_WRITER_AND_CONTINUATION_PROTOTYPE_CHECKPOINT_AT_a6551fe
```

已经成立：

```text
内容中立最高原则；
Writer v4主路径；
source role不作资格门禁；
zero/retry/continuation新状态；
oversize source windows；
routing不做敏感分类；
历史memory-provider fail-closed；
Core无变更。
```

尚未成立：

```text
活动运行时只有一条内容中立语义管线；
Tool输出拥有exact canonical Evidence；
多Capture continuation彼此隔离；
Provider内容多样性；
正式Live和可见回答；
所有历史过滤资产已隔离。
```

---

# 2. 基础核验

```text
Bundle verify：通过；
完整历史：是；
输入后提交：3；
diff：+8224 / -1290；
tracked/manifest：2077 / 2077；
unclassified：0；
boundary：0 production violations / 0 cycles；
Evidence verifier：PASS；
Core/Snapshot/Trace：98 passed；
选定Access/OpenClaw/Lab：50 passed；
完整Access套件在审核环境超过10分钟，未独立跑完；
Node依赖未随Bundle提供，未独立重建。
```

Evidence：

```text
JSONL：
5 lines；
3023 bytes；
SHA-256 c1b5146428f9c52a1cf3576768d80e8be5788a7efe200e57d346b3ad3b4d9297；

Summary：
454 bytes；
SHA-256 2afe69ff1ce4026d2f16d17452067b45146b70fbe49b23d1e445287bdc1f4091。
```

---

# 3. P0发现

## P0-1 活动Legacy语义旁路仍存在

`registerDreamAgent()`：

```text
captureStore不存在
→ legacyFormationEnabled=true
→ message_sent/agent_end启动旧launch。
```

插件schema没有强制memory/capture workspace，默认配置可进入该分支。

旧Prompt仍包含：

```text
tool noise；
no_memory；
generic assistant content不作为memory；
only question/instruction defer；
max_statement_chars/max_total_chars硬限制。
```

此外bridge仍公开旧：

```text
build_dream_prompt；
parse_dream_result；
build_dream_sculptor_prompt；
apply_dream_sculptor_result；
旧Formation selector。
```

因此“活动资格分支=0”不成立。

## P0-2 静态Gate漏检

当前Lab只扫描：

```text
cartographer.py中以if/elif开头且包含若干英文词的行。
```

它没有扫描：

```text
index.ts fallback；
dream_adapter.py Prompt；
sculptor.py Prompt；
adapter.py question/instruction规则；
bridge action allowlist；
nollm-memory-companion。
```

Evidence中的：

```text
active_content_eligibility_branch_count=0
```

只能说明一个文件的少数条件行没有对应词，不能证明活动系统无过滤旁路。

## P0-3 多Capture continuation状态互相污染

活动代码将：

```text
所有record的prior_statement_ids取并集；
第一个continuation作为全batch cursor；
全batch source coverage写回每个record。
```

结果可能是：

```text
Capture B state带有Capture A Statement ID；
Capture B覆盖范围包含A；
multi-Capture zero delta因单Capture重算hash而反复re-evaluate；
不同Capture无法独立完成/继续。
```

## P0-4 final zero会覆盖此前成功语义

若前几pass已Admission，最后pass返回：

```text
zero_new_propositions
```

当前代码最终写：

```text
evaluated_no_new_propositions
```

而不是“已有Statements完成”。

这会错误描述Capture终态，并可能触发后续重复评估。

## P0-5 Tool内容中立只有标签，没有Evidence

Writer Evidence role仍只有：

```text
user；
assistant。
```

`tool` origin来自：

```text
memory_tool_actions存在。
```

系统没有保存被引用的tool result exact bytes，也无法生成tool span。

因此当前只能声称：

```text
tool-associated provenance
```

不能声称：

```text
tool-originated canonical Evidence同等Admission。
```

## P0-6 Provider Gate被错误跳过

报告称活动仓库禁止：

```text
Live OpenClaw / model calls。
```

但：

```text
AGENTS要求真实Provider；
任务Gate G明确要求；
当前活动权威没有禁令。
```

Gate G未执行属于任务未完成，不是架构阻断。

---

# 4. P1发现

## P1-1 Diagnose仍使用旧终态

`diagnose.ps1`仍把：

```text
admitted / no_memory / deferred
```

作为terminal，且只统计旧no_memory/deferred。

它不能正确显示：

```text
zero delta；
retryable defer；
continuation；
structural invalid；
reuse/revision。
```

## P1-2 其他历史过滤资产未完整隔离

`nollm-memory-provider`已标 invalid，但以下仍存在内容过滤语义：

```text
nollm-memory-companion；
formation-loop adapter.py；
dream_adapter.py；
sculptor.py；
部分旧bridge actions。
```

有些为MIGRATION_ASSET，有些仍在ACTIVE包内。

## P1-3 continuation Provider行为未验证

20命题证据由fixture直接构造：

```text
8 + 8 + 4。
```

没有验证真实LLM：

```text
能否避免重复；
能否正确声明remaining；
能否在restart后继续；
能否在多Capture batch独立结束。
```

## P1-4 交付HEAD未写入活动状态

状态绑定：

```text
implementation commit 6cbaeb7
```

最终Bundle HEAD：

```text
a6551fe
```

可以分别记录implementation/evidence/delivery，但当前状态没有完整绑定最终HEAD，也没有精确tag。

---

# 5. 实际推进建议

```text
CORE 0% | SNAPSHOT 0% | TRACE 0% | ACCESS +7% |
HISTORY 0% | AUDIT 0% | OPENCLAW +8% |
LAB +5% | DISTRIBUTIONS +3%
```

建议完成度：

| 模块 | 完成度 |
|---|---:|
| CORE | 93% |
| SNAPSHOT | 50% |
| TRACE | 40% |
| ACCESS | 91% |
| HISTORY | 10% |
| AUDIT | 10% |
| OPENCLAW | 90% |
| LAB | 86% |
| DISTRIBUTIONS | 92% |

---

# 6. 审核结论

内容中立原则没有被推翻；主要Writer v4也不是内容分类器。

真正需要下一步修复的是：

```text
让内容中立成为唯一活动入口；
让batch不污染Capture身份；
让tool有真实Evidence；
让Provider真正验证。
```
