# Nollm 第一性原理与防漂移约束

**日期**：2026-07-11  
**状态**：项目最高层目标约束  
**用途**：供 ChatGPT、Codex 和后续交接在开始任务前读取，防止因历史任务书、局部性能目标或对话截断而偏离项目初衷。

> 当本文件与旧任务书、旧交接文件、旧阶段实现发生冲突时，以本文件为准。旧实现可以删除，不因“已经完成”而保留错误方向。

---

## 1. Nollm 的第一性原理目标

Nollm 不是传统数据库、向量数据库、知识图谱或检索框架。

Nollm 的目标是：

> **为 LLM 提供一个证据优先、文件优先、由几何结构直接承载关系的长期记忆场；LLM 负责语义理解和放置判断，Core 负责确定性验证、几何执行、持久化与回放。**

最小记忆单位是：

```text
一段独立、有意义、可回到原文的表达
```

不是：

```text
token
固定长度 chunk
摘要
embedding
实体节点
```

---

## 2. 不可动摇的原则

### 2.1 Evidence first

```text
原始 Evidence 是事实源。
解释、位置、覆盖、路径和召回结果都不能替代原文。
```

必须始终成立：

```text
Evidence ≠ Interpretation
Interpretation ≠ Placement
Placement ≠ Fact confirmation
Recall path ≠ Proof
```

### 2.2 File first

```text
文件是持久事实源。
缓存、快照、索引和运行时对象都只能是可重建派生物。
```

### 2.3 Architecture is the Index

Nollm 的关系必须主要来自：

```text
几何地址
Cell occupancy
Coverage kernel
层间覆盖
局部邻接
可逆 Stitch
有界传播
```

不得再建立一套外部关系索引，先找对象，再让几何做装饰。

正确方向：

```text
Geometry address
→ Cell / Partition
→ Local relation field
→ Sparse propagation
→ Evidence fallback
```

错误方向：

```text
Object ID / source / entity
→ 倒排索引 / route table / graph
→ 找到对象
→ 再进入 Geometry
```

### 2.4 LLM 决定语义放置

以下判断必须由真实 LLM 完成：

```text
这是新内容还是重复内容；
是相似但不同，还是同一事实；
是否是旧内容的 revision；
是否复用原 placement；
是否创建新 placement；
是否形成新簇；
是否提出 stitch；
是否暂缓准入。
```

Python/Core 不得用以下方式模拟语义：

```text
hash placement
固定权重打分
关键词规则
伪向量相似度
人工硬编码答案
```

Core 只负责：

```text
验证对象存在；
验证几何地址合法；
验证密度、边界和预算；
执行放置；
保存 Evidence；
回放；
拒绝非法输入。
```

### 2.5 OpenClaw 是语义 Host

应尽快让 OpenClaw 中的真实 LLM 进入 Placement 流程。

正确关系：

```text
OpenClaw / LLM
  负责理解、比较、选择和提出 PlacementDecision

Nollm Core
  负责验证、执行、存储和几何传播
```

OpenClaw 不是事实源，LLM 判断也不是事实本身；原始 Evidence 始终保留。

### 2.6 Capture、Placement、Admission、Recall 分离

```text
Capture 是记住原文；
Placement 是选择几何位置；
Admission 是正式进入可回放结构；
Recall 是从有限入口重建相关现场。
```

不得因为 Capture 成功就强制完成全部几何工作。

### 2.7 Geometry 不是语义真相

```text
Coverage 不是 parent；
Cell 不是文件夹；
Stitch 不是事实合并；
Gravity 不是重要性；
位置不是可信度；
距离不是事实关系证明。
```

---

## 3. 必须删除的错误方向

当发现以下结构成为正确性主路径时，原则上删除，不做兼容性保留。

### 3.1 外置关系索引

包括但不限于：

```text
PlacementIndex._by_shard

RelationField._entry_lookup_cache

RelationField._patch_lookup_cache

GlobalShardedField._unique_routes

GlobalShardedField._shared_routes

GlobalFieldDirectory._source_intervals

source_window → placements 倒排表

island / patch → placements 倒排表

object → related objects

identity → partition 全局关系路由
```

允许保留的仅是：

```text
对象文件的最小物理定位；
由几何坐标直接计算的 partition；
Cell 自身的局部 occupancy；
删除后不影响正确性的临时缓存。
```

判断标准：

