# Nollm 路线书 V3.8：平移协变 Coverage、历史数学复用与单入口跨层召回

**版本**：V3.8
**日期**：2026-07-14
**当前输入**：`ac8ebaa44cda35e1d2f73e0bfc95055bae425a86`
**输入 Bundle SHA-256**：`4dd31eafe7e0a33ec9116a14a18fc9fb44f01c16d319dbb56fcc31e902a8bb64`
**性质**：V3.7 数学 Gate 失败后的活动纠偏路线

# 0. 当前定性

`ac8ebaa4` 保留为：

```text
ROTATED_PROFILE_ADDRESS_SEPARATION_AND_SINGLE_ENTRY_WIRE_IN_PROGRESS_CHECKPOINT
```

它证明：

```text
硬参数进入 Profile；
Physical/Surface 地址分离；
Order 0..8 API；
单入口 Wire；
无 Cursor；
真实 OpenClaw 集成。
```

它没有证明：

```text
平移协变 Coverage；
全平面 candidate completeness；
真实 overlap 权重；
真实 Surface 聚合；
跨层 Coverage Recall。
```

# 1. 本次执行效果差的根因

## 1.1 未先盘点历史资产

任务书没有把历史 DG1/GVR1/GRA1/GRC1/GKD1/GPR1 代码列为必读和复用输入。

结果：

```text
已有 polygon overlap 和 translation variation 被忽略；
另写 phase-only 简化编译器；
同一问题重复实现；
更弱的新代码覆盖更强的旧验证思路。
```

## 1.2 架构书自身留下错误假设

V3.7 把“8 phase”写成了足以生成 Coverage 模板，未明确 translation residue 随 `(q,r)` 变化。

Codex 因而按最短路径实现：

```text
每 phase 原点采样
→ 固定 offsets/weights
→ 全平面复用。
```

## 1.3 编译器与验证器同源

所谓认证再次调用同一个 `canonical_overlap()`，所以只能证明代码自洽。

## 1.4 数学 Gate 被 Live 成功覆盖

R1/R2/P1 可以只依赖同层 lateral。聊天成功掩盖了跨层 Coverage 没有实际参与。

## 1.5 权威文档未完整进 Git

完整路线书、架构书、任务书没有提交，仓库只留下摘要，导致约束无法真正控制执行。

# 2. 新路线原则

```text
复用盘点先于编码；
两个 Oracle 先于 certification；
全平移先于 phase template；
数学 Gate 先于 Surface；
跨层 fixture 先于 Live；
完整文档先于 COMPLETED；
正确性先于 runtime 无 polygon；
缓存后置。
```

# 3. 路线阶段

## R0：权威与状态纠偏

```text
完整 V3.8 架构、路线、任务、AGENTS 进入 Git；
ACTIVE_PROJECT 改为 IN_PROGRESS；
ac8ebaa4 完成 Tag 只保留历史，不提供物理 Coverage 信用；
模块完成度重算；
提交 checkpoint。
```

## R1：历史数学资产复用 Gate

```text
生成资产清单和 SHA；
运行 46 个快速 DG1 tests；
运行/拆分 GVR1、GRA1、GRC1、GKD1、GPR1；
分类 Oracle/Port/Reference；
禁止新代码前置。
```

## R2：独立 Oracle Gate

```text
保留历史 float64 polygon Oracle；
建立独立 Decimal/interval Oracle；
修正 world transform 方向；
验证 q/r、phase、direction、gap；
候选 false negative = 0；
零 overlap 正传播 = 0。
```

## R3：Core 平移协变 Runtime

```text
完整 source address 决定 Coverage；
首版允许确定性 polygon overlap；
phase constants 可预编译；
固定权重模板退出 default profile；
derived cache 可选；
legacy profile 保留。
```

## R4：真实 Surface

```text
Surface 使用全部 overlap members；
原生多层内容可见；
真实 dense/sparse stats；
selected_within_budget 与 overflow 分离；
删除 nearest-only 证据。
```

## R5：单入口跨层 Recall

```text
一个 entry；
目标 Atom 位于相邻物理层；
关闭 Coverage 不命中；
开启 Coverage 命中；
实际 path 包含 coverage_up/down；
无 Bridge、无 lateral 替代。
```

## R6：OpenClaw 回归与数据保留

```text
只有 R1-R5 通过后进行；
R1/R2/R3/P1；
插件启用；
Gateway 重启；
旧工作区保留；
不把同层 Live 扩大为跨层证据。
```

## R7：状态、完成度与 Bundle

```text
实际向量；
全部模块完成度；
完整报告；
clean tree；
完整历史 Bundle；
未完成也交付 IN_PROGRESS。
```

# 4. 长期防复发 Gate

每次几何任务必须回答：

```text
1. 搜过哪些历史分支和文件？
2. 为什么不能直接复用？
3. Oracle 是否与实现独立？
4. 是否覆盖非原点和平移余量？
5. 是否有真实跨层 fixture？
6. Live 是否可能只靠 lateral 通过？
7. 完整架构/路线是否在 Git？
8. 能力名称是否超过证据？
```

任何一项没有答案，不得进入 COMPLETED。

# 5. 当前模块基线

| 模块 | 状态 | 完成度 | 主要事实 | 主要缺口 |
|---|---|---:|---|---|
| CORE | IMPLEMENTED | 80% | 地址分离、原子状态、单入口 Recall API | Coverage 非平移协变 |
| SNAPSHOT | IMPLEMENTED | 50% | 状态字节和 tests | 版本迁移 |
| TRACE | IMPLEMENTED | 40% | 状态隔离 | kernel path 观察不足 |
| ACCESS | IMPLEMENTED | 85% | Surface/单入口编排 | 依赖错误 Coverage |
| HISTORY | PROPOSED | 10% | 章程 | 暂停 |
| AUDIT | PROPOSED | 10% | 章程 | 暂停 |
| OPENCLAW | CAPABILITY_VALIDATED | 85% | 单入口 Live | 未证明跨层 Coverage |
| LAB | IMPLEMENTED | 80% | 新 Decimal 原型和旧完整资产 | 独立认证未连接 |
| DISTRIBUTIONS | IMPLEMENTED | 70% | v0.7.0 组合 | 错误 physical validated 名称 |

# 6. 当前任务推进向量

```text
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +15% | DISTRIBUTIONS +5%
```

# 7. 进入后续能力的条件

在 V3.8 通过前暂停：

```text
多物理层 Placement；
Stitch；
density relocation；
PB 性能；
持久 Surface cache；
正式发布。
```
