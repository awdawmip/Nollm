# 进取数论研究在 Nollm 覆盖算法中的迁移 · 2026-11-22

## 结果与适用范围

本轮在已发布的压力与变形实现上，完成三项结果等价优化：Core 的带标签残差位集覆盖、Lab 的平移边界事件维护、候选压力比较中的请求内几何复用。另新增独立的相对世界坐标 v2 接口，处理巨大共同锚点吞掉小位移的问题。统一功能测试 **90/90 通过，20.642 秒**。

七轮交错顺序的本地版本对比中，完整冷覆盖调用加速 **3.18–3.44 倍**，冷写入压力调用 **3.10 倍**，小幅连续跨界平移 **4.42–5.06 倍**，相同地图或局部扭转的完整压力比较 **1.70–1.76 倍**。已经命中完整覆盖缓存、全局扭转和无可复用的源 frame 变化基本持平；不能把前述倍数推广到这些场景。

这是对 Nollm 固定采样计算的实现改进。Core 仍以当前 Q40 变换、96 个采样点、原 half-even/cube 舍入、Q16 归一化和入库范围为准；没有提高曲边交叠真面积的精度，也没有端到端语义召回质量或延迟的实验结论。1–100 压力仍为建议值，同层写入仍可由 Host 选择。关系继续由原生几何覆盖产生。

