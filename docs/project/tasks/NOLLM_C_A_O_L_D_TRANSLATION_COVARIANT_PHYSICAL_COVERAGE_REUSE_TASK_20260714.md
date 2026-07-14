# Nollm C/A/O/L/D：平移协变物理 Coverage、历史数学复用与单入口跨层 Recall 任务书

**任务文件名**：`NOLLM_C_A_O_L_D_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_REUSE_TASK_20260714.md`
**日期**：2026-07-14
**受影响模块**：`C=Core | A=Access | O=OpenClaw | L=Lab | D=Distributions`
**输入 Bundle**：`nollm_caold_rotated_physical_field_single_entry_surface_20260714_ac8ebaa4.bundle`
**输入 Bundle SHA-256**：`4dd31eafe7e0a33ec9116a14a18fc9fb44f01c16d319dbb56fcc31e902a8bb64`
**输入 HEAD**：`ac8ebaa44cda35e1d2f73e0bfc95055bae425a86`
**建议分支**：`codex/caold-translation-covariant-physical-coverage-reuse`
**主环境**：Windows 10/11 + PowerShell
**交付**：所有真实进展 commit；工作树 clean；仓库外单一完整历史 Git bundle
**状态边界**：数学 Gate 未通过时必须交付 `IN_PROGRESS`，不得用 Live 成功替代。

# 0. 可验证结果

```text
完整 V3.8 权威文档进入 Git
→ 历史纯几何资产完成复用清单
→ 两个独立 Oracle
→ 修正完整地址 world transform
→ 任意 q/r 平移 Coverage candidate 完整
→ 零 overlap 不传播
→ 权重与 residual 有界
→ Core default profile 采用平移协变真值路径
→ Surface 使用全部 overlap members
→ 一个 entry 的跨物理层 Recall 必须依赖 Coverage
→ OpenClaw 回归、插件启用、数据保留
→ clean tree
→ 完整历史 Bundle。
```

# 1. 任务推进向量

```text
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +15% | DISTRIBUTIONS +5%
```

主方向：

```text
历史数学复用
→ 独立 Oracle
→ 平移协变 Coverage
→ 真实 Surface
→ 单入口跨层 Recall
→ Live 回归。
```

范围变化：

```text
V3.8 成为活动路线；
ac8ebaa4 降为 IN_PROGRESS；
“Core runtime 无 polygon”从硬约束降为未来优化；
phase-only 固定权重退出 default_dream_v1；
历史 reference geometry 升级为活动 Oracle 资产。
```

# 2. 任务开始前模块完成度

| 模块 | 生命周期 | 当前 | 置信度 | 证据 | 主要缺口 | 是否影响 |
|---|---|---:|---|---|---|---|
| CORE | IMPLEMENTED | 80% | 中 | 地址分离、状态、API | Coverage 错误 | 是 |
| SNAPSHOT | IMPLEMENTED | 50% | 中高 | 7 tests | 迁移 | 否 |
| TRACE | IMPLEMENTED | 40% | 中 | 状态隔离 | path 观察 | 否，仅最小报告 |
| ACCESS | IMPLEMENTED | 85% | 中高 | 单入口/预算 | 错误 Surface | 是 |
| HISTORY | PROPOSED | 10% | 低 | 章程 | 暂停 | 否 |
| AUDIT | PROPOSED | 10% | 低 | 章程 | 暂停 | 否 |
| OPENCLAW | CAPABILITY_VALIDATED | 85% | 中高 | 单入口 Live | 跨层未证 | 是 |
| LAB | IMPLEMENTED | 80% | 中高 | 历史资产/Decimal 原型 | 无独立认证 | 是 |
| DISTRIBUTIONS | IMPLEMENTED | 70% | 中高 | v0.7.0 | 能力名/合同 | 是 |

# 3. 目标完成度

| 模块 | 任务前 | 目标 | 增量 | 交付能力 | 验收 |
|---|---:|---:|---:|---|---|
| CORE | 80% | 90% | +10 | 平移协变 Coverage、真实 Surface | Oracle/跨层 fixture |
| SNAPSHOT | 50% | 50% | 0 | 回归 | tests |
| TRACE | 40% | 40% | 0 | 不扩展产品合同 | 回归 |
| ACCESS | 85% | 90% | +5 | 真实 Surface 单入口映射 | integration |
| HISTORY | 10% | 10% | 0 | 无 | 章程 |
| AUDIT | 10% | 10% | 0 | 无 | 章程 |
| OPENCLAW | 85% | 90% | +5 | 单入口跨层真实使用 | Windows Live |
| LAB | 80% | 95% | +15 | 两个 Oracle、全平移认证 | reports |
| DISTRIBUTIONS | 70% | 75% | +5 | V3.8 profile/wire/version | plugin check |

