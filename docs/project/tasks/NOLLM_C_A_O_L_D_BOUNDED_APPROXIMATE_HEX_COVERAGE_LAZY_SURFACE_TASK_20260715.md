# Nollm C/A/O/L/D：有界近似六边形 Coverage 与惰性 Surface Runtime 任务书

**日期**：2026-07-15
**输入 Bundle**：`nollm_caold_translation_normalized_coverage_physical_entry_p1_20260715_871f7820.bundle`
**输入 HEAD**：`871f78203a7ef05584abf893ea0059640c7e2829`
**建议分支**：`codex/caold-bounded-approximate-coverage-lazy-surface`
**主环境**：Windows 10/11 + PowerShell
**交付**：全部进展 commit；clean tree；仓库外单一完整历史 Git Bundle

# 0. 任务推进向量

```text
任务推进向量：
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +10% | DISTRIBUTIONS +5%

主方向：
撤销生产 Decimal/polygon 精确 Coverage；以等面积六边形 quadrature 建立误差有界的快速结构核；Surface 改为惰性按需构建；保持单入口 P1 和无 Cursor。

范围变化：
Coverage 从“精确物理面积”调整为“硬物理变换下的有界近似结构关系”；精确面积保留为 Lab Oracle。产品地址域限定为 hex radius <= 2^31-1。
```

# 1. 可验证结果

```text
生产每 Cell Decimal polygon = 0
→ 54 点或 96 点等面积 quadrature
→ 固定点变换与整数 nearest axial
→ sparse Q16 Coverage
→ p95 TV <= 5%
→ p99 missed/false mass <= 2%
→ fanout <= 8
→ Surface Order 惰性选择
→ 11-Cell geometry <= 1s target / 5s ceiling
→ 217-Cell dense geometry <= 5s target / 15s ceiling
→ R1/R2/R3/P1 保持
→ clean tree + Bundle
```

# 2. 活动依据

按顺序读取：

```text
1. NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. V3.9 架构修订
3. V3.9 路线书
4. 当前状态和 Ledger
5. 本任务书
6. 根 AGENTS.md
7. Core/Access/OpenClaw/Lab/Distribution 章程
```

V3.8 文档作为历史输入；与 V3.9 冲突时，以 V3.9 为准。

# 3. 必须保留的资产

```text
GeometryAddress / SurfaceAggregateAddress 分离；
Δθ=22.5°、β=2^(1/4)、β²=√2；
PhysicalEntryCandidate；
单入口 Wire；
P1 闭环；
无 Cursor/Anchor route；
Statement/Handle/Core 原子性；
历史 polygon Oracle；
source-centered transform；
Coverage path reporting；
插件和旧数据。
```

# 4. 退出活动主路径

```text
packages/nollm-core/.../physical_coverage.py 中 Decimal polygon per-call；
动态 Decimal sin/cos；
每个 source 扫描 radius-6 polygon candidates；
signed-64 全闭包作为主 Gate；
zero false-negative/zero false-positive Gate；
精确 physical residual 阻止运行；
Surface begin/page 重建全部 0..8 Orders。
```

旧实现迁入 Lab/Oracle 或明确 `reference`，不得删除历史验证价值。

# 5. 模块完成度

## 5.1 任务前

| 模块 | 当前完成度 | 本任务影响 | 主要缺口 |
|---|---:|---|---|
| CORE | 85% | 是 | Coverage 和 Surface 过慢 |
| SNAPSHOT | 50% | 否 | 仅回归 |
| TRACE | 40% | 否 | 仅回归 |
| ACCESS | 90% | 是 | Surface API 依赖 eager build |
| HISTORY | 10% | 否 | 暂停 |
| AUDIT | 10% | 否 | 暂停 |
| OPENCLAW | 88% | 是 | 几何耗时影响真实操作 |
| LAB | 90% | 是 | 缺近似方法校准和性能基线 |
| DISTRIBUTIONS | 75% | 是 | 缺 approximation contract |

## 5.2 目标

