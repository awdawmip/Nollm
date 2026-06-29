# Nollm 几何架构修正书 V2：局部图册、双向覆盖核与内生重力

> **英文名称**：Nollm Geometry Architecture Amendment V2: Local Atlas, Bidirectional Coverage Kernels, and Endogenous Gravity  
> **简称**：LA-BCK-EG 修正  
> **状态**：正式架构修正；尚未实施；作为后续纯几何内核、协议、迁移与实验设计的约束性来源。  
> **日期**：2026-06-29  
> **适用范围**：Nollm Dream Geometry 主线。  
> **与既有文件的关系**：本文件在不冲突处继承《Nollm 几何架构修正书：逆向生长、潜在重力与双向几何召回》（RG-LG-BGR）；在 **Anchor 的外部可见性、局部 chart、跨尺度覆盖、读取入口、参数反共振、图卡粘合** 等事项上，本文件优先。  
> **不变的高位原则**：Not an LLM；Architecture is the Index；反树；文件优先；可审计；可追溯；Core/Cortex 分离；不以向量数据库、图数据库或 SQLite 作为主记忆路径或事实源。

---

## 0. 结论摘要

本修正确认：Nollm 不能只被理解为“多层旋转蜂巢 + 若干锚场”。其真正可持续的几何内核应是：

```text
局部六边形 chart
  + chart 之间可验证的相似变换
  + 多对多的跨尺度覆盖核
  + 精确梦片向宽尺度的多轴逆向生长
  + 查询以同构方式生成临时几何探针
  + 仅在 Core 内部生效的潜在重力场
  + 在局部一致性满足时逐步形成的 atlas
```

由此，Nollm 的读写逻辑改写为：

```text
写入
Dream Shard
  → Cortex 提出带依据的多轴 Growth Proposal
  → Core 在局部 chart 中生成 Growth Trace
  → Trace 经细→粗覆盖核向上投影
  → 局部 Cover、势场、拼接候选与压缩结构逐步形成

读取
Query Probe
  → Cortex 以同一语义基底提出临时 Growth Proposal
  → Core 在已有局部几何中生成 Probe Trace
  → Probe 与既有 Cover / Trace 发生多轴交叠
  → 以粗→细覆盖核回落至精确 Dream Shard
  → 返回带来源、状态、修订边界的 Recall Digest
```

本修正作出以下正式决定：

1. **Nollm 的基本几何对象是局部图册（local atlas），不是单一全局蜂巢。** 全局 atlas 可形成，但不得被预设为所有写入的共同前提。
2. **跨尺度关系的基本对象是双向归一化覆盖核（coverage kernels），不是单一 `parent/child` 边、单向 `scale_link` 或外部锚权重。**
3. **Anchor 不得继续作为外部 LLM 可选择、可命名、可传入的 recall 入口。** 旧 `anchor_fields` 仅可作为迁移期历史兼容与诊断信息。
4. **“重力井”是由 traces、covers、稳定性、交汇、歧义、拥挤与冲突共同产生的 Core 内部势场。** 它可以影响几何操作；不得直接充当事实索引、查询参数或主 AI 可见目录。
5. **局部 chart 的粘合必须有证据、残差与循环一致性。** “两个区域看起来相关”不足以合并；未通过验证的关系只能保持为 `proposed` 或 `deferred`。
6. **逆向生长必须有语义依据链。** “昆明是城市”不能因为“昆明下雨”就被伪装为该事实本身证明的结论；每一条生长射线都必须说明其依据。
7. **宽泛入口需要足够宽，但不得形成泛概念黑洞。** 入口充分性与可区分性必须同时优化；“地点”“时间”“事物”等泛概念只能宽而浅，不能成为吞没一切查询的深井。
8. **层间参数不得只凭直觉固定。** 当前 `density × √2 / layer` 与 `22.5°` 仍可作为实验基线；必须加入多层共振、相位复现、覆盖熵和嵌套倾向的验证后，才能成为长期默认。
9. **不得将 Nollm 称为严格意义上的概形（scheme）或把日常 recall 说成上同调计算。** Grothendieck 的 site、sheaf、descent、atlas 仅作为局部—整体、限制—汇聚、粘合—一致性的数学灵感与边界语言；工程内核使用可验证的胞腔图册、广群、核与图算法。

---

## 1. 修正动因、范围与证据等级

### 1.1 已验证事实

以下事实已经通过项目材料或人工实验获得支持：

```text
1. 当前 Nollm 设计曾将 active_anchor_fields / anchors_used 等对象放入 recall 路径；
2. Iris-47 人工正向实验中，主 AI 命中过一条新注入的约束型记忆；
3. 同批实验中的普通事实、路线与 retired/current 关系未稳定命中；
4. 项目已经确定：最小写入单位是独立有意义的梦片，而不是 token；
5. 项目已经确定：蜂巢不是视觉装饰，而是放置、覆盖、读取与压缩逻辑的一部分；
6. 项目已经确定：局部 chart 优先，全局 atlas 后置；
7. 项目已经确定：跨尺度关系应多对多，而非预定义父子树。
```

### 1.2 合理推断

下列判断是架构推断，不是对现有代码内部实现的既成事实：

```text
1. 约束型记忆较易被召回，可能与其覆盖较宽、语义边界较强或现有选择策略偏好有关；
2. 普通事实召回不稳，可能与缺乏足够的上行结构痕迹、修订关系表达不足或候选选择偏差有关；
3. 外部可见 anchor 即使不被称为目录，也会在功能上趋向可调用索引；
4. 多层旋转与缩放若出现周期性相位复现，可能提高局部隐性嵌套和模板重复风险。
```

### 1.3 本修正不作出的结论

本文件不得被解释为：

