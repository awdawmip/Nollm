# 接受量化结构差异的维护记录

任务日期：2026-11-23。实现、实验与说明来源固定于 `0e98a79584349bf5f236b9e3262c470d62d8ae0e`。

## 本轮判断

用户允许低精度下偶发的关系缺项成为工作结构，运行时不主动修正，询问成本合适的精度。本轮在 Lab 新增显式 `mode="quantized"`，执行一次固定精度舍入，最终默认保留 12 个二进小数位。8 位作为接受约 1.1%–1.3% 结构差异的速度档，10–12 位是本次平衡区。

这一判断与此前精确执行的适用目标不同，故新增独立表达 `nollm.quantized-structure.v1`，保留 `nollm.precision-budget.v2` 和 `nollm.rational-geometry.v2` 的当前绑定。新表达说明固定精度关系的定义、96 个命中仍完整分配、确定性缺项与随机遗忘的区别、分层误差集中、五轮时间与压力取舍，以及有限实验不证明普遍最优。

## 实际相遇与放置

本轮实际执行原生 `project encounter`，先阅读压力、覆盖精度与变形的 Surface 正文预览，再选择本轮返回的精度 Surface 与物理候选，进入 `[0,-3,-2]`。之后沿同一入口显式使用 `steps=2, beam=32, limit=20, via=local`，读取已有精度、有理几何、变形、压力及几何判断。

新表达通过 `project_memory.decide(..., action="new")` 放入此次局部已显示的空格 `[0,-3,-3]`，与精度预算判断相邻。语义位置由 Host 根据实际读到的内容选择；没有建立概念到入口的路由表。

本地是已核对的部分源码快照。先将实现与完整实验发布到主干并回读，再以固定提交的真实说明窗口写入 `sources`。该原生 API 允许直接接收已核实的来源引用；没有在缺少 Git 仓库的目录里伪造提交。

## 实际回读与保留检查

同一物理入口的原生局部展开已返回新表达完整正文、固定来源和 `current=true`，临时导航游标随后删除。

- 表达文件 **44 → 45**；原有 44 份文件字节均保留。
- 绑定 **21 → 22**；原有 21 个绑定逐项保持原值。
- Core 新增一个格内 Atom；原有所有格与 Atom、桥及几何注册均保持原值。
- 本轮不新增桥。当前工作场依旧以实际占用和原生几何关系展开。

实现最终运行 **154 项整合测试，22.687 秒**；本轮另行执行上述真实原生写入与同入口回读。基准主组与第二组各含 192 源格、18,432 个标签，均完成五轮交错计时；主组全扫 2–16、20、24、32 位，第二组复核 6、8、10、12、16、24 位。单列控制与临界探针完整保留。

## 固定证据

- [合同、实验设计、全精度表与选择依据](https://github.com/awdawmip/Nollm/blob/0e98a79584349bf5f236b9e3262c470d62d8ae0e/docs/architecture/NOLLM_QUANTIZED_STRUCTURE_TRADEOFF_20261123.md)
- [单次定点执行器](https://github.com/awdawmip/Nollm/blob/0e98a79584349bf5f236b9e3262c470d62d8ae0e/lab/nollm-lab/geometry/quantized_rational_kernel.py)
- [全部参数、标签、计时顺序与五轮时长](https://github.com/awdawmip/Nollm/blob/0e98a79584349bf5f236b9e3262c470d62d8ae0e/lab/nollm-lab/geometry/results/quantized_structure_benchmark_20261123.json)
- [独立舍入调度、接受缺项与公共 API 测试](https://github.com/awdawmip/Nollm/blob/0e98a79584349bf5f236b9e3262c470d62d8ae0e/lab/nollm-lab/geometry/tests/test_quantized_rational.py)

本轮实测对象是 Python Lab 中的离散采样结构、份额、压力与候选选择。固定小数位本身不能保证每个局部的错误比例相同；语义召回是否受益仍需具体任务数据回答。
