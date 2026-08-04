# Nollm 路线书 V3.13 Rev1：Direct Encounter Activation 与延后神经适配

**版本**：V3.13 Rev1
**日期**：2026-08-04
**职责**：规定当前真实闭环、实施顺序、GitHub 连续交付和未来神经研究触发条件
**配套架构**：`NOLLM_ARCHITECTURE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_DEFERRED_NEURAL_ADAPTER_20260804.md`
**当前任务**：`NOLLM_A_O_L_D_DIRECT_ENCOUNTER_ACTIVATION_PROVIDER_LIVE_GITHUB_EXECUTION_TASK_20260804.md`

---

# 0. 一句话路线

```text
先让 Field Encounter 的结果直接成为当前 run 的精确文本激活，
真实证明写入、召回、注入和回答；
只有文本模式成为经验证瓶颈后，才研究 Prefix/KV/Attention。
```

---

# 1. 路线硬约束

```text
1. V3.12 Unified Field Encounter 继续作为唯一读写操作；
2. 一次 Traversal 一个 Entry；
3. Direct Activation 只读 current Statement；
4. 不新增 Packet、正式 Adapter 模块、epoch 或派生缓存；
5. 不增加额外 Provider 调用；
6. 隐藏文本仅活在当前 run；
7. Provider 失败开放；
8. 每个大 Gate commit 并 push；
9. 环境受限项必须留下恢复命令；
10. 只有 REMOVABLE 可删除；
11. AGENTS.md 保持严格 0 bytes；
12. 完整历史 Git Bundle 交付。
```

---

# 2. 当前阶段

## R0：活动权威

```text
唯一 Active architecture；
唯一 Current task；
六类 HEAD 分离；
生命周期计划非空；
通用 Boundary。
```

## R1：修改前 baseline

```text
V3.12 query/write/mixed；
调用数；
时延；
重启；
并发；
真实阻断。
```

## R2：Direct Activation

```text
FieldEncounterResult
→ current Statement
→ 一个 exact-text renderer
→ current run hidden context。
```

## R3：离线闭合

```text
预算；
Unicode；
失效 ID；
NONE；
顺序；
失败开放；
无持久状态；
无新抽象。
```

## R4：真实 Live

```text
query-only；
write-only；
mixed；
single-entry；
one Writer session；
no Reader/Cartographer child；
读取/写入 p50/p95/max。
```

## R5：有限退出

```text
只删除真实 Live 覆盖且 REMOVABLE 的重复 renderer 或旧接线；
不扩大到全 Legacy 清理。
```

## R6：主线交付

```text
完整回归；
状态回填；
checkpoint push；
PR/main；
短期分支清理；
完整 Bundle。
```

---

# 3. GitHub 连续交付路线

```text
Gate 0 建短期分支
→ Gate 1 authority checkpoint push
→ Gate 3 code checkpoint push
→ Gate 4 offline checkpoint push
→ Gate 5 Live evidence checkpoint push
→ Gate 6 cleanup checkpoint push
→ Gate 8 report checkpoint push
→ PR / fast-forward main
→ 删除已合并短期分支
→ Git Bundle。
```

GitHub 不可用：

```text
本地 commit 继续；
生成 Bundle；
保存失败证据；
状态保持 IN_PROGRESS；
下一环境从 Bundle 恢复后继续 push。
```

---

# 4. 未来神经研究触发条件

只有同时满足：

```text
Text Direct Activation 已真实稳定；
Text 的 Token/延迟成为主要瓶颈；
存在可控制自托管推理引擎；
出现第二种真实激活消费者；
Lab 原型证明质量不下降且有净收益；
撤销残留可以验证。
```

才启动新任务研究：

```text
Soft Prefix
Prefix KV
Attention Bias
Memory Encoder
```

这些研究不得反向进入当前任务。

---

# 5. 阶段完成判定

当前路线完成只意味着：

```text
Direct Encounter Activation 在指定 HEAD 和环境被验证；
读写时延可复算；
GitHub 主线有真实进展；
现有文本路径收敛；
未来研究仍暂停。
```

不意味着：

```text
Nollm 封版；
所有 Legacy 删除；
神经 Adapter 可用；
多 Provider 通过；
PB 规模通过。
```