```text
1. 已证明现有运行时完全没有真实读取路径；
2. 已证明现有普通事实失败只由几何模型造成；
3. 已证明某一组 β、θ 参数最优；
4. 已证明所有 local chart 必须最终粘合成单一全局平面；
5. 已证明 Core 可以不依赖 Cortex 的语义提议而自行理解事实；
6. 已证明 Grothendieck 上同调可直接解决实际 recall。
```

---

## 2. 规范性词汇与架构层级

### 2.1 规范性强度

```text
必须（MUST）：不满足即不得宣称符合本架构。
应当（SHOULD）：默认遵守；偏离时需说明原因、影响和替代验证。
可以（MAY）：允许的可选实现。
不得（MUST NOT）：违反反树、可审计、事实边界或安全边界的反模式。
```

### 2.2 三层对象边界

```text
Cortex / LLM 层：
  语言理解、事实解析、Growth Proposal、Query Probe Proposal、证据依据声明。

Core / Geometry 层：
  chart、胞腔、覆盖核、Trace、Cover、势场、变换验证、循环一致性、压缩、确定性 recall 路径。

Evidence / Audit 层：
  原始梦片、来源、状态、时间、修订链、ledger、可复现几何计算输入输出。
```

不得跨越的边界：

```text
Core 不得自行从自然语言创设实体、分类、事实或价值判断。
Cortex 不得绕过 Core 直接把“语义相近”当作已验证的几何关联。
Evidence 层不得被粗尺度摘要、势场或压缩结果覆盖或替代。
```

---

## 3. 数学对象：多尺度胞腔图册，而非“单一全局蜂巢”

### 3.1 标准六边形参考格

令：

\[
\omega=e^{2\pi i/3}=-\frac12+\frac{\sqrt3}{2}i,
\qquad
E=\mathbb Z[\omega].
\]

`E` 作为六边形中心的参考坐标格。对于工程实现：

```text
Eisenstein / complex coordinates：用于相似变换、精确旋转缩放、chart gluing；
axial coordinates：用于持久地址；
cube coordinates：用于 ring、邻接与格距离；
polygon geometry：用于真实面积交叠与覆盖核。
```

注意：`E` 是**参考坐标语言**，不是“每一个 Nollm cell 都是代数几何中的仿射概形”。

### 3.2 Local Chart

一个局部图卡记为：

\[
\chi=(\mathrm{id},\ell,s,\theta,t,U,\varphi,\pi),
\]

其中：

```text
id       ：chart 的稳定标识；
ℓ        ：局部尺度级别或尺度参数；
s > 0   ：六边形边长；
θ        ：相对于参考格的旋转；
t ∈ ℂ   ：局部平移；
U        ：chart 的支持区域，可为有限胞腔内并或其开邻域；
φ        ：局部 cell 与参考坐标之间的编码；
π        ：phase / offset 元数据，用于反共振与复现检测。
```

局部 cell 的中心坐标可写为：

\[
\Phi_\chi(z)=s e^{i\theta}z+t,\qquad z\in E.
\]

一个 chart 不要求与任何其他 chart 共用原点、同一旋转或同一平移。全局参考点 `O` 最多是调试、可视化或观测基准，**不得成为写入或 recall 的语义中心**。

### 3.3 Atlas

Nollm 的 atlas 是局部 chart 与其经过验证的过渡关系的集合：

\[
\mathcal A=(\{\chi_i\},\{g_{ji}\}_{\mathrm{verified}}).
\]

它允许：

```text
局部 chart 长期独立存在；
仅在有足够 overlap witness 时提出 transform；
仅在残差与循环条件满足时升级为 verified；
部分区域永远不粘合为一个全局平面；
多个 atlas component 并存。
```

因此，Nollm 的“整体”应理解为**一致的局部几何网络**，不是必须完成的单一全球坐标系。

---

## 4. Chart Transformation Groupoid：变换广群与粘合纪律

### 4.1 为什么不能把“非空相交”直接当作态射

两个胞腔非空相交是一种对称的几何事实；它本身不提供可组合、可逆、带坐标意义的态射。故必须区分：

```text
same-layer adjacency：共享边、共享顶点、近邻；
coverage correspondence：跨尺度多边形面积交叠；
chart transition：经证据验证的坐标相似变换。
```

只有第三类构成可组合的 chart transformation groupoid。

### 4.2 过渡变换

若 chart `χ_i` 与 `χ_j` 在支持区域中有可信对应见证，则候选过渡变换为保向相似：

\[
g_{ji}(z)=a_{ji}z+b_{ji},
\qquad a_{ji}\in\mathbb C\setminus\{0\}.
\]

其中：

\[
|a_{ji}|=s_j/s_i,
\qquad \arg(a_{ji})=\theta_j-\theta_i.
\]

要求：

```text
1. 两个不同的、非重合对应中心可提出一个 orientation-preserving similarity；
2. 三个或更多不共线见证必须用于验证残差；
3. 若允许镜像，必须显式标记 orientation_reversing，不得静默混入；
4. 未通过残差阈值的变换不得用于 atlas merge 或 recall 的同一性推断。
```

### 4.3 Chart Transform Record

```yaml
id: transform_chi_a_to_chi_b_v1
from_chart: chi_a
to_chart: chi_b
kind: orientation_preserving_similarity
transform:
  a_real: 0.0
  a_imag: 0.0
  b_real: 0.0
  b_imag: 0.0
support_witnesses:
  - witness_id: ...
    source_cell: ...
    target_cell: ...
fit_method: exact_two_point | least_squares | robust_fit
residual:
  rms: 0.0
  max: 0.0
confidence: 0.0
state: proposed | verified | rejected | superseded
ledger_refs: []
```