| 模块 | 目标完成度 | 预计增量 | 交付能力 |
|---|---:|---:|---|
| CORE | 95% | +10% | 固定点 quadrature Coverage、lazy Surface |
| SNAPSHOT | 50% | 0% | 回归 |
| TRACE | 40% | 0% | 回归 |
| ACCESS | 95% | +5% | lazy order/page/descent 编排 |
| HISTORY | 10% | 0% | 无变化 |
| AUDIT | 10% | 0% | 无变化 |
| OPENCLAW | 93% | +5% | 秒级几何主路径下的 P1/R1/R2/R3 |
| LAB | 100% | +10% | 当前章程下近似核校准矩阵 |
| DISTRIBUTIONS | 80% | +5% | approximation/profile/budget 版本 |

# 6. 数学方法合同

## 6.1 等面积 quadrature

首选 `m=3`：

```text
6 sectors × 3² micro-triangles = 54 equal-area samples
```

如果 Gate 不满足，允许 `m=4`：

```text
96 samples
```

不得直接把 K 调到数百点以掩盖方法问题。

## 6.2 Runtime

每个 source：

```text
预编译 fixed-point matrix
+ 预编译 canonical sample offsets
→ target fractional axial
→ deterministic cube rounding
→ hit counter
→ relation-threshold prune
→ Q16 stable normalization
```

禁止：

```text
Decimal；
polygon；
sin/cos；
query/Statement；
nearest center only；
phase-only fixed weights without residue。
```

## 6.3 误差 Gate

与 Lab polygon Oracle 比较：

```text
missed_mass_p99 <= 0.02
false_mass_p99 <= 0.02
total_variation_p95 <= 0.05
dominant_target_agreement >= 0.95
max_fanout <= 8
partition Q16 sum = 65536
all targets within declared local radius
```

低于 `relation_threshold=0.02` 的支持差异不作为硬失败，但必须进入 residual/报告。

## 6.4 运行域

```text
max(|q|,|r|,|q+r|) <= 2^31-1
physical layer in current supported range
chart_id=default
phase=null
```

越界在 mutation/parse 时拒绝，不进入 Coverage。

# 7. Gate 0：活动切换和保护性 Checkpoint

工作：

```text
加入完整 V3.9 文档和 AGENTS；
ACTIVE_PROJECT 指向本任务；
撤回 lossless signed-64 草案；
记录 871f7820 输入能力；
确认旧工作区、插件和数据；
commit。
```

建议提交：

```text
checkpoint(caold): activate bounded approximate coverage route
```

# 8. Gate 1：Quadrature 数学校准

工作：

```text
复用历史 float polygon Oracle；
复用 Decimal source-centered Oracle；
实现独立 quadrature prototype；
覆盖 8 phases、2 directions、正负 q/r、dense translation samples；
输出 K=54、K=96 比较；
记录 TV、missed/false mass、fanout、dominant target、耗时。
```

硬条件：

```text
至少 K=54 或 K=96 满足误差 Gate；
Oracle 不进入生产 import；
支持差异按权重报告；
不再要求 exact support equality。
```

建议提交：

```text
test(lab): calibrate bounded hex quadrature coverage
```

# 9. Gate 2：Core 固定点近似 Coverage

新增/重建建议：

```text
packages/nollm-core/src/nollm_core/approximate_coverage.py
packages/nollm-core/src/nollm_core/coverage_contract.py
```

工作：

```text
生成 8 phase×2 direction fixed-point matrices；
生成 canonical micro-triangle centroids；
整数 cube rounding；
小整数 hit counts；
Q16 输出；
threshold residual；
LRU keyed by full address or residue；
旧 Decimal path 移出生产。
```

Core 输出至少：

```text
members；
method_id；
sample_count；
threshold_residual_q16；
q16_rounding_residual；
fanout；
relation_threshold_q16。
```

不再输出虚假的 exact/certified/physical-area 字段。

硬条件：

```text
生产源码 Decimal/polygon/sin/cos = 0；
同输入确定性；
越界明确失败；
缓存清除结果一致；
误差与 Lab Gate 一致。
```

建议提交：

```text
feat(core): replace polygon coverage with bounded quadrature kernel
```

