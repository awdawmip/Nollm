# 支撑压力与几何变形：速记本维护 · 2026-11-22

本轮从速记本的已保存预览进入几何局部，随后实现支撑压力、显式多层写入和 Lab 变形计算。实现固定在 [6819d9644e82d0cbb8508ff45eae7e640a7684fc](https://github.com/awdawmip/Nollm/commit/6819d9644e82d0cbb8508ff45eae7e640a7684fc)，[实现说明与 63 项测试](https://github.com/awdawmip/Nollm/blob/6819d9644e82d0cbb8508ff45eae7e640a7684fc/docs/project/NOLLM_SUPPORT_PRESSURE_AND_DEFORMATION_IMPLEMENTATION_20261122.md)记录具体范围。本记录说明源码变化后的原生理解维护，不提供概念到物理入口的路由表。

## 实际观察和决定

开发前，Host 从实际 Surface 的几何预览选择一个物理入口。以 vertical、2 步、beam 16、limit 20 读取几何、架构和 Surface 三条当前理解；结果报告 `budget_exhausted=true`。代码检查与固定源码读取属于后续证据核对，不计为原生发现。

代码提交并回读后，Host 使用 `project_memory.encounter/decide` 的现有入口维护该局部：

| 表达 | 本次决定 | 固定源码依据 |
|---|---|---|
| `nollm.geometry.v1 → nollm.geometry.v2` | 原位修订。普通写入继续默认 L0，同时说明显式多层策略、现场层号保留、incoming-up 的完整候选和固定 Core / Lab 变形边界。 | `write_policy.py`、`project_memory.py`、`incoming_coverage.py` 和固定核源码。 |
| `nollm.pressure.v1` | 在现场显示的空格新增。记录按当前 atom 计数的 1–100 建议压力、份额守恒、未知库存和复用修订不虚增支撑。 | `support_pressure.py`、`incoming_coverage.py` 和现场计数实现。 |
| `nollm.deformation.v1` | 在现场显示的另一空格新增。记录 Q40 跨界余量、被动换锚与实际旋转、保面积径向扭转和候选压力比较的范围。 | `motion.py`、`deformation.py`、`pressure_evaluation.py` 和实现说明。 |

每次终态决定后结束对应游标；后续写入重新从当次 Surface 的已保存几何预览选择入口，并选择该局部实际展示的候选。新表达没有通过对象 ID 查表选择隐藏入口。三条表达共引用 **18 个固定源码窗口**；窗口按上述代码提交读取，保存后正文、来源与 current 状态均已回读核对。原生场的既有保存、绑定与 Core 状态接口执行了全部写入，没有直接替换场 JSON。

本次只维护被代码变化影响的几何理解及两个新命题。其他 current 表达继续保留原来的来源版本。速记本里的知识条目仍置于 L0；真实 L1/L2 写入和压力反馈已经在该实现的临时场测试中验证，本次知识维护不冒充一次真实研究材料的多层语义效果实验。

## 维护后回读

保留本轮已经选定的单一物理入口，以 local、1 步、beam 32、limit 20 回读。几何 v2 在入口返回，压力与变形两条新理解均沿 `lateral` 返回，架构和 Surface 两条原有理解也返回。该次结果仍报告 `budget_exhausted=true`；这里核对的是已维护的局部，不声称观察了全场。

| 项目 | 维护前 | 维护后 |
|---|---:|---:|
| 当前判断 / atom | 16 | 18 |
| 表达版本 | 35 | 38 |
| L0 占用格 | 14 | 16 |
| 原生有向桥 | 2 | 2 |

原有 35 个表达文件逐字保留。几何旧版仍可读且 `current=false`，新版 `current=true` 并继承同一 handle；其他 15 个绑定保持不变。两个新增 atom 来自两个不同新命题。两条原有桥逐项不变，本轮没有新增桥，回读也没有启用 bridge 核。三个新版本的保存正文和来源与 Host 提交内容相同，临时游标已清除。

这是形成者对实际源码变化的局部维护与回读，不是独立新读者盲测，也不证明任意默认预算下都能发现这些理解。后续开发继续从速记本的实际预览进入，并以新任务需要核对固定证据。