### 4.4 循环一致性

对闭环：

```text
χ_A → χ_B → χ_C → χ_A
```

必须计算：

\[
\Delta_{ABC}=g_{AC}\circ g_{CB}\circ g_{BA}.
\]

并检验其偏离恒等变换的残差：

\[
\varepsilon_{ABC}
=
\sup_{z\in W_{ABC}}
\frac{|\Delta_{ABC}(z)-z|}{s_{\mathrm{ref}}}.
\]

规则：

```text
ε ≤ ε_verified：可保留 verified；
ε_verified < ε ≤ ε_review：降为 proposed / requires_review；
ε > ε_review：标记 transform_conflict，禁止 merge。
```

这是一种可实现的“下降一致性”纪律；不应把它夸张描述为已经完成代数几何意义上的有效下降定理。

---

## 5. 双向覆盖核：跨尺度关系的正式对象

### 5.1 几何交叠

对来自 chart `χ_f` 的细胞 `f` 与 chart `χ_c` 的粗胞 `c`，定义：

\[
I(c,f)=\operatorname{Area}(c\cap f).
\]

候选对可由最近中心、ring 邻域或包围圆生成；但**真实关系必须由多边形交叠或经验证的等价算法确认**。

### 5.2 细→粗投影核

\[
K^{\uparrow}(c\mid f)
=
\frac{I(c,f)}{\operatorname{Area}(f)}.
\]

含义：细胞 `f` 的几何质量中，有多大比例可以投影到粗胞 `c`。

若固定一个有效的粗层 partition 或经归一化的候选族 \(\mathcal C(f)\)，应满足：

\[
\sum_{c\in\mathcal C(f)}K^{\uparrow}(c\mid f)
\le 1.
\]

未被承接的质量记录为：

\[
r^{\uparrow}(f)=1-
\sum_{c\in\mathcal C(f)}K^{\uparrow}(c\mid f).
\]

`r↑` 不得静默丢弃；它表示边界、跨 chart、阈值截断或尚未建立覆盖的残余。

### 5.3 粗→细回落核

\[
K^{\downarrow}(f\mid c)
=
\frac{I(c,f)}{\operatorname{Area}(c)}.
\]

含义：粗胞 `c` 的局部质量有多大比例可以回落到 `f`。

同样，若固定有效的细层 partition 或归一化候选族 \(\mathcal F(c)\)，应记录残余：

\[
r^{\downarrow}(c)=1-
\sum_{f\in\mathcal F(c)}K^{\downarrow}(f\mid c).
\]

### 5.4 对称诊断量

可选使用：

\[
J(c,f)=
\frac{I(c,f)}{\operatorname{Area}(c\cup f)}
\]

作为交叠质量诊断，不得替代两个方向各自的核。

### 5.5 核的工程规则

```text
1. K↑ 与 K↓ 不得被混成一个无方向 coverage weight；
2. candidate generator 可以近似，确认核必须可复现；
3. 每次截断都必须记录阈值、被截断质量和原因；
4. 跨 chart 的核只有在变换状态允许时方可用于高置信传播；
5. 多对多关系是常态，不得以单一最大覆盖强行生成父子边；
6. 任何“nearest center”关系不得单独作为长期结构事实。
```

---

## 6. 逆向生长：从精确梦片形成宽尺度入口

### 6.1 Dream Shard

Dream Shard 是不可被粗化替代的原始证据单元：

```yaml
id: shard_km_rain_20260629
kind: dream_shard
text: "昆明于2026年6月29日下雨了。"
state: loose | placed | placed_uncertain | crystallized | rejected | archived
source:
  kind: user_statement | observation | document | tool_output | llm_inference
  ref: optional
trust: unverified | source_backed | human_approved | derived | deprecated
occurred_at: "2026-06-29"
recorded_at: "2026-06-29T..."
revision_thread: optional
```

### 6.2 Growth Proposal

Growth Proposal 是 Cortex 对某一 Dream Shard 的有限结构化解释。它必须声明：

```text
生长轴；
每条轴的语义表达；
每一步的依据；
可扩展的最大尺度或预算；
不应推断的内容；
可能的冲突与不确定性。
```

示意：

```yaml
proposal_id: gp_km_rain_v1
shard_id: shard_km_rain_20260629
axes:
  - axis: location
    ray:
      - expr: "昆明"
        basis: explicit_in_shard
      - expr: "城市"
        basis: backed_by_other_shard_or_source_backed_rule
      - expr: "行政地理实体"
        basis: source_backed_rule
      - expr: "地点"
        basis: deterministic_projection
  - axis: phenomenon
    ray:
      - expr: "降雨"
        basis: explicit_in_shard
      - expr: "降水"
        basis: source_backed_rule
      - expr: "天气现象"
        basis: source_backed_rule
      - expr: "天气"
        basis: deterministic_projection
  - axis: absolute_time
    ray:
      - expr: "2026-06-29"
        basis: explicit_in_shard
      - expr: "2026年6月"
        basis: deterministic_projection
      - expr: "2026年"
        basis: deterministic_projection
      - expr: "历史时间"
        basis: deterministic_projection
forbidden_inferences:
  - "该日期在任何未来时刻均属于近期过去"
  - "昆明是城市这一分类由本句单独证明"
```

### 6.3 依据等级

每个生长步骤必须采用下列之一：

```text
explicit_in_shard
  梦片文本、来源文件或人工确认中直接出现。

deterministic_projection
  由稳定、无歧义、版本化的规则导出，例如“日 → 月 → 年”。

backed_by_other_shard
  由另一个明确可追溯的梦片支持。

source_backed_rule
  由可引用、可版本化的外部或项目规则支持。

provisional_llm_generalization
  Cortex 的候选泛化；只能产生 provisional trace，不能直接成为 confirmed fact。

rejected
  已被否定；可留作审计，不得参与正向主路径。
```