```text
删除后结果不变，只是变慢：
  可丢弃缓存

删除后仍能从文件直接找到对象：
  最小物理定位器

删除后无法进入正确关系路径：
  错误的关系索引，必须重构
```

### 3.2 Python 模拟语义 Placement

以下路径必须退出主流程：

```text
source hash → cell

shard_id hash → cell

固定评分公式决定 placement

伪向量相似度决定复用或新建

纯 Python 决定 duplicate / revision / stitch
```

它们最多可作为测试对照，不得作为产品 Placement。

### 3.3 Graph / Vector / Embedding 主路径

不得把 Nollm 变成：

```text
弱版知识图谱
弱版向量数据库
GraphRAG 包装层
embedding + geometry 可视化
```

可以保留基线实验，但不能进入 Core 主路径。

### 3.4 为错误架构做性能优化

不得因为某个索引已经很快，就继续固化它。

禁止以以下指标证明 Nollm 成功：

```text
indexed lookup 比 linear scan 快

route table 命中率高

倒排表查询达到微秒级
```

必须测量：

```text
无外置关系索引时，
由 LLM 选择的几何入口能否正确放置与召回。
```

### 3.5 重复安全与审计基础设施

当前开发环境默认：

```text
用户、ChatGPT、Codex 均为善意主体；
Windows-first；
安全由外部系统负责。
```

Nollm Core 不再建设：

```text
多层 SHA 链
Merkle root
evidence capsule
delivery receipt
供应链安全框架
攻击矩阵
重复权限系统
```

只保留：

```text
功能测试
数学验证
回放一致性
性能验证
Git 历史
单一 Git bundle
```

### 3.6 小任务和重复外审

默认采用：

```text
大跨度任务
+
内部 Gate
+
失败直接修复
+
最终单一 bundle
```

不要为文档格式、小型日志、非架构问题反复拆任务。

---

## 4. 正确的目标架构

```text
Raw Evidence
    ↓
Capture
    ↓
LLM compares local context and existing nearby memory
    ↓
PlacementDecision:
  reuse / new / revision / stitch / defer
    ↓
Core validates deterministic constraints
    ↓
Geometry address
    ↓
Cell occupancy + Coverage / Bridge kernels
    ↓
Sparse bounded propagation
    ↓
Original Evidence fallback
```

### 数据的关系来源

```text
局部关系：
由同一 Cell、相邻 Cell 和 Coverage kernel 直接产生

跨层关系：
由预计算 Coverage template 产生

跨簇关系：
由 LLM 提出的、Core 验证的可逆 Stitch 产生

修订关系：
由 LLM 判断，Evidence revision 记录明确保存
```

不得由全局 object-to-object 索引预先维护。

---

## 5. 每次设计前必须回答的问题

开始任何新任务前，逐项检查：

```text
1. 它是否保留原始 Evidence？

2. 关系来自几何结构，还是另建索引？

3. 删除缓存后，正确性是否保持？

4. 语义判断是否交给真实 LLM？

5. Python/Core 是否只做确定性验证和执行？

6. 是否正在为错误架构做性能优化？

7. 是否重新引入 graph/vector/embedding 主路径？

8. 是否把 Host 或 Terminal 变成事实源？

9. 是否增加与核心记忆无关的安全、审计或交付复杂度？

10. 是否可以用更少的组件完成同一核心目标？
```

若任一答案与本文件冲突：

```text
停止扩展；
删除错误结构；
回到第一性原理重新设计。
```

---

## 6. 当前执行顺序

日期化执行顺序只记录历史阶段上下文，不再授权活动工作。当前排期只由
`ACTIVE_PROJECT.md` 指向的任务书控制，且不得覆盖本文件的架构不变量。

当前活动方向必须优先：

```text
1. 审计活动路径中的 Index / Route / Lookup / Cache；

2. 删除所有承担关系和召回正确性的外置索引；

3. 将 partition routing 改为几何坐标函数；

4. 将 Cell occupancy 还原为几何结构本身；

5. 删除 Python hash / 固定评分 Placement 主路径；

6. 接入 OpenClaw 真实 LLM Placement；

7. 让 LLM 判断 duplicate / similar / revision / reuse / new / stitch / defer；

8. 重新测试无关系索引条件下的效率和召回质量。
```

截至 2026-07-15，活动物理 Coverage 路径还必须遵守：

