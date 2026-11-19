# 原生跨物理层几何实验

参考源码：`awdawmip/Nollm` 的
`bafc6de4e8213d50a5ec64754c7bc87983f853ac`。2026-11-19 的本地运行使用
从 GitHub connector 恢复、逐文件 Git blob 一致的该版 Core、Access 和 Lab
源码；没有修改原生包。输出里的 `reference_commit` 标明参考输入，脚本不会
验证传入目录的 Git 版本。换用其他源码时，应按实际运行版本记录结果。

## 复现

从包含此实验和原生包的 Nollm 仓库根运行。输出参数必须明确指定；结果写入仓库外的临时目录：

```bash
python lab/nollm-lab/repository_memory/self_study/essence_20261119/cross_layer_probe.py \
  --source-root . \
  --output /tmp/nollm-essence/cross_layer_probe.json \
  --polygons /tmp/nollm-essence/cross_layer_polygons.json
```

脚本只需要 Python 标准库及仓库原有模块。全部记忆场使用
`TemporaryDirectory`，运行后清除。几何坐标是显式实验条件，文件路径和文本
不参与坐标计算。没有外部 LLM 调用，也没有调用真实用户记忆。

## 本次实测

入口为 `L0(2,-1)`。层号增大表示更细的格，`coverage_up` 到层号减一；
相邻层旋转 22.5°，格边长相差 `beta=2^(1/4)`。原生上行覆盖为：

| 目标 | 96 点采样命中 | Q16 权重 |
|---|---:|---:|
| `L-1(1,0)` | 45 | 30720 |
| `L-1(2,-1)` | 20 | 13653 |
| `L-1(2,0)` | 31 | 21163 |

三条边都由原生 Coverage 算出。已有 Lab 的有理区间程序计算理想面积份额，
已有 72 位 Decimal 世界多边形程序作数值交叉检查。两层多边形和覆盖数值
分别保存在输出 JSON 中。生产权重是采样近似，双向按各自源格面积归一化；
它们不要求数值相同。本样本的上行总变差约 0.0126711，下行约 0.0150456。

### 两条写入路径

1. **Core 几何能力实验**：直接 `CoreRuntime.put` 创建第 `-1、0、1` 三层
   fixture，单入口召回得到上下层和横向路径；重开文件并清 Coverage 缓存后
   结果一致。这里沿用仓库跨层测试的底层种入方式。
2. **当前 Access 写入实验**：用 `capture + apply(AccessDecision)` 正式接口
   在第 0 层放入两个 fixture，`decided_by=fixture`。上层没有 atom，仍实际
   召回 `L0(2,-1) → L-1(2,-1) → L0(3,-3)`，边权为 `13653、2731`，
   得分为 `floor(13653*2731/65536)=568`，Access 返回原文。

当前 `ActiveSemanticWritePolicy` 对新位置和当前修订要求层号 0；实验实际
检查了非零层新建被拒。Core 的多层存取能力与这条活动写入政策分别记录，
不能用底层 fixture 代称 Host 已能正式写入任意物理层。

## 结果解释

- 只存第 0 层也能利用空上层的物理覆盖传播。该样本用两步横向传播同样
  可以到达目标；本实验验证跨层路径可用，没有证明它优于同预算 lateral。
- 混合核中，同层邻居 `L0(3,-1)` 经上去再下来的得分为 11904，高于直接
  lateral 的 10922；Core 保存最高路径得分，不把多条路径的权重相加。
- `beam=1` 的样本只返回入口和一个细层目标，`budget_exhausted=false`。
  当前实现没有把 beam 丢弃的分支计入此标志，不能把 false 当成覆盖完备。
- 只含两个原生 atom 的场，Surface order 0–3 对应 2、5、9、12 个观察格；
  每阶原生 atom 数仍为 2、总质量仍为 131072，canonical 字节和物理占用
  不变。聚合阶是派生观察尺度，稀疏样本的观察格数量未必逐阶减少。
- 原生 recall 结果只保存 kernel 名序列。JSON 的 `witness` 用原生核重放
  该序列，展示一条得分一致的地址路径；存在并列时它不是唯一内部路径的断言。

这是有限几何 fixture 的可复算实验。它没有测量 LLM 语义放置、入口选择或
真实知识问答质量，也没有改变生产 Coverage 契约。