### 6.4 逆向生长的禁止事项

```text
不得把一个事实的“可能上下文”静默改写为该事实本身。
不得因为需要更宽入口而自动捏造实体类型、因果关系、法律关系或价值判断。
不得把 Growth Proposal 的文本本身当成已确认 Dream Shard。
不得生成无终止条件的“事物 → 存在 → 一切”泛化链。
不得用单一、唯一、固定父链替代多轴射线。
```

### 6.5 Entry Sufficiency：入口充分性

某个上行层级可作为粗尺度入口，必须同时满足：

```text
宽度：足以使当前或未来相近问题可在不读取全部细节的前提下靠近该区域；
区分度：不至于与绝大多数无关记忆混成一个超级区域；
多轴性：至少由两个相互独立的轴、或一条高可信专轴加一个约束轴支持；
依据性：每条关键射线具有可审计 basis；
预算性：继续向上生长的边际进入收益低于阈值时停止。
```

可抽象为：

\[
\mathrm{EntryScore}(C)
=
\alpha\,\mathrm{Reach}(C)
+
\beta\,\mathrm{AxisDiversity}(C)
+
\gamma\,\mathrm{EvidenceQuality}(C)
-
\delta\,\mathrm{Ambiguity}(C)
-
\eta\,\mathrm{Genericity}(C).
\]

这是一种设计目标，不是当前需要锁死的唯一数值公式。

---

## 7. Growth Trace 与 Coarse Cover：证据、痕迹与可读结构分离

### 7.1 Growth Trace

Growth Trace 是梦片经某条生长射线在某个 chart、某个尺度留下的结构性痕迹；它不是自动生成的一篇新的完整事实卡。

```yaml
id: trace_...
shard_id: shard_...
chart_id: chi_...
cell_id: cell_...
scale_level: ...
axis: location | phenomenon | absolute_time | revision | source | constraint | ...
basis: explicit_in_shard | deterministic_projection | backed_by_other_shard | source_backed_rule | provisional_llm_generalization
basis_refs: []
mass: 0.0
state: proposed | accepted | suppressed | superseded
created_by: cortex_proposal_id
```

### 7.2 Coarse Cover

Coarse Cover 是多个 traces 在粗尺度上形成的、可被读取与压缩使用的覆盖体：

```yaml
id: cover_...
chart_id: chi_...
support_cells: []
support_traces: []
axes_present: []
coverage_mass: 0.0
stability: 0.0
ambiguity: 0.0
state: candidate | stable | crystallized | deprecated
```

规则：

```text
Cover 不等于目录。
Cover 不拥有 Dream Shard。
Cover 不得列出 children 作为唯一读取路径。
Cover 可覆盖彼此不相连的局部片段，但必须保留实际 support cells 与质量分布。
Cover 若失去支持 traces，不得继续以稳定入口自居。
```

### 7.3 何时允许结晶为可读 Card

只有当以下条件满足时，Cover 才可以形成较稳定的摘要 Card：

```text
至少存在可追溯的支持梦片或来源；
跨多次写入或读取保持稳定；
摘要未抹去状态、时间、冲突或修订边界；
摘要的读取收益大于其错误泛化风险；
人类确认或协议允许其状态升级。
```

---

## 8. 潜在重力场：仅 Core 内部的内生几何势场

### 8.1 定义

潜在重力场不是 `anchor_id`，不是 tag，不是目录，也不是 LLM 的输入参数。它是 Core 从 traces、covers、局部结构和审计状态计算出的内部势能。

对 chart 中位置或胞腔 \(x\)，可以定义一个概念性势函数：

\[
\Psi(x)
=
\alpha\,\mathrm{Cohesion}(x)
+
\beta\,\mathrm{IndependentSupport}(x)
+
\gamma\,\mathrm{TransverseConvergence}(x)
+
\delta\,\mathrm{TemporalStability}(x)
+
\epsilon\,\mathrm{ReuseValue}(x)
-
\zeta\,\mathrm{Genericity}(x)
-
\eta\,\mathrm{Ambiguity}(x)
-
\kappa\,\mathrm{Congestion}(x)
-
\lambda\,\mathrm{Conflict}(x).
\]

解释：

```text
Cohesion                ：局部 trace 是否形成连续、低碎片的结构；
IndependentSupport      ：是否有独立来源、独立梦片或独立轴支持；
TransverseConvergence   ：不同轴是否在此交汇，而非单一高频词反复堆积；
TemporalStability       ：时间、修订和状态是否稳定；
ReuseValue              ：是否多次在不同任务中提供有效定位；
Genericity              ：是否过度泛化；
Ambiguity               ：是否对应太多互不相干的候选；
Congestion              ：是否成为拥挤、不可分辨的黑洞；
Conflict                ：是否存在未处理冲突、过期或相斥状态。
```

### 8.2 重力场允许参与的操作

```text
新 trace 的局部放置候选排序；
局部平移；
局部旋转；
chart 拼接候选；
cluster 的合并与分裂建议；
cover 的压缩优先级；
query path 的几何代价排序；
泛概念区域的拥挤抑制；
反共振时的局部相位调整建议。
```

### 8.3 重力场不得参与的操作

```text
不得作为外部 API 参数；
不得要求 LLM “先选择某个重力井”；
不得单独决定事实为真；
不得隐藏修订、冲突或来源；
不得因高频而自动成为全局中心；
不得替代 coverage kernel、chart transform 或证据依据；
不得把低势区域视为无价值或可无痕删除。
```

### 8.4 泛概念反黑洞规则