```text
source-centered / residue-centered bounded arithmetic；
raw physical partition mass 在 Q16 前验证；
candidate-window、threshold、numeric 和 Q16 residual 分离；
Host 从有限页明确选择一个 physical entry；
Python/Core 不以 stable-key 或关键词代替最终语义选择。
```

---

## 7. 项目协作与交付规则

```text
主环境：
Windows 10/11 + PowerShell

任务：
大跨度 + 内部 Gate

交付：
单一 Git bundle

版本识别：
文件名 + Git HEAD

安全：
外部负责

外审重点：
架构方向、功能正确性、数学、性能、真实 LLM 工作流
```

---

## 8. 最终一句话

> **Nollm 不是用索引找到记忆后再展示几何，而是让 LLM 把证据放入几何关系场，使几何结构本身成为记忆关系和召回路径。**
---

## 9. 2026-07-14 数学真值、历史资产复用与独立 Oracle 修订

本节是最高约束的组成部分。其目的不是增加外围治理，而是防止数学内核在局部实现中被简化、重写或由同源测试自证。

### 9.1 先复用、后重建

开始任何几何、Coverage、Surface、坐标变换或多尺度任务前，必须先审计仓库现有数学资产。

至少检查：

```text
reference/python/nollm/dream_geometry/geometry/**
reference/python/tests/fixtures/gvr1/**
reference/python/tests/fixtures/gra1/**
reference/python/tests/fixtures/grc1/**
reference/python/tests/fixtures/gkd1/**
reference/python/tests/fixtures/gpr1/**
validation/gvr1/**
validation/gra1/**
validation/grc1/**
validation/gkd1/**
validation/gpr1/**
```

未经书面差距分析，不得重新实现：

```text
正六边形 world transform；
axial/world 双向变换；
凸多边形相交；
Coverage candidate；
Coverage distribution；
残差质量；
旋转—尺度 schedule；
平移变化验证；
双向 Coverage；
phase recurrence；
共振/非共振诊断。
```

历史代码不是因为位于 `reference/` 或旧分支就自动错误。应按以下分类：

```text
REUSE_AS_ORACLE：
  数学逻辑正确，可直接作为独立真值或回归 Oracle。

PORT_WITH_ADAPTATION：
  数学逻辑可复用，但需改为当前类型、精度或模块边界。

REFERENCE_ONLY：
  只保留实验设计、数据窗口或失败教训，不直接进入生产。
```

### 9.2 数学真值不能由同源实现自证

任何标记为：

```text
physical
certified
exact
validated
```

的几何能力，至少需要两个相互独立的实现路径交叉验证。

最低要求：

```text
Oracle A：
  历史纯几何 world transform + polygon overlap 实现。

Oracle B：
  独立 Decimal、区间、整数固定点或有理实现。
```

禁止：

```text
编译器调用函数 F；
测试再次调用同一个函数 F；
二者结果一致；
因此宣称数学真值已认证。
```

Parity 只证明实现一致，不自动证明物理正确。

### 9.3 Origin-only、phase-only 验证不足

当旋转角和尺度比不是格自同构时，Coverage 权重通常依赖完整平移余量。

因此：

```text
8 个 layer phase
≠
全平面 Coverage 权重表。
```

必须验证：

```text
多个正负 q/r；
多个 layer；
两个 Coverage 方向；
全部旋转 phase；
候选完整性；
零重叠误传播；
非零重叠遗漏；
权重误差；
残差质量。
```

原点只能是一个样本，不能代表全格。

The exact-support requirement in this section governs Oracle truth and method calibration. Production approximate Coverage is evaluated under section 10 by weighted missed mass, false mass, total variation, dominant-target agreement, fanout, locality, and Q16 conservation. This distinction does not authorize production polygon work and does not remove the independent Oracle.

### 9.4 正确性优先于“运行时禁止多边形”的局部限制

以下属于实现策略，不是第一性原理：

```text
Core 运行时绝不做 polygon；
Core 运行时只能查静态模板；
每个 phase 只能有一组固定权重。
```

若这些策略导致物理关系错误，应先采用可复现、确定性的真实 overlap 计算，再研究缓存和加速。

允许的正确性优先路径包括：

```text
固定上下文 Decimal；
整数固定点；
有理数；
区间算术；
预编译顶点常量；
可删除的 residue cache。
```

不得为了微秒级 lookup 固化错误 Coverage。

### 9.5 数学 Gate 必须先于 Live Gate