# 10. Gate 3：惰性 Surface

重构：

```text
surface_orders 不再预构建 0..8；
select_active_surface 从 Order 0 逐阶请求 info；
首个满足预算的 Order 后停止；
page 复用 selected order；
descend 只构建当前 parent 所需子投影；
operation-local cache；
mutation/import/reopen 失效。
```

硬性能 Gate：

```text
11-Cell：target <=1s，ceiling 5s；
217-Cell：target <=5s，ceiling 15s；
同一 operation page 不重复全量 build；
Order 0 满足时不得计算 Order 1..8。
```

建议提交：

```text
feat(core): build surface orders lazily within budget
feat(access): reuse lazy surface traversal state
```

# 11. Gate 4：可选 residue atlas

仅当 Gate 3 ceiling 未达到时启用。

```text
N=32 起步；
key=(direction, layer_mod8, residue_bin_q, residue_bin_r)；
value=sparse offsets + Q16 weights；
由 quadrature 生成；
删除 Atlas 后直接 quadrature 结果仍可用；
Atlas 误差不得超过 direct quadrature Gate 太多。
```

不得用 Atlas 替代 quadrature/Oracle 合同。

# 12. Gate 5：Access/OpenClaw 组合回归

保持：

```text
one Surface path；
one physical entry；
无 Cursor；
query-agnostic Order；
LLM 语义 Placement；
P1 原子写入；
隐藏 Recall；
NONE。
```

真实场景：

```text
R1 Alpha；
R2 Office；
R3 NONE；
P1 新 Alpha 记忆；
Gateway restart；
P1 restart Recall。
```

报告分段：

```text
coverage_ms；
surface_build_ms；
page_projection_ms；
subagent_ms；
placement_apply_ms；
total_operation_ms。
```

硬条件：几何时间显著低于模型时间，不再占数十秒或分钟。

建议提交：

```text
test(openclaw): validate fast bounded geometry memory loop
```

# 13. Gate 6：完整回归和边界

运行：

```powershell
python -m pytest packages/nollm-core/tests -q
python -m pytest packages/nollm-snapshot/tests -q
python -m pytest packages/nollm-trace/tests -q
python -m pytest packages/nollm-access/tests -q
python -m pytest integrations/openclaw/formation-loop/tests -q
python -m pytest reference/python/tests/m0 -q
python tools/generate_module_ownership_manifest.py
python tools/generate_module_ownership_manifest.py --check
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py
Push-Location integrations/openclaw/formation-loop
npm test
npm run plugin:check
Pop-Location
```

要求：

```text
tracked=manifest；
unclassified=0；
violations=0；
cycles=[]；
OpenClaw direct Core import=0；
生产 Decimal/polygon=0；
select_entries/Cursor=0。
```

# 14. Gate 7：状态和 Bundle

严格顺序：

```text
代码和测试完成；
生成 Manifest；
提交报告/状态；
再次生成 Manifest；
最终回归；
commit；
确认 clean；
生成完整历史 Bundle；
verify + SHA256。
```

Tag 仅在全部 Gate 通过时：

```text
FAST_BOUNDED_APPROXIMATE_COVERAGE_SURFACE_VALIDATED_AT_<HEAD>
```

未完成：

```text
V39_BOUNDED_APPROXIMATE_COVERAGE_IN_PROGRESS_AT_<HEAD>
```

# 15. 非目标

```text
Stitch/Unstitch；
多物理层语义 Placement；
精确全平面 Coverage；
signed-64 全闭包；
PB 长跑；
多 Chart；
持久 Surface cache；
新的安全、Audit 或 release Gate。
```

# 16. 最终报告

新增单一报告：

```text
docs/project/CAOLD_BOUNDED_APPROXIMATE_COVERAGE_LAZY_SURFACE_REPORT.md
```

必须记录：

```text
输入/输出 HEAD；
预计/实际向量；
K=54/96 方法选择；
误差分位数；
耗时；
生产依赖扫描；
Surface lazy 证据；
R1/R2/R3/P1；
插件/数据；
测试；
Manifest；
known limitations；
Bundle SHA。
```