```text
“地点”“时间”“天气”“实体”“事件”等泛概念可形成宽背景场；
背景场的最大势深必须受 genericity / congestion 惩罚约束；
任何单轴高频出现不得单独形成深井；
深井应优先来自多轴交汇、独立证据、稳定修订和较低歧义；
读取时不得只因处于泛概念场就跳过具体轴交集验证。
```

---

## 9. 读取：Query Probe 与事实同构，但不等于外部模糊搜索

### 9.1 Query Probe

Query Probe 是一次读取请求的临时几何对象：

```yaml
id: probe_...
query_text: "昆明昨天是否下雨？"
proposal_id: qgp_...
axes:
  - location
  - phenomenon
  - relative_time
absolute_time_resolution:
  requested: "昨天"
  resolved_at_runtime: "2026-06-29"
state: ephemeral
budget:
  max_charts: ...
  max_layers: ...
  max_cells_per_layer: ...
```

它不得被静默写成长期事实。只有在用户明确要求保存、或其本身构成可独立审计的决策/任务残留时，才可转换为新的 Dream Shard。

### 9.2 Query 与事实的同构

Query Probe 与 Dream Shard 使用相同的：

```text
轴类型；
Growth Proposal schema；
coverage kernels；
chart 规则；
时间和修订边界；
预算和停止规则。
```

因此读取不是：

```text
query → 猜 anchor → 搜索一批卡。
```

而是：

```text
query → 临时多轴生长 → 粗尺度交叠 → 多种子回落 → 精确证据。
```

### 9.3 语义编译与“非模糊搜索”边界

必须承认：Cortex/LLM 需要理解问题，才能提出“昆明、降雨、昨天”等生长轴。这是**查询语义编译**，不是 Nollm Core 对全库做向量相似度 top-k。

约束如下：

```text
1. Core 不接收 select_anchor、anchor_name 或 semantic_search_query；
2. Core 接收的是有限、结构化、带 basis 的 Query Growth Proposal；
3. Core 仅在已存在的 traces、covers、核和 chart 中执行确定性或可复现的几何传播；
4. 不得以全库 embedding nearest-neighbor 结果替代几何交叠；
5. 可使用文本、实体或规则的规范化作为 Cortex 编译的一部分，但必须版本化、可审计，并不得伪装成 Core 自发理解。
```

### 9.4 粗尺度交叠与细尺度回落

设 Query Probe 在粗尺度形成质量 \(q_c\)，既有 Cover / Trace 质量为 \(m_c\)。候选交叠可按：

\[
\mathrm{IntersectScore}(c)
=
q_c\cdot m_c\cdot
\mathrm{AxisCompatibility}(c)
\cdot\mathrm{EvidenceQuality}(c)
\cdot\mathrm{RevisionValidity}(c).
\]

选择多个种子后，以粗→细核回落：

\[
q_f^{(r+1)}
=
\sum_{c}
K^{\downarrow}(f\mid c)\,q_c^{(r)}.
\]

最终 Dream Shard 候选必须经过：

```text
来源与 trust 过滤；
状态过滤；
有效时间过滤；
revision thread 过滤；
冲突显示；
证据充分性判断。
```

### 9.5 多种子和横向纠偏

不得选择唯一“最佳锚”或唯一“最佳父链”。应当：

```text
每层保留有限数量、彼此有差异的候选种子；
允许沿同尺度 adjacency 横向移动；
允许跨 verified chart transform 移动；
当新轴交叠显著提高时允许局部转向；
记录被放弃、截断和纠偏的原因。
```

### 9.6 停止规则

读取停止应至少满足：

```text
已经达到充分尺度且可回答当前问题；
新增细尺度的证据增益低于阈值；
剩余质量主要落在低 trust、过期、冲突或高歧义区域；
预算达到上限；
跨 chart transform 未被验证，继续扩展会制造伪同一性。
```

---

## 10. 时间、相对时间与修订几何

### 10.1 绝对时间必须持久，关系时间必须运行时投影

```text
“2026-06-29”               ：可持久化的绝对时间事实；
“2026年6月”                ：可由绝对日期确定性投影；
“昨天”“近期过去”“上周”     ：相对当前读取时刻的运行时投影；
“当前”“现行”“已退役”       ：必须依赖 valid_time、recorded_at 与 revision thread。
```

不得把“近期过去的时间”作为永久上层事实写死。

### 10.2 Revision Thread

```yaml
thread_id: revision_...
subject: ...
revisions:
  - shard_id: ...
    valid_from: ...
    valid_to: ...
    recorded_at: ...
    relation: current | supersedes | superseded_by | retired | corrected | disputed
```

`retired/current` 不是两张互不相关的事实卡，而是带有效时间和替代关系的几何—证据结构。读取时：

```text
先按请求时间筛选 valid_time；
再按状态和 revision relation 过滤；
最后才允许摘要表达“当前”或“已退役”。
```

---

## 11. 参数、相位与反共振政策

### 11.1 现有基线仍可保留，但不得被神圣化

当前工程基线可继续使用：

\[
D_{\ell+1}=\sqrt2\,D_{\ell},
\qquad
s_{\ell+1}=2^{-1/4}s_{\ell},
\qquad
\theta_\ell=(\ell\cdot22.5^\circ)\bmod60^\circ.
\]

它的价值是：缓慢增密、有限旋转模板、工程可调试。它不是已证明的最优参数。

### 11.2 多层共振风险

在上述旋转规则下：

\[
\theta_{\ell+8}\equiv\theta_\ell\pmod{60^\circ},
\qquad
s_{\ell+8}=s_\ell/4.
\]

若局部平移相位也重复或可公度，则可能出现：

