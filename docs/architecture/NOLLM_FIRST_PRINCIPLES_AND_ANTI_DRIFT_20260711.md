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

### 2.1 Evidence and semantic-memory ownership (V3.3 amended)

```text
Host-owned conversation material is temporary semantic input by default.
Nollm's canonical persistent semantic unit is `MemoryStatement`; it may be
rewritten, split, or merged by a real LLM. Nollm guarantees structural and
state correctness, not model semantic accuracy. Optional transcript and
exact-span provenance belong to Host, History, Audit, debug, or migration
policy and are not an active default persistence requirement.
```

必须始终成立：

```text
Conversation Material ≠ MemoryStatement
MemoryStatement ≠ Placement
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

OpenClaw 不是事实源，LLM 判断也不是事实本身；Host-owned conversation
material 默认不进入 Nollm 持久状态。

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
1. 它是否遵守 ConversationMaterial 临时性与 MemoryStatement 持久边界？

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

GRF8 已在执行，不中途打断。

GRF8 完成后，下一阶段必须优先：

```text
1. 审计 GRF8 中所有 Index / Route / Lookup / Cache；

2. 删除所有承担关系和召回正确性的外置索引；

3. 将 partition routing 改为几何坐标函数；

4. 将 Cell occupancy 还原为几何结构本身；

5. 删除 Python hash / 固定评分 Placement 主路径；

6. 接入 OpenClaw 真实 LLM Placement；

7. 让 LLM 判断 duplicate / similar / revision / reuse / new / stitch / defer；

8. 重新测试无关系索引条件下的效率和召回质量。
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

> **Nollm 不是用索引找到记忆后再展示几何，而是让 LLM 把 MemoryStatement 放入几何关系场，使几何结构本身成为记忆关系和召回路径。**
