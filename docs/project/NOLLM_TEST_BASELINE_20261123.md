# 当前引擎、读写策略与精度的固定测试版本

日期：2026-11-23（UTC+08）。测试版本：**`nollm-test-20261123.1`**。

本轮按用户要求恢复另一对话的低精度前沿，审核最新主线并实际运行测试。代码、原始测试场和已有规则统一固定于提交 **`f37667bf232360d0c26d37de0639285084230ddc`**。本版本不修改运行时几何，也不把尚未实现的局部 p8 当作当前默认。

[机器可读版本清单](NOLLM_TEST_BASELINE_20261123.json)记录引擎标识、精度、样本、场配置、预算、读写方式与真实未完项；[本轮测试结果](../../lab/nollm-lab/repository_memory/results/frozen_baseline_20261123.json)记录实际运行。版本分支 `test/nollm-20261123-1` 用于打开这份测试包；复现实验时以其固定提交及清单中的源提交为准，后续 main 可继续发展。

## 1. 冻结对象

| 对象 | 本版本固定值 |
|---|---|
| 引擎与原始测试场 | `f37667bf232360d0c26d37de0639285084230ddc` |
| Core / Access 包版本 | 均为 `0.1.0`；实际版本由上述 Git 提交识别 |
| 当前实现 | `parity_preserving_q40_residual_mask_kernel_v2` |
| 公开 Coverage method | `equal_area_hex_microtriangle_q40_m4_v1` |
| 公开 Coverage contract | `nollm_bounded_approximate_hex_coverage_v1` |
| 默认几何 | `default_dream_v1`，相邻层旋转22.5°、尺度基数为2的四次方根 |
| 当前算术与采样 | Q40；96点；保留每一个命中；Q16输出合计65536 |
| 地址 | 完整整数；可写hex半径≤2³⁰−1，存储半径≤2³¹−1；物理层−64..64 |
| 舍入 | 既有signed half-even、cube修复顺序和偶数整格锚恢复 |
| 工作场 | 同一提交中的 `sujiben/field`，41个占用格、43条当前表达、69份版本文件、2条既有桥 |

历史 PR #4 的说明仍使用 `phase_kernel_v1` 名称。当前残差掩码实现已更新为 v2，但公开几何合同与持久化身份保持；不能只依据旧说明或通用包版本识别本次引擎。源码依据：[实现标识](../../packages/nollm-core/src/nollm_core/approximate_coverage.py)、[覆盖合同](../../packages/nollm-core/src/nollm_core/coverage_contract.py)。

## 2. 从中断对话恢复的低精度选择

已保存的实现与方案顺序为：有理 adaptive 执行器 `dcd04cc3`；接受固定精度结构变化的 Lab `quantized` 实现 `0e98a795`；用户选定相邻层局部 p8 与容量方案 `8bb8f805`，并在 `55871fc6` 更新原生理解。后续工作转向 Surface 分层提炼，通用局部单位执行器没有在这些提交后完成。

当前应分别记录：

| 配置 | 实际状态 | 精度含义 |
|---|---|---|
| 活跃 Core | 已实现，当前场实际使用 | Q40/96，保持既有采样关系 |
| Lab `auto/reference` | 已实现，显式实验入口 | 有理参数定义的96点精确标签与份额 |
| Lab `adaptive` | 已实现，显式实验入口 | 默认16位起步、最多128位区间尝试，未决样本最终精确回退 |
| Lab `quantized` v1 | 已实现，默认12位，可显式传8位 | 现有世界中间单位下的固定精度递推，直接接受其样本标签；纯仿射保留廉价整数核 |
| 用户已选的下一配置 | **局部单位执行器待实现** | 只算相邻层；局部格单位p8；96点；完整整数地址；规范物理锚 |

