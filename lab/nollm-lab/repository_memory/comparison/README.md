# 当前检查与性能探针

这个目录保留两项仍可独立使用的工具。它们通过现行公开接口检查安装接入或运行时成本；
Nollm 日常开发从[速记本](../../../../sujiben/README.md)进入原生场。

## 宿主发现检查

[check_skill_discovery.py](check_skill_discovery.py) 在临时用户目录和临时空仓库中调用
现行安装器，再读取宿主自己的技能目录。需要本机已安装所选宿主的 CLI。
从 Nollm 仓库根运行：

```sh
python3 lab/nollm-lab/repository_memory/comparison/check_skill_discovery.py codex
```

参数也可选择 `claude`、`copilot`、`opencode`，或一次给出多个宿主。
检查覆盖项目级和用户级发现；它不表示模型已经使用该技能完成开发任务。
安装位置和普通使用方式见 [HOSTS.md](../HOSTS.md)。

## Access 原生召回计时

[time_access_recall.py](time_access_recall.py) 自建临时场：64 个绑定中有 7 个处在指定
局部邻域，然后测量同一进程内的热召回。构场、预热和带检测的调用不计入计时。
从仓库根运行：

```sh
PYTHONPATH=packages/nollm-core/src:packages/nollm-access/src \
  python3 lab/nollm-lab/repository_memory/comparison/time_access_recall.py --rounds 50
```

若比较两个运行时，分别把 `PYTHONPATH` 指向相应检出的 Core/Access，并保持脚本和参数一致。
结果只描述这组临时绑定的 Access 成本，不包含模型用量、CLI 冷启动或完整开发时间。

## 已归档的固定实验

旧三组改动任务、配套评分和复放、固定源码性能比较已移到
`archive/legacy-code-20261122`。以下链接固定到归档锚点
`beaafabfe8dec4ba1c154ecd324954fa81417489`：

- [2026-11-18 三组改动实验、失败与复现](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/comparison/README.md)
- [当时的端到端性能比较](https://github.com/awdawmip/Nollm/blob/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/comparison/FIELD_PERFORMANCE.md)
- [原任务、验收与复放脚本](https://github.com/awdawmip/Nollm/tree/beaafabfe8dec4ba1c154ecd324954fa81417489/lab/nollm-lab/repository_memory/comparison)

复现旧实验时使用该快照的脚本、输入和依赖。它们固定的 `314eb47…` 任务来源及原始失败保持有效；
本目录的两个现用工具不再依赖这些旧实验材料。