```text
覆盖模板重复；
局部方向重新对齐；
多层嵌套倾向升高；
局部图结构重新表现出隐性父子性。
```

这不是“必然形成树”的证明，但必须成为实测风险。

### 11.3 反共振指标

几何内核必须至少能计算或估计：

```text
repeat_overlap_entropy
  多层覆盖矩阵是否高度重复。

multi_layer_nesting_tendency
  跨多个尺度是否出现稳定的一对一或近一对一包含。

phase_recurrence_score
  chart translation / offset 是否周期性回到等价相位。

coverage_branching_factor
  每个 cell 的有效跨尺度候选数量。

coverage_ambiguity
  质量是否过度平均到不可区分的广域区域。

chart_gluing_stability
  相似变换残差与循环残差是否持续可控。
```

### 11.4 参数实验矩阵

不得仅实现一组硬编码参数。至少保留如下对照：

```text
A. β = 2^(1/4), θ = 15°
B. β = 2^(1/4), θ = 22.5°
C. β = √2,      θ = 15°
D. β = φ,       θ = 15°（研究模型）
Benchmark. β = √3, θ = 30°
```

说明：对 \(\omega=e^{2\pi i/3}\)，

\[
1-\omega^2=\sqrt3\,e^{i30^\circ}.
\]

因此 `√3 + 30°` 在 Eisenstein 格上具有强算术兼容性，应作为证明/基准模型；但它也更可能出现强可公度与刚性嵌套，不能因“数学自然”自动成为 Nollm 的长期默认。

### 11.5 原点与平移政策

```text
不得要求所有 chart 共享同一神圣原点；
可以保留 O 作为观测、调试、渲染或局部构造基准；
平移 / offset 应作为 chart 的一等参数；
相位可由局部结构、覆盖熵与反共振策略建议调整；
任何相位调整不得覆盖既有地址、trace 或 ledger，应产生可追溯 transform / migration 记录。
```

---

## 12. 压缩、合并、分裂与长期运行

### 12.1 可压缩的是结构，不是原始证据

可压缩对象：

```text
重复 Growth Trace；
稳定的粗尺度 Cover；
覆盖核的模板或分块表示；
已证实冗余的局部 adjacency 说明；
局部势场缓存；
重复 chart transform 候选。
```

不可静默丢失对象：

```text
Dream Shard 原文；
来源与 trust；
有效时间与记录时间；
revision thread；
状态变化；
ledger；
压缩前后的可追溯映射；
关键残余质量与冲突。
```

### 12.2 合并与分裂

合并候选应至少考虑：

```text
coverage coherence；
axis diversity；
independent support；
chart transform confidence；
cycle consistency；
压缩收益；
冲突与歧义惩罚。
```

分裂候选应至少考虑：

```text
局部双峰或多峰势场；
跨轴支持明显分离；
revision / time 语义相斥；
chart transform 残差长期不可消解；
覆盖质量被泛概念错误汇聚。
```

### 12.3 不允许“为了省空间”制造假一致性

```text
不得将两个局部区域仅因文本相似或同属泛概念而合并；
不得因压缩删除冲突版本；
不得将多个来源的相同表述视为独立支持，除非其来源独立性可说明；
不得以单一摘要 Card 代替其完整 revision thread。
```

---

## 13. 对旧 Anchor 模型的正式迁移

### 13.1 废止的主路径

以下对象不得再作为新协议中的主 recall 路径：

```text
active_anchor_fields
anchors_used
anchors_discovered
anchor_name as recall parameter
anchor_field_card as external navigation entry
“先识别锚、再按锚读卡”的 Cortex 规则
```

### 13.2 可保留的迁移用途

```text
legacy_anchor_fields
  仅用于读旧数据、审计和迁移映射。

anchor_diagnostic_label
  仅用于开发人员解释某个局部势场或历史结构，非 API 查询入口。

anchor_to_trace_migration
  用于将旧 anchor weight 转化为带 provenance 的候选 Growth Trace，不得直接升级为 confirmed trace。
```

### 13.3 迁移规则

```text
1. 旧 card 不得因包含 anchor_fields 而失效；
2. 新写入不得产生外部可调用 anchor 作为主字段；
3. 迁移必须将每个 legacy anchor weight 标记为 historical / inferred / verified 之一；
4. 迁移后的 trace 必须补充 basis、support、chart、cell、state 与 ledger；
5. 在未建立覆盖核和 Query Probe 前，旧 recall 可作为兼容路径，但必须标注 legacy_fallback。
```

---

## 14. 反模式与不变量

### 14.1 反模式

```text
A1. 将 Anchor 改名为 gravity，但仍要求 LLM 传入其名字。
A2. 为每一条事实机械复制几十张完整自然语言卡。
A3. 把 LLM 泛化当作事实，不保留 basis。
A4. 用 nearest-center 代替真实跨尺度关系。
A5. 将任何 cell overlap 当成可组合的 chart morphism。
A6. 强制所有 chart 围绕一个全局 O 对齐。
A7. 只按高频词形成势井。
A8. 用“概形、拓扑斯、上同调”替代可实现的几何定义。
A9. 用全库 embedding top-k 偷换 Query Probe 的几何交叠。
A10. 为压缩而抹去来源、冲突、修订或残余质量。
```

### 14.2 必须保持的不变量