执行顺序必须是：

```text
历史资产盘点
→ 独立 Oracle
→ 全平移数学验证
→ Core runtime
→ Surface
→ 单入口跨层 Recall
→ OpenClaw Live。
```

数学 Gate 未通过时：

```text
不得以聊天回答正确；
不得以 R1/R2/R3 通过；
不得以插件启用；
不得以 Tag；
```

替代物理几何证明。

### 9.6 能力名称必须包含真实边界

如果只验证：

```text
地址分离；
单入口 Wire；
无 Cursor；
同层 Recall；
```

就只能以这些能力命名。

不得扩大为：

```text
rotated physical field validated；
certified Coverage；
full multi-scale；
exact geometry。
```

### 9.7 完整权威文档必须进入 Git

活动架构书、路线书、任务书和 `AGENTS.md` 必须以完整正文进入仓库。

禁止：

```text
只提交数千字节摘要替代完整架构书；
聊天附件存在但 Git 中缺失；
ACTIVE_PROJECT 指向不存在的任务；
状态先写 COMPLETED，数学报告后补。
```

> **已有正确数学资产必须成为下一实现的起点；新代码必须证明自己比历史 Oracle 更正确，而不是只证明自己能通过自己编写的测试。**

---

## 10. 2026-07-15 结构正确优先于面积精确修订

本节纠正上一阶段把“真实几何”误解为“生产运行必须逐 Cell 高精度计算精确多边形相交”的过度收敛。

### 10.1 Coverage 的第一职责是稳定关系，不是测量学真值

Nollm Coverage 的产品职责是：

```text
从真实旋转、尺度和坐标产生局部稀疏关系；
保持质量近似守恒；
控制误传播和漏传播的总权重；
让 Surface、Recall 和未来 Stitch 获得稳定几何骨架。
```

Coverage 不要求在生产运行时逐次恢复精确相交面积。允许：

```text
低于声明阈值的小面积真实重叠被省略；
低于声明阈值的小权重近邻被保守加入；
权重在声明总变差界内偏离 polygon Oracle；
候选支持因离散采样产生小幅边界抖动。
```

前提是误差有界、无长程跳跃、与语义无关、可复现且经过独立 Oracle 校准。

### 10.2 硬几何与近似 Coverage 分离

不可改变：

```text
Δθ = 22.5°；
θL = L × 22.5° mod 60°；
β = 2^(1/4)；
β² = √2；
Physical Memory Layer 与 Aggregation Order 分离。
```

允许近似：

```text
Cell overlap support；
Coverage weight；
阈值以下边界关系；
Surface aggregate mass。
```

不得通过改变硬物理参数换取性能。

### 10.3 精确 Oracle 与生产核分工

```text
Lab Oracle：
  polygon / Decimal / high precision；
  用于校准、抽样验证和误差报告；
  不进入每次聊天主路径。

Production Coverage：
  固定点坐标变换；
  等面积采样或经认证的 residue atlas；
  有界 fanout；
  固定时间；
  可丢弃缓存。
```

### 10.4 允许的误差必须按权重而不是边数量定义

不得要求：

```text
所有真实非零 overlap 均命中；
所有零 overlap target 均绝对排除；
生产核与精确 Oracle 支持集逐项相等。
```

必须限制：

```text
missed_mass；
false_mass；
total_variation_distance；
partition_mass_error；
max_fanout；
max_spatial_radius；
dominant_target_agreement。
```

默认阈值由 V3.9 架构和任务书规定，并可通过新证据版本化调整。

### 10.5 产品地址域按容量需求确定

数学格可以无限；活动产品地址域是资源 `POLICY`，不需要为 signed-64 全闭包支付主路径复杂度。

默认活动域：

```text
hex_radius = max(|q|, |r|, |q+r|) <= 2^31 - 1
```

This bound is the storage and transport domain. The active writable field is a separate policy and is currently `hex_radius <= 2^30 - 1`, closed under two consecutive `coverage_down` steps. Active mutation must reject a larger target before any write; existing storage-only state remains readable and is never silently deleted.

单层约可表达 `1 + 3R(R+1) ≈ 1.38×10^19` 个 Cell，远高于 PB 级需要。跨语言 Wire 在该域内可安全使用标准整数。

> **Nollm 要求几何关系真实地来自几何，不要求每条几何边都具有测量学级精确面积；结构稳定和运算可持续高于无必要的数值完美。**