# 4. 开工前必须读取

```text
1. docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md
2. docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_8_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_20260714.md
3. docs/project/NOLLM_ROUTE_BOOK_V3_8_TRANSLATION_COVARIANT_COVERAGE_REUSE_20260714.md
4. docs/validation/NOLLM_REUSABLE_GEOMETRY_ASSET_INVENTORY_20260714.md
5. docs/validation/NOLLM_INDEPENDENT_GEOMETRY_ORACLE_CONTRACT_20260714.md
6. 本任务书
7. 根 AGENTS.md
8. C/A/O/L/D 章程
```

# 5. 必须复用的代码

开工前逐文件审阅：

```text
reference/python/nollm/dream_geometry/geometry/chart.py
reference/python/nollm/dream_geometry/geometry/hexgrid.py
reference/python/nollm/dream_geometry/geometry/polygon.py
reference/python/nollm/dream_geometry/geometry/coverage.py
reference/python/nollm/dream_geometry/geometry/schedules.py
reference/python/nollm/dream_geometry/geometry/transform.py
reference/python/nollm/dream_geometry/geometry/metrics.py
```

以及：

```text
GVR1、GRA1、GRC1、GKD1、GPR1 fixtures/runners/tests。
```

禁止在完成资产清单前新增第二套：

```text
world transform；
polygon clipping；
Coverage distribution；
translation validation。
```

# 6. 所有权变化

## Core

新增/修正：

```text
完整 source address 的 Coverage expansion；
确定性真实 overlap runtime；
safe candidate enumeration；
Q16/residual；
Surface 使用真实 members；
Recall kernel path 最小可观测结果。
```

不新增：

```text
LLM、query、Evidence、动态 Lab compiler、语义路由。
```

## Lab

负责：

```text
Oracle A/B；
高精度 constants；
translation windows；
candidate completeness；
误差认证；
复用清单；
性能对照。
```

## Access/OpenClaw

只适配真实 Surface/Recall 结果，不重写数学。

# 7. 明确非目标

```text
多物理层语义 Placement；
Stitch；
density relocation；
PB scale；
持久 cache；
vector/graph/embedding；
Topic/Source/Entity route；
安全/攻击 Gate；
正式发布。
```

# 8. Gate 0：权威、状态与保护性 Checkpoint

开始向量：

```text
C +10 | A +5 | O +5 | L +15 | D +5
```

工作：

```text
核验 Bundle/HEAD/Tag/clean tree；
把本执行包完整文件复制进仓库；
ACTIVE_PROJECT 指向 V3.8 和本任务 IN_PROGRESS；
CURRENT_STATUS 与 Ledger 重算；
保留旧 Tag 但撤销活动物理 Coverage 信用；
记录旧工作区/插件/数据摘要；
commit。
```

Gate：

```text
完整架构书、路线书、任务书、AGENTS 均在 Git；
文件不是摘要；
任务状态不是 COMPLETED；
无数据删除。
```

# 9. Gate 1：历史数学资产复用

工作：

```text
运行 tools/verify_reusable_geometry_assets.py；
生成/确认 SHA；
运行 46 fast DG1 tests；
运行 GVR1/GRA1/GRC1/GKD1/GPR1 smoke；
在 Windows 完整运行重型窗口；
分类 REUSE_AS_ORACLE / PORT_WITH_ADAPTATION / REFERENCE_ONLY；
commit。
```

停止条件：

```text
历史 Oracle 代码损坏且无法从 Git 恢复；
关键 world/polygon/coverage tests 失败。
```

不得因运行慢重写简化版本。

# 10. Gate 2：独立 Oracle 与变换修正

工作：

```text
Oracle A 保持历史代码不变；
建立独立 Oracle B；
由 world chart 直接推导 source/target，不复制当前错误 matrix；
验证 q/r 非原点、负坐标、8 phase、up/down；
输出 false negative / false positive / weight error / residual；
修正当前 axial transform；
commit。
```

