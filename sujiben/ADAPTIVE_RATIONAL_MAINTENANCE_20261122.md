# 自适应有理几何维护记录

任务日期：2026-11-22。实现来源固定于 `dcd04cc3bbf3f8e42ceda8976033b53791d527ff`。

## 实际消费与原位修订

本轮先用原生 `project encounter` 打开速记本，阅读压力、覆盖精度和变形的 Surface 正文预览；选择实际返回的精度 Surface，再选择该轮显示的物理候选，进入 `[0,-3,-2]`。调用采用 `steps=2, beam=32, limit=20, via=local`，此前共经过两次 Surface 选择。这个有限局部同时给出精度预算、有理几何、变形、压力及几何当前判断；预算耗尽只说明此次观察范围，没有被当作全场召回完整性。

在读取新执行器和固定提交的说明后，使用 `project_memory.decide(..., action="revision")` 在该实际游标现场完成两次原位修订：

- `nollm.precision-budget.v1 → nollm.precision-budget.v2`：保留原固定 Q40/有限库存的精度结论，加入实际逐步整数区间、严格格归属认证、仅未决样本升精度和精确回退。明确 0 位可作为起点、16 位为默认成本选择，以及 24 位只在所测一组输入中最快。
- `nollm.rational-geometry.v1 → nollm.rational-geometry.v2`：区分原 `auto/reference` 和新增 `adaptive`，记录有序共同外层后缀消去、精确世界重锚和端点向外舍入；替换“不同扭转只能执行完整分数链”的过时判断。

本地是已核对的部分源码快照；来源先经连接器发布、回读固定提交，再通过原生 API 的 `sources` 参数保存这些已核实的提交与行号。没有在缺少 Git 仓库的目录中伪造本地提交。

## 回读结果

同一物理入口的原生局部展开已经返回两条 v2 的完整正文、固定来源与 `current=true`；两条 v1 保留可读且不再为当前版本。

- 表达文件由 **42 增至 44**，原有 42 份正文文件字节均保留。
- **21 个绑定**保持原句柄和物理位置，仅上述两个当前表达 ID 更新。
- Core 快照只更新对应两个 Atom 的当前正文；格位置、Atom ID、桥、几何注册和其余材料均保持原值。
- 没有新增桥或概念到物理入口的路由表。临时导航游标在完成读回后删除。

本轮复用已完成的 **145 项整合测试，23.032 秒**，并另行执行上述真实原生写入与同入口读回。没有把部分源码环境表述为全仓库 CI 已通过。

## 固定证据

- [完整设计、证明、API 与实测](https://github.com/awdawmip/Nollm/blob/dcd04cc3bbf3f8e42ceda8976033b53791d527ff/docs/architecture/NOLLM_ADAPTIVE_RATIONAL_EXECUTION_20261122.md)
- [整数区间执行器](https://github.com/awdawmip/Nollm/blob/dcd04cc3bbf3f8e42ceda8976033b53791d527ff/lab/nollm-lab/geometry/adaptive_rational_kernel.py)
- [五轮完整基准及精度统计](https://github.com/awdawmip/Nollm/blob/dcd04cc3bbf3f8e42ceda8976033b53791d527ff/lab/nollm-lab/geometry/results/adaptive_rational_benchmark_20261122.json)
- [独立算术参考测试](https://github.com/awdawmip/Nollm/blob/dcd04cc3bbf3f8e42ceda8976033b53791d527ff/lab/nollm-lab/geometry/tests/test_adaptive_rational_oracle.py)

说明中的性能是指定输入在本地 CPython 的实测；标签保持范围是既有 96 点离散采样合同。长期原理仍为几何原生的多目标覆盖、精确份额和末端输出投影。