用户选择的8位是一个局部格长度单位中的1/256，既不是float8，也不是整数总位宽、地址容量或记录数限制。旧实验 `depth=1/2/3/5` 指同一对相邻层中的扭转总段数，不是跨越物理层的数量。降低算术小数位与减少96个采样点是不同改动。

### 本轮再次核实的单位问题

既有八源格、768标签探针显示：共同世界长度缩放为1、1/256、1/65536时，精确与adaptive的标签保持；旧p8相对精确标签变化分别为9、645、696。人工恢复共同局部单位后，原p8的768个标签逐项恢复，保留原来的9个允许差异。这项探针证明单位处理确实影响旧量化路径，不能把“默认12改成8”作为局部p8的完成条件。

本轮还审阅了换锚的相位：旧量化核使用目标frame的表示原点抵消共同锚；表示重锚可能改变其量化结果。独立复现的p8、默认p12例子中，精确物理映射不变而一个采样标签变化。该问题属于Lab量化v1，活跃Core的固定Q40路径不调用它。具体输入、样本和复现见本轮结果中的 `precision_review`。

两例分别来自固定主组 `d1_compact_weak_up` 与 `d1_medium_up`，目标仅重锚到 `(1/3,1/7)`，各改变768个标签中的1个。新保存的[重放探针](../../lab/nollm-lab/geometry/probe_quantized_reanchor.py)读取原冻结库存，不重新挑选样例；成功表示复现旧合同的已知问题。

下一配置应按[相邻p8方案](NOLLM_ADJACENT_P8_CAPACITY_PLAN_20261123.md)处理规范物理锚与局部长度单位，并复用已冻结的主组/第二组输入比较新结果。改变执行含义时给出新的明确合同，保留本版本作为对照。

## 3. 本版本的读写规则

这些设置是当前测试场的使用配置，数值不成为所有项目的永久限制。

| 配置 | 固定值 |
|---|---|
| Surface入口层 | L−2 |
| 可写层 | L−2、L−1、L0，显式多层写策略 |
| 观察 | order=0，page_size=8，compact=true |
| 默认展开 | downward，steps=1，beam=16，limit=20 |
| L−2容量 | 每格2条/128 UTF-8字节；整层16占用格/2048字节 |
| L−1容量 | 每格2条/512字节 |
| L0容量 | 每格2条/8192字节 |

原始配置位于 `sujiben/field/access/encounter.json` 和 `content_budget.json`，同时原样记录在机器清单中。

- 第一层保存完整、有来源的短判断，条件和详细表达沿相邻蜂巢覆盖展开。
- Host根据已显示的内容选择一个物理入口；`entry`保持，`focus`沿实际显示的相邻目标下降，`ascend`返回本次已走路径。
- Host决定新增、支持、修订或放置。Core执行几何，Access保存表达、来源与当前绑定；历史版本继续可读。
- 默认downward不经过桥；选择允许桥的传播模式才会使用既有Stitch。
- 可写候选不必然被当前格向下读到。放置和重组应从实际读取方向回读；全局无孤儿不足以判断旧读法是否仍可用。
- 日常维护使用已经走过的路径与向下巡查，按需反查可作局部加速。自动巡查调度尚未实现。

完整规则的既有来源：[分层实现](NOLLM_STORED_SURFACE_IMPLEMENTATION_20261123.md)、[向下维护与重组](NOLLM_TOP_DOWN_MAINTENANCE_AND_REORGANIZATION_20261123.md)、[原生使用](../../lab/nollm-lab/repository_memory/skills/nollm-repository-memory/SKILL.md)。AOCI用于工程回源，语义关系继续由原生覆盖承载。

## 4. 本轮审核与实际测试

对本地用于审核/运行的现存Core、Access、几何、仓库记忆与活跃场文件作了一次固定Git对象核对：306份与源提交一致，无差异。工作目录仍是部分源码快照，未声称完整仓库CI验证。