版本对比基线为 [Nollm `58ad03a5`](https://github.com/awdawmip/Nollm/commit/58ad03a5457a6a8c57768368f4d9a3448c7827cd)。本轮没有修改进取数论仓库、其研究状态或原生数学路线。

## 1. 实际吸收了哪些研究

进取数论本轮读取固定于 [`fad409d5`](https://github.com/awdawmip/enterprise-math/commit/fad409d5ffacfbcc66acd7f8879a244ea66a63d1)。下表链接指向实际阅读的研究原文。它们提供迁移原则；Nollm 的几何条件、浮点适用域和性能需要自己的推导与验证。

| 研究原文 | 本轮迁移 | 迁移边界 |
|---|---|---|
| [自适应残差排序 THEORY](https://github.com/awdawmip/enterprise-math/blob/fad409d5ffacfbcc66acd7f8879a244ea66a63d1/experiments/brc_residual_sort_adaptive_20261110_b0e94005/THEORY.md) | 将所有输入严格分成已确定主体和完整残差；残差不丢失、不重复。 | 原文的整数多重集排序不自动保留附着对象身份。本实现明确保留 96 个采样标签。 |
| [R284DS 带标签事件扫描](https://github.com/awdawmip/enterprise-math/blob/fad409d5ffacfbcc66acd7f8879a244ea66a63d1/research_notes/portable_direct/R284DS_HEAP_LABELED_SWEEP_AND_BATCH_OBSERVER_20261122.md) | 对固定投影排序，按越界事件处理例外，保留同位置的全部标签，计入预处理和输出成本。 | 原文为辅助圆周观察模型，状态为作者证明、有限精确验证、尚未评审。本轮实现静态投影加动态成员位集，尚未实现任意扭转的时间事件扫描。 |
| [R85 固定谓词复用证明](https://github.com/awdawmip/enterprise-math/blob/f951a675d30d66ffeb72b0080f396f54dfbd66e4/research_notes/brc_s23_av_incremental_certificate_cache_20261112_r85/PROOF.md) | 把几何判定的有效输入与当前材料数量分开。源格和地图不变可复用覆盖，当前库存与压力重新聚合。 | 只在一个候选比较请求内复用；没有新增持久缓存或跨版本关系索引。 |
| [R91 整组排除证明](https://github.com/awdawmip/enterprise-math/blob/970708169086e6ab8f3525da1020ff890d8d3fcd/research_notes/brc_s23_av_point_subtree_interval_cache_20261112_r91/PROOF.md) | 证明整组点都不会受到追加扭转影响，才跳过该来源的重算。 | 排除失败只表示需要计算，不表示一定发生覆盖变化。 |
| [残差预分类实验](https://github.com/awdawmip/enterprise-math/blob/fad409d5ffacfbcc66acd7f8879a244ea66a63d1/experiments/brc_residual_sort_preflight_20261111_b118ef26c242/README.md) | 将分类、构建、维护、结果物化纳入实测，保留不划算的情况。 | 数学上能分类不等于运行更快；未借用 EM 历史实验的加速倍数。 |

自适应排序的关键恒等式是每个输入出现次数都落在计数主体或完整例外中：

\[
\mu_A=\sum_{x\in I}c_x\delta_x+\sum_{y\in E}\delta_y.
\]

这里迁移的是精确保全思想。Nollm 使用采样标签集合进行分割，几何目标计数只是最后的读出；不能用几个独立投影直方图代替共同的标签集合。

## 2. Core：三投影位集与完整边界残差

实现：[approximate_coverage.py](../../packages/nollm-core/src/nollm_core/approximate_coverage.py)。实现标识更新为 `parity_preserving_q40_residual_mask_kernel_v2`，几何与近似合同标识保持原值。

设 `S = 2**40`，精确相位为 `p`，第 `i` 个固定偏移为 `o_i`，候选轴向目标为整数对 `t`。目标六边形的严格内部由三个法向共同决定：

\[
h\in\{(2,1),(1,2),(-1,1)\},\qquad
-S<h\cdot(p+o_i-St)<S.
\]

每个方向只需为 96 个固定偏移的三个投影排序一次。排序前缀保存原采样标签的位集。对一个目标，每个法向使用两次整数二分找到开区间，将三个区间位集相交，再用 `bit_count()` 得到内部命中数。

三个位集必须保留共同的标签：只知道三个方向各有多少点落在区间里，并不能知道它们的交集有多少点。重复位置也仍有不同采样位，不能合并掉其多重性。

候选完整性来自闭六边形的轴向界 `|q|, |r| <= 2S/3`。加上当前固定采样偏移的极值，以精确 ceil/floor 形成包含全部可能目标的矩形；两个轴的区间宽均小于 3，因此任意相位最多九个候选。这是固定核常量上的界，不是随机测试观察到的最大值。

不同目标的严格内部互不相交。所有尚未分配的标签形成完整残差，逐点调用原 `_nearest_axial_q40`。因此边界的 half-even 和 cube-error 比较顺序继续由原代码决定，不另造近似阈值或 epsilon。

绝对中心仍分解为偶数整格锚和模 `2S` 相位。只取模 `S` 会丢失半数舍入的奇偶信息；本轮没有改变这一周期。完整成员排序、低命中处理、Q16 权重及存储半径核对沿用原实现。

新增的只有可清空、可重建的数学投影缓存；没有保存语义对象、跨层边或来源路由。完整调用仍支付成员物化与归一化成本，所以完整调用倍数小于单独相位核的微测倍数。

## 3. 平移：只维护实际越界的标签

实现：[motion.py](../../lab/nollm-lab/geometry/motion.py)。现有 `TranslationFootprint` 接口与 `lab_q40_translation_reuse_v1` 合同保持不变。

对原始点 `p_i`、当前目标 `t_i`、累计位移 `d`，取 `v_i=h·p_i`、`k_i=h·t_i`、`z=h·d`。一对相反面的严格内部条件为：

\[
S(k_i-1)-z<v_i<S(k_i+1)-z.
\]

固定 `v_i` 的排序数组跨步共享；动态位集维护当前 `k_i` 相同的成员。二分取出两侧闭尾区间，与成员位集相交，再对三个法向求并，即得到无法证明留在严格内部的全部标签。等号一并进入例外，由原 rounder 判断。

只有目标真正改变的标签才更新成员、余量和计数。分组的投影秩位集直接给出极值，避免每次跨界后重建 96 行六面余量。纯安全位移共享原数组；第一次小幅跨界时才构造排序事件。单次大步及显式 `mode="full"` 仍走完整路径。

原始点相位和标签始终保留。测试专门构造了“当前目标直方图相同、下一次移动结果不同”的两个状态，防止把当前读出误当成可替代所有未来运动的状态。旧分支的成员字典在更新前复制，分支之间不会相互污染。

大步门限依据本步除去偶锚后的残差距离，只影响成本选择；累计位移仍以 Python 整数精确保留。基准的大跳案例仍调用全部 96 个 rounder，不将其小幅提速归因于跳过采样。

## 4. 压力候选比较：复用几何，重新计算当前材料

实现：[pressure_evaluation.py](../../lab/nollm-lab/geometry/pressure_evaluation.py) 与 [deformation.py](../../lab/nollm-lab/geometry/deformation.py)。`evaluate_pressure()`、`compare_pressure()` 新增 `mode="auto" | "full"`，默认 `auto`；报告新增顶层 `work` 诊断。

同一请求中，覆盖的实际输入为源格、目标层、源地图和目标地图。完全相同的输入复用完整来源分配；源地图不变而目标地图改变时，可以复用源 world samples，再计算目标逆映射与舍入。

当地图变化仅为字面上的追加扭转时，使用实际 96 个源 world samples 的包围盒。只有所有新增扭转都可证明对全部点进入原 `RadialTwist._map` 的早退分支，才复用整来源覆盖。比较采用 `bbox_endpoint - center` 的原浮点顺序，避免改写成 `center ± radius` 后移动临界边界。没有通过浮点逆变换“理论上相消”来跳过计算。

每个来源的 before/after 处理完即释放其临时样本缓存。普通目标变形比较峰值为 96 点；源地图追加且实际受影响时最多两套，共 192 点。该临时保留量不随来源总数增长；完整分配与最终报告本身仍随输入和输出规模增长。

当前库存、支撑量、需求量及压力始终重新聚合。删除来源、零单位、部分库存、未知需求和前后影响区域并集都继续走原规则。每个来源对全部目标的份额保留原归一化。源 frame 改变而无可复用条件时直接完整计算，避免为无效复用支付额外成本。

在最终局部扭转基准中，128 个来源里 111 个通过整组排除：覆盖求值从 256 次降至 145 次，rounder 调用从 24,576 次降至 13,920 次。这个计数针对本报告的 radius=2 输入；其他局部扭转半径的数量不能混用。

## 5. 换锚：显式相对坐标 v2

实现：[relative_geometry.py](../../lab/nollm-lab/geometry/relative_geometry.py)。这项是数值表示改进，独立于前述三个结果等价优化。

`relative_layer_maps(source_map, target_map)` 以目标 frame 的世界原点为共同锚 `A`，从两个 frame 的世界原点及所有扭转世界中心减去 `A`。局部锚、尺度、角度和变换顺序保留。

理想几何上，每层满足 `F' = T(-A) ∘ F`，因此：

\[
(F'_t)^{-1}\circ F'_s=F_t^{-1}\circ F_s.
\]

径向扭转依赖点与中心的差，共同平移两者保持这个差。局部锚属于局部坐标，不应减去世界锚。

`sampled_relative_coverage()` 在添加小样本以前就去掉共同大数，返回合同 `lab_float64_relative_layer_map_quadrature_v2`。默认 v1 和持久 Core 均未切换；该接口也未静默接管 `compare_pressure()`。

实际反例：源 L0 `(1,0)` 到 L1 的普通命中为 `(1,-1,22), (1,0,41), (2,-1,30), (2,0,3)`。两层同时增加世界原点 `(2**54, 2**54)` 后，旧 v1 得到 `(0,0,63), (3,-1,33)`；新 v2 恢复原来的四项命中。测试保留旧结果，明确新执行顺序不同，不能宣称对旧浮点输出逐位等价。

若相对偏移在构造输入 float 时已经丢失，例如 `2**54 + 1` 已舍入成 `2**54`，此接口无法恢复那个 `1`。有限输入相减而超出 float64 数值域时报告 `ValueError`。它仍是浮点采样，不是任意巨大坐标或精确实数面积求解器。

## 6. 完整版本基准

可复跑脚本：[benchmark_em_residuals.py](../../packages/nollm-core/tests/benchmark_em_residuals.py)。原始七轮数据、环境、工作量和一致性结果：[em_residual_benchmark_20261122.json](../../lab/nollm-lab/geometry/results/em_residual_benchmark_20261122.json)。

旧版四份模块从固定基线独立加载，尤其旧压力模块绑定旧 deformation 模块；没有用已经增加维护成本的新 `full` 路径冒充旧版。其他依赖本轮未改变。每项相同输入先核对结果，随后交替旧→新、新→旧计时七轮，表中为批次中位数，单位毫秒；倍数为旧/新。Python 3.12.14，Linux x86_64，2026-11-22 19:30 香港时间。本地共享执行环境有抖动，约 1.0 倍的小差异不作收益结论。

| 完整工作负载 | 旧版 ms | 新版 ms | 旧/新 |
|---|---:|---:|---:|
| 2,000 个唯一冷覆盖，up | 338.921 | 98.461 | 3.44× |
| 2,000 个唯一冷覆盖，down | 353.202 | 111.164 | 3.18× |
| 2,000 次跨 8 层共享相位，up | 90.265 | 68.043 | 1.33× |
| 2,000 次跨 8 层共享相位，down | 97.808 | 68.943 | 1.42× |
| 2,000 次完整缓存命中，up | 4.131 | 4.001 | 1.03× |
| 2,000 次完整缓存命中，down | 4.083 | 4.074 | 1.00× |
| 256 个冷写入压力计算 | 296.154 | 95.590 | 3.10× |
| 256 步安全平移，up | 2.158 | 1.783 | 1.21× |
| 256 步安全平移，down | 2.003 | 1.604 | 1.25× |
| 256 步小幅随机跨界，up | 32.949 | 6.514 | 5.06× |
| 256 步小幅随机跨界，down | 33.204 | 7.513 | 4.42× |
| 256 步大幅随机跳动，up | 89.382 | 62.371 | 1.43× |
| 256 步大幅随机跳动，down | 85.768 | 63.005 | 1.36× |
| 128 来源，地图不变的压力比较 | 82.376 | 46.714 | 1.76× |
| 128 来源，局部目标扭转 | 89.513 | 52.627 | 1.70× |
| 128 来源，全局目标扭转 | 98.826 | 95.713 | 1.03× |
| 128 来源，源 frame 改变 | 87.438 | 85.561 | 1.02× |

计时口径：

- 冷覆盖每轮清空派生缓存，包含固定投影初始化、完整展开、成员物化与 Q16 权重读出；输入地址预先生成。
- 原生压力含完整 incoming-up 覆盖、当前单位回调及压力映射输出；回调提供确定的物理单位身份，不含磁盘 I/O。
- 平移含每条轨迹初始化、全部状态维护和每步中心/Q16 结果物化。正确性阶段另外对照每一步全部 96 个采样目标。小跨界 up 的新旧 rounder 数同为 152，down 同为 159；主要收益是去掉残差选择与证书重建中的重复扫描。
- Lab 压力含每次全新请求、完整来源分配、所有区域压力和 JSON-ready 报告构造；不含 `json.dumps` 或磁盘写入。除新增 `work` 诊断外，与发布旧版报告逐字段相等。
- 大跳仍为每方向 24,576 次舍入；全局扭转仍为 256 次覆盖求值。这些场景没有凭空变成稀疏残差问题。

### 保留的未采用尝试

第一版平移索引在构造时立即排序。其独立试测中，构造从 353.029 微秒增到 506.699 微秒；safe/up 的 256 步从 3.944 ms 增到 4.711 ms。最终改成首次小跨界才构建，并优化纯位置复制与三法向余量计算。早期压力复用在源 frame 改变而没有复用机会时曾慢约 7%，最终改为直接完整路径。

这些是开发中间版本的负结果，不与最终七轮表混算。原始中间试测保存在 [em_residual_discarded_trials_20261122.json](../../lab/nollm-lab/geometry/results/em_residual_discarded_trials_20261122.json)，注明了各自不同的测量口径；被放弃的中间实现没有作为运行版本保留。

## 7. 测试与调用

统一运行：

```bash
python3 lab/nollm-lab/geometry/run_support_deformation_tests.py
```

结果为 90 项全部通过，其中原有 63 项保持，新加 27 项：

| 新测试 | 数量 | 主要行为 |
|---|---:|---|
| `test_residual_mask_coverage.py` | 6 | 至多九候选的全相位界、两方向各 2,500 相位含构造边界、所有 129 层及有符号大地址、重复边界标签、原舍入与可清空缓存。 |
| `test_motion_residual_events.py` | 7 | 例外标签与逐点六面扫描相同、同直方图不同未来相位、分支不可变、累计移动、边界预测、超大诊断整数与 full 回退。 |
| `test_pressure_reuse.py` | 8 | 实际 rounder 计数、追加扭转排除、精确包围盒边界与一个 float 步长、地图失效、新库存、部分未知、旧浮点执行路径对照。 |
| `test_relative_geometry.py` | 6 | 巨大共同锚反例、所有扭转中心一起换锚、独立 80 位 Decimal 几何、输入不变、已丢偏移与差值溢出。 |

带本地 Git 历史的 checkout 可直接复跑版本基准：

```bash
python3 packages/nollm-core/tests/benchmark_em_residuals.py \
  --repeats 7 --sources 2000 --motion-steps 256 \
  --output /tmp/nollm-em-residual-benchmark.json
```

没有本地历史的部分 checkout 可通过 `--baseline-dir` 提供固定提交的四份源文件，文件名在脚本 `PATHS` 中列出。本轮使用经 GitHub 连接器读取的固定版本；脚本自身不联网。计时没有加入 CI 断言。

压力比较调用沿用现有参数，并可选择完整对照：

```python
from geometry.pressure_evaluation import compare_pressure

report = compare_pressure(
    upper_units, lower_units, upper_layer=0,
    after_upper_map=candidate_map,
    inventory_complete=True, mode="auto",
)
print(report["delta"], report["work"])
```

`inventory_complete=True` 只适用于调用方确实提供了该相邻层对的全部有限材料；部分库存保留默认值。新相对坐标接口在 Lab 的 `geometry.relative_geometry` 中导入使用，默认 v1 调用保持原行为。

治理检查沿当前完整 Git 路径清单和生成器更新 ownership；新增 Lab 实现归入原 support-deformation 功能门禁。部分 checkout 未运行全仓库校验，不能把本轮功能切片通过写成全仓库 CI 通过。Core 公共导出与运行时操作集合未扩展。速记本在代码固定提交后沿实际相遇维护受影响理解，保留旧表达版本与原有连接。