硬验收：

```text
false_negative_count = 0；
positive_weight_on_zero_overlap = 0；
Oracle A/B 地址集合一致；
误差有声明上限；
origin 只是一个样本；
compiler 与 validator 非同源。
```

# 11. Gate 3：Core 平移协变 Runtime

首选实现：

```text
Core 内部确定性 Decimal/区间/整数固定点 overlap；
Lab 生成 phase/scale constants；
runtime 读取完整 GeometryAddress；
候选 disk 由物理上界推导；
每个候选真实 overlap；
Q16 和 residual；
可选 derived cache。
```

规则：

```text
default_dream_v1 不再使用 phase-only 固定权重；
旧 static templates 仅保留 legacy profile；
Core 不 import Lab/reference；
canonical state 不保存 cache。
```

验收：

```text
与两个 Oracle 全样本一致；
mutation/reopen 一致；
缓存删除结果不变；
无二进制 float 写入 state；
性能如实记录，不因慢失败。
```

# 12. Gate 4：真实 Surface

工作：

```text
Order 0..8 使用相同 Coverage runtime；
全部 overlap member 进入 projection；
native 多层 Atom 可见；
mass/residual 保留；
dense/sparse fixture 重新计算；
预算选择使用真实 infos。
```

验收：

```text
不使用 nearest-only/最多双 target；
观察面积严格增长；
dense 至少一次真实粗化；
sparse 不强制下降；
selected_within_budget 与 overflow 分开；
Oracle 对 projection member 抽样一致。
```

# 13. Gate 5：单入口跨层 Recall

建立 fixture：

```text
entry 在 layer L；
target 在 layer L+1 或 L-1；
不同层，无同层 lateral 替代；
无 Bridge；
一个 entry；
关闭 Coverage 时 target 不命中；
开启 Coverage 时命中；
path 明确包含 coverage_up/down。
```

验收：

```text
生产 Wire 无多入口；
Handle 去重仅路径重合；
错误 Coverage target 不出现；
Recall budget 有界；
重开后结果一致。
```

# 14. Gate 6：Access/OpenClaw Live

前置：Gate 1-5 全通过。

工作：

```text
新工作区或受控迁移；
插件指向 V3.8；
Gateway restart；
R1/R2/R3/P1；
至少一次跨层受控 Recall；
隐藏注入；
数据和旧工作区保留。
```

若真实模型或环境不可用：

```text
不补造；
交付 IN_PROGRESS；
不阻止 commit/bundle。
```

# 15. Gate 7：回归、状态与 Bundle

运行：

```powershell
python -m pytest packages/nollm-core/tests -q
python -m pytest packages/nollm-snapshot/tests -q
python -m pytest packages/nollm-trace/tests -q
python -m pytest packages/nollm-access/tests -q
python -m pytest integrations/openclaw/formation-loop/tests -q
python -m pytest reference/python/tests/m0 -q

python -m pytest -q `
  reference/python/tests/test_dg1_hex_coordinates.py `
  reference/python/tests/test_dg1_polygon_overlap.py `
  reference/python/tests/test_dg1_coverage_kernels.py `
  reference/python/tests/test_dg1_anti_resonance_metrics.py

python validation/gvr1/run_gvr1_translation_variation.py --output <path>
python validation/gra1/run_gra1_rotation_scale_resonance.py --output <path>
python validation/grc1/run_grc1_resonance_conditioned_coverage.py --output <path>
python validation/gkd1/run_gkd1_bidirectional_coverage.py --output <path>
python validation/gpr1/run_gpr1_geometry_profile_regime.py --output <path>

python tools/generate_module_ownership_manifest.py
python tools/validate_module_ownership_manifest.py
python tools/check_module_boundaries.py
npm test
npm run plugin:check
```

最终：

```text
更新实际向量；
更新全部模块完成度；
工作树 clean；
完整历史 Bundle；
Bundle verify；
SHA-256。
```

# 16. 完成条件

只有全部满足才允许：

```text
TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_AND_SINGLE_ENTRY_CROSS_LAYER_RECALL_VALIDATED_AT_<HEAD>
```

否则：

```text
CAOLD_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_REUSE_IN_PROGRESS_AT_<HEAD>
```

无论完成与否均必须交付 Bundle。