```text
I1. 每个 Dream Shard 可追溯到来源、状态与时间。
I2. 每条长期 Growth Trace 都有 basis 与生成记录。
I3. 每个 coverage kernel 可复现或注明近似边界。
I4. K↑ 与 K↓ 方向不可混淆；截断残余不可静默丢失。
I5. 未验证 chart transform 不得创造“同一位置”事实。
I6. Chart cycle residual 超阈值时不得 merge。
I7. 重力势场不可作为外部查询索引。
I8. Query Probe 与 Dream Shard 使用同构的生长与传播规则。
I9. 相对时间不得固化为永久历史事实。
I10. revision/current/retired 必须有时间与替代关系。
I11. 泛概念不得单独形成无限深井。
I12. 几何压缩不得损害证据可追溯性。
I13. 任何 runtime 成功声明仍需独立运行时证据；几何内核测试不能替代真实主 AI 正向召回验证。
```

---

## 15. 示例：昆明于 2026 年 6 月 29 日下雨

### 15.1 原始梦片

```yaml
id: shard_km_rain_20260629
text: "昆明于2026年6月29日下雨了。"
source: user_statement
trust: human_approved
occurred_at: 2026-06-29
```

### 15.2 不应采用的旧式处理

```text
写入 card
  anchor_fields:
    kunming: 0.9
    weather: 0.9
    date: 0.8

读取时
  LLM 先猜 “kunming / weather” 两个 anchor
  → 取该 anchor 下候选。
```

问题：`kunming`、`weather` 已在功能上变成外部索引入口；上层关系缺乏 basis；普通事实能否被看见依赖 LLM 是否猜中锚名。

### 15.3 应采用的新式处理

1. Cortex 生成 Growth Proposal：

```text
location：昆明 → 城市 → 行政地理实体 → 地点
phenomenon：降雨 → 降水 → 天气现象 → 天气
time：2026-06-29 → 2026年6月 → 2026年 → 历史时间
```

2. 每步明确依据：

```text
“昆明” / “降雨” / “2026-06-29”：explicit_in_shard；
日→月→年：deterministic_projection；
昆明→城市：必须来自其他支持梦片或 source_backed_rule；
“近期过去”：不得写入长期 trace，只能在 Query Probe 的运行时求值。
```

3. Core 选择或创建局部 chart，并生成细尺度 trace；

4. Trace 使用 \(K^\uparrow\) 向多个粗尺度胞腔投影，记录质量与残余；

5. 多条轴在若干粗尺度区域交汇，形成 candidate Cover；

6. 若长期稳定、来源充分且不产生过度泛化，可结晶为摘要 Card；否则仅保留 traces 和 covers。

### 15.4 查询示例

问题：

```text
“昆明昨天是否下雨？”
```

在 `now = 2026-06-30` 时：

```text
relative_time “昨天” → 运行时解析为 2026-06-29；
location / phenomenon / time 三轴形成 Query Probe；
Query Probe 与既有粗尺度 covers 相交；
通过 K↓ 回落到 shard_km_rain_20260629；
验证 source、trust、valid_time 和 revision；
生成回答与证据摘要。
```

在 `now = 2028-01-01` 时，同一梦片仍然可由绝对日期找到；但“近期过去”不应再作为其长期上层结构标签。

---

## 16. 数据模型与工具面建议

### 16.1 最小持久对象

```text
DreamShard
GrowthProposal
GrowthTrace
CoverageKernel
CoarseCover
Chart
ChartTransform
TransformCycleCheck
RevisionThread
CompressionMap
LedgerEvent
```

### 16.2 最小读取对象

```text
QueryProbe
ProbeTrace
IntersectSeed
RecallPath
RecallDigest
RecallAuditRecord
```

### 16.3 建议工具面

```text
geometry_validate
chart_create
chart_propose_transform
chart_verify_transform
chart_check_cycles
coverage_candidates
coverage_compute
trace_apply_growth_proposal
cover_recompute
gravity_recompute
growth_validate_basis
probe_compile
probe_place
probe_intersect
probe_descend
recall_geometry
revision_resolve
compression_plan
compression_apply
ledger
```

约束：

```text
不得提供 recall_by_anchor；
不得提供 select_gravity_well；
不得允许无 basis 的长期 trace 写入；
不得允许未验证 transform 参与高置信 recall；
不得将 coverage_candidates 的近似结果伪装为 coverage_compute 的确认结果。
```

---

## 17. 验证计划：先纯几何，后语义编译，最后运行时

### G0：文档与协议一致性

验证：

```text
旧 Anchor 主路径已被标记为 deprecated；
新对象和状态机在协议、README、Cortex 文档中一致；
无文件继续要求外部 LLM 先选 anchor 才可 recall。
```

### G1：无 LLM 的纯几何内核

固定 chart、cell、polygon 后验证：

```text
K↑ / K↓ 正确；
质量残余正确记录；
nearest-center 仅生成候选；
多对多覆盖有界；
同尺度邻接正确；
chart transform 拟合和残差正确；
三角循环一致性检查正确；
未验证 transform 不可 merge。
```

### G2：固定夹具下的逆向生长

给定人工编写的 Growth Proposal，验证：

```text
basis 缺失会被拒绝或降级；
日→月→年可确定性投影；
“昆明→城市”若无支持不得升级为 confirmed；
每层产生 trace 而非全文复制；
入口充分性与反黑洞惩罚可解释。
```

### G3：Query Probe 同构读取

在无 OpenClaw 环境下，验证：

```text
Query Probe 与 Dream Shard 使用同一轴 schema；
粗尺度交叠后可经 K↓ 回落到正确 shard；
多个种子并存；
修订、状态、time filter 能排除不应回答的 shard；
未知问题不会通过几何路径制造不存在的证据。
```

### G4：参数与反共振实验

对参数矩阵计算：

```text
coverage branching factor；
repeat overlap entropy；
multi-layer nesting tendency；
phase recurrence score；
chart gluing stability；
coverage ambiguity；
traversal budget。
```

### G5：压缩与审计

验证：