| 项目 | 本轮实际结果 |
|---|---|
| 既有支撑、变形、有理、adaptive、quantized与相遇集成测试 | 154/154通过，14.522秒 |
| Surface内容读取、写入预算与逐层相遇测试 | 24/24通过，1.253秒 |
| 当前场Surface检查 | 首屏8条完整短判断，398字节；不读取更深层Statement正文 |
| 当前场逐层回读 | 23/23详细表达返回，19条有多个上层入口 |
| 复制场原位修订 | 旧版本可读，原23条详细路径保持 |
| 复制场移动 | 正文/来源保持；复现全局可达仍失去一个旧入口的见证 |
| 复制场保留检查 | 原69份版本文件保留；原始活跃场未被探针改变 |

178项是本轮重新执行的结果。精度审阅中的9项quantized复核属于154项的已含子集，不重复累计。完整向下复制场检查包含空中间格；形成场检查仅证明这份既有短判断通路的实际返回。

本轮测试覆盖当前内部功能基线。跨模型盲测、海量容量吞吐、Windows/OpenClaw Provider Live、全仓CI以及新的五轮性能基准未在本轮执行。现有固定量化库存及原计时结果保留原生成来源，不重报为本轮新性能测量。

## 5. 复现

在版本分支的固定提交打开测试包；其运行时与原始场对应机器清单中的源提交 `f37667bf232360d0c26d37de0639285084230ddc`，新增换锚重放脚本随测试包保存。需要Python3.11+；本轮实测为Linux/Python3.12.14。测试在副本或临时目录中写入。本轮使用仓库中的packages与CLI，未使用另一份已安装的 `scripts/runtime`；更新场文件不会自动更新外部已安装运行时。

```bash
python3 -B lab/nollm-lab/geometry/run_support_deformation_tests.py
python3 -B lab/nollm-lab/repository_memory/check_layered_surface.py \
  --field sujiben/field --output /tmp/nollm-frozen-surface.json
python3 -B lab/nollm-lab/repository_memory/probe_top_down_reorganization.py \
  --field sujiben/field --output /tmp/nollm-frozen-reorganization-new
python3 -B lab/nollm-lab/geometry/probe_adjacent_p8_world_units.py \
  --output /tmp/nollm-frozen-p8-units.json
python3 -B lab/nollm-lab/geometry/probe_quantized_reanchor.py \
  --repo . --output /tmp/nollm-frozen-reanchor.json
```

额外24项测试在仓库根目录执行：

```python
from pathlib import Path
import sys
import unittest

root = Path.cwd()
sys.path[:0] = [str(root / path) for path in (
    "packages/nollm-core/src", "packages/nollm-access/src",
    "lab/nollm-lab/repository_memory", "lab/nollm-lab")]
suite = unittest.TestSuite()
for name in (
    "packages/nollm-access/tests/test_content_budget.py",
    "packages/nollm-access/tests/test_surface_page_content_reads.py",
    "lab/nollm-lab/repository_memory/test_stored_surface_encounter.py",
):
    path = root / name
    suite.addTests(unittest.TestLoader().discover(str(path.parent), pattern=path.name))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
```

重组探针重放已经由Host作出的选择，不是新的语义分类器或模型家族测试。其输出目录须是新目录，以保留原实验。量化基准输入已保存在 `lab/nollm-lab/geometry/results/quantized_structure_benchmark_20261123.json`；后续直接消费原scenario与reference_labels，不重新生成同名输入代替它们。

## 6. 后续从这里继续

本测试版首先固定已有可运行能力和真实研究前沿。低精度下一步是局部p8执行器：相邻层、规范物理锚、长度归一化、完整整数地址与局部余量分离，然后在相同冻结库存上比较标签、份额、压力和实际成本。

局部Core/绑定持久化、真正分页、自动前向维护和多动作重组事务继续分别列为未实现能力。它们的改变应在后续测试版本中记录；无需为了本次固定版本改写当前几何、迁移原场或引入永久反向关系表。