```text
压缩前后 Dream Shard、来源、revision、ledger 仍可回溯；
压缩不制造无来源的摘要；
冲突和残余仍可见；
势场缓存可重算。
```

### G6：运行时正向验证

仅在 G0-G5 通过后进行：

```text
受控注入；
真实 main AI 独立新会话人工提问；
事实、约束、修订、负控制分别测试；
证明路径以可因果关联的 receipt 为准；
不以 sidecar 自报 loaded / injected 代替主 AI 结果。
```

---

## 18. 实施迁移顺序

```text
LA0  固化本修正书，不改运行时。
LA1  建立纯几何 chart / polygon / coverage kernel 内核。
LA2  建立 ChartTransform、residual、cycle consistency。
LA3  建立 DreamShard → GrowthProposal → GrowthTrace 数据模型与 basis 验证。
LA4  建立 CoarseCover、残余质量、反黑洞和潜在势场计算。
LA5  建立 QueryProbe、intersect seed、K↓ 回落和 evidence filter。
LA6  建立 RevisionThread 与相对时间运行时投影。
LA7  建立参数反共振实验矩阵与报告。
LA8  迁移 legacy anchor 数据为历史诊断 / 候选 trace。
LA9  仅在纯几何验证通过后，重新设计 OpenClaw 最小正向实验。
```

不得跳过 `LA1-LA7`，直接把新的术语接入现有 runtime。

---

## 19. 暂不锁死的研究事项

以下具有研究价值，但当前不得进入强制工程协议：

```text
1. β、θ 与 translation 的全局最优性；
2. 是否存在可证明最小化 overlap variance 的参数族；
3. 全 atlas 是否应形成单一连通对象；
4. 是否应允许无理旋转或准周期模型；
5. 更高维胞腔系统；
6. sheaf / cosheaf 的严格范畴化；
7. Čech 高维复形、上同调或拓扑斯不变量；
8. 非阿基米德 / p-adic 类比；
9. motive、Hodge、derived 或 higher-stack 语言。
```

它们可以放入 `docs/research/`，不得替代现阶段可测试的 Kernel 定义。

---

## 20. 最终架构表述

```text
Nollm 是一个多尺度六边形胞腔图册。

精确梦片不依赖外部可见锚场进入记忆；
它们通过带依据的多轴逆向生长，
在局部 chart 中形成可审计的跨尺度覆盖痕迹。

细→粗与粗→细关系由双向覆盖核表达；
局部 chart 仅在相似变换、残差和循环一致性满足时粘合。

潜在重力场由结构自身内生，
只在 Core 内部参与放置、平移、旋转、拼接、压缩和路径排序。

查询以同构 Query Probe 进入同一几何，
从多轴粗尺度交叠回落到精确证据，
而不是先猜一个外部 anchor 再搜索目录或全库相似结果。
```

简写：

```text
Local Atlas, not Global Tree.
Coverage Kernels, not Parent Links.
Latent Gravity, not Exposed Anchors.
Query Probe, not Fuzzy Global Search.
Evidence First, Geometry as Index.
```

---

## 21. 决策记录

### 已确认的架构决定

```text
1. Anchor 不再是外部 recall 起点。
2. 重力井只在 Core 内部参与几何操作。
3. 写入和读取均采用多轴逆向生长。
4. 上层必须形成入口痕迹，但不逐层复制全文事实。
5. 局部 chart 优先，global atlas 后置。
6. 覆盖关系必须多对多且以真实几何交叠为核心。
7. 时间、修订与来源不能被粗化结构抹去。
8. 纯几何验证先于运行时接入。
```

### 合理假设

```text
1. 双向覆盖核和 chart cycle consistency 可提高普通事实路径的可解释性与稳定性；
2. 入口充分性 + 反黑洞约束能避免“宽泛入口”退化为隐性索引目录；
3. 参数反共振测试会揭示当前基线的局部重复风险；
4. 运行时 ordinary-fact recall 的改善需要同时依赖几何内核、Cortex 语义编译和真实数据面接入。
```

### 待验证事项

```text
1. 现有 22.5° / √2 密度基线的真实 nesting tendency；
2. Query Probe 是否可在不借助全库模糊检索的条件下稳定形成足够入口；
3. chart groupoid 在真实长期数据下的 transform witness 供给与残差表现；
4. Growth Proposal 的 basis schema 是否足以兼顾入口宽度与事实克制；
5. 压缩后对 recall 质量、成本和审计性的实际影响；
6. 新几何路径在 OpenClaw main AI 上的真实正向召回提升。
```

---

## 22. 与既有文件的关系

本文件应与下列文件共同阅读：

```text
NOLLM_PROJECT_SPEC_CN_20260612.md
NOLLM_GEOMETRY_FINDINGS_20260615.md
NOLLM_PROJECT_BOOK_V2_DREAM_GEOMETRY_20260615.md
NOLLM_EVOLUTION_OUTLINE_V2_20260615.md
NOLLM_GEOMETRY_ARCHITECTURE_AMENDMENT_REVERSE_GROWTH_LATENT_GRAVITY_20260629.md
```

建议源内位置：

```text
docs/geometry/
  NOLLM_GEOMETRY_ARCHITECTURE_AMENDMENT_REVERSE_GROWTH_LATENT_GRAVITY_20260629.md
  NOLLM_GEOMETRY_ARCHITECTURE_AMENDMENT_V2_ATLAS_COVERAGE_KERNELS_20260629.md
```

若旧文档与本文件冲突，以本文件为准，尤其是：

```text
Anchor 的外部可见性；
Local Chart / Atlas 的定义；
Coverage Kernel 的方向性；
Chart Transform 的验证门槛；
Query Probe 的入口机制；
反共振和原点政策；
概形/拓扑斯术语的使用边界。
```
